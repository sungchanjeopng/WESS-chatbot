"""WESS-Global 제품 AI 챗봇 (Streamlit)"""
import os
import streamlit as st
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Streamlit Cloud Secrets 지원
if hasattr(st, "secrets") and "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")

PRODUCTS = {
    "농도계 (ENV200)": "wess_density",
    "계면계 (ENV130)": "wess_interface",
    "계면계 (ENV120)": "wess_interface_120",
}

LANGUAGES = {
    "한국어": {
        "greeting": "안녕하세요! WESS-Global 제품에 대해 궁금한 점을 물어보세요.",
        "caption": "ENV200 초음파 슬러지 농도계에 대해 궁금한 점을 물어보세요.",
        "placeholder": "질문을 입력하세요...",
        "spinner": "답변을 생성하고 있습니다...",
        "new_chat": "새 대화",
        "lang_rule": "반드시 한국어로만 답변하세요. 영어 문서를 참조하더라도 한국어로 번역하여 답변하세요. 제품명, 모델명 등 고유명사만 영어 그대로 사용하세요.",
        "unknown": "해당 정보는 확인되지 않습니다. 추가 문의는 WESS-Global 고객지원(041-584-8820)으로 연락해주세요.",
    },
    "English": {
        "greeting": "Hello! Ask me anything about WESS-Global products.",
        "caption": "Ask any questions about the ENV200 Ultrasonic Sludge Density Meter.",
        "placeholder": "Type your question...",
        "spinner": "Generating answer...",
        "new_chat": "New Chat",
        "lang_rule": "You must answer only in English. Even if the document is in Korean, translate and answer in English. Keep product names and model names as-is.",
        "unknown": "The requested information could not be found. Please contact WESS-Global support at 041-584-8820.",
    },
    "日本語": {
        "greeting": "こんにちは！WESS-Global製品についてお気軽にご質問ください。",
        "caption": "ENV200超音波スラッジ濃度計についてご質問ください。",
        "placeholder": "質問を入力してください...",
        "spinner": "回答を生成しています...",
        "new_chat": "新しい会話",
        "lang_rule": "必ず日本語のみで回答してください。英語や韓国語の文書を参照しても日本語に翻訳して回答してください。製品名・モデル名はそのまま英語で使用してください。",
        "unknown": "該当情報は確認できませんでした。詳細はWESS-Globalサポート(041-584-8820)までお問い合わせください。",
    },
    "中文": {
        "greeting": "您好！欢迎咨询WESS-Global产品相关问题。",
        "caption": "关于ENV200超声波污泥浓度计，请随时提问。",
        "placeholder": "请输入您的问题...",
        "spinner": "正在生成回答...",
        "new_chat": "新对话",
        "lang_rule": "必须仅用中文回答。即使参考英文或韩文文档，也请翻译成中文回答。产品名称和型号保持英文原样。",
        "unknown": "未找到相关信息。如需进一步咨询，请联系WESS-Global客服(041-584-8820)。",
    },
    "Español": {
        "greeting": "¡Hola! Pregúnteme sobre los productos de WESS-Global.",
        "caption": "Haga preguntas sobre el medidor de densidad de lodos ultrasónico ENV200.",
        "placeholder": "Escriba su pregunta...",
        "spinner": "Generando respuesta...",
        "new_chat": "Nueva conversación",
        "lang_rule": "Debes responder solo en español. Aunque el documento esté en otro idioma, traduce y responde en español. Mantén los nombres de productos y modelos en su forma original.",
        "unknown": "No se encontró la información solicitada. Contacte al soporte de WESS-Global al 041-584-8820.",
    },
    "Français": {
        "greeting": "Bonjour ! Posez vos questions sur les produits WESS-Global.",
        "caption": "Posez vos questions sur le densimètre à ultrasons ENV200.",
        "placeholder": "Tapez votre question...",
        "spinner": "Génération de la réponse...",
        "new_chat": "Nouvelle conversation",
        "lang_rule": "Vous devez répondre uniquement en français. Même si le document est dans une autre langue, traduisez et répondez en français. Gardez les noms de produits et modèles tels quels.",
        "unknown": "L'information demandée n'a pas été trouvée. Veuillez contacter le support WESS-Global au 041-584-8820.",
    },
    "Deutsch": {
        "greeting": "Hallo! Fragen Sie mich zu WESS-Global Produkten.",
        "caption": "Stellen Sie Fragen zum Ultraschall-Schlammkonzentrationsmesser ENV200.",
        "placeholder": "Geben Sie Ihre Frage ein...",
        "spinner": "Antwort wird generiert...",
        "new_chat": "Neues Gespräch",
        "lang_rule": "Sie müssen ausschließlich auf Deutsch antworten. Auch wenn das Dokument in einer anderen Sprache ist, übersetzen und antworten Sie auf Deutsch. Produktnamen und Modellbezeichnungen bleiben im Original.",
        "unknown": "Die angeforderten Informationen wurden nicht gefunden. Bitte kontaktieren Sie den WESS-Global Support unter 041-584-8820.",
    },
    "Português": {
        "greeting": "Olá! Pergunte sobre os produtos da WESS-Global.",
        "caption": "Faça perguntas sobre o medidor de densidade ultrassônico ENV200.",
        "placeholder": "Digite sua pergunta...",
        "spinner": "Gerando resposta...",
        "new_chat": "Nova conversa",
        "lang_rule": "Você deve responder apenas em português. Mesmo que o documento esteja em outro idioma, traduza e responda em português. Mantenha nomes de produtos e modelos como estão.",
        "unknown": "A informação solicitada não foi encontrada. Entre em contato com o suporte WESS-Global pelo 041-584-8820.",
    },
    "Tiếng Việt": {
        "greeting": "Xin chào! Hãy hỏi tôi về sản phẩm WESS-Global.",
        "caption": "Đặt câu hỏi về máy đo nồng độ bùn siêu âm ENV200.",
        "placeholder": "Nhập câu hỏi của bạn...",
        "spinner": "Đang tạo câu trả lời...",
        "new_chat": "Cuộc trò chuyện mới",
        "lang_rule": "Bạn phải trả lời chỉ bằng tiếng Việt. Ngay cả khi tài liệu bằng ngôn ngữ khác, hãy dịch và trả lời bằng tiếng Việt. Giữ nguyên tên sản phẩm và model.",
        "unknown": "Không tìm thấy thông tin yêu cầu. Vui lòng liên hệ hỗ trợ WESS-Global theo số 041-584-8820.",
    },
    "ภาษาไทย": {
        "greeting": "สวัสดี! สอบถามเกี่ยวกับผลิตภัณฑ์ WESS-Global ได้เลย",
        "caption": "สอบถามเกี่ยวกับเครื่องวัดความเข้มข้นตะกอนอัลตราโซนิก ENV200",
        "placeholder": "พิมพ์คำถามของคุณ...",
        "spinner": "กำลังสร้างคำตอบ...",
        "new_chat": "แชทใหม่",
        "lang_rule": "ต้องตอบเป็นภาษาไทยเท่านั้น แม้เอกสารจะเป็นภาษาอื่น ให้แปลและตอบเป็นภาษาไทย ชื่อผลิตภัณฑ์และรุ่นให้คงภาษาอังกฤษ",
        "unknown": "ไม่พบข้อมูลที่ร้องขอ กรุณาติดต่อฝ่ายสนับสนุน WESS-Global ที่ 041-584-8820",
    },
    "Bahasa Indonesia": {
        "greeting": "Halo! Tanyakan tentang produk WESS-Global.",
        "caption": "Ajukan pertanyaan tentang pengukur kepadatan lumpur ultrasonik ENV200.",
        "placeholder": "Ketik pertanyaan Anda...",
        "spinner": "Membuat jawaban...",
        "new_chat": "Obrolan baru",
        "lang_rule": "Anda harus menjawab hanya dalam Bahasa Indonesia. Meskipun dokumen dalam bahasa lain, terjemahkan dan jawab dalam Bahasa Indonesia. Pertahankan nama produk dan model apa adanya.",
        "unknown": "Informasi yang diminta tidak ditemukan. Silakan hubungi dukungan WESS-Global di 041-584-8820.",
    },
    "العربية": {
        "greeting": "مرحباً! اسألني عن منتجات WESS-Global.",
        "caption": "اطرح أسئلتك حول جهاز قياس كثافة الحمأة بالموجات فوق الصوتية ENV200.",
        "placeholder": "اكتب سؤالك...",
        "spinner": "جاري إنشاء الإجابة...",
        "new_chat": "محادثة جديدة",
        "lang_rule": "يجب الإجابة باللغة العربية فقط. حتى لو كانت الوثيقة بلغة أخرى، قم بالترجمة والإجابة بالعربية. احتفظ بأسماء المنتجات والطرازات كما هي.",
        "unknown": "لم يتم العثور على المعلومات المطلوبة. يرجى الاتصال بدعم WESS-Global على الرقم 041-584-8820.",
    },
    "Русский": {
        "greeting": "Здравствуйте! Задавайте вопросы о продукции WESS-Global.",
        "caption": "Задавайте вопросы об ультразвуковом измерителе плотности осадка ENV200.",
        "placeholder": "Введите ваш вопрос...",
        "spinner": "Генерация ответа...",
        "new_chat": "Новый чат",
        "lang_rule": "Отвечайте только на русском языке. Даже если документ на другом языке, переведите и ответьте на русском. Названия продуктов и моделей оставляйте на английском.",
        "unknown": "Запрашиваемая информация не найдена. Свяжитесь со службой поддержки WESS-Global по номеру 041-584-8820.",
    },
}


@st.cache_resource
def init_clients():
    """OpenAI, ChromaDB 클라이언트 초기화"""
    openai_client = OpenAI()
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    collections = {}
    for product_name, col_name in PRODUCTS.items():
        try:
            collections[product_name] = chroma_client.get_collection(col_name)
        except Exception:
            collections[product_name] = None
    return openai_client, collections


def search_docs(collection, openai_client, query, n_results=15):
    """질문과 관련된 문서 검색"""
    query_embedding = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    ).data[0].embedding

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    return results["documents"][0]


def stream_answer(openai_client, question, context_docs, lang="한국어", chat_history=None, product="", model="gpt-5.4-mini"):
    """GPT 스트리밍 답변 생성"""
    context = "\n\n---\n\n".join(context_docs)
    lang_cfg = LANGUAGES[lang]

    # 공통 규칙
    common_rules = (
        "How to answer:\n"
        "1. Cross-reference multiple documents to ensure consistency before answering.\n"
        "2. Even if the exact answer is not directly stated, infer and reason based on related information. Provide practical tips.\n"
        "3. Provide step-by-step procedures that can be followed immediately.\n"
        "4. Think deeply before answering. Consider the context, related parameters, and potential issues.\n"
        "5. If the answer is ambiguous, say: '정확하지 않을 수 있습니다. 좀 더 확인이 필요합니다.'\n"
        "6. If documents contain conflicting information, note that 'versions may differ'.\n\n"
        "Rules:\n"
        "- Never reference table/figure/chapter numbers like '표 3-3', 'Figure 2.1', 'Chapter 5'. The customer does not have the manual.\n"
        "- Explain the content directly instead.\n"
        "- But always try your best to find related information and provide a helpful answer before giving up.\n"
        f"- {lang_cfg['lang_rule']}\n"
        f"- If truly no relevant information exists, say: '{lang_cfg['unknown']}'\n"
    )

    # ENV200 (농도계) 전용 용어 규칙
    env200_terms = (
        "\nProduct-specific terminology rules (ENV200 - Density Meter):\n"
        "- Use these terms: EEA, Detection Area, 농도/Density, 댐핑/Damping, 배관 외경/Pipe Diameter, 교정/Calibration, AGC, Profile, Clamp-on, Spool-piece\n"
        "- Units: %, ppm, mg/L, g/L\n"
        "- Calibration: multi-point calibration (EEA ↔ Density)\n"
        "- Channel: single\n"
        "- DO NOT use these terms (they belong to interface meters): Threshold/문턱전압, Echo AMP/수신감도, ASF, Light/Heavy, Level/Distance, m/ft, CH1/CH2\n"
    )

    # ENV130 (계면계) 전용 용어 규칙
    env130_terms = (
        "\nProduct-specific terminology rules (ENV130 - Interface Meter):\n"
        "- Use these terms: Threshold/문턱전압, Echo AMP/수신감도, ASF, Light/Heavy, 댐핑/Damping, Level/Distance, Echo, CH1/CH2\n"
        "- Units: m, ft\n"
        "- Channel: dual (CH1/CH2)\n"
        "- DO NOT use these terms (they belong to density meters): EEA, Detection Area, Pipe Diameter, AGC, Profile, Clamp-on, Spool-piece, %, ppm, mg/L, g/L\n"
    )

    # ENV120 (계면계) 전용 용어 규칙
    env120_terms = (
        "\nProduct-specific terminology rules (ENV120 - Interface Meter):\n"
        "- Use these terms: Threshold/문턱전압, Echo AMP/수신감도, ASF, 댐핑/Damping, Level/Distance, Echo\n"
        "- Units: m, ft\n"
        "- Channel: single\n"
        "- DO NOT use these terms: EEA, Detection Area, Pipe Diameter, AGC, Profile, Clamp-on, Spool-piece, Light/Heavy, CH1/CH2, %, ppm, mg/L, g/L\n"
    )

    # 제품별 프롬프트 조합
    if "ENV200" in product:
        base_prompt = (
            "You are a WESS-Global product support specialist for ultrasonic sludge density meter (ENV200).\n\n"
            + common_rules + env200_terms
            + f"\n[Product Documents]\n{context}"
        )
    elif "ENV130" in product:
        base_prompt = (
            "You are a WESS-Global product support specialist for ultrasonic sludge interface meter (ENV130).\n\n"
            + common_rules + env130_terms
            + f"\n[Product Documents]\n{context}"
        )
    else:
        base_prompt = (
            "You are a WESS-Global product support specialist.\n\n"
            + common_rules
            + f"\n[Product Documents]\n{context}"
        )

    # ENV120 전용 프롬프트
    env120_prompt = (
        "You are a WESS-Global product support specialist with deep field experience in ultrasonic sludge interface meters (ENV120). "
        "You have extensive knowledge of installation, calibration, troubleshooting, and field operation.\n\n"
        "How to answer:\n"
        "1. Thoroughly analyze ALL the product documents provided below before answering. Cross-reference multiple documents to ensure consistency.\n"
        "2. Combine and synthesize information from multiple documents to give comprehensive, practical answers.\n"
        "3. Even if the exact answer is not directly stated, infer and reason based on related information. Provide practical field tips.\n"
        "4. Provide step-by-step procedures that a field engineer can follow immediately.\n"
        "5. When relevant, include recommended values, typical ranges, and real-world tips from field experience.\n"
        "6. If the question is about settings, explain both HOW to access the menu (button sequence) AND what values to set.\n"
        "7. Think deeply before answering. Consider the context, related parameters, and potential issues.\n"
        "8. For measurement error questions, emphasize that 수신감도(Echo AMP) should be checked before Threshold.\n"
        "9. For relay questions, always clarify R1/R2 contact open/close conditions to prevent confusion.\n"
        "10. Use clear option names (문턱전압/Threshold, ASF, 수신감도/Echo AMP, 센서 세정장치, etc.) to aid understanding.\n\n"
        "Rules:\n"
        "- Never reference table/figure/chapter numbers like '표 3-3', 'Figure 2.1', 'Chapter 5'. The customer does not have the manual.\n"
        "- Explain the content directly instead.\n"
        "- If documents contain conflicting information, note that 'versions may differ'.\n"
        "- Do not use the term 'TVG' unless the user specifically asks about it.\n"
        "- If truly no relevant information exists, say: '" + lang_cfg['unknown'] + "'\n"
        "- If the answer is ambiguous, say: '정확하지 않을 수 있습니다. 좀 더 확인이 필요합니다.'\n"
        "- But always try your best to find related information and provide a helpful answer before giving up.\n"
        f"- {lang_cfg['lang_rule']}\n"
        + env120_terms +
        f"\n[Product Documents]\n{context}"
    )

    sys_prompt = env120_prompt if "ENV120" in product else base_prompt

    messages = [
        {
            "role": "system",
            "content": sys_prompt
        }
    ]

    # 최근 대화 기록 추가 (최대 20개)
    if chat_history:
        for msg in chat_history[-20:]:
            if msg["role"] in ("user", "assistant"):
                messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": question})

    stream = openai_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
        stream=True
    )
    return stream


# --- Streamlit UI ---
st.set_page_config(
    page_title="WESS-Global 제품 지원 챗봇",
    page_icon="🔧",
    layout="centered"
)

# ChatGPT 스타일 CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600&display=swap');

    /* 전체 배경 - ChatGPT 다크 */
    .stApp {
        background-color: #212121 !important;
        font-family: 'Noto Sans KR', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }

    /* 전체 레이아웃 */
    .block-container {
        max-width: 768px;
        padding: 0.5rem 1rem 5rem;
    }

    /* 채팅 메시지 공통 */
    .stChatMessage {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 1rem 0 !important;
        margin-bottom: 0 !important;
        border-radius: 0 !important;
    }

    /* 사용자 메시지 */
    [data-testid="stChatMessageUser"] {
        background: #2f2f2f !important;
        border-radius: 20px !important;
        padding: 0.8rem 1.2rem !important;
        margin: 0.3rem 0 !important;
    }
    [data-testid="stChatMessageUser"] p {
        color: #ececec !important;
    }

    /* AI 메시지 */
    [data-testid="stChatMessageAssistant"] {
        background: transparent !important;
        padding: 0.8rem 0 !important;
    }
    [data-testid="stChatMessageAssistant"] p {
        color: #d1d5db !important;
    }

    /* 아바타 숨기기 */
    .stChatMessage [data-testid="stImage"] {
        display: none !important;
    }

    /* 입력창 - ChatGPT 스타일 */
    .stChatInput > div {
        border-radius: 24px !important;
        border: 1px solid #424242 !important;
        background: #2f2f2f !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.3) !important;
        padding: 4px !important;
    }
    .stChatInput textarea {
        font-family: 'Noto Sans KR', sans-serif !important;
        font-size: 15px !important;
        color: #ececec !important;
        background: transparent !important;
    }
    .stChatInput textarea::placeholder {
        color: #8e8ea0 !important;
    }

    /* 셀렉트박스 */
    .stSelectbox > div > div {
        border-radius: 10px !important;
        border: 1px solid #424242 !important;
        background: #2f2f2f !important;
        color: #ececec !important;
        font-size: 13px !important;
    }
    .stSelectbox label {
        font-size: 11px !important;
        font-weight: 500 !important;
        color: #8e8ea0 !important;
    }
    .stSelectbox svg {
        fill: #8e8ea0 !important;
    }

    /* 버튼 (새 대화) */
    .stButton > button {
        border-radius: 10px !important;
        border: 1px solid #424242 !important;
        background: #2f2f2f !important;
        font-family: 'Noto Sans KR', sans-serif !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        color: #ececec !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover {
        background: #424242 !important;
        border-color: #616161 !important;
    }

    /* 캡션 */
    .stCaption, .stCaption p {
        color: #8e8ea0 !important;
        font-size: 12px !important;
    }

    /* 마크다운 텍스트 */
    .stMarkdown p {
        font-size: 15px !important;
        line-height: 1.75 !important;
        color: #d1d5db !important;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #ececec !important;
    }
    .stMarkdown li {
        color: #d1d5db !important;
    }
    .stMarkdown strong {
        color: #ececec !important;
    }

    /* 코드 블록 */
    code {
        background: #1a1a1a !important;
        color: #e06c75 !important;
        border-radius: 4px !important;
        padding: 2px 5px !important;
        font-size: 13px !important;
    }
    pre {
        background: #1a1a1a !important;
        border-radius: 8px !important;
        border: 1px solid #333 !important;
    }

    /* 테이블 */
    table {
        border-color: #424242 !important;
    }
    th {
        background: #2f2f2f !important;
        color: #ececec !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        border-color: #424242 !important;
    }
    td {
        font-size: 13px !important;
        color: #d1d5db !important;
        border-color: #424242 !important;
        background: transparent !important;
    }

    /* 워닝 메시지 */
    .stWarning {
        background: #2f2f2f !important;
        color: #ececec !important;
        border-radius: 10px !important;
    }

    /* 스피너 */
    .stSpinner > div {
        color: #8e8ea0 !important;
    }

    /* 스크롤바 */
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #212121;
    }
    ::-webkit-scrollbar-thumb {
        background: #424242;
        border-radius: 3px;
    }

    /* 모바일 반응형 */
    @media (max-width: 768px) {
        .block-container { padding: 0.3rem 0.5rem 5rem; }
        .stMarkdown p { font-size: 14px !important; }
    }

    /* Streamlit 기본 요소 숨기기 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


MODELS = {
    "GPT-5.4 mini (빠름, 저렴)": "gpt-5.4-mini",
    "GPT-5.4 (최고 성능)": "gpt-5.4",
}

# 제품 / 언어 / 모델 / 새 대화 버튼
col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
with col1:
    product = st.selectbox("Product / 제품", list(PRODUCTS.keys()), index=0)
with col2:
    lang = st.selectbox("Language / 언어", list(LANGUAGES.keys()), index=0)
with col3:
    model_name = st.selectbox("Model", list(MODELS.keys()), index=0)
with col4:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(LANGUAGES[lang]["new_chat"], use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": LANGUAGES[lang]["greeting"]}
        ]
        st.rerun()

lang_cfg = LANGUAGES[lang]
st.caption(lang_cfg["caption"])

# 클라이언트 초기화
try:
    openai_client, collections = init_clients()
except Exception as e:
    st.error(f"초기화 실패: {e}")
    st.stop()

collection = collections.get(product)
if collection is None:
    st.warning("해당 제품의 문서가 아직 준비되지 않았습니다. / Documents not yet available for this product.")
    st.stop()

# 채팅 히스토리
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": lang_cfg["greeting"]}
    ]

# 이전 메시지 표시
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 사용자 입력
if prompt := st.chat_input(lang_cfg["placeholder"]):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # 관련 문서 검색
        context_docs = search_docs(collection, openai_client, prompt)
        # 스트리밍 답변
        stream = stream_answer(openai_client, prompt, context_docs, lang, st.session_state.messages, product, MODELS[model_name])
        answer = st.write_stream(stream)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()
