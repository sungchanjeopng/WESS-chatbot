"""Configuration and language resources for WESS chatbot."""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", str(BASE_DIR / "chroma_db")))
DEFAULT_EMBEDDING_MODEL = os.getenv("WESS_EMBEDDING_MODEL", "text-embedding-3-small")
DEFAULT_CHAT_MODEL = os.getenv("WESS_CHAT_MODEL", "gpt-5.5")
FAST_CHAT_MODEL = os.getenv("WESS_FAST_MODEL", "gpt-5.5")
# openai: normal OPENAI_API_KEY path. codex-oauth: experimental ChatGPT Codex OAuth path for chat only.
DEFAULT_CHAT_PROVIDER = os.getenv("WESS_CHAT_PROVIDER", "openai").strip().lower()
DEFAULT_N_RESULTS = int(os.getenv("WESS_RAG_N_RESULTS", "18"))
MAX_HISTORY_MESSAGES = int(os.getenv("WESS_MAX_HISTORY_MESSAGES", "16"))
MAX_CONTEXT_CHARS = int(os.getenv("WESS_MAX_CONTEXT_CHARS", "18000"))

MODEL_OPTIONS = {
    "빠른 답변": FAST_CHAT_MODEL,
    "정밀 답변": DEFAULT_CHAT_MODEL,
}

LANGUAGES = {
    "English": {
        "code": "en",
        "greeting": "Hello!",
        "placeholder": "Type your question...",
        "spinner": "Generating answer...",
        "new_chat": "New Chat",
        "unknown": "The requested information could not be found in the product documents. Please contact customer support at 041-584-8820.",
        "lang_rule": "Answer only in English. Translate Korean source content into natural English. Keep product names and menu names as-is when helpful.",
    },
    "한국어": {
        "code": "ko",
        "greeting": "안녕하세요.",
        "placeholder": "질문을 입력하세요...",
        "spinner": "답변을 생성하고 있습니다...",
        "new_chat": "새 대화",
        "unknown": "문서에서 해당 정보를 확인하지 못했습니다. 추가 문의는 고객지원(041-584-8820)으로 연락해주세요.",
        "lang_rule": "반드시 한국어로 답변하세요. 영어 문서를 참조하더라도 자연스러운 한국어로 번역해 답변하세요. 제품명, 모델명, 메뉴명은 필요하면 원문을 병기하세요.",
    },
    "日本語": {
        "code": "ja",
        "greeting": "こんにちは。",
        "placeholder": "質問を入力してください...",
        "spinner": "回答を生成しています...",
        "new_chat": "新しい会話",
        "unknown": "該当情報は製品資料で確認できませんでした。詳細はカスタマーサポート(041-584-8820)までお問い合わせください。",
        "lang_rule": "必ず日本語で回答してください。韓国語や英語の資料は自然な日本語に翻訳してください。製品名やメニュー名は必要に応じて原文を残してください。",
    },
    "中文": {
        "code": "zh",
        "greeting": "您好！",
        "placeholder": "请输入您的问题...",
        "spinner": "正在生成回答...",
        "new_chat": "新对话",
        "unknown": "在产品资料中未找到该信息。请联系客户支持：041-584-8820。",
        "lang_rule": "必须仅用中文回答。请将韩文或英文资料自然翻译成中文；产品名和菜单名可保留原文。",
    },
    "Español": {
        "code": "es",
        "greeting": "¡Hola!",
        "placeholder": "Escriba su pregunta...",
        "spinner": "Generando respuesta...",
        "new_chat": "Nueva conversación",
        "unknown": "No se encontró la información en los documentos del producto. Contacte al soporte al cliente al 041-584-8820.",
        "lang_rule": "Responde solo en español. Traduce el contenido coreano o inglés de forma natural. Mantén nombres de productos y menús cuando sea útil.",
    },
    "Français": {
        "code": "fr",
        "greeting": "Bonjour.",
        "placeholder": "Tapez votre question...",
        "spinner": "Génération de la réponse...",
        "new_chat": "Nouvelle conversation",
        "unknown": "L'information demandée n'a pas été trouvée dans les documents produit. Veuillez contacter le support client au 041-584-8820.",
        "lang_rule": "Répondez uniquement en français. Traduisez naturellement les sources coréennes ou anglaises. Gardez les noms de produits et de menus si utile.",
    },
    "Deutsch": {
        "code": "de",
        "greeting": "Hallo.",
        "placeholder": "Geben Sie Ihre Frage ein...",
        "spinner": "Antwort wird generiert...",
        "new_chat": "Neues Gespräch",
        "unknown": "Die Information wurde in den Produktunterlagen nicht gefunden. Bitte kontaktieren Sie den Kundensupport unter 041-584-8820.",
        "lang_rule": "Antworte ausschließlich auf Deutsch. Übersetze koreanische oder englische Quellen natürlich. Produkt- und Menünamen können beibehalten werden.",
    },
    "Português": {
        "code": "pt",
        "greeting": "Olá.",
        "placeholder": "Digite sua pergunta...",
        "spinner": "Gerando resposta...",
        "new_chat": "Nova conversa",
        "unknown": "A informação não foi encontrada nos documentos do produto. Entre em contato com o suporte ao cliente pelo 041-584-8820.",
        "lang_rule": "Responda somente em português. Traduza fontes coreanas ou inglesas naturalmente. Mantenha nomes de produtos e menus quando útil.",
    },
    "Tiếng Việt": {
        "code": "vi",
        "greeting": "Xin chào.",
        "placeholder": "Nhập câu hỏi của bạn...",
        "spinner": "Đang tạo câu trả lời...",
        "new_chat": "Cuộc trò chuyện mới",
        "unknown": "Không tìm thấy thông tin trong tài liệu sản phẩm. Vui lòng liên hệ hỗ trợ khách hàng theo số 041-584-8820.",
        "lang_rule": "Chỉ trả lời bằng tiếng Việt. Dịch tự nhiên nội dung tiếng Hàn hoặc tiếng Anh. Giữ tên sản phẩm và menu khi cần thiết.",
    },
    "ภาษาไทย": {
        "code": "th",
        "greeting": "สวัสดี",
        "placeholder": "พิมพ์คำถามของคุณ...",
        "spinner": "กำลังสร้างคำตอบ...",
        "new_chat": "แชทใหม่",
        "unknown": "ไม่พบข้อมูลนี้ในเอกสารผลิตภัณฑ์ กรุณาติดต่อฝ่ายสนับสนุนลูกค้าที่ 041-584-8820",
        "lang_rule": "ตอบเป็นภาษาไทยเท่านั้น แปลข้อมูลภาษาเกาหลีหรืออังกฤษให้เป็นธรรมชาติ คงชื่อผลิตภัณฑ์และเมนูไว้เมื่อจำเป็น",
    },
    "Bahasa Indonesia": {
        "code": "id",
        "greeting": "Halo.",
        "placeholder": "Ketik pertanyaan Anda...",
        "spinner": "Membuat jawaban...",
        "new_chat": "Obrolan baru",
        "unknown": "Informasi tidak ditemukan dalam dokumen produk. Silakan hubungi dukungan pelanggan di 041-584-8820.",
        "lang_rule": "Jawab hanya dalam Bahasa Indonesia. Terjemahkan sumber Korea atau Inggris secara alami. Pertahankan nama produk dan menu bila perlu.",
    },
    "العربية": {
        "code": "ar",
        "greeting": "مرحباً.",
        "placeholder": "اكتب سؤالك...",
        "spinner": "جاري إنشاء الإجابة...",
        "new_chat": "محادثة جديدة",
        "unknown": "لم يتم العثور على هذه المعلومات في مستندات المنتج. يرجى الاتصال بدعم العملاء على الرقم 041-584-8820.",
        "lang_rule": "أجب باللغة العربية فقط. ترجم المصادر الكورية أو الإنجليزية بشكل طبيعي. أبقِ أسماء المنتجات والقوائم كما هي عند الحاجة.",
    },
    "Русский": {
        "code": "ru",
        "greeting": "Здравствуйте.",
        "placeholder": "Введите ваш вопрос...",
        "spinner": "Генерация ответа...",
        "new_chat": "Новый чат",
        "unknown": "Информация не найдена в документах продукта. Свяжитесь со службой поддержки: 041-584-8820.",
        "lang_rule": "Отвечайте только на русском языке. Естественно переводите корейские или английские источники. Названия продуктов и меню можно сохранять.",
    },
}

LANGUAGE_ALIASES = {
    "ko": "한국어",
    "kr": "한국어",
    "korean": "한국어",
    "한국어": "한국어",
    "en": "English",
    "english": "English",
    "ja": "日本語",
    "jp": "日本語",
    "japanese": "日本語",
    "zh": "中文",
    "cn": "中文",
    "chinese": "中文",
    "es": "Español",
    "fr": "Français",
    "de": "Deutsch",
    "pt": "Português",
    "vi": "Tiếng Việt",
    "th": "ภาษาไทย",
    "id": "Bahasa Indonesia",
    "ar": "العربية",
    "ru": "Русский",
}


def normalize_language(value: str | None) -> str:
    if not value:
        return "한국어"
    raw = str(value).strip()
    if raw in LANGUAGES:
        return raw
    return LANGUAGE_ALIASES.get(raw.lower(), "한국어")
