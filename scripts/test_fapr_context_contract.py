import sys
from typing import Dict, List

import requests


BASE_URL = "http://127.0.0.1:8000"
TEST_STUDENT_ID = 999951
TEST_SESSION_ID = 8101


TEST_INTERACTIONS: List[Dict[str, object]] = [
    {
        "student_id": TEST_STUDENT_ID,
        "session_id": TEST_SESSION_ID,
        "problem_id": 9101,
        "concept_name": "Percent Of",
        "correct": 0,
        "attempt_count": 2,
        "hint_count": 1,
        "hint_total": 3,
        "response_time_ms": 18000
    },
    {
        "student_id": TEST_STUDENT_ID,
        "session_id": TEST_SESSION_ID,
        "problem_id": 9102,
        "concept_name": "Percent Of",
        "correct": 1,
        "attempt_count": 1,
        "hint_count": 0,
        "hint_total": 3,
        "response_time_ms": 9000
    }
]


TOP_LEVEL_FIELDS = {
    "student_id",
    "session_id",
    "current_skill_id",
    "current_skill_name",
    "recent_interactions",
    "current_attempt",
    "previous_repair",
    "last_student_utterance",
}

RECENT_INTERACTION_FIELDS = {
    "order_id",
    "skill_id",
    "correct",
    "hint_count",
    "attempt_count",
    "ms_first_response",
}

CURRENT_ATTEMPT_FIELDS = {
    "skill_id",
    "correct",
    "hint_count",
    "attempt_count",
    "ms_first_response",
}


def post_test_interactions() -> None:
    for payload in TEST_INTERACTIONS:
        response = requests.post(
            f"{BASE_URL}/memory/update",
            json=payload,
            timeout=10
        )
        response.raise_for_status()


def assert_fapr_contract(payload: Dict[str, object]) -> None:
    if set(payload.keys()) != TOP_LEVEL_FIELDS:
        raise AssertionError(
            f"Top-level fields mismatch. Got {sorted(payload.keys())}"
        )

    if payload["student_id"] != str(TEST_STUDENT_ID):
        raise AssertionError("student_id should be a string matching the test student")

    if payload["session_id"] != str(TEST_SESSION_ID):
        raise AssertionError("session_id should be a string matching the test session")

    if payload["current_skill_id"] != 312:
        raise AssertionError(f"Expected current_skill_id 312, got {payload['current_skill_id']}")

    if payload["current_skill_name"] != "Percent Of":
        raise AssertionError(
            f"Expected current_skill_name Percent Of, got {payload['current_skill_name']}"
        )

    recent_interactions = payload["recent_interactions"]
    if not isinstance(recent_interactions, list) or len(recent_interactions) == 0:
        raise AssertionError("recent_interactions must be a non-empty list")

    order_ids = []
    for interaction in recent_interactions:
        if set(interaction.keys()) != RECENT_INTERACTION_FIELDS:
            raise AssertionError(
                f"Recent interaction fields mismatch. Got {sorted(interaction.keys())}"
            )
        order_ids.append(interaction["order_id"])
        if interaction["skill_id"] != 312:
            raise AssertionError(f"Expected interaction skill_id 312, got {interaction['skill_id']}")

    if order_ids != sorted(order_ids):
        raise AssertionError("recent_interactions must be ordered oldest to newest")

    current_attempt = payload["current_attempt"]
    if set(current_attempt.keys()) != CURRENT_ATTEMPT_FIELDS:
        raise AssertionError(
            f"Current attempt fields mismatch. Got {sorted(current_attempt.keys())}"
        )

    if current_attempt["skill_id"] != 312:
        raise AssertionError(f"Expected current_attempt skill_id 312, got {current_attempt['skill_id']}")


def main() -> int:
    try:
        health_response = requests.get(f"{BASE_URL}/", timeout=5)
        health_response.raise_for_status()
        post_test_interactions()

        response = requests.get(
            f"{BASE_URL}/memory/fapr-context/{TEST_STUDENT_ID}",
            params={
                "session_id": TEST_SESSION_ID,
                "current_skill_id": 312,
                "current_skill_name": "Percent Of",
                "limit": 2
            },
            timeout=10
        )
        response.raise_for_status()
        payload = response.json()

        assert_fapr_contract(payload)
        print("PASS: FAPR-LB context contract is valid.")
        print(payload)
        return 0
    except Exception as error:
        print(f"FAIL: FAPR-LB context contract test failed: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
