"""WESS product-support chatbot UI (Streamlit)."""
from __future__ import annotations

import os
import threading
from typing import Iterable

import streamlit as st
from dotenv import load_dotenv

from wessbot.config import LANGUAGES, MODEL_OPTIONS, normalize_language
from wessbot.products import PRODUCTS
from wessbot.rag import WessRagEngine, RetrievalResult

load_dotenv()

# Streamlit Cloud Secrets 지원: secrets 값은 화면에 출력하지 않는다.
if hasattr(st, "secrets") and "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]


def start_api_server_if_enabled() -> None:
    """Optionally run Flask API next to Streamlit for simple single-process demos.

    Production/API deployment should run `python api.py` or gunicorn separately.
    Set START_EMBEDDED_API=1 only when this mixed mode is intentionally needed.
    """
    if os.getenv("START_EMBEDDED_API", "0") not in {"1", "true", "TRUE", "yes"}:
        return
    if st.session_state.get("api_started"):
        return
    st.session_state.api_started = True

    def _run() -> None:
        try:
            from api import app as flask_app, init as api_init

            api_init()
            api_port = int(os.environ.get("API_PORT", "5001"))
            flask_app.run(host="0.0.0.0", port=api_port, use_reloader=False)
        except Exception as exc:  # pragma: no cover - visible in Streamlit logs
            print(f"API server failed: {exc}")

    threading.Thread(target=_run, daemon=True).start()


@st.cache_resource(show_spinner=False)
def get_engine() -> WessRagEngine:
    return WessRagEngine()


def stream_text(openai_stream: Iterable) -> Iterable[str]:
    for chunk in openai_stream:
        delta = chunk.choices[0].delta
        if getattr(delta, "content", None):
            yield delta.content


def render_sources(retrieval: RetrievalResult) -> None:
    if not retrieval.chunks:
        return
    with st.expander("참고한 문서 / Retrieved sources", expanded=False):
        for idx, source in enumerate(retrieval.public_sources(limit=8), start=1):
            distance = source.get("distance")
            distance_text = "" if distance is None else f" / distance {distance:.4f}"
            st.markdown(
                f"{idx}. **{source['product']}** · `{source['source']}` · chunk `{source['chunk_index']}`{distance_text}"
            )


start_api_server_if_enabled()

st.set_page_config(page_title="WESS 제품 지원 챗봇", page_icon="🔧", layout="centered")
st.markdown(
    """
<style>
    .block-container { max-width: 920px; padding-top: 1rem; padding-bottom: 2rem; }
    #MainMenu, footer, header { visibility: hidden; }
    .small-note { color: #666; font-size: 0.86rem; }
    @media (max-width: 768px) {
        .stSelectbox > div { font-size: 14px; }
        .stChatMessage { padding: 0.5rem; }
    }
</style>
""",
    unsafe_allow_html=True,
)

st.title("WESS 제품 지원 챗봇")
st.caption("ENV120 · ENV130 · ENV200 문서 기반 답변 / 설치·설정·교정·오류 대응")

try:
    engine = get_engine()
except Exception as exc:
    st.error(f"초기화 실패: {exc}")
    st.stop()

health = engine.health()
product_options = {"auto": "자동 선택"} | {k: v.display_name for k, v in PRODUCTS.items()}

col1, col2, col3, col4 = st.columns([2.3, 2, 1.8, 1.2])
with col1:
    product = st.selectbox(
        "Product / 제품",
        list(product_options.keys()),
        format_func=lambda k: product_options[k],
        index=0,
    )
with col2:
    lang = st.selectbox("Language / 언어", list(LANGUAGES.keys()), index=list(LANGUAGES.keys()).index("한국어"))
with col3:
    model_label = st.selectbox("Answer mode", list(MODEL_OPTIONS.keys()), index=1)
with col4:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(LANGUAGES[lang]["new_chat"], use_container_width=True):
        st.session_state.messages = [{"role": "assistant", "content": LANGUAGES[lang]["greeting"]}]
        st.session_state.last_sources = None
        st.rerun()

ready_products = [k for k, v in health["products"].items() if v.get("ready")]
if not ready_products:
    st.warning("제품 문서 DB가 준비되지 않았습니다. chroma_db를 확인하거나 load_docs.py를 실행하세요.")
    st.stop()

with st.expander("제품별 문서 상태", expanded=False):
    for key, item in health["products"].items():
        status = "준비됨" if item["ready"] else "없음"
        st.write(f"- {key}: {status}, chunks={item.get('count')}")
    st.markdown(
        "<div class='small-note'>공개 GitHub에 chroma_db를 올릴 경우 문서 원문 조각이 노출될 수 있습니다.</div>",
        unsafe_allow_html=True,
    )

lang = normalize_language(lang)
lang_cfg = LANGUAGES[lang]

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": lang_cfg["greeting"]}]
if "last_sources" not in st.session_state:
    st.session_state.last_sources = None

# 추천 질문
sample_cols = st.columns(3)
sample_questions = [
    "ENV130 Threshold 설정 방법 알려줘",
    "ENV200 4-20mA 출력 설정은 어떻게 하나요?",
    "ENV120 측정값이 튈 때 점검 순서 알려줘",
]
for i, q in enumerate(sample_questions):
    if sample_cols[i].button(q, use_container_width=True):
        st.session_state.queued_prompt = q
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input(lang_cfg["placeholder"])
if st.session_state.get("queued_prompt"):
    prompt = st.session_state.pop("queued_prompt")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner(lang_cfg["spinner"]):
                stream, retrieval = engine.answer_stream(
                    prompt,
                    product=product,
                    language=lang,
                    history=st.session_state.messages,
                    model=MODEL_OPTIONS[model_label],
                )
            answer = st.write_stream(stream_text(stream))
            render_sources(retrieval)
            st.session_state.last_sources = retrieval.public_sources(limit=8)
        except Exception as exc:
            answer = f"답변 생성 중 오류가 발생했습니다: {exc}"
            st.error(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()
