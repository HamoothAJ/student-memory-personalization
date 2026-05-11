import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import requests


BASE_URL = "http://127.0.0.1:8000"

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

REPO_ROOT = Path(__file__).resolve().parent.parent
API_RESULTS_DIR = REPO_ROOT / "outputs" / "api_results"
TABLES_DIR = REPO_ROOT / "outputs" / "tables"
RESULTS_CSV = TABLES_DIR / "final_integration_test_results.csv"


def ensure_output_dirs() -> None:
    API_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)


def write_json(filename: str, payload: Dict[str, Any]) -> None:
    output_path = API_RESULTS_DIR / filename
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)
        file.write("\n")


def add_result(
    results: List[Dict[str, str]],
    step: str,
    status: str,
    detail: str,
) -> None:
    results.append({
        "step": step,
        "status": status,
        "detail": detail,
    })


def save_results(results: List[Dict[str, str]]) -> pd.DataFrame:
    dataframe = pd.DataFrame(results, columns=["step", "status", "detail"])
    dataframe.to_csv(RESULTS_CSV, index=False)
    return dataframe


def finish(results: List[Dict[str, str]], exit_code: int) -> int:
    dataframe = save_results(results)
    print("\nFinal Memory Integration Evidence Summary")
    print(dataframe.to_string(index=False))

    if exit_code == 0:
        print("\nPASS: Final Memory integration evidence test passed.")
    else:
        print("\nFAIL: Final Memory integration evidence test failed.")

    print(f"Results CSV: {RESULTS_CSV}")
    return exit_code


def request_json(method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
    response = requests.request(
        method=method,
        url=f"{BASE_URL}{path}",
        timeout=10,
        **kwargs,
    )
    response.raise_for_status()
    return response.json()


def build_test_ids() -> Dict[str, int]:
    run_id = int(time.time() * 1000)
    return {
        "student_id": 970000000 + (run_id % 100000000),
        "session_id": run_id,
    }


def build_interactions(student_id: int, session_id: int) -> List[Dict[str, Any]]:
    return [
        {
            "student_id": student_id,
            "session_id": session_id,
            "problem_id": 9601,
            "concept_name": "Percent Of",
            "correct": 0,
            "attempt_count": 2,
            "hint_count": 1,
            "hint_total": 3,
            "response_time_ms": 18000,
        },
        {
            "student_id": student_id,
            "session_id": session_id,
            "problem_id": 9602,
            "concept_name": "Percent Of",
            "correct": 0,
            "attempt_count": 1,
            "hint_count": 0,
            "hint_total": 3,
            "response_time_ms": 12000,
        },
        {
            "student_id": student_id,
            "session_id": session_id,
            "problem_id": 9603,
            "concept_name": "Percent Of",
            "correct": 1,
            "attempt_count": 1,
            "hint_count": 0,
            "hint_total": 3,
            "response_time_ms": 9000,
        },
        {
            "student_id": student_id,
            "session_id": session_id,
            "problem_id": 9604,
            "concept_name": "Circle Graph",
            "correct": 1,
            "attempt_count": 3,
            "hint_count": 2,
            "hint_total": 4,
            "response_time_ms": 24000,
        },
    ]


def assert_clear_question_context(payload: Dict[str, Any]) -> None:
    detected_topic = payload.get("detected_topic") or {}

    if detected_topic.get("skill_id") != 312:
        raise AssertionError(f"Expected skill_id 312, got {detected_topic.get('skill_id')}")

    if detected_topic.get("skill_name") != "Percent Of":
        raise AssertionError(
            f"Expected skill_name Percent Of, got {detected_topic.get('skill_name')}"
        )

    if detected_topic.get("needs_review") is not False:
        raise AssertionError("Expected needs_review false for clear percent question")

    if payload.get("topic_memory") is None:
        raise AssertionError("Expected topic_memory for clear percent question")


def assert_unclear_question_context(payload: Dict[str, Any]) -> None:
    detected_topic = payload.get("detected_topic") or {}
    recommendation_context = payload.get("recommendation_context") or {}

    if detected_topic.get("skill_id") is not None:
        raise AssertionError("Expected null skill_id for unclear question")

    if detected_topic.get("needs_review") is not True:
        raise AssertionError("Expected needs_review true for unclear question")

    if payload.get("topic_memory") is not None:
        raise AssertionError("Expected null topic_memory for unclear question")

    if recommendation_context.get("support_need") != "topic_clarification_needed":
        raise AssertionError(
            "Expected recommendation_context.support_need topic_clarification_needed"
        )


def assert_fapr_context(payload: Dict[str, Any], expect_previous_repair: bool) -> None:
    if payload.get("current_skill_id") is None:
        raise AssertionError("current_skill_id is missing")

    if payload.get("current_skill_name") is None:
        raise AssertionError("current_skill_name is missing")

    recent_interactions = payload.get("recent_interactions")
    if not isinstance(recent_interactions, list) or not recent_interactions:
        raise AssertionError("recent_interactions must be a non-empty list")

    for interaction in recent_interactions:
        missing_fields = RECENT_INTERACTION_FIELDS.difference(interaction.keys())
        if missing_fields:
            raise AssertionError(
                f"recent_interaction missing fields {sorted(missing_fields)}"
            )

    current_attempt = payload.get("current_attempt")
    if not isinstance(current_attempt, dict):
        raise AssertionError("current_attempt must exist")

    missing_current_fields = CURRENT_ATTEMPT_FIELDS.difference(current_attempt.keys())
    if missing_current_fields:
        raise AssertionError(
            f"current_attempt missing fields {sorted(missing_current_fields)}"
        )

    previous_repair = payload.get("previous_repair")
    if expect_previous_repair:
        if previous_repair is None:
            raise AssertionError("previous_repair should not be null after storage")

        if previous_repair.get("prev_action") != "prerequisite_review":
            raise AssertionError("previous_repair.prev_action mismatch")

        prev_outcome = previous_repair.get("prev_outcome") or {}
        if prev_outcome.get("correct") != 1:
            raise AssertionError("previous_repair.prev_outcome.correct mismatch")
    elif previous_repair is not None:
        raise AssertionError("previous_repair should be null before storage")


def assert_store_repair_outcome(payload: Dict[str, Any]) -> None:
    if payload.get("stored") is not True:
        raise AssertionError(f"Expected stored true, got {payload}")


def assert_meta_signals(payload: Dict[str, Any]) -> None:
    signals = payload.get("signals")
    if not isinstance(signals, list) or not signals:
        raise AssertionError("signals must be a non-empty list")

    signal_types = []
    percent_signal_types = []

    for signal in signals:
        if "skill" not in signal or "signal_type" not in signal:
            raise AssertionError(f"Signal missing skill or signal_type: {signal}")

        signal_type = signal["signal_type"]
        if signal_type not in ALLOWED_SIGNAL_TYPES:
            raise AssertionError(f"Unknown signal_type {signal_type}")

        signal_types.append(signal_type)
        if signal["skill"] == "Percent Of":
            percent_signal_types.append(signal_type)

    if "incorrect_answer" not in signal_types:
        raise AssertionError("Expected at least one incorrect_answer signal")

    if (
        "correct_answer" not in signal_types
        and "partial_correct" not in signal_types
    ):
        raise AssertionError("Expected at least one positive correctness signal")

    if "repeated_misunderstanding" not in percent_signal_types:
        raise AssertionError(
            "Expected repeated_misunderstanding for Percent Of"
        )


def main() -> int:
    ensure_output_dirs()
    results: List[Dict[str, str]] = []
    ids = build_test_ids()
    student_id = ids["student_id"]
    session_id = ids["session_id"]

    print("Final Memory integration evidence test")
    print(f"Backend: {BASE_URL}")
    print(f"Test student_id: {student_id}")
    print(f"Test session_id: {session_id}")

    try:
        health_response = requests.get(f"{BASE_URL}/", timeout=5)
        health_response.raise_for_status()
        add_result(results, "Backend reachable", "PASS", BASE_URL)
    except requests.RequestException as error:
        add_result(
            results,
            "Backend reachable",
            "FAIL",
            f"Backend is not running at {BASE_URL}: {error}",
        )
        print(
            f"Backend is not reachable at {BASE_URL}. "
            "Start it before running this evidence script."
        )
        return finish(results, 1)

    try:
        for interaction in build_interactions(student_id, session_id):
            request_json("POST", "/memory/update", json=interaction)
        add_result(
            results,
            "Seed interactions",
            "PASS",
            "Inserted 4 fresh Percent Of and Circle Graph interactions.",
        )
    except Exception as error:
        add_result(results, "Seed interactions", "FAIL", str(error))
        return finish(results, 1)

    try:
        clear_question = request_json(
            "POST",
            "/memory/question-context",
            json={
                "student_id": student_id,
                "session_id": session_id,
                "question": "Can you explain how to find 25 percent of 80?",
            },
        )
        assert_clear_question_context(clear_question)
        write_json("final_question_context_clear.json", clear_question)
        add_result(
            results,
            "Topic-aware clear question",
            "PASS",
            "Detected Percent Of with skill_id 312 and topic memory.",
        )
    except Exception as error:
        add_result(results, "Topic-aware clear question", "FAIL", str(error))
        return finish(results, 1)

    try:
        unclear_question = request_json(
            "POST",
            "/memory/question-context",
            json={
                "student_id": student_id,
                "session_id": session_id,
                "question": "Can you help me understand this?",
            },
        )
        assert_unclear_question_context(unclear_question)
        write_json("final_question_context_unclear.json", unclear_question)
        add_result(
            results,
            "Safe unclear question",
            "PASS",
            "Returned needs_review true and topic_clarification_needed.",
        )
    except Exception as error:
        add_result(results, "Safe unclear question", "FAIL", str(error))
        return finish(results, 1)

    try:
        fapr_before = request_json(
            "GET",
            f"/memory/fapr-context/{student_id}",
            params={
                "session_id": session_id,
                "current_skill_id": 312,
                "current_skill_name": "Percent Of",
                "limit": 10,
            },
        )
        assert_fapr_context(fapr_before, expect_previous_repair=False)
        write_json("final_fapr_before_repair.json", fapr_before)
        add_result(
            results,
            "FAPR-LB context before repair",
            "PASS",
            "Returned skill identifiers, recent interactions, current attempt, and null previous_repair.",
        )
    except Exception as error:
        add_result(results, "FAPR-LB context before repair", "FAIL", str(error))
        return finish(results, 1)

    try:
        repair_outcome = request_json(
            "POST",
            "/memory/store-repair-outcome",
            json={
                "student_id": student_id,
                "session_id": session_id,
                "skill_id": 312,
                "chosen_action": "prerequisite_review",
                "after_outcome": {
                    "correct": 1,
                    "hint_used": 0,
                    "pps_score": 0.51,
                    "reward": 0.65,
                },
            },
        )
        assert_store_repair_outcome(repair_outcome)
        write_json("final_store_repair_outcome.json", repair_outcome)
        add_result(
            results,
            "Repair outcome storage",
            "PASS",
            "Stored prerequisite_review repair outcome.",
        )
    except Exception as error:
        add_result(results, "Repair outcome storage", "FAIL", str(error))
        return finish(results, 1)

    try:
        fapr_after = request_json(
            "GET",
            f"/memory/fapr-context/{student_id}",
            params={
                "session_id": session_id,
                "current_skill_id": 312,
                "current_skill_name": "Percent Of",
                "limit": 10,
            },
        )
        assert_fapr_context(fapr_after, expect_previous_repair=True)
        write_json("final_fapr_after_repair.json", fapr_after)
        add_result(
            results,
            "Previous repair retrieval",
            "PASS",
            "Returned prerequisite_review previous_repair with correct outcome.",
        )
    except Exception as error:
        add_result(results, "Previous repair retrieval", "FAIL", str(error))
        return finish(results, 1)

    try:
        meta_signals = request_json(
            "GET",
            f"/memory/meta-signals/{student_id}/{session_id}",
        )
        assert_meta_signals(meta_signals)
        write_json("final_meta_signals.json", meta_signals)
        add_result(
            results,
            "Meta-Agent signal export",
            "PASS",
            "Returned allowed signal types including Percent Of repeated_misunderstanding.",
        )
    except Exception as error:
        add_result(results, "Meta-Agent signal export", "FAIL", str(error))
        return finish(results, 1)

    return finish(results, 0)


if __name__ == "__main__":
    sys.exit(main())
