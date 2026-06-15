"""Experimental ChatGPT Codex OAuth chat backend.

This backend is intentionally separate from the normal OpenAI API-key path.
It reads an existing Hermes/OpenAI-Codex OAuth token and calls the Codex
Responses endpoint for answer generation only. Embeddings still use the normal
OpenAI API-key path because Codex OAuth does not provide embeddings here.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable

from openai import OpenAI


DEFAULT_CODEX_BASE_URL = "https://chatgpt.com/backend-api/codex"
DEFAULT_CODEX_REASONING_EFFORT = "xhigh"
DEFAULT_CODEX_FALLBACK_MODELS = ("gpt-5.4",)


class CodexOAuthError(RuntimeError):
    """Raised when the experimental Codex OAuth backend cannot be used."""


def _default_auth_file() -> Path:
    return Path(os.path.expanduser(os.getenv("WESS_CODEX_AUTH_FILE", "~/.hermes/auth.json")))


def _dig(data: dict[str, Any], *keys: str) -> Any:
    cur: Any = data
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def load_codex_access_token(auth_file: str | os.PathLike[str] | None = None) -> str:
    """Load an access token from Hermes' OpenAI Codex OAuth auth file.

    Supported locations match current Hermes auth.json shapes:
    - providers.openai-codex.tokens.access_token
    - credential_pool.openai-codex[0].access_token
    """
    path = Path(auth_file).expanduser() if auth_file else _default_auth_file()
    if not path.exists():
        raise CodexOAuthError(
            f"Codex OAuth auth file not found: {path}. Run `hermes auth add openai-codex` on this host first."
        )

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - exact JSON errors vary
        raise CodexOAuthError(f"Failed to read Codex OAuth auth file {path}: {exc}") from exc

    token = _dig(data, "providers", "openai-codex", "tokens", "access_token")
    if not token:
        pool = _dig(data, "credential_pool", "openai-codex")
        if isinstance(pool, list):
            for item in pool:
                if isinstance(item, dict) and item.get("access_token"):
                    token = item["access_token"]
                    break

    if not isinstance(token, str) or not token.strip():
        raise CodexOAuthError(
            f"OpenAI Codex OAuth access token not found in {path}. Re-login with `hermes auth add openai-codex`."
        )
    return token.strip()


def _text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if not isinstance(item, dict):
                continue
            item_type = item.get("type")
            if item_type == "text":
                parts.append(str(item.get("text") or ""))
            elif item_type == "image_url":
                raise CodexOAuthError(
                    "Codex OAuth experimental backend currently supports text answers only. "
                    "Use WESS_CHAT_PROVIDER=openai for image analysis."
                )
        return "\n".join(part for part in parts if part)
    return str(content or "")


def messages_to_codex_payload(messages: list[dict[str, Any]]) -> tuple[str, list[dict[str, str]]]:
    """Convert Chat Completions-style messages to Codex Responses input."""
    instructions = ""
    input_items: list[dict[str, str]] = []
    for msg in messages:
        role = str(msg.get("role") or "user")
        text = _text_from_content(msg.get("content"))
        if not text:
            continue
        if role == "system" and not instructions:
            instructions = text
            continue
        if role not in {"user", "assistant"}:
            role = "user"
        input_items.append({"role": role, "content": text})
    if not input_items:
        raise CodexOAuthError("No user/assistant input messages to send to Codex OAuth backend.")
    return instructions, input_items


def _fake_chat_stream_chunk(text: str) -> SimpleNamespace:
    """Return a minimal chat.completions-like chunk used by app.py/api.py."""
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text))])


def _parse_model_list(value: str | None) -> tuple[str, ...]:
    if value is None:
        return DEFAULT_CODEX_FALLBACK_MODELS
    return tuple(item.strip() for item in value.split(",") if item.strip())


def is_usage_limit_error(exc: BaseException) -> bool:
    text = str(exc).lower()
    return "usage_limit_reached" in text or "rate limit" in text or "429" in text


class CodexOAuthChatClient:
    """Small adapter around ChatGPT Codex OAuth Responses streaming."""

    def __init__(
        self,
        *,
        auth_file: str | None = None,
        base_url: str | None = None,
        reasoning_effort: str | None = None,
        fallback_models: tuple[str, ...] | None = None,
    ) -> None:
        self.auth_file = auth_file
        self.base_url = base_url or os.getenv("WESS_CODEX_BASE_URL", DEFAULT_CODEX_BASE_URL)
        self.reasoning_effort = (reasoning_effort or os.getenv("WESS_CODEX_REASONING_EFFORT", DEFAULT_CODEX_REASONING_EFFORT)).strip().lower()
        self.fallback_models = fallback_models if fallback_models is not None else _parse_model_list(os.getenv("WESS_CODEX_FALLBACK_MODELS"))

    def _client(self) -> OpenAI:
        # Load on every request so a refreshed Hermes token is picked up without restarting the app.
        token = load_codex_access_token(self.auth_file)
        return OpenAI(api_key=token, base_url=self.base_url)

    def _candidate_models(self, model: str) -> tuple[str, ...]:
        seen: set[str] = set()
        ordered: list[str] = []
        for item in (model, *self.fallback_models):
            if item and item not in seen:
                seen.add(item)
                ordered.append(item)
        return tuple(ordered)

    def stream_chat(self, *, model: str, messages: list[dict[str, Any]]) -> Iterable[SimpleNamespace]:
        instructions, input_items = messages_to_codex_payload(messages)
        last_error: Exception | None = None
        for candidate_model in self._candidate_models(model):
            try:
                stream = self._client().responses.create(
                    model=candidate_model,
                    instructions=instructions or "Answer helpfully and follow the user's requested language.",
                    input=input_items,
                    store=False,
                    include=[],
                    stream=True,
                    reasoning={"effort": self.reasoning_effort, "summary": "auto"},
                )
                for event in stream:
                    if getattr(event, "type", "") == "response.output_text.delta":
                        delta = getattr(event, "delta", "") or ""
                        if delta:
                            yield _fake_chat_stream_chunk(delta)
                return
            except Exception as exc:
                last_error = exc
                if is_usage_limit_error(exc) and candidate_model != self._candidate_models(model)[-1]:
                    continue
                break
        raise CodexOAuthError(
            "Codex OAuth chat request failed after trying "
            f"{', '.join(self._candidate_models(model))}. If the token expired, run `hermes auth reset openai-codex` "
            "or `hermes auth add openai-codex` on this host. Original error: "
            f"{last_error}"
        ) from last_error

    def complete_chat(self, *, model: str, messages: list[dict[str, Any]]) -> str:
        return "".join(
            chunk.choices[0].delta.content or ""
            for chunk in self.stream_chat(model=model, messages=messages)
        )
