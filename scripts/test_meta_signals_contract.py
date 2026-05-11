import json
import sys
import time
from pathlib import Path
from typing import Dict, List

import requests


BASE_URL = "http://127.0.0.1:8000"
TEST_STUDENT_ID = 999001

ALLOWED_SIGNAL_TYPES = {
    "correct_answer",
    "correct_explanation",
    "partial_correct",
    "evaluator_positive",
    "incorrect_answer",
    "repeated_misunderstanding",
    "confusion",
    "clarification_request",
    "evaluator_negative",
}

TOP_LEVEL_FIELDS = {
    "session_id",
    "student_id",
    "signals",
    "misconceptions",
}

SIGNAL_FIELDS = {
    "skill",
    "signal_type",
}


def load_canonical_skill_names() -> set:
    repo_root = Path(__file__).resolve().parent.parent
    skills_path = repo_root / "models" / "canonical_skills.json"

    with skills_path.open("r", encoding="utf-8") as file:
        skills = json.load(file)

    return {skill["canonical_skill_name"] for skill in skills}


def build_test_interactions(session_id: int) -> List[Dict[str, object]]:
    return [
        {
            "student_id": TEST_STUDENT_ID,
            "session_id": session_id,
            "problem_id": 9401,
            "concept_name": "Percent Of",
            "correct": 0,
            "hint_count": 1,
            "attempt_count": 2,
            "hint_total": 3,
            "response_time_ms": 18000,
        },
        {
            "student_id": TEST_STUDENT_ID,
            "session_id": session_id,
            "problem_id": 9402,
            "concept_name": "Percent Of",
            "correct": 0,
            "hint_count": 0,
            "attempt_count": 1,
            "hint_total": 3,
            "response_time_ms": 12000,
        },
        {
            "student_id": TEST_STUDENT_ID,
            "session_id": session_id,
            "problem_id": 9403,
            "concept_name": "Percent Of",
            "correct": 1,
            "hint_count": 0,
            "attempt_count": 1,
            "hint_total": 3,
            "response_time_ms": 9000,
        },
        {
            "student_id": TEST_STUDENT_ID,
            "session_id": session_id,
            "problem_id": 9404,
            "concept_name": "Circle Graph",
            "correct": 1,
            "hint_count": 2,
            "attempt_count": 3,
            "hint_total": 4,
            "response_time_ms": 24000,
        },
    ]


def post_test_interactions(session_id: int) -> None:
    for payload in build_test_interactions(session_id):
        response = requests.post(
            f"{BASE_URL}/memory/update",
            json=payload,
            timeout=10,
        )
        response.raise_for_status()


def assert_meta_signals_contract(
    payload: Dict[str, object],
    session_id: int,
    canonical_skill_names: set,
) -> None:
    missing_fields = TOP_LEVEL_FIELDS.difference(payload.keys())
    if missing_fields:
        raise AssertionError(f"Missing top-level fields {sorted(missing_fields)}")

    if payload["student_id"] != str(TEST_STUDENT_ID):
        raise AssertionError("student_id should be a string matching the test student")

    if payload["session_id"] != str(session_id):
        raise AssertionError("session_id should be a string matching the test session")

    signals = payload["signals"]
    if not isinstance(signals, list) or len(signals) == 0:
        raise AssertionError("signals must be a non-empty list")

    if not isinstance(payload["misconceptions"], list):
        raise AssertionError("misconceptions must be a list")

    for signal in signals:
        missing_signal_fields = SIGNAL_FIELDS.difference(signal.keys())
        if missing_signal_fields:
            raise AssertionError(
                f"Signal missing fields {sorted(missing_signal_fields)}"
            )

        if signal["signal_type"] not in ALLOWED_SIGNAL_TYPES:
            raise AssertionError(
                f"Unknown signal_type {signal['signal_type']}"
            )

        if signal["skill"] not in canonical_skill_names:
            raise AssertionError(f"Non-canonical skill {signal['skill']}")

    percent_signals = [
        signal["signal_type"]
        for signal in signals
        if signal["skill"] == "Percent Of"
    ]

    if percent_signals.count("incorrect_answer") < 2:
        raise AssertionError("Expected two Percent Of incorrect_answer signals")

    if "repeated_misunderstanding" not in percent_signals:
        raise AssertionError(
            "Expected repeated_misunderstanding for Percent Of"
        )

    if "correct_answer" not in percent_signals:
        raise AssertionError("Expected correct_answer for Percent Of")

    if {
        "skill": "Circle Graph",
        "signal_type": "partial_correct",
    } not in signals:
        raise AssertionError("Expected partial_correct for Circle Graph")


def main() -> int:
    session_id = int(time.time())
    canonical_skill_names = load_canonical_skill_names()

    try:
        health_response = requests.get(f"{BASE_URL}/", timeout=5)
        health_response.raise_for_status()
        post_test_interactions(session_id)

        response = requests.get(
            f"{BASE_URL}/memory/meta-signals/{TEST_STUDENT_ID}/{session_id}",
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()

        assert_meta_signals_contract(
            payload=payload,
            session_id=session_id,
            canonical_skill_names=canonical_skill_names,
        )

        print("PASS: Meta-Agent signal export contract is valid.")
        print(payload)
        return 0

    except Exception as error:
        print(f"FAIL: Meta-Agent signal export contract test failed: {error}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
