import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests


BASE_URL = "http://127.0.0.1:8000"
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_TABLES_DIR = REPO_ROOT / "outputs" / "tables"


API_EVALUATION_CASES: List[Dict[str, Any]] = [
    {
        "question": "Can you explain how to find 25 percent of 80?",
        "expected_skill_id": 312,
        "expected_skill_name": "Percent Of",
        "category": "Percent Of",
    },
    {
        "question": "What is 30 percent of 90?",
        "expected_skill_id": 312,
        "expected_skill_name": "Percent Of",
        "category": "Percent Of",
    },
    {
        "question": "Can you explain how to add fractions with different denominators?",
        "expected_skill_id": 415,
        "expected_skill_name": "Addition and Subtraction Fractions",
        "category": "Addition and Subtraction Fractions",
    },
    {
        "question": "How do I subtract fractions with a common denominator?",
        "expected_skill_id": 415,
        "expected_skill_name": "Addition and Subtraction Fractions",
        "category": "Addition and Subtraction Fractions",
    },
    {
        "question": "How do I solve this equation for x?",
        "expected_skill_id": 101,
        "expected_skill_name": "Equation Solving Two or Fewer Steps",
        "category": "Equation Solving Two or Fewer Steps",
    },
    {
        "question": "How do I find the middle value in a list of numbers?",
        "expected_skill_id": 502,
        "expected_skill_name": "Median",
        "category": "Median",
    },
    {
        "question": "Can you help me understand this?",
        "expected_skill_id": None,
        "expected_skill_name": None,
        "category": "unclear",
    },
    {
        "question": "I need help with this.",
        "expected_skill_id": None,
        "expected_skill_name": None,
        "category": "unclear",
    },
]


def ensure_output_dir() -> None:
    OUTPUT_TABLES_DIR.mkdir(parents=True, exist_ok=True)


def call_question_context(
    student_id: int,
    session_id: int,
    question: str,
) -> Dict[str, Any]:
    response = requests.post(
        f"{BASE_URL}/memory/question-context",
        json={
            "student_id": student_id,
            "session_id": session_id,
            "question": question,
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def evaluate_api_case(
    index: int,
    test_case: Dict[str, Any],
) -> Dict[str, Any]:
    payload = call_question_context(
        student_id=999500 + index,
        session_id=8800 + index,
        question=test_case["question"],
    )
    detected_topic = payload.get("detected_topic") or {}
    expected_skill_id = test_case["expected_skill_id"]
    is_unclear = expected_skill_id is None

    if is_unclear:
        passed = (
            detected_topic.get("needs_review") is True
            and detected_topic.get("skill_id") is None
            and payload.get("topic_memory") is None
        )
    else:
        passed = (
            detected_topic.get("skill_id") == expected_skill_id
            and payload.get("topic_memory") is not None
        )

    recommendation_context = payload.get("recommendation_context") or {}

    return {
        "question": test_case["question"],
        "expected_skill_id": expected_skill_id,
        "expected_skill_name": test_case["expected_skill_name"],
        "predicted_skill_id": detected_topic.get("skill_id"),
        "predicted_skill_name": detected_topic.get("skill_name"),
        "confidence": detected_topic.get("confidence"),
        "method": detected_topic.get("method"),
        "needs_review": detected_topic.get("needs_review"),
        "topic_memory_present": payload.get("topic_memory") is not None,
        "support_need": recommendation_context.get("support_need"),
        "category": test_case["category"],
        "status": "PASS" if passed else "FAIL",
    }


def safe_accuracy(passed_count: int, total_count: int) -> Optional[float]:
    if total_count == 0:
        return None

    return round(passed_count / total_count, 4)


def print_summary(results: List[Dict[str, Any]]) -> None:
    total_count = len(results)
    passed_count = len([row for row in results if row["status"] == "PASS"])
    failed_rows = [row for row in results if row["status"] == "FAIL"]

    print("\nQuestion Context API Evaluation Summary")
    print(f"Total: {total_count}")
    print(f"PASS: {passed_count}")
    print(f"FAIL: {len(failed_rows)}")
    print(f"Accuracy: {safe_accuracy(passed_count, total_count):.2f}")

    if failed_rows:
        print("\nFailed Cases:")
        for row in failed_rows:
            print(
                "- "
                f"{row['category']}: {row['question']} | "
                f"expected={row['expected_skill_name']} "
                f"({row['expected_skill_id']}), "
                f"predicted={row['predicted_skill_name']} "
                f"({row['predicted_skill_id']}), "
                f"confidence={row['confidence']}, method={row['method']}"
            )
    else:
        print("\nFailed Cases: none")


def main() -> int:
    ensure_output_dir()

    try:
        health_response = requests.get(f"{BASE_URL}/", timeout=5)
        health_response.raise_for_status()
    except requests.RequestException as error:
        print(
            f"Backend is not reachable at {BASE_URL}: {error}. "
            "Start the FastAPI backend before running this API evaluation."
        )
        return 1

    try:
        results = [
            evaluate_api_case(index, test_case)
            for index, test_case in enumerate(API_EVALUATION_CASES, start=1)
        ]
    except Exception as error:
        print(f"FAIL: Question context API evaluation failed: {error}")
        return 1

    output_path = OUTPUT_TABLES_DIR / "question_context_api_evaluation_results.csv"
    pd.DataFrame(results).to_csv(output_path, index=False)

    print_summary(results)
    print(f"\nSaved output: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
