import sys
from pathlib import Path
from typing import Dict, List, Optional


REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from topic_extractor import TopicExtractor


TEST_CASES: List[Dict[str, object]] = [
    {
        "name": "percent question",
        "question": "Can you explain how to find 25 percent of 80?",
        "expected_skill_id": 312,
        "expected_skill_name": "Percent Of",
        "expected_needs_review": False,
    },
    {
        "name": "fraction question",
        "question": "Can you explain how to add fractions with different denominators?",
        "expected_skill_id": 415,
        "expected_skill_name": "Addition and Subtraction Fractions",
        "expected_needs_review": False,
    },
    {
        "name": "equation question",
        "question": "How do I solve this equation for x?",
        "expected_skill_id": 101,
        "expected_skill_name": "Equation Solving Two or Fewer Steps",
        "expected_needs_review": False,
    },
    {
        "name": "median question",
        "question": "How do I find the middle value in a list of numbers?",
        "expected_skill_id": 502,
        "expected_skill_name": "Median",
        "expected_needs_review": False,
    },
    {
        "name": "unclear question",
        "question": "Can you help me understand this?",
        "expected_skill_id": None,
        "expected_skill_name": None,
        "expected_needs_review": True,
    },
]


def assert_prediction(
    test_name: str,
    prediction: Dict[str, object],
    expected_skill_id: Optional[int],
    expected_skill_name: Optional[str],
    expected_needs_review: bool,
) -> None:
    required_fields = {
        "skill_id",
        "skill_name",
        "canonical_skill_name",
        "confidence",
        "method",
        "needs_review",
    }
    missing_fields = required_fields.difference(prediction.keys())
    if missing_fields:
        raise AssertionError(
            f"{test_name}: missing fields {sorted(missing_fields)}"
        )

    if prediction["needs_review"] != expected_needs_review:
        raise AssertionError(
            f"{test_name}: expected needs_review {expected_needs_review}, "
            f"got {prediction['needs_review']}"
        )

    if prediction["skill_id"] != expected_skill_id:
        raise AssertionError(
            f"{test_name}: expected skill_id {expected_skill_id}, "
            f"got {prediction['skill_id']}"
        )

    if prediction["skill_name"] != expected_skill_name:
        raise AssertionError(
            f"{test_name}: expected skill_name {expected_skill_name}, "
            f"got {prediction['skill_name']}"
        )

    if expected_needs_review:
        if prediction["canonical_skill_name"] is not None:
            raise AssertionError(
                f"{test_name}: canonical_skill_name should be null"
            )
    elif prediction["canonical_skill_name"] is None:
        raise AssertionError(f"{test_name}: canonical_skill_name is missing")


def main() -> int:
    extractor = TopicExtractor()
    print("TopicExtractor embedding status:", extractor.embedding_status)

    failures = []

    for test_case in TEST_CASES:
        name = str(test_case["name"])
        prediction = extractor.detect_topic(str(test_case["question"]))

        try:
            assert_prediction(
                test_name=name,
                prediction=prediction,
                expected_skill_id=test_case["expected_skill_id"],
                expected_skill_name=test_case["expected_skill_name"],
                expected_needs_review=bool(test_case["expected_needs_review"]),
            )
            print(f"PASS: {name} -> {prediction}")
        except Exception as error:
            failures.append((name, str(error), prediction))
            print(f"FAIL: {name} -> {error}; prediction={prediction}")

    if failures:
        print("\nFailures:")
        for name, error, prediction in failures:
            print(f"- {name}: {error}; prediction={prediction}")
        return 1

    print("\nPASS: Pre-trained topic extractor contract is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
