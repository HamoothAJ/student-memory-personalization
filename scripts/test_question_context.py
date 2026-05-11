import sys
from typing import Dict, List

import requests


BASE_URL = "http://127.0.0.1:8000"


TEST_CASES: List[Dict[str, object]] = [
    {
        "name": "percent question",
        "expected_skill_id": 312,
        "expected_skill_name": "Percent Of",
        "expected_needs_review": False,
        "payload": {
            "student_id": 999001,
            "session_id": 7001,
            "question": "Can you explain how to find 25 percent of 80?"
        }
    },
    {
        "name": "fraction question",
        "expected_skill_id": 415,
        "expected_skill_name": "Addition and Subtraction Fractions",
        "expected_needs_review": False,
        "payload": {
            "student_id": 999001,
            "session_id": 7001,
            "question": "Can you explain how to add fractions with different denominators?"
        }
    },
    {
        "name": "equation question",
        "expected_skill_id": 101,
        "expected_skill_name": "Equation Solving Two or Fewer Steps",
        "expected_needs_review": False,
        "payload": {
            "student_id": 999001,
            "session_id": 7001,
            "question": "How do I solve this equation for x?"
        }
    },
    {
        "name": "unclear question",
        "expected_skill_id": None,
        "expected_skill_name": None,
        "expected_needs_review": True,
        "payload": {
            "student_id": 999001,
            "session_id": 7001,
            "question": "Can you help me understand this?"
        }
    }
]


def assert_response_shape(test_name: str, response_json: Dict[str, object]) -> None:
    detected_topic = response_json.get("detected_topic", {})
    topic_memory = response_json.get("topic_memory", {})

    required_topic_fields = {
        "skill_id",
        "skill_name",
        "canonical_skill_name",
        "confidence",
        "method",
        "needs_review",
    }
    required_memory_fields = {
        "skill_id",
        "skill_name",
        "total_interactions",
        "correct_count",
        "wrong_count",
        "accuracy",
        "total_hints",
        "avg_hints",
        "avg_attempts",
        "avg_response_time_ms",
    }

    missing_topic_fields = required_topic_fields.difference(detected_topic.keys())
    missing_memory_fields = required_memory_fields.difference(topic_memory.keys())

    if missing_topic_fields:
        raise AssertionError(
            f"{test_name}: missing detected_topic fields {sorted(missing_topic_fields)}"
        )

    if missing_memory_fields:
        raise AssertionError(
            f"{test_name}: missing topic_memory fields {sorted(missing_memory_fields)}"
        )

    if response_json.get("recommendation_context") is None:
        raise AssertionError(f"{test_name}: recommendation_context is missing")


def main() -> int:
    try:
        health_response = requests.get(f"{BASE_URL}/", timeout=5)
        health_response.raise_for_status()
    except requests.RequestException as error:
        print(f"Backend is not reachable at {BASE_URL}: {error}")
        return 1

    failures = []

    for test_case in TEST_CASES:
        name = str(test_case["name"])
        payload = test_case["payload"]

        try:
            response = requests.post(
                f"{BASE_URL}/memory/question-context",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            response_json = response.json()
            assert_response_shape(name, response_json)
            detected_topic = response_json["detected_topic"]

            if detected_topic["needs_review"] != test_case["expected_needs_review"]:
                raise AssertionError(
                    f"{name}: expected needs_review "
                    f"{test_case['expected_needs_review']}, got "
                    f"{detected_topic['needs_review']}"
                )

            if detected_topic["skill_id"] != test_case["expected_skill_id"]:
                raise AssertionError(
                    f"{name}: expected skill_id {test_case['expected_skill_id']}, "
                    f"got {detected_topic['skill_id']}"
                )

            if detected_topic["skill_name"] != test_case["expected_skill_name"]:
                raise AssertionError(
                    f"{name}: expected skill_name {test_case['expected_skill_name']}, "
                    f"got {detected_topic['skill_name']}"
                )

            if detected_topic["needs_review"]:
                if response_json.get("topic_memory") is not None:
                    raise AssertionError(f"{name}: topic_memory should be null")
                support_need = response_json["recommendation_context"]["support_need"]
                if support_need != "topic_clarification_needed":
                    raise AssertionError(
                        f"{name}: expected topic_clarification_needed, got {support_need}"
                    )
            else:
                if response_json.get("topic_memory") is None:
                    raise AssertionError(f"{name}: topic_memory is missing")

            print(f"PASS: {name} -> {response_json['detected_topic']}")
        except Exception as error:
            failures.append((name, str(error)))
            print(f"FAIL: {name} -> {error}")

    if failures:
        print("\nFailures:")
        for name, error in failures:
            print(f"- {name}: {error}")
        return 1

    print("\nAll question-context tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
