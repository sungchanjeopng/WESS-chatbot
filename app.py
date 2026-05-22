"""WESS product-support chatbot UI (Streamlit)."""
from __future__ import annotations

import base64
import os
import threading
from typing import Iterable

from dotenv import load_dotenv
import streamlit as st

load_dotenv()


def _apply_streamlit_cloud_secrets() -> None:
    """Expose Streamlit Community Cloud secrets as env vars before config import."""
    secret_keys = (
        "OPENAI_API_KEY",
        "WESS_CHAT_MODEL",
        "WESS_FAST_MODEL",
        "WESS_EMBEDDING_MODEL",
        "WESS_RAG_N_RESULTS",
        "WESS_MAX_HISTORY_MESSAGES",
        "WESS_MAX_CONTEXT_CHARS",
        "CHROMA_DIR",
        "WESS_API_KEY",
        "CORS_ALLOW_ORIGIN",
        "START_EMBEDDED_API",
    )
    try:
        secrets = st.secrets
    except Exception:
        return

    for key in secret_keys:
        try:
            value = secrets.get(key)
        except Exception:
            continue
        if value is not None and str(value).strip():
            os.environ[key] = str(value)


_apply_streamlit_cloud_secrets()

from wessbot.config import LANGUAGES, MODEL_OPTIONS, normalize_language
from wessbot.rag import WessRagEngine, RetrievalResult


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


def uploaded_image_to_data_url(uploaded_file) -> str:
    """Convert a Streamlit uploaded image to an OpenAI-compatible data URL."""
    mime_type = uploaded_file.type or "image/png"
    encoded = base64.b64encode(uploaded_file.getvalue()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


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


SAMPLE_QUESTIONS_BY_PRODUCT = {
    "ENV200": {
        "한국어": (
            "ENV200에서 EEA 보정은 어떻게 하나요?",
            "농도계 4-20mA 출력 설정 방법 알려줘",
            "측정값이 흔들릴 때 확인할 항목은?",
        ),
        "English": (
            "How do I perform EEA calibration on ENV200?",
            "How do I set the density meter 4-20 mA output?",
            "What should I check when the measured value is unstable?",
        ),
        "日本語": (
            "ENV200でEEA校正はどのように行いますか？",
            "濃度計の4-20mA出力設定方法を教えてください。",
            "測定値が揺れるときに確認する項目は？",
        ),
        "中文": (
            "ENV200 如何进行 EEA 校准？",
            "浓度计 4-20mA 输出如何设置？",
            "测量值波动时应检查哪些项目？",
        ),
        "Español": (
            "¿Cómo realizo la calibración EEA en ENV200?",
            "¿Cómo configuro la salida 4-20 mA del medidor de densidad?",
            "¿Qué debo revisar cuando el valor medido es inestable?",
        ),
        "Français": (
            "Comment effectuer l'étalonnage EEA sur ENV200 ?",
            "Comment régler la sortie 4-20 mA du densimètre ?",
            "Que vérifier lorsque la valeur mesurée est instable ?",
        ),
        "Deutsch": (
            "Wie führe ich die EEA-Kalibrierung beim ENV200 durch?",
            "Wie stelle ich den 4-20-mA-Ausgang des Dichtemessers ein?",
            "Was soll ich prüfen, wenn der Messwert schwankt?",
        ),
        "Português": (
            "Como faço a calibração EEA no ENV200?",
            "Como configuro a saída 4-20 mA do medidor de densidade?",
            "O que devo verificar quando o valor medido está instável?",
        ),
        "Tiếng Việt": (
            "Làm thế nào để hiệu chuẩn EEA trên ENV200?",
            "Cách cài đặt ngõ ra 4-20 mA của máy đo nồng độ?",
            "Cần kiểm tra gì khi giá trị đo dao động?",
        ),
        "ภาษาไทย": (
            "จะทำการสอบเทียบ EEA บน ENV200 ได้อย่างไร?",
            "จะตั้งค่าเอาต์พุต 4-20 mA ของเครื่องวัดความหนาแน่นได้อย่างไร?",
            "ควรตรวจสอบอะไรเมื่อค่าที่วัดไม่นิ่ง?",
        ),
        "Bahasa Indonesia": (
            "Bagaimana cara melakukan kalibrasi EEA pada ENV200?",
            "Bagaimana mengatur output 4-20 mA pada density meter?",
            "Apa yang harus diperiksa saat nilai pengukuran tidak stabil?",
        ),
        "العربية": (
            "كيف أقوم بمعايرة EEA على ENV200؟",
            "كيف أضبط خرج 4-20mA لمقياس الكثافة؟",
            "ما الذي يجب فحصه عند تذبذب قيمة القياس؟",
        ),
        "Русский": (
            "Как выполнить калибровку EEA на ENV200?",
            "Как настроить выход 4-20 мА измерителя плотности?",
            "Что проверить, если измеренное значение нестабильно?",
        ),
    },
    "ENV130": {
        "한국어": (
            "ENV130 Threshold 설정 방법 알려줘",
            "CH1 CH2 계면 측정이 이상할 때 확인할 것",
            "R1 릴레이 동작 조건 설명해줘",
        ),
        "English": (
            "How do I set the Threshold on ENV130?",
            "What should I check when CH1/CH2 interface measurement is abnormal?",
            "Explain the R1 relay operating conditions.",
        ),
        "日本語": (
            "ENV130のThreshold設定方法を教えてください。",
            "CH1/CH2の界面測定が異常なときに確認することは？",
            "R1リレーの動作条件を説明してください。",
        ),
        "中文": (
            "ENV130 的 Threshold 如何设置？",
            "CH1/CH2 界面测量异常时应检查什么？",
            "请说明 R1 继电器动作条件。",
        ),
        "Español": (
            "¿Cómo configuro el Threshold en ENV130?",
            "¿Qué debo revisar cuando la medición de interfaz CH1/CH2 es anormal?",
            "Explique las condiciones de operación del relé R1.",
        ),
        "Français": (
            "Comment régler le Threshold sur ENV130 ?",
            "Que vérifier lorsque la mesure d'interface CH1/CH2 est anormale ?",
            "Expliquez les conditions de fonctionnement du relais R1.",
        ),
        "Deutsch": (
            "Wie stelle ich den Threshold beim ENV130 ein?",
            "Was soll ich prüfen, wenn die CH1/CH2-Grenzschichtmessung abnormal ist?",
            "Erkläre die Betriebsbedingungen des R1-Relais.",
        ),
        "Português": (
            "Como configuro o Threshold no ENV130?",
            "O que verificar quando a medição de interface CH1/CH2 está anormal?",
            "Explique as condições de operação do relé R1.",
        ),
        "Tiếng Việt": (
            "Cách cài đặt Threshold trên ENV130?",
            "Cần kiểm tra gì khi đo giao diện CH1/CH2 bất thường?",
            "Giải thích điều kiện hoạt động của rơ-le R1.",
        ),
        "ภาษาไทย": (
            "จะตั้งค่า Threshold บน ENV130 ได้อย่างไร?",
            "ควรตรวจสอบอะไรเมื่อการวัดชั้นตะกอน CH1/CH2 ผิดปกติ?",
            "อธิบายเงื่อนไขการทำงานของรีเลย์ R1",
        ),
        "Bahasa Indonesia": (
            "Bagaimana cara mengatur Threshold pada ENV130?",
            "Apa yang harus diperiksa saat pengukuran interface CH1/CH2 tidak normal?",
            "Jelaskan kondisi kerja relay R1.",
        ),
        "العربية": (
            "كيف أضبط Threshold على ENV130؟",
            "ما الذي يجب فحصه عند وجود خلل في قياس الواجهة CH1/CH2؟",
            "اشرح شروط تشغيل مرحل R1.",
        ),
        "Русский": (
            "Как настроить Threshold на ENV130?",
            "Что проверить при ненормальном измерении границы CH1/CH2?",
            "Объясните условия срабатывания реле R1.",
        ),
    },
    "ENV120": {
        "한국어": (
            "ENV120에서 수신감도는 언제 조정하나요?",
            "측정값이 갑자기 튈 때 점검 순서 알려줘",
            "ENV120 릴레이 설정 방법 알려줘",
        ),
        "English": (
            "When should I adjust Echo AMP on ENV120?",
            "What is the check sequence when the measured value suddenly jumps?",
            "How do I set the ENV120 relay?",
        ),
        "日本語": (
            "ENV120で受信感度はいつ調整しますか？",
            "測定値が急に跳ねるときの点検手順を教えてください。",
            "ENV120のリレー設定方法を教えてください。",
        ),
        "中文": (
            "ENV120 什么时候需要调整接收灵敏度？",
            "测量值突然跳动时的检查顺序是什么？",
            "ENV120 继电器如何设置？",
        ),
        "Español": (
            "¿Cuándo debo ajustar Echo AMP en ENV120?",
            "¿Cuál es la secuencia de revisión cuando el valor medido salta repentinamente?",
            "¿Cómo configuro el relé del ENV120?",
        ),
        "Français": (
            "Quand faut-il ajuster Echo AMP sur ENV120 ?",
            "Quelle est la séquence de vérification lorsque la valeur mesurée saute soudainement ?",
            "Comment régler le relais de l'ENV120 ?",
        ),
        "Deutsch": (
            "Wann sollte ich Echo AMP beim ENV120 einstellen?",
            "Welche Prüfschritte gelten, wenn der Messwert plötzlich springt?",
            "Wie stelle ich das ENV120-Relais ein?",
        ),
        "Português": (
            "Quando devo ajustar o Echo AMP no ENV120?",
            "Qual é a sequência de verificação quando o valor medido salta de repente?",
            "Como configuro o relé do ENV120?",
        ),
        "Tiếng Việt": (
            "Khi nào cần chỉnh Echo AMP trên ENV120?",
            "Trình tự kiểm tra khi giá trị đo đột ngột nhảy là gì?",
            "Cách cài đặt rơ-le ENV120?",
        ),
        "ภาษาไทย": (
            "ควรปรับ Echo AMP บน ENV120 เมื่อใด?",
            "ลำดับการตรวจสอบเมื่อค่าที่วัดกระโดดกะทันหันคืออะไร?",
            "จะตั้งค่ารีเลย์ ENV120 ได้อย่างไร?",
        ),
        "Bahasa Indonesia": (
            "Kapan Echo AMP pada ENV120 perlu disesuaikan?",
            "Bagaimana urutan pengecekan saat nilai pengukuran tiba-tiba melonjak?",
            "Bagaimana cara mengatur relay ENV120?",
        ),
        "العربية": (
            "متى يجب ضبط Echo AMP على ENV120؟",
            "ما تسلسل الفحص عند قفز قيمة القياس فجأة؟",
            "كيف أضبط مرحل ENV120؟",
        ),
        "Русский": (
            "Когда нужно регулировать Echo AMP на ENV120?",
            "Какова последовательность проверки, если значение измерения внезапно скачет?",
            "Как настроить реле ENV120?",
        ),
    },
}


def get_sample_questions(product: str, language: str) -> tuple[str, str, str]:
    product_questions = SAMPLE_QUESTIONS_BY_PRODUCT.get(product, SAMPLE_QUESTIONS_BY_PRODUCT["ENV200"])
    lang = normalize_language(language)
    return product_questions.get(lang, product_questions["한국어"])


start_api_server_if_enabled()

st.set_page_config(page_title="WESS-AI", page_icon="🔧", layout="centered")
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

try:
    engine = get_engine()
except Exception as exc:
    st.error(f"초기화 실패: {exc}")
    st.stop()

product_options = ["ENV200", "ENV130", "ENV120"]

col1, col2, col3 = st.columns([2.3, 2, 1.2])
with col1:
    product = st.selectbox("Product / 제품", product_options, index=0)
with col2:
    lang = st.selectbox("Language / 언어", list(LANGUAGES.keys()), index=list(LANGUAGES.keys()).index("한국어"))
with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(LANGUAGES[lang]["new_chat"], use_container_width=True):
        st.session_state.messages = [{"role": "assistant", "content": LANGUAGES[lang]["greeting"]}]
        st.session_state.last_sources = None
        st.rerun()

lang = normalize_language(lang)
lang_cfg = LANGUAGES[lang]
model_name = MODEL_OPTIONS["정밀 답변"]

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": lang_cfg["greeting"]}]
if "last_sources" not in st.session_state:
    st.session_state.last_sources = None

# 추천 질문
sample_cols = st.columns(3)
sample_questions = get_sample_questions(product, lang)
for i, q in enumerate(sample_questions):
    if sample_cols[i].button(q, use_container_width=True):
        st.session_state.queued_prompt = q
        st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

chat_value = st.chat_input(
    lang_cfg["placeholder"] + "  ·  사진은 드래그하거나 Ctrl+V로 붙여넣을 수 있습니다.",
    accept_file="multiple",
    file_type=["png", "jpg", "jpeg", "webp"],
)
image_files = []
prompt = None
if chat_value:
    if isinstance(chat_value, str):
        prompt = chat_value
    else:
        prompt = (getattr(chat_value, "text", "") or "").strip()
        image_files = list(getattr(chat_value, "files", []) or [])[:4]
        if image_files and not prompt:
            prompt = "첨부한 파형/화면 사진 분석해줘"
if st.session_state.get("queued_prompt"):
    prompt = st.session_state.pop("queued_prompt")

if prompt:
    image_note = f"\n\n[첨부 이미지: {len(image_files)}장]" if image_files else ""
    st.session_state.messages.append({"role": "user", "content": prompt + image_note})
    with st.chat_message("user"):
        st.markdown(prompt)
        for image_file in image_files:
            st.image(image_file, caption=image_file.name, use_container_width=True)

    with st.chat_message("assistant"):
        try:
            with st.spinner(lang_cfg["spinner"]):
                if image_files:
                    image_data_urls = [uploaded_image_to_data_url(image_file) for image_file in image_files]
                    answer, retrieval = engine.answer_once_with_images(
                        prompt,
                        image_data_urls,
                        product=product,
                        language=lang,
                        history=st.session_state.messages,
                        model=model_name,
                    )
                    st.markdown(answer)
                else:
                    stream, retrieval = engine.answer_stream(
                        prompt,
                        product=product,
                        language=lang,
                        history=st.session_state.messages,
                        model=model_name,
                    )
                    answer = st.write_stream(stream_text(stream))
            render_sources(retrieval)
            st.session_state.last_sources = retrieval.public_sources(limit=8)
        except Exception as exc:
            answer = f"답변 생성 중 오류가 발생했습니다: {exc}"
            st.error(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()
