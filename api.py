"""WESSGLOBAL 챗봇 REST API (Flask) — 안드로이드 앱용"""
import os
import json
from flask import Flask, request, jsonify, Response, stream_with_context
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")

PRODUCTS = {
    "density": "wess_density",
    "interface": "wess_interface",
    "interface_120": "wess_interface_120",
}

# 클라이언트 초기화 (앱 시작 시 1회)
openai_client = None
collections = {}

def init():
    global openai_client, collections
    openai_client = OpenAI()
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    for key, col_name in PRODUCTS.items():
        try:
            collections[key] = chroma_client.get_collection(col_name)
        except Exception:
            collections[key] = None

def search_docs(collection, query, n_results=15):
    query_embedding = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    ).data[0].embedding
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    return results["documents"][0]

def build_system_prompt(product, context, lang="ko"):
    common_rules = (
        "How to answer:\n"
        "1. Cross-reference multiple documents to ensure consistency before answering.\n"
        "2. Even if the exact answer is not directly stated, infer and reason based on related information.\n"
        "3. Provide step-by-step procedures that can be followed immediately.\n"
        "4. Think deeply before answering.\n"
        "5. If the answer is ambiguous, say so.\n"
        "6. If documents contain conflicting information, note that 'versions may differ'.\n\n"
        "Rules:\n"
        "- Never reference table/figure/chapter numbers.\n"
        "- Explain the content directly.\n"
        "- 반드시 한국어로 답변하세요.\n"
        "- If truly no relevant information exists, say: '해당 정보는 확인되지 않습니다. 추가 문의는 WESSGLOBAL 고객지원(041-584-8820)으로 연락해주세요.'\n"
    )

    if product == "density":
        return (
            "You are a WESSGLOBAL product support specialist for ultrasonic sludge density meter (ENV200).\n\n"
            + common_rules
            + f"\n[Product Documents]\n{context}"
        )
    elif product == "interface":
        return (
            "You are a WESSGLOBAL product support specialist for ultrasonic sludge interface meter (ENV130).\n\n"
            + common_rules
            + f"\n[Product Documents]\n{context}"
        )
    else:
        return (
            "You are a WESSGLOBAL product support specialist.\n\n"
            + common_rules
            + f"\n[Product Documents]\n{context}"
        )


@app.route("/api/chat", methods=["POST"])
def chat():
    """채팅 API — JSON 요청/응답"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    question = data.get("question", "").strip()
    product = data.get("product", "density")  # density, interface, interface_120
    history = data.get("history", [])  # [{"role":"user","content":"..."}, ...]
    model = data.get("model", "gpt-4.1-mini")

    if not question:
        return jsonify({"error": "Empty question"}), 400

    collection = collections.get(product)
    if collection is None:
        return jsonify({"error": "Product not found"}), 404

    # 벡터 검색
    context_docs = search_docs(collection, question)
    context = "\n\n---\n\n".join(context_docs)

    # 시스템 프롬프트
    sys_prompt = build_system_prompt(product, context)

    messages = [{"role": "system", "content": sys_prompt}]
    for msg in history[-20:]:
        if msg.get("role") in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": question})

    # OpenAI 호출 (비스트리밍)
    response = openai_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
    )

    answer = response.choices[0].message.content
    return jsonify({"answer": answer})


@app.route("/api/chat/stream", methods=["POST"])
def chat_stream():
    """스트리밍 채팅 API — SSE 응답"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    question = data.get("question", "").strip()
    product = data.get("product", "density")
    history = data.get("history", [])
    model = data.get("model", "gpt-4.1-mini")

    if not question:
        return jsonify({"error": "Empty question"}), 400

    collection = collections.get(product)
    if collection is None:
        return jsonify({"error": "Product not found"}), 404

    context_docs = search_docs(collection, question)
    context = "\n\n---\n\n".join(context_docs)
    sys_prompt = build_system_prompt(product, context)

    messages = [{"role": "system", "content": sys_prompt}]
    for msg in history[-20:]:
        if msg.get("role") in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": question})

    def generate():
        stream = openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield f"data: {json.dumps({'text': delta.content})}\n\n"
        yield "data: [DONE]\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    init()
    port = int(os.environ.get("API_PORT", 5000))
    app.run(host="0.0.0.0", port=port)
