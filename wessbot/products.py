"""Product definitions and product auto-detection for WESS chatbot."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Dict, Iterable, Optional


@dataclass(frozen=True)
class ProductSpec:
    """Static support metadata for one WESS product."""

    key: str
    api_key: str
    collection: str
    display_name: str
    korean_name: str
    description: str
    channel: str
    answer_role: str
    required_context_fields: tuple[str, ...]
    preferred_terms: tuple[str, ...]
    forbidden_terms: tuple[str, ...]
    aliases: tuple[str, ...]
    sample_questions: tuple[str, ...]


PRODUCTS: Dict[str, ProductSpec] = {
    "ENV200": ProductSpec(
        key="ENV200",
        api_key="density",
        collection="wess_density",
        display_name="ENV200 / Density Meter / 농도계",
        korean_name="농도계",
        description="Ultrasonic sludge density meter for density/concentration measurement.",
        channel="single",
        answer_role="product support specialist for ultrasonic sludge density meter (ENV200)",
        required_context_fields=("fluid/sludge type", "pipe size", "installation type", "calibration status", "output setting"),
        preferred_terms=(
            "EEA", "Detection Area", "Density", "농도", "Damping", "댐핑", "Pipe Diameter",
            "배관 외경", "Calibration", "보정", "AGC", "Profile", "Clamp-on", "Spool-piece",
            "%", "ppm", "mg/L", "g/L",
        ),
        forbidden_terms=(
            "Threshold/문턱전압", "Echo AMP/수신감도", "ASF", "Light/Heavy", "CH1/CH2",
            "Level/Distance", "m/ft as level units",
        ),
        aliases=("ENV200", "ENV-200", "농도계", "density", "concentration", "eea", "agc", "profile", "clamp-on", "spool"),
        sample_questions=(
            "ENV200에서 EEA 보정은 어떻게 하나요?",
            "농도계 4-20mA 출력 설정 방법 알려줘",
            "측정값이 흔들릴 때 확인할 항목은?",
        ),
    ),
    "ENV130": ProductSpec(
        key="ENV130",
        api_key="interface",
        collection="wess_interface",
        display_name="ENV130 / Interface Meter / 계면계",
        korean_name="계면계",
        description="Dual-channel ultrasonic sludge interface meter.",
        channel="dual / CH1, CH2",
        answer_role="product support specialist for ultrasonic sludge interface meter (ENV130)",
        required_context_fields=("channel CH1/CH2", "tank/site condition", "sensor type", "Threshold", "Echo AMP", "relay/output setting"),
        preferred_terms=(
            "Threshold", "문턱전압", "Echo AMP", "수신감도", "ASF", "Light", "Heavy",
            "Damping", "댐핑", "Level", "Distance", "Echo", "CH1", "CH2", "m", "ft",
        ),
        forbidden_terms=(
            "EEA", "Detection Area", "Pipe Diameter", "AGC", "Profile", "Clamp-on", "Spool-piece",
            "density units %, ppm, mg/L, g/L",
        ),
        aliases=("ENV130", "ENV-130", "계면계", "interface", "threshold", "문턱", "echo amp", "수신감도", "light", "heavy", "ch1", "ch2"),
        sample_questions=(
            "ENV130 Threshold 설정 방법 알려줘",
            "CH1 CH2 계면 측정이 이상할 때 확인할 것",
            "R1 릴레이 동작 조건 설명해줘",
        ),
    ),
    "ENV120": ProductSpec(
        key="ENV120",
        api_key="interface_120",
        collection="wess_interface_120",
        display_name="ENV120 / Interface Meter / 계면계",
        korean_name="계면계",
        description="Single-channel ultrasonic sludge interface meter.",
        channel="single",
        answer_role="product support specialist for ultrasonic sludge interface meter (ENV120)",
        required_context_fields=("tank/site condition", "sensor type", "Threshold", "Echo AMP", "relay/output setting", "measurement symptom"),
        preferred_terms=(
            "Threshold", "문턱전압", "Echo AMP", "수신감도", "ASF", "Damping", "댐핑",
            "Level", "Distance", "Echo", "m", "ft", "sensor cleaning", "센서 세정장치",
        ),
        forbidden_terms=(
            "EEA", "Detection Area", "Pipe Diameter", "AGC", "Profile", "Clamp-on", "Spool-piece",
            "Light/Heavy", "CH1/CH2", "density units %, ppm, mg/L, g/L",
        ),
        aliases=("ENV120", "ENV-120", "interface_120", "single channel", "단채널", "threshold", "문턱", "echo amp", "수신감도", "센서 세정", "세정장치"),
        sample_questions=(
            "ENV120에서 수신감도는 언제 조정하나요?",
            "측정값이 갑자기 튈 때 점검 순서 알려줘",
            "ENV120 릴레이 설정 방법 알려줘",
        ),
    ),
}

PRODUCT_ALIASES: Dict[str, str] = {}
for key, spec in PRODUCTS.items():
    PRODUCT_ALIASES[key.lower()] = key
    PRODUCT_ALIASES[spec.api_key.lower()] = key
    for alias in spec.aliases:
        PRODUCT_ALIASES[alias.lower()] = key

# Legacy API keys and Korean UI values.
PRODUCT_ALIASES.update({
    "auto": "auto",
    "자동": "auto",
    "density": "ENV200",
    "interface": "ENV130",
    "interface_120": "ENV120",
    "env200 / density meter / 농도계": "ENV200",
    "env130 / interface meter / 계면계": "ENV130",
    "env120 / interface meter / 계면계": "ENV120",
})

AMBIGUITY_TERMS = (
    "안돼", "안되", "이상", "오류", "에러", "문제", "불량", "안나", "튀", "흔들", "불안정",
    "설정", "보정", "배선", "릴레이", "출력", "센서", "설치", "값", "측정",
    "not working", "error", "alarm", "unstable", "wrong", "calibration", "relay", "output", "wiring", "sensor",
)


def normalize_product(value: Optional[str], default: str = "ENV200") -> str:
    """Normalize UI/API product input to ENV200/ENV130/ENV120/auto."""
    if not value:
        return default
    raw = str(value).strip()
    lowered = raw.lower()
    if lowered in PRODUCT_ALIASES:
        return PRODUCT_ALIASES[lowered]
    for key in PRODUCTS:
        if key.lower() in lowered:
            return key
    return default


def _alias_score(query_l: str, aliases: Iterable[str]) -> int:
    score = 0
    for alias in aliases:
        a = alias.lower()
        if not a or len(a) < 2:
            continue
        if a in query_l:
            score += 3 if a.startswith("env") else 1
    return score


def detect_product(question: str, selected: str = "auto") -> tuple[str, bool, dict[str, int]]:
    """Detect product from question and selected UI value.

    Returns (product_key, conflict, score_by_product). conflict=True means the user selected
    one product but the question strongly mentions another product.
    """
    normalized = normalize_product(selected, default="auto")
    q = (question or "").lower()
    scores: dict[str, int] = {}
    for key, spec in PRODUCTS.items():
        score = _alias_score(q, (key, spec.api_key, spec.korean_name, *spec.aliases))
        # Explicit model mention is decisive.
        if re.search(rf"\b{key.lower()}\b", q):
            score += 10
        scores[key] = score

    detected = max(scores, key=scores.get)
    if scores[detected] <= 0:
        return (normalized if normalized != "auto" else "ENV200", False, scores)

    if normalized != "auto" and normalized in PRODUCTS and detected != normalized and scores[detected] >= 4:
        return detected, True, scores
    return (detected if normalized == "auto" else normalized), False, scores


def question_needs_context(question: str) -> bool:
    q = (question or "").lower()
    return any(term.lower() in q for term in AMBIGUITY_TERMS)
