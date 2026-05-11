import sys
import time
from typing import Dict

import requests


BASE_URL = "http://127.0.0.1:8000"


def assert_update_response(payload: Dict[str, object]) -> None:
    if payload.get("updated") is not True:
        raise AssertionError(f"Expected updated true, got {payload}")

    detected_topic = payload.get("detected_topic") or {}
    if detected_topic.get("skill_id") != 312:
        raise AssertionError(
            f"Expected detected skill_id 312, got {detected_topic.get('skill_id')}"
        )

    if detected_topic.get("skill_name") != "Percent Of":
        raise AssertionError(
            f"Expected Percent Of, got {detected_topic.get('skill_name')}"
        )

    if payload.get("memory_context") is None:
        raise AssertionError("Expected memory_context in update-from-text response")


def assert_fapr_context(payload: Dict[str, object], utterance: str) -> None:
    if payload.get("last_student_utterance") != utterance:
        raise AssertionError(
            "Expected FAPR last_student_utterance to equal stored utterance"
        )

    if payload.get("current_skill_id") != 312:
        raise AssertionError(
            f"Expected current_skill_id 312, got {payload.get('current_skill_id')}"
        )


def assert_meta_signals(payload: Dict[str, object]) -> None:
    signals = payload.get("signals")
    if not isinstance(signals, list) or not signals:
        raise AssertionError("Expected non-empty Meta-Agent signals")

    signal_types = [signal.get("signal_type") for signal in signals]

    if "incorrect_answer" not in signal_types:
        raise AssertionError("Expected incorrect_answer signal")

    if "confusion" not in signal_types and "clarification_request" not in signal_types:
        raise AssertionError(
            "Expected confusion or clarification_request signal from utterance"
        )


def assert_unclear_response(payload: Dict[str, object]) -> None:
    if payload.get("updated") is not False:
        raise AssertionError(f"Expected updated false for unclear topic, got {payload}")

    if payload.get("reason") != "topic_clarification_needed":
        raise AssertionError(
            f"Expected topic_clarification_needed, got {payload.get('reason')}"
        )

    detected_topic = payload.get("detected_topic") or {}
    if detected_topic.get("needs_review") is not True:
        raise AssertionError("Expected needs_review true for unclear utterance")


def main() -> int:
    student_id = 998000 + int(time.time()) % 100000
    session_id = int(time.time())
    utterance = "I don't understand how to find 25 percent of 80."

    try:
        health_response = requests.get(f"{BASE_URL}/", timeout=5)
        health_response.raise_for_status()
    except requests.RequestException as error:
        print(f"Backend is not reachable at {BASE_URL}: {error}")
        return 1

    try:
        update_response = requests.post(
            f"{BASE_URL}/memory/update-from-text",
            json={
                "student_id": student_id,
                "session_id": session_id,
                "problem_id": 1001,
                "student_utterance": utterance,
                "tutor_response": "Percent means out of 100.",
                "correct": 0,
                "attempt_count": 2,
                "hint_count": 1,
                "hint_total": 3,
                "response_time_ms": 45000,
            },
            timeout=10,
        )
        update_response.raise_for_status()
        update_payload = update_response.json()
        assert_update_response(update_payload)
        print("PASS: update-from-text stored detected Percent Of interaction.")

        fapr_response = requests.get(
            f"{BASE_URL}/memory/fapr-context/{student_id}",
            params={"session_id": session_id},
            timeout=10,
        )
        fapr_response.raise_for_status()
        fapr_payload = fapr_response.json()
        assert_fapr_context(fapr_payload, utterance)
        print("PASS: FAPR context exposes stored student utterance and skill_id.")

        meta_response = requests.get(
            f"{BASE_URL}/memory/meta-signals/{student_id}/{session_id}",
            timeout=10,
        )
        meta_response.raise_for_status()
        meta_payload = meta_response.json()
        assert_meta_signals(meta_payload)
        print("PASS: Meta-Agent signals include correctness and text evidence.")

        unclear_response = requests.post(
            f"{BASE_URL}/memory/update-from-text",
            json={
                "student_id": student_id,
                "session_id": session_id + 1,
                "problem_id": 1002,
                "student_utterance": "Can you help me understand this?",
                "tutor_response": "What topic is this question about?",
                "correct": 0,
                "attempt_count": 1,
                "hint_count": 0,
                "hint_total": 0,
                "response_time_ms": 5000,
            },
            timeout=10,
        )
        unclear_response.raise_for_status()
        unclear_payload = unclear_response.json()
        assert_unclear_response(unclear_payload)
        print("PASS: unclear update-from-text asks for topic clarification.")

        print("\nPASS: update-from-text contract is valid.")
        return 0

    except Exception as error:
        print(f"FAIL: update-from-text test failed: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
