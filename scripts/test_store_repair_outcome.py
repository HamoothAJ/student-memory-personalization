import sys
import time
from typing import Dict

import requests


BASE_URL = "http://127.0.0.1:8000"
TEST_STUDENT_ID = 999961
TEST_SKILL_ID = 312
TEST_SKILL_NAME = "Percent Of"


def assert_previous_repair_is_null(payload: Dict[str, object]) -> None:
    if payload.get("previous_repair") is not None:
        raise AssertionError(
            f"Expected previous_repair to be null, got {payload['previous_repair']}"
        )


def assert_previous_repair_is_stored(payload: Dict[str, object]) -> None:
    expected = {
        "prev_action": "prerequisite_review",
        "prev_outcome": {
            "correct": 1,
            "hint_used": 0
        }
    }

    if payload.get("previous_repair") != expected:
        raise AssertionError(
            f"Expected previous_repair {expected}, got {payload.get('previous_repair')}"
        )


def main() -> int:
    session_id = int(time.time())

    interaction_payload = {
        "student_id": TEST_STUDENT_ID,
        "session_id": session_id,
        "problem_id": 9301,
        "concept_name": TEST_SKILL_NAME,
        "correct": 0,
        "attempt_count": 2,
        "hint_count": 1,
        "hint_total": 3,
        "response_time_ms": 18000
    }

    store_payload = {
        "student_id": TEST_STUDENT_ID,
        "session_id": session_id,
        "skill_id": TEST_SKILL_ID,
        "chosen_action": "prerequisite_review",
        "after_outcome": {
            "correct": 1,
            "hint_used": 0,
            "pps_score": 0.51,
            "reward": 0.65
        }
    }

    try:
        health_response = requests.get(f"{BASE_URL}/", timeout=5)
        health_response.raise_for_status()

        update_response = requests.post(
            f"{BASE_URL}/memory/update",
            json=interaction_payload,
            timeout=10
        )
        update_response.raise_for_status()

        before_response = requests.get(
            f"{BASE_URL}/memory/fapr-context/{TEST_STUDENT_ID}",
            params={
                "session_id": session_id,
                "current_skill_id": TEST_SKILL_ID,
                "current_skill_name": TEST_SKILL_NAME,
                "limit": 10
            },
            timeout=10
        )
        before_response.raise_for_status()
        assert_previous_repair_is_null(before_response.json())

        store_response = requests.post(
            f"{BASE_URL}/memory/store-repair-outcome",
            json=store_payload,
            timeout=10
        )
        store_response.raise_for_status()
        store_result = store_response.json()

        if not store_result.get("stored"):
            raise AssertionError(f"Repair outcome was not stored: {store_result}")

        after_response = requests.get(
            f"{BASE_URL}/memory/fapr-context/{TEST_STUDENT_ID}",
            params={
                "session_id": session_id,
                "current_skill_id": TEST_SKILL_ID,
                "current_skill_name": TEST_SKILL_NAME,
                "limit": 10
            },
            timeout=10
        )
        after_response.raise_for_status()
        assert_previous_repair_is_stored(after_response.json())

        print("PASS: Repair outcome storage updates previous_repair.")
        print("Store response:", store_result)
        print("FAPR previous_repair:", after_response.json()["previous_repair"])
        return 0

    except Exception as error:
        print(f"FAIL: Repair outcome storage test failed: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
