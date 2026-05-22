"""Prompt builder for WESS product-support answers."""
from __future__ import annotations

from .config import LANGUAGES, normalize_language
from .products import PRODUCTS, ProductSpec, question_needs_context


def _bullet_list(items: tuple[str, ...]) -> str:
    return "\n".join(f"- {item}" for item in items)


def build_system_prompt(
    product_key: str,
    context: str,
    language: str = "한국어",
    *,
    retrieval_summary: str = "",
) -> str:
    """Build one consistent support prompt for Streamlit and API."""
    lang = normalize_language(language)
    lang_cfg = LANGUAGES[lang]
    spec: ProductSpec = PRODUCTS[product_key]

    source_policy = (
        "Evidence policy:\n"
        "- Use the provided [Product Documents] as the primary source of truth.\n"
        "- Do not invent parameter values, wiring details, menu paths, or specifications that are not supported by the documents.\n"
        "- Do not invent abbreviations, acronyms, or alternative names for product features, sensor types, or calibration methods. Use only the exact terms that literally appear in the [Product Documents] (e.g. 'Clamp-on', not 'CL type').\n"
        "- Do not use 'CL' or 'SP' as abbreviations for sensor types; write the exact terms 'Clamp-on' and 'Spool-piece' instead.\n"
        "- Never claim that a term 'comes from the manual', 'is in the product documents', or 'is the official wording' unless that exact term literally appears in the [Product Documents] above. If unsure, say it is your interpretation.\n"
        "- If the user uses an abbreviation or term that is not in the [Product Documents], ask which official term they mean instead of guessing.\n"
        "- If the documents are insufficient, say what is missing and ask the minimum clarifying questions.\n"
        "- Do not cite table/figure/chapter numbers such as '표 3-3' or 'Figure 2.1'; explain the content directly because the customer may not have the manual.\n"
        "- If documents conflict, mention that versions may differ and give the safest next check.\n"
    )

    answer_shape = (
        "Answer style:\n"
        "- Be practical, conversational, and helpful for a customer, field engineer, or sales/support engineer.\n"
        "- For general product introduction, feature explanation, comparison, sales-support questions, wording help, and simple background questions: answer directly and naturally. You may synthesize the documents into an easier explanation instead of only quoting them.\n"
        "- If the question asks for a broad explanation and the documents only partly cover it, give a useful best-effort answer, clearly separating document-supported facts from general interpretation.\n"
        "- For troubleshooting, installation, wiring, calibration, parameter setting, output setting, relay behavior, sensor, or measurement-error questions: ask 1 to 3 short clarifying questions first if required details are missing.\n"
        "- If enough information is available, answer in this order when useful: 1) short conclusion, 2) procedure/checklist, 3) normal/abnormal interpretation, 4) cautions, 5) next question or next action.\n"
        "- If making an assumption is unavoidable, state the assumption before the answer.\n"
        "- Keep menu names, product names, and parameter names exact.\n"
        "- In Korean answers, use '보정' for Calibration and do not use '교정'.\n"
        "- For ENV200 density meter calibration, never describe 1-point calibration; it supports only 2-point to 5-point calibration.\n"
        "- For measurement instability, recommend checking signal/installation/sensor condition before changing critical parameters.\n"
        "- For relay questions, clarify contact open/close condition and alarm/action direction to prevent field wiring mistakes.\n"
        f"- {lang_cfg['lang_rule']}\n"
        f"- If truly no relevant information exists, still try to explain the likely meaning or next check when it is safe, but explicitly say that the product documents do not confirm it. If no safe answer is possible, say: '{lang_cfg['unknown']}'\n"
    )

    product_policy = (
        f"Product context:\n"
        f"- Product: {spec.key} ({spec.display_name})\n"
        f"- Description: {spec.description}\n"
        f"- Channel: {spec.channel}\n"
        "- Preferred terms for this product:\n"
        f"{_bullet_list(spec.preferred_terms)}\n"
        "- Terms that must not be used unless the user explicitly asks or the document clearly supports them:\n"
        f"{_bullet_list(spec.forbidden_terms)}\n"
        "- Details that often change the correct answer:\n"
        f"{_bullet_list(spec.required_context_fields)}\n"
    )

    retrieval_block = f"\n[Retrieval Summary]\n{retrieval_summary}\n" if retrieval_summary else ""
    return (
        f"You are a {spec.answer_role}.\n\n"
        + source_policy
        + "\n"
        + answer_shape
        + "\n"
        + product_policy
        + retrieval_block
        + f"\n[Product Documents]\n{context}\n"
    )


def build_product_conflict_message(selected_product: str, detected_product: str, language: str = "한국어") -> str:
    lang = normalize_language(language)
    if lang == "한국어":
        return (
            f"선택된 제품은 {selected_product}인데, 질문 내용은 {detected_product}에 더 가까워 보입니다. "
            f"어느 제품 기준으로 답변할까요? ({selected_product} / {detected_product})"
        )
    return (
        f"The selected product is {selected_product}, but the question appears closer to {detected_product}. "
        f"Which product should I use as the basis? ({selected_product} / {detected_product})"
    )


def build_low_evidence_message(product_key: str, language: str = "한국어") -> str:
    lang = normalize_language(language)
    spec = PRODUCTS[product_key]
    if lang == "한국어":
        return (
            f"{spec.key} 문서에서 질문과 직접 관련된 근거를 충분히 찾지 못했습니다. "
            "제품 모델, 증상, 현재 설정값, 설치 조건 중 확인 가능한 정보를 알려주시면 더 정확히 답변하겠습니다."
        )
    return (
        f"I could not find enough directly relevant evidence in the {spec.key} documents. "
        "Please provide the product model, symptom, current settings, or installation condition for a more accurate answer."
    )


def build_clarification_hint(question: str, product_key: str, language: str = "한국어") -> str:
    """Optional short reminder appended to user message when a question is likely under-specified."""
    if not question_needs_context(question):
        return ""
    spec = PRODUCTS[product_key]
    lang = normalize_language(language)
    fields = ", ".join(spec.required_context_fields[:4])
    if lang == "한국어":
        return f"\n\n[주의] 답변이 조건에 따라 달라질 수 있습니다. 필요하면 먼저 다음 정보를 짧게 질문하세요: {fields}."
    return f"\n\n[Note] The answer may depend on conditions. If needed, ask briefly for: {fields}."
