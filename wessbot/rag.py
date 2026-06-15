"""RAG retrieval and OpenAI chat orchestration for WESS chatbot."""
from __future__ import annotations

from dataclasses import dataclass, asdict
import math
import os
import re
from typing import Any, Iterable, Optional

import chromadb
from openai import OpenAI

from .codex_oauth import CodexOAuthChatClient, CodexOAuthError, is_usage_limit_error
from .config import (
    CHROMA_DIR,
    DEFAULT_CHAT_MODEL,
    DEFAULT_CHAT_PROVIDER,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_N_RESULTS,
    MAX_CONTEXT_CHARS,
    MAX_HISTORY_MESSAGES,
    normalize_language,
)
from .products import PRODUCTS, detect_product, normalize_product
from .prompts import (
    build_clarification_hint,
    build_low_evidence_message,
    build_product_conflict_message,
    build_system_prompt,
)


# Short questions without any product/term signal are usually follow-ups
# ("그건 어떻게 설정해?") and embed poorly on their own.
FOLLOWUP_MAX_CHARS = 40
FOLLOWUP_HISTORY_TURNS = 2

IMAGE_ANALYSIS_INSTRUCTION = (
    "If the image is a WESS waveform/screen capture, inspect the visible waveform, threshold line, "
    "measurement bar, peaks, noise, and displayed values. For ENV120 waveform screens, interpret the "
    "upper-left value as measurement range and Empty; it is absolutely not the live measurement value. "
    "Interpret the upper-right value as Threshold/문턱전압. "
    "Empty is a fixed site/configuration reference and does not change during normal waveform viewing "
    "unless the Empty setting is intentionally changed. The lower-left and lower-right label rule is fixed: "
    "if either label is D, interpret it as Distance/거리, the distance from the sensor to the interface; "
    "if either label is S, interpret it as Sludge Level/슬러지 레벨, the sludge height. "
    "Do not confuse D with sludge level or S with distance. If glare, reflection, blur, or poor image quality "
    "makes the D/S label unreadable but Empty and one lower value are legible, you may make a conditional guess "
    "using the fixed formula Sludge Level = Empty - Distance. State the assumption clearly, e.g. if the visible value "
    "is Distance then Sludge Level is Empty minus Distance, or if the visible value is Sludge Level then Distance is "
    "Empty minus Sludge Level. If the needed numbers are not legible, say the label/value cannot be determined. "
    "Do not invent unreadable numbers; say when a value is not legible. Give practical field "
    "interpretation and next checks."
)


@dataclass
class RetrievedChunk:
    product: str
    collection: str
    document: str
    source: str
    chunk_index: int | str | None
    distance: float | None
    keyword_score: int
    combined_score: float

    def to_public_dict(self) -> dict[str, Any]:
        data = asdict(self)
        # Do not expose raw full document text by default through the public API.
        data.pop("document", None)
        return data


@dataclass
class RetrievalResult:
    product: str
    selected_product: str
    detected_product: str
    product_conflict: bool
    chunks: list[RetrievedChunk]
    low_evidence: bool
    score_by_product: dict[str, int]

    def context_text(self, max_chars: int = MAX_CONTEXT_CHARS) -> str:
        parts: list[str] = []
        total = 0
        for idx, chunk in enumerate(self.chunks, start=1):
            header = f"[Source {idx}: {chunk.product} / {chunk.source} / chunk {chunk.chunk_index}]\n"
            doc = (chunk.document or "").strip()
            text = header + doc
            if total + len(text) > max_chars:
                break
            parts.append(text)
            total += len(text)
        return "\n\n---\n\n".join(parts)

    def retrieval_summary(self) -> str:
        if not self.chunks:
            return "No relevant chunks retrieved."
        lines = []
        for idx, c in enumerate(self.chunks[:8], start=1):
            dist = "" if c.distance is None else f", distance={c.distance:.4f}"
            lines.append(f"{idx}. {c.product} / {c.source} / chunk={c.chunk_index}{dist}, keyword_score={c.keyword_score}")
        return "\n".join(lines)

    def public_sources(self, limit: int = 6) -> list[dict[str, Any]]:
        return [c.to_public_dict() for c in self.chunks[:limit]]


class WessRagEngine:
    """Shared WESS RAG engine used by Streamlit UI and Flask API."""

    def __init__(
        self,
        *,
        chroma_dir: str | os.PathLike[str] = CHROMA_DIR,
        openai_client: Optional[OpenAI] = None,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    ) -> None:
        self.chroma_dir = str(chroma_dir)
        self.openai_client = openai_client or (OpenAI() if os.getenv("OPENAI_API_KEY") else None)
        self.chat_provider = DEFAULT_CHAT_PROVIDER
        self.codex_chat_client = CodexOAuthChatClient() if self.chat_provider in {"codex-oauth", "openai-codex", "codex"} else None
        self.embedding_model = embedding_model
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_dir)
        self.collections = self._load_collections()

    def _load_collections(self) -> dict[str, Any | None]:
        collections: dict[str, Any | None] = {}
        for key, spec in PRODUCTS.items():
            try:
                collections[key] = self.chroma_client.get_collection(spec.collection)
            except Exception:
                collections[key] = None
        return collections

    def _client(self) -> OpenAI:
        if self.openai_client is None:
            raise RuntimeError("OPENAI_API_KEY is not configured. Set it in .env or Streamlit secrets before asking questions.")
        return self.openai_client

    def health(self) -> dict[str, Any]:
        products: dict[str, Any] = {}
        for key, spec in PRODUCTS.items():
            col = self.collections.get(key)
            count = None
            ready = col is not None
            if col is not None:
                try:
                    count = col.count()
                except Exception:
                    ready = False
            products[key] = {
                "collection": spec.collection,
                "ready": ready,
                "count": count,
            }
        return {
            "status": "ok" if any(p["ready"] for p in products.values()) else "degraded",
            "chroma_dir": self.chroma_dir,
            "openai_ready": self.openai_client is not None,
            "chat_provider": self.chat_provider,
            "codex_oauth_ready": self.codex_chat_client is not None,
            "embedding_model": self.embedding_model,
            "products": products,
        }

    def embed(self, text: str) -> list[float]:
        response = self._client().embeddings.create(model=self.embedding_model, input=text)
        return response.data[0].embedding

    @staticmethod
    def is_followup_question(question: str) -> bool:
        """True when the question is short and carries no product/term signal of its own."""
        q = (question or "").strip()
        if not q or len(q) > FOLLOWUP_MAX_CHARS:
            return False
        _, _, scores = detect_product(q, "auto")
        return max(scores.values()) <= 0

    @classmethod
    def build_search_query(cls, question: str, history: Optional[list[dict[str, str]]]) -> str:
        """Augment follow-up questions with recent user turns so retrieval keeps the topic."""
        if not history or not cls.is_followup_question(question):
            return question
        prev_user = [
            (m.get("content") or "").strip()
            for m in history
            if m.get("role") == "user" and (m.get("content") or "").strip()
        ]
        prev_user = [m for m in prev_user if m != question]
        if not prev_user:
            return question
        context = "\n".join(prev_user[-FOLLOWUP_HISTORY_TURNS:])
        return f"{context}\n{question}"

    @staticmethod
    def _keyword_terms(query: str) -> set[str]:
        tokens = set(re.findall(r"[A-Za-z0-9가-힣%/.-]{2,}", query.lower()))
        important = {
            "eea", "agc", "profile", "threshold", "echo", "amp", "asf", "relay", "r1", "r2",
            "4-20ma", "calibration", "density", "interface", "농도", "계면", "문턱전압", "수신감도",
            "릴레이", "출력", "보정", "설정", "배선", "센서", "측정", "오류", "에러",
        }
        return tokens | {t for t in important if t in query.lower()}

    @classmethod
    def _keyword_score(cls, query: str, document: str, source: str) -> int:
        hay = f"{source}\n{document}".lower()
        return sum(1 for t in cls._keyword_terms(query) if t and t.lower() in hay)

    @staticmethod
    def _distance_score(distance: float | None) -> float:
        if distance is None:
            return 0.0
        if math.isnan(distance):
            return 0.0
        return max(0.0, 1.0 - float(distance))

    def _query_collection(self, product_key: str, query: str, query_embedding: list[float], n_results: int) -> list[RetrievedChunk]:
        collection = self.collections.get(product_key)
        if collection is None:
            return []
        spec = PRODUCTS[product_key]
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            return []

        docs = (results.get("documents") or [[]])[0]
        metas = (results.get("metadatas") or [[]])[0]
        distances = (results.get("distances") or [[]])[0]
        chunks: list[RetrievedChunk] = []
        for doc, meta, dist in zip(docs, metas, distances):
            meta = meta or {}
            source = str(meta.get("source") or "unknown")
            chunk_index = meta.get("chunk_index")
            kw = self._keyword_score(query, doc or "", source)
            combined = self._distance_score(dist) + (kw * 0.08)
            chunks.append(
                RetrievedChunk(
                    product=product_key,
                    collection=spec.collection,
                    document=doc or "",
                    source=source,
                    chunk_index=chunk_index,
                    distance=float(dist) if dist is not None else None,
                    keyword_score=kw,
                    combined_score=combined,
                )
            )
        return chunks

    @staticmethod
    def _dedupe_chunks(chunks: Iterable[RetrievedChunk]) -> list[RetrievedChunk]:
        seen: set[tuple[str, str, str]] = set()
        out: list[RetrievedChunk] = []
        for c in sorted(chunks, key=lambda x: x.combined_score, reverse=True):
            # Dedupe by product/source/document prefix to reduce repeated neighboring chunks.
            key = (c.product, c.source, (c.document or "")[:180])
            if key in seen:
                continue
            seen.add(key)
            out.append(c)
        return out

    def retrieve(
        self,
        question: str,
        *,
        product: str = "auto",
        n_results: int = DEFAULT_N_RESULTS,
        history: Optional[list[dict[str, str]]] = None,
    ) -> RetrievalResult:
        selected = normalize_product(product, default="auto")
        detected, conflict, scores = detect_product(question, selected)
        search_query = self.build_search_query(question, history)
        if selected == "auto" and search_query != question and scores.get(detected, 0) <= 0:
            # Follow-up without its own product signal: inherit the product from recent turns.
            detected, _, scores = detect_product(search_query, "auto")
            conflict = False
        query_embedding = self.embed(search_query)

        if selected == "auto":
            target_products = list(PRODUCTS.keys())
        else:
            target_products = [detected if conflict else selected]

        chunks: list[RetrievedChunk] = []
        per_product_n = max(4, n_results if len(target_products) == 1 else max(6, n_results // len(target_products)))
        for key in target_products:
            chunks.extend(self._query_collection(key, search_query, query_embedding, per_product_n))

        ranked = self._dedupe_chunks(chunks)[:n_results]
        low_evidence = not ranked or (ranked[0].combined_score < 0.28 and ranked[0].keyword_score == 0)
        answer_product = detected if detected in PRODUCTS else (selected if selected in PRODUCTS else "ENV200")
        return RetrievalResult(
            product=answer_product,
            selected_product=selected,
            detected_product=detected,
            product_conflict=conflict,
            chunks=ranked,
            low_evidence=low_evidence,
            score_by_product=scores,
        )

    def build_messages(
        self,
        question: str,
        retrieval: RetrievalResult,
        *,
        language: str = "한국어",
        history: Optional[list[dict[str, str]]] = None,
    ) -> list[dict[str, str]]:
        lang = normalize_language(language)
        if retrieval.product_conflict and retrieval.selected_product in PRODUCTS:
            prompt = build_system_prompt(retrieval.product, retrieval.context_text(), lang, retrieval_summary=retrieval.retrieval_summary())
            user_question = build_product_conflict_message(retrieval.selected_product, retrieval.detected_product, lang)
        elif retrieval.low_evidence:
            prompt = build_system_prompt(retrieval.product, retrieval.context_text(), lang, retrieval_summary=retrieval.retrieval_summary())
            user_question = question + "\n\n" + build_low_evidence_message(retrieval.product, lang)
        else:
            prompt = build_system_prompt(retrieval.product, retrieval.context_text(), lang, retrieval_summary=retrieval.retrieval_summary())
            user_question = question + build_clarification_hint(question, retrieval.product, lang)

        messages = [{"role": "system", "content": prompt}]
        for msg in (history or [])[-MAX_HISTORY_MESSAGES:]:
            role = msg.get("role")
            content = (msg.get("content") or "").strip()
            if role in {"user", "assistant"} and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_question})
        return messages

    @staticmethod
    def _chat_kwargs(model: str, messages: list[dict[str, Any]], temperature: float, *, stream: bool = False) -> dict[str, Any]:
        """Build chat.completions kwargs while avoiding unsupported model parameters."""
        kwargs: dict[str, Any] = {"model": model, "messages": messages}
        # GPT-5.5 currently accepts only temperature=1 on chat.completions.
        # Keep it explicit so the runtime configuration is visible and stable.
        kwargs["temperature"] = 1 if str(model).startswith("gpt-5.5") else temperature
        if stream:
            kwargs["stream"] = True
        return kwargs

    def _use_codex_oauth_chat(self) -> bool:
        return self.codex_chat_client is not None

    def _complete_openai_chat(self, model: str, messages: list[dict[str, Any]], temperature: float) -> str:
        response = self._client().chat.completions.create(
            **self._chat_kwargs(model, messages, temperature)
        )
        return response.choices[0].message.content or ""

    def _stream_openai_chat(self, model: str, messages: list[dict[str, Any]], temperature: float):
        return self._client().chat.completions.create(
            **self._chat_kwargs(model, messages, temperature, stream=True)
        )

    def _complete_chat(self, model: str, messages: list[dict[str, Any]], temperature: float) -> str:
        if self._use_codex_oauth_chat():
            try:
                return self.codex_chat_client.complete_chat(model=model, messages=messages)  # type: ignore[union-attr]
            except CodexOAuthError as exc:
                if self.openai_client is not None and is_usage_limit_error(exc):
                    return self._complete_openai_chat(model, messages, temperature)
                raise
        return self._complete_openai_chat(model, messages, temperature)

    def _stream_codex_then_openai_chat(self, model: str, messages: list[dict[str, Any]], temperature: float):
        try:
            yield from self.codex_chat_client.stream_chat(model=model, messages=messages)  # type: ignore[union-attr]
        except CodexOAuthError as exc:
            if self.openai_client is not None and is_usage_limit_error(exc):
                yield from self._stream_openai_chat(model, messages, temperature)
                return
            raise

    def _stream_chat(self, model: str, messages: list[dict[str, Any]], temperature: float):
        if self._use_codex_oauth_chat():
            return self._stream_codex_then_openai_chat(model, messages, temperature)
        return self._stream_openai_chat(model, messages, temperature)

    def answer_once(
        self,
        question: str,
        *,
        product: str = "auto",
        language: str = "한국어",
        history: Optional[list[dict[str, str]]] = None,
        model: str = DEFAULT_CHAT_MODEL,
        temperature: float = 1.0,
    ) -> tuple[str, RetrievalResult]:
        retrieval = self.retrieve(question, product=product, history=history)
        messages = self.build_messages(question, retrieval, language=language, history=history)
        return self._complete_chat(model, messages, temperature), retrieval

    def answer_once_with_images(
        self,
        question: str,
        image_data_urls: list[str],
        *,
        product: str = "auto",
        language: str = "한국어",
        history: Optional[list[dict[str, str]]] = None,
        model: str = DEFAULT_CHAT_MODEL,
        temperature: float = 1.0,
    ) -> tuple[str, RetrievalResult]:
        """Answer one question with attached waveform/screen images."""
        retrieval = self.retrieve(question, product=product, history=history)
        messages = self.build_messages(question, retrieval, language=language, history=history)
        text = messages[-1]["content"]
        messages[-1]["content"] = [
            {
                "type": "text",
                "text": (
                    text
                    + "\n\n[Attached image analysis instruction]\n"
                    + IMAGE_ANALYSIS_INSTRUCTION
                ),
            },
            *({"type": "image_url", "image_url": {"url": url}} for url in image_data_urls[:4]),
        ]
        return self._complete_chat(model, messages, temperature), retrieval

    def answer_stream(
        self,
        question: str,
        *,
        product: str = "auto",
        language: str = "한국어",
        history: Optional[list[dict[str, str]]] = None,
        model: str = DEFAULT_CHAT_MODEL,
        temperature: float = 1.0,
    ):
        retrieval = self.retrieve(question, product=product, history=history)
        messages = self.build_messages(question, retrieval, language=language, history=history)
        stream = self._stream_chat(model, messages, temperature)
        return stream, retrieval
