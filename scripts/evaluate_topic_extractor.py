import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
OUTPUT_TABLES_DIR = REPO_ROOT / "outputs" / "tables"
OUTPUT_API_RESULTS_DIR = REPO_ROOT / "outputs" / "api_results"

# Avoid noisy network retries during evidence runs. If the embedding model is
# already cached locally, sentence-transformers can still load it.
os.environ.setdefault("HF_HUB_OFFLINE", "1")

sys.path.insert(0, str(BACKEND_DIR))

from topic_extractor import TopicExtractor


EVALUATION_CASES: List[Dict[str, Any]] = [
    {
        "question": "How do I find 25 percent of 80?",
        "expected_skill_id": 312,
        "expected_skill_name": "Percent Of",
        "category": "Percent Of",
    },
    {
        "question": "Can you explain percent of a number?",
        "expected_skill_id": 312,
        "expected_skill_name": "Percent Of",
        "category": "Percent Of",
    },
    {
        "question": "What is 15 percent of 60?",
        "expected_skill_id": 312,
        "expected_skill_name": "Percent Of",
        "category": "Percent Of",
    },
    {
        "question": "How do I calculate a percentage part from the whole?",
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
        "question": "How do I subtract fractions when the denominator is not the same?",
        "expected_skill_id": 415,
        "expected_skill_name": "Addition and Subtraction Fractions",
        "category": "Addition and Subtraction Fractions",
    },
    {
        "question": "Why do I need a common denominator before adding fractions?",
        "expected_skill_id": 415,
        "expected_skill_name": "Addition and Subtraction Fractions",
        "category": "Addition and Subtraction Fractions",
    },
    {
        "question": "How do numerators change when I subtract fractions?",
        "expected_skill_id": 415,
        "expected_skill_name": "Addition and Subtraction Fractions",
        "category": "Addition and Subtraction Fractions",
    },
    {
        "question": "How do I read a circle graph?",
        "expected_skill_id": 220,
        "expected_skill_name": "Circle Graph",
        "category": "Circle Graph",
    },
    {
        "question": "Can you help me use a pie chart to find the answer?",
        "expected_skill_id": 220,
        "expected_skill_name": "Circle Graph",
        "category": "Circle Graph",
    },
    {
        "question": "How do I find a sector in a circle graph?",
        "expected_skill_id": 220,
        "expected_skill_name": "Circle Graph",
        "category": "Circle Graph",
    },
    {
        "question": "What percentage does this part of the pie chart show?",
        "expected_skill_id": 220,
        "expected_skill_name": "Circle Graph",
        "category": "Circle Graph",
    },
    {
        "question": "How do I solve this equation for x?",
        "expected_skill_id": 101,
        "expected_skill_name": "Equation Solving Two or Fewer Steps",
        "category": "Equation Solving Two or Fewer Steps",
    },
    {
        "question": "Can you show me how to isolate the variable?",
        "expected_skill_id": 101,
        "expected_skill_name": "Equation Solving Two or Fewer Steps",
        "category": "Equation Solving Two or Fewer Steps",
    },
    {
        "question": "How do I solve a two step algebra equation?",
        "expected_skill_id": 101,
        "expected_skill_name": "Equation Solving Two or Fewer Steps",
        "category": "Equation Solving Two or Fewer Steps",
    },
    {
        "question": "What should I do first when x is on one side of the equation?",
        "expected_skill_id": 101,
        "expected_skill_name": "Equation Solving Two or Fewer Steps",
        "category": "Equation Solving Two or Fewer Steps",
    },
    {
        "question": "How do I find the mean of these numbers?",
        "expected_skill_id": 501,
        "expected_skill_name": "Mean",
        "category": "Mean",
    },
    {
        "question": "Can you explain how to calculate an average?",
        "expected_skill_id": 501,
        "expected_skill_name": "Mean",
        "category": "Mean",
    },
    {
        "question": "Do I add the numbers and divide by the count?",
        "expected_skill_id": 501,
        "expected_skill_name": "Mean",
        "category": "Mean",
    },
    {
        "question": "How do I divide the sum by how many values there are?",
        "expected_skill_id": 501,
        "expected_skill_name": "Mean",
        "category": "Mean",
    },
    {
        "question": "How do I find the median?",
        "expected_skill_id": 502,
        "expected_skill_name": "Median",
        "category": "Median",
    },
    {
        "question": "How do I find the middle value in a list of numbers?",
        "expected_skill_id": 502,
        "expected_skill_name": "Median",
        "category": "Median",
    },
    {
        "question": "Do I order the numbers first to find the median?",
        "expected_skill_id": 502,
        "expected_skill_name": "Median",
        "category": "Median",
    },
    {
        "question": "Which value is in the middle after the numbers are ordered?",
        "expected_skill_id": 502,
        "expected_skill_name": "Median",
        "category": "Median",
    },
    {
        "question": "How do I solve this probability question?",
        "expected_skill_id": 503,
        "expected_skill_name": "Probability",
        "category": "Probability",
    },
    {
        "question": "What is the chance that this event happens?",
        "expected_skill_id": 503,
        "expected_skill_name": "Probability",
        "category": "Probability",
    },
    {
        "question": "How do I count favorable outcomes for probability?",
        "expected_skill_id": 503,
        "expected_skill_name": "Probability",
        "category": "Probability",
    },
    {
        "question": "Can you explain likelihood and possible outcomes?",
        "expected_skill_id": 503,
        "expected_skill_name": "Probability",
        "category": "Probability",
    },
    {
        "question": "How do I write a ratio?",
        "expected_skill_id": 504,
        "expected_skill_name": "Ratio",
        "category": "Ratio",
    },
    {
        "question": "How do I compare two quantities with a ratio?",
        "expected_skill_id": 504,
        "expected_skill_name": "Ratio",
        "category": "Ratio",
    },
    {
        "question": "What relationship between numbers does this ratio show?",
        "expected_skill_id": 504,
        "expected_skill_name": "Ratio",
        "category": "Ratio",
    },
    {
        "question": "Can you help me compare quantities in this word problem?",
        "expected_skill_id": 504,
        "expected_skill_name": "Ratio",
        "category": "Ratio",
    },
    {
        "question": "How do I solve this proportion?",
        "expected_skill_id": 505,
        "expected_skill_name": "Proportion",
        "category": "Proportion",
    },
    {
        "question": "Can you explain equivalent ratios?",
        "expected_skill_id": 505,
        "expected_skill_name": "Proportion",
        "category": "Proportion",
    },
    {
        "question": "When do I cross multiply in a proportion?",
        "expected_skill_id": 505,
        "expected_skill_name": "Proportion",
        "category": "Proportion",
    },
    {
        "question": "How do I know if two ratios form a proportion?",
        "expected_skill_id": 505,
        "expected_skill_name": "Proportion",
        "category": "Proportion",
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
    {
        "question": "I don't understand this.",
        "expected_skill_id": None,
        "expected_skill_name": None,
        "category": "unclear",
    },
    {
        "question": "Can you help me with this?",
        "expected_skill_id": None,
        "expected_skill_name": None,
        "category": "unclear",
    },
    {
        "question": "What should I do here?",
        "expected_skill_id": None,
        "expected_skill_name": None,
        "category": "unclear",
    },
    {
        "question": "This problem is confusing.",
        "expected_skill_id": None,
        "expected_skill_name": None,
        "category": "unclear",
    },
]


def ensure_output_dirs() -> None:
    OUTPUT_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_API_RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def evaluate_case(
    extractor: TopicExtractor,
    test_case: Dict[str, Any],
) -> Dict[str, Any]:
    prediction = extractor.detect_topic(test_case["question"])
    expected_skill_id = test_case["expected_skill_id"]
    is_unclear = expected_skill_id is None

    if is_unclear:
        passed = prediction.get("needs_review") is True and prediction.get("skill_id") is None
    else:
        passed = prediction.get("skill_id") == expected_skill_id

    return {
        "question": test_case["question"],
        "expected_skill_id": expected_skill_id,
        "expected_skill_name": test_case["expected_skill_name"],
        "predicted_skill_id": prediction.get("skill_id"),
        "predicted_skill_name": prediction.get("skill_name"),
        "confidence": prediction.get("confidence"),
        "method": prediction.get("method"),
        "needs_review": prediction.get("needs_review"),
        "category": test_case["category"],
        "status": "PASS" if passed else "FAIL",
    }


def safe_accuracy(passed_count: int, total_count: int) -> Optional[float]:
    if total_count == 0:
        return None

    return round(passed_count / total_count, 4)


def average_confidence(rows: List[Dict[str, Any]]) -> Optional[float]:
    confidences = [
        float(row["confidence"])
        for row in rows
        if row.get("confidence") is not None
    ]
    if not confidences:
        return None

    return round(sum(confidences) / len(confidences), 4)


def build_summary(
    results: List[Dict[str, Any]],
    embedding_status: Dict[str, Any],
) -> Dict[str, Any]:
    total_count = len(results)
    passed_rows = [row for row in results if row["status"] == "PASS"]
    failed_rows = [row for row in results if row["status"] == "FAIL"]
    clear_rows = [row for row in results if row["category"] != "unclear"]
    unclear_rows = [row for row in results if row["category"] == "unclear"]

    method_counts = {
        "keyword_rule": 0,
        "pretrained_embedding_similarity": 0,
        "tfidf_cosine_fallback": 0,
    }
    for row in results:
        method = row.get("method")
        if method in method_counts:
            method_counts[method] += 1

    return {
        "total_test_cases": total_count,
        "passed_count": len(passed_rows),
        "failed_count": len(failed_rows),
        "accuracy": safe_accuracy(len(passed_rows), total_count),
        "clear_question_accuracy": safe_accuracy(
            len([row for row in clear_rows if row["status"] == "PASS"]),
            len(clear_rows),
        ),
        "unclear_question_handling_accuracy": safe_accuracy(
            len([row for row in unclear_rows if row["status"] == "PASS"]),
            len(unclear_rows),
        ),
        "keyword_rule_count": method_counts["keyword_rule"],
        "pretrained_embedding_similarity_count": method_counts[
            "pretrained_embedding_similarity"
        ],
        "tfidf_cosine_fallback_count": method_counts["tfidf_cosine_fallback"],
        "average_confidence_correct": average_confidence(passed_rows),
        "average_confidence_wrong": average_confidence(failed_rows),
        "embedding_model_available": embedding_status.get("available"),
        "embedding_model_name": embedding_status.get("model_name"),
        "embedding_model_error": embedding_status.get("error"),
    }


def save_outputs(
    results: List[Dict[str, Any]],
    summary: Dict[str, Any],
) -> None:
    results_path = OUTPUT_TABLES_DIR / "topic_extractor_evaluation_results.csv"
    summary_path = OUTPUT_TABLES_DIR / "topic_extractor_evaluation_summary.csv"
    sample_predictions_path = (
        OUTPUT_API_RESULTS_DIR / "topic_extractor_sample_predictions.json"
    )

    pd.DataFrame(results).to_csv(results_path, index=False)
    pd.DataFrame(
        [{"metric": key, "value": value} for key, value in summary.items()]
    ).to_csv(summary_path, index=False)

    sample_payload = {
        "summary": summary,
        "sample_predictions": results[:12],
        "failed_predictions": [
            row for row in results if row["status"] == "FAIL"
        ],
    }
    with sample_predictions_path.open("w", encoding="utf-8") as file:
        json.dump(sample_payload, file, indent=2)
        file.write("\n")


def print_summary(results: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    print("\nTopic Extractor Evaluation Summary")
    print(f"Total: {summary['total_test_cases']}")
    print(f"PASS: {summary['passed_count']}")
    print(f"FAIL: {summary['failed_count']}")
    print(f"Accuracy: {summary['accuracy']:.2f}")
    print(f"Clear Question Accuracy: {summary['clear_question_accuracy']:.2f}")
    print(
        "Unclear Handling Accuracy: "
        f"{summary['unclear_question_handling_accuracy']:.2f}"
    )
    print("Method Distribution:")
    print(f"- keyword_rule: {summary['keyword_rule_count']}")
    print(
        "- pretrained_embedding_similarity: "
        f"{summary['pretrained_embedding_similarity_count']}"
    )
    print(f"- tfidf_cosine_fallback: {summary['tfidf_cosine_fallback_count']}")
    print(f"Average Confidence Correct: {summary['average_confidence_correct']}")
    print(f"Average Confidence Wrong: {summary['average_confidence_wrong']}")

    failed_rows = [row for row in results if row["status"] == "FAIL"]
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
    ensure_output_dirs()
    extractor = TopicExtractor()
    print("TopicExtractor embedding status:", extractor.embedding_status)

    results = [
        evaluate_case(extractor, test_case)
        for test_case in EVALUATION_CASES
    ]
    summary = build_summary(results, extractor.embedding_status)
    save_outputs(results, summary)
    print_summary(results, summary)

    print("\nSaved outputs:")
    print(OUTPUT_TABLES_DIR / "topic_extractor_evaluation_results.csv")
    print(OUTPUT_TABLES_DIR / "topic_extractor_evaluation_summary.csv")
    print(OUTPUT_API_RESULTS_DIR / "topic_extractor_sample_predictions.json")

    return 0


if __name__ == "__main__":
    sys.exit(main())
