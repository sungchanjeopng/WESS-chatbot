"""Keyword/BM25 retrieval that works without embeddings or OpenAI API access."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import math
import re
from typing import Iterable, Sequence

from .ingest import SourceGroup, chunk_text, default_source_groups, extract_text, iter_source_files
from .products import PRODUCTS

TOKEN_RE = re.compile(r"[A-Za-z0-9가-힣%/.-]{2,}")


@dataclass(frozen=True)
class IndexedChunk:
    product: str
    collection: str
    document: str
    source: str
    chunk_index: int
    term_counts: Counter[str]
    length: int


class FtsRetriever:
    """Load bundled docs into an in-memory BM25 index."""

    def __init__(
        self,
        *,
        source_groups: Sequence[SourceGroup] | None = None,
        chunk_size: int = 900,
        overlap: int = 120,
    ) -> None:
        self.source_groups = list(source_groups or default_source_groups())
        self.chunk_size = chunk_size
        self.overlap = overlap
        self._chunks: list[IndexedChunk] = []
        self._doc_freq: dict[str, int] = defaultdict(int)
        self._products: dict[str, dict[str, object]] = {}
        self._avg_doc_length = 0.0
        self._build_index()

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [match.group(0).lower() for match in TOKEN_RE.finditer(text or "")]

    @classmethod
    def _keyword_score(cls, query: str, document: str, source: str) -> int:
        haystack = f"{source}\n{document}".lower()
        return sum(1 for token in set(cls._tokenize(query)) if token in haystack)

    def _build_index(self) -> None:
        chunks: list[IndexedChunk] = []
        doc_freq: dict[str, int] = defaultdict(int)
        products: dict[str, dict[str, object]] = {}

        for group in self.source_groups:
            files = iter_source_files(group.paths)
            product_chunks = 0
            for path in files:
                text = extract_text(path)
                for chunk_index, document in enumerate(chunk_text(text, chunk_size=self.chunk_size, overlap=self.overlap)):
                    tokens = self._tokenize(document)
                    term_counts = Counter(tokens)
                    indexed = IndexedChunk(
                        product=group.product,
                        collection=group.collection,
                        document=document,
                        source=path.name,
                        chunk_index=chunk_index,
                        term_counts=term_counts,
                        length=max(len(tokens), 1),
                    )
                    chunks.append(indexed)
                    product_chunks += 1
                    for term in term_counts:
                        doc_freq[term] += 1
            products[group.product] = {
                "collection": group.collection,
                "ready": product_chunks > 0,
                "count": product_chunks,
            }

        self._chunks = chunks
        self._doc_freq = dict(doc_freq)
        self._products = products
        if chunks:
            self._avg_doc_length = sum(chunk.length for chunk in chunks) / len(chunks)
        else:
            self._avg_doc_length = 0.0

    def health(self) -> dict[str, object]:
        return {
            "status": "ok" if any(info.get("ready") for info in self._products.values()) else "degraded",
            "provider": "fts",
            "products": self._products,
        }

    def _bm25_score(self, query_terms: Iterable[str], chunk: IndexedChunk) -> float:
        if not self._chunks or not self._avg_doc_length:
            return 0.0
        k1 = 1.5
        b = 0.75
        score = 0.0
        total_docs = len(self._chunks)
        for term in query_terms:
            freq = chunk.term_counts.get(term)
            if not freq:
                continue
            df = self._doc_freq.get(term, 0)
            idf = math.log(1.0 + ((total_docs - df + 0.5) / (df + 0.5)))
            denom = freq + k1 * (1.0 - b + b * (chunk.length / self._avg_doc_length))
            score += idf * ((freq * (k1 + 1.0)) / denom)
        return score

    def query(self, query: str, *, product_keys: Sequence[str], n_results: int):
        from .rag import RetrievedChunk

        requested_products = {key for key in product_keys if key in PRODUCTS or key in self._products}
        query_terms = self._tokenize(query)
        scored: list[RetrievedChunk] = []

        for chunk in self._chunks:
            if requested_products and chunk.product not in requested_products:
                continue
            bm25 = self._bm25_score(query_terms, chunk)
            keyword_score = self._keyword_score(query, chunk.document, chunk.source)
            combined = bm25 + (keyword_score * 0.12)
            if combined <= 0:
                continue
            scored.append(
                RetrievedChunk(
                    product=chunk.product,
                    collection=chunk.collection,
                    document=chunk.document,
                    source=chunk.source,
                    chunk_index=chunk.chunk_index,
                    distance=None,
                    keyword_score=keyword_score,
                    combined_score=combined,
                )
            )

        scored.sort(key=lambda item: (item.combined_score, item.keyword_score, item.product), reverse=True)
        return scored[:n_results]
