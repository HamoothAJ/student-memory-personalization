import sys
import time
from typing import Dict

import requests


BASE_URL = "http://127.0.0.1:8000"


def assert_clear_question(payload: Dict[str, object]) -> None:
    detected_topic = payload.get("detected_topic") or {}

    if detected_topic.get("skill_id") != 312:
        raise AssertionError(
            f"Expected skill_id 312, got {detected_topic.get('skill_id')}"
        )

    if detected_topic.get("skill_name") != "Percent Of":
        raise AssertionError(
            f"Expected skill_name Percent Of, got {detected_topic.get('skill_name')}"
        )

    if detected_topic.get("needs_review") is not False:
        raise AssertionError("Expected needs_review false for clear question")

    if payload.get("topic_memory") is None:
        raise AssertionError("Expected topic_memory for clear question")


def assert_unclear_question(payload: Dict[str, object]) -> None:
    detected_topic = payload.get("detected_topic") or {}
    recommendation_context = payload.get("recommendation_context") or {}

    if detected_topic.get("skill_id") is not None:
        raise AssertionError("Expected null skill_id for unclear question")

    if detected_topic.get("skill_name") is not None:
        raise AssertionError("Expected null skill_name for unclear question")

    if detected_topic.get("canonical_skill_name") is not None:
        raise AssertionError("Expected null canonical_skill_name for unclear question")

    if detected_topic.get("needs_review") is not True:
        raise AssertionError("Expected needs_review true for unclear question")

    if payload.get("topic_memory") is not None:
        raise AssertionError("Expected null topic_memory for unclear question")

    if recommendation_context.get("support_need") != "topic_clarification_needed":
        raise AssertionError(
            "Expected recommendation_context.support_need topic_clarification_needed"
        )


def main() -> int:
    session_id = int(time.time())
    student_id = 999071

    try:
        health_response = requests.get(f"{BASE_URL}/", timeout=5)
        health_response.raise_for_status()
    except requests.RequestException as error:
        print(f"Backend is not reachable at {BASE_URL}: {error}")
        return 1

    try:
        clear_response = requests.post(
            f"{BASE_URL}/memory/question-context",
            json={
                "student_id": student_id,
                "session_id": session_id,
                "question": "Can you explain how to find 25 percent of 80?",
            },
            timeout=10,
        )
        clear_response.raise_for_status()
        clear_payload = clear_response.json()
        assert_clear_question(clear_payload)
        print(f"PASS: clear question -> {clear_payload['detected_topic']}")

        unclear_response = requests.post(
            f"{BASE_URL}/memory/question-context",
            json={
                "student_id": student_id,
                "session_id": session_id,
                "question": "Can you help me understand this?",
            },
            timeout=10,
        )
        unclear_response.raise_for_status()
        unclear_payload = unclear_response.json()
        assert_unclear_question(unclear_payload)
        print(f"PASS: unclear question -> {unclear_payload['detected_topic']}")

        print("\nPASS: Pre-trained question-context API contract is valid.")
        return 0

    except Exception as error:
        print(f"FAIL: Pre-trained question-context API test failed: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
