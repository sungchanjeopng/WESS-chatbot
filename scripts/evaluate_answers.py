"""Lightweight WESS chatbot evaluation helpers.

This script intentionally has a no-OpenAI mode so product routing can be checked
in CI or local development without API credentials.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from wessbot.products import detect_product  # noqa: E402
from wessbot.rag import WessRagEngine  # noqa: E402

FOLLOWUP_CASES = [
    {
        "history": [{"role": "user", "content": "ENV120 수신감도 조정 방법 알려줘"}],
        "question": "그건 언제 조정해?",
        "must_contain": "ENV120",
    },
    {
        "history": [{"role": "user", "content": "ENV130 Threshold 설정 방법"}],
        "question": "좀 더 자세히 알려줘",
        "must_contain": "Threshold",
    },
]


def load_cases(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_product_detection(cases: list[dict]) -> tuple[int, list[str]]:
    failures: list[str] = []
    for case in cases:
        question = case["question"]
        expected = case["expected_product"]
        detected, conflict, scores = detect_product(question, "auto")
        if detected != expected:
            failures.append(f"FAIL product: {question!r} expected={expected} detected={detected} scores={scores}")
    return len(cases) - len(failures), failures


def evaluate_followup_queries(cases: list[dict]) -> tuple[int, list[str]]:
    failures: list[str] = []
    for case in cases:
        query = WessRagEngine.build_search_query(case["question"], case["history"])
        if case["must_contain"] not in query:
            failures.append(
                f"FAIL followup: {case['question']!r} expected query to contain {case['must_contain']!r}, got {query!r}"
            )
    return len(cases) - len(failures), failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", default=str(ROOT / "eval" / "eval_cases.json"))
    args = parser.parse_args(argv)

    cases = load_cases(Path(args.cases))
    passed, failures = evaluate_product_detection(cases)
    print(f"product-detection: {passed}/{len(cases)} passed")
    followup_passed, followup_failures = evaluate_followup_queries(FOLLOWUP_CASES)
    print(f"followup-query: {followup_passed}/{len(FOLLOWUP_CASES)} passed")
    failures += followup_failures
    for failure in failures:
        print(failure)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
