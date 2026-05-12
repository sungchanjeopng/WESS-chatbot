"""WESS chatbot REST API for mobile apps and external clients."""
from __future__ import annotations

import json
import os
from typing import Any

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request, stream_with_context

load_dotenv()

from wessbot.config import DEFAULT_CHAT_MODEL, normalize_language
from wessbot.products import PRODUCTS, normalize_product
from wessbot.rag import WessRagEngine

app = Flask(__name__)
engine: WessRagEngine | None = None


def init() -> WessRagEngine:
    """Initialize shared RAG engine once."""
    global engine
    if engine is None:
        engine = WessRagEngine()
    return engine


@app.after_request
def add_cors_headers(response):
    """Small no-dependency CORS support for mobile/web clients.

    Limit allowed origins in production by setting CORS_ALLOW_ORIGIN.
    """
    origin = os.getenv("CORS_ALLOW_ORIGIN", "*")
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-API-Key"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


def _check_api_key() -> tuple[bool, Any]:
    expected = os.getenv("WESS_API_KEY")
    if not expected:
        return True, None
    supplied = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if supplied == expected:
        return True, None
    return False, jsonify({"error": "Unauthorized"})


def _json_body() -> dict[str, Any] | tuple[Any, int]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "No JSON body"}), 400
    return data


def _safe_history(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, str]] = []
    for msg in value[-20:]:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        content = msg.get("content")
        if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
            out.append({"role": role, "content": content.strip()})
    return out


@app.route("/api/health", methods=["GET"])
def health():
    try:
        e = init()
        return jsonify(e.health())
    except Exception as exc:
        return jsonify({"status": "error", "error": str(exc)}), 500


@app.route("/api/products", methods=["GET"])
def products():
    e = init()
    health_data = e.health()["products"]
    return jsonify(
        {
            "products": [
                {
                    "key": spec.key,
                    "api_key": spec.api_key,
                    "display_name": spec.display_name,
                    "collection": spec.collection,
                    "ready": health_data.get(key, {}).get("ready", False),
                    "count": health_data.get(key, {}).get("count"),
                    "sample_questions": list(spec.sample_questions),
                }
                for key, spec in PRODUCTS.items()
            ],
            "aliases": {"density": "ENV200", "interface": "ENV130", "interface_120": "ENV120", "auto": "auto"},
        }
    )


@app.route("/api/chat", methods=["OPTIONS"])
@app.route("/api/chat/stream", methods=["OPTIONS"])
def options():
    return ("", 204)


@app.route("/api/chat", methods=["POST"])
def chat():
    ok, error = _check_api_key()
    if not ok:
        return error, 401
    data = _json_body()
    if isinstance(data, tuple):
        return data

    question = str(data.get("question", "")).strip()
    if not question:
        return jsonify({"error": "Empty question"}), 400

    product = normalize_product(data.get("product", "auto"), default="auto")
    language = normalize_language(data.get("language") or data.get("lang") or "ko")
    history = _safe_history(data.get("history", []))
    model = str(data.get("model") or DEFAULT_CHAT_MODEL)

    try:
        e = init()
        answer, retrieval = e.answer_once(
            question,
            product=product,
            language=language,
            history=history,
            model=model,
        )
        return jsonify(
            {
                "answer": answer,
                "product": retrieval.product,
                "selected_product": retrieval.selected_product,
                "detected_product": retrieval.detected_product,
                "product_conflict": retrieval.product_conflict,
                "low_evidence": retrieval.low_evidence,
                "sources": retrieval.public_sources(),
            }
        )
    except Exception as exc:
        return jsonify({"error": "Answer generation failed", "detail": str(exc)}), 500


@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    ok, error = _check_api_key()
    if not ok:
        return error, 401
    data = _json_body()
    if isinstance(data, tuple):
        return data

    question = str(data.get("question", "")).strip()
    if not question:
        return jsonify({"error": "Empty question"}), 400

    product = normalize_product(data.get("product", "auto"), default="auto")
    language = normalize_language(data.get("language") or data.get("lang") or "ko")
    history = _safe_history(data.get("history", []))
    model = str(data.get("model") or DEFAULT_CHAT_MODEL)

    try:
        e = init()
        stream, retrieval = e.answer_stream(
            question,
            product=product,
            language=language,
            history=history,
            model=model,
        )
    except Exception as exc:
        return jsonify({"error": "Stream initialization failed", "detail": str(exc)}), 500

    def generate():
        meta = {
            "type": "meta",
            "product": retrieval.product,
            "selected_product": retrieval.selected_product,
            "detected_product": retrieval.detected_product,
            "product_conflict": retrieval.product_conflict,
            "low_evidence": retrieval.low_evidence,
            "sources": retrieval.public_sources(),
        }
        yield f"data: {json.dumps(meta, ensure_ascii=False)}\n\n"
        try:
            for chunk in stream:
                delta = chunk.choices[0].delta
                text = getattr(delta, "content", None)
                if text:
                    yield f"data: {json.dumps({'type': 'text', 'text': text}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'error': str(exc)}, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/retrieve", methods=["POST"])
def retrieve_debug():
    """Internal retrieval debug endpoint. Protect with WESS_API_KEY in production."""
    ok, error = _check_api_key()
    if not ok:
        return error, 401
    data = _json_body()
    if isinstance(data, tuple):
        return data
    question = str(data.get("question", "")).strip()
    if not question:
        return jsonify({"error": "Empty question"}), 400
    product = normalize_product(data.get("product", "auto"), default="auto")
    try:
        e = init()
        retrieval = e.retrieve(question, product=product)
        return jsonify(
            {
                "product": retrieval.product,
                "selected_product": retrieval.selected_product,
                "detected_product": retrieval.detected_product,
                "product_conflict": retrieval.product_conflict,
                "low_evidence": retrieval.low_evidence,
                "score_by_product": retrieval.score_by_product,
                "sources": retrieval.public_sources(limit=12),
            }
        )
    except Exception as exc:
        return jsonify({"error": "Retrieval failed", "detail": str(exc)}), 500


if __name__ == "__main__":
    init()
    port = int(os.environ.get("API_PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
