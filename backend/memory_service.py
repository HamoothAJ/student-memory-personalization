import pandas as pd
from typing import Optional, Dict, Any
from config import (
    SHORT_TERM_MEMORY_PATH,
    LONG_TERM_MEMORY_PATH,
    CONCEPT_MEMORY_PATH,
    INTERACTION_LOG_PATH
)


class MemoryService:
    def __init__(self):
        self.short_term_df = pd.read_csv(SHORT_TERM_MEMORY_PATH)
        self.long_term_df = pd.read_csv(LONG_TERM_MEMORY_PATH)
        self.concept_memory_df = pd.read_csv(CONCEPT_MEMORY_PATH)
        self.interaction_df = pd.read_csv(INTERACTION_LOG_PATH)

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return default

    def _safe_float(self, value, default=0.0):
        try:
            return float(value)
        except Exception:
            return default

    def get_student_profile(self, student_id: int) -> Dict[str, Any]:
        long_term = self.long_term_df[self.long_term_df["student_id"] == student_id]

        if long_term.empty:
            return {
                "found": False,
                "message": "Student not found in long-term memory."
            }

        record = long_term.iloc[0].to_dict()

        return {
            "found": True,
            "student_id": student_id,
            "long_term_memory": {
                "total_interactions": self._safe_int(record.get("total_interactions")),
                "total_sessions": self._safe_int(record.get("total_sessions")),
                "total_concepts": self._safe_int(record.get("total_concepts")),
                "overall_accuracy": self._safe_float(record.get("overall_accuracy")),
                "average_attempts": self._safe_float(record.get("average_attempts")),
                "average_hint_count": self._safe_float(record.get("average_hint_count")),
                "total_hint_count": self._safe_int(record.get("total_hint_count")),
                "average_response_time_ms": self._safe_float(record.get("average_response_time_ms")),
                "preferred_support_style": record.get("preferred_support_style")
            }
        }

    def get_concept_memory(self, student_id: int, concept_name: str) -> Dict[str, Any]:
        records = self.concept_memory_df[
            (self.concept_memory_df["student_id"] == student_id) &
            (self.concept_memory_df["concept_name"].str.lower() == concept_name.lower())
        ]

        if records.empty:
            return {
                "found": False,
                "message": "Concept memory not found for this student and concept.",
                "student_id": student_id,
                "concept_name": concept_name
            }

        record = records.iloc[0].to_dict()

        return {
            "found": True,
            "student_id": student_id,
            "concept_name": record.get("concept_name"),
            "concept_based_memory": {
                "total_interactions": self._safe_int(record.get("total_interactions")),
                "correct_count": self._safe_int(record.get("correct_count")),
                "wrong_count": self._safe_int(record.get("wrong_count")),
                "accuracy": self._safe_float(record.get("accuracy")),
                "total_hints": self._safe_int(record.get("total_hints")),
                "avg_hints": self._safe_float(record.get("avg_hints")),
                "avg_attempts": self._safe_float(record.get("avg_attempts")),
                "avg_response_time_ms": self._safe_float(record.get("avg_response_time_ms")),
                "last_interaction_order": self._safe_int(record.get("last_interaction_order"))
            }
        }

    def get_memory_context(self, student_id: int, target_concept: Optional[str] = None) -> Dict[str, Any]:
        short_term = self.short_term_df[self.short_term_df["student_id"] == student_id]
        long_term = self.long_term_df[self.long_term_df["student_id"] == student_id]
        concept_records = self.concept_memory_df[self.concept_memory_df["student_id"] == student_id]

        if short_term.empty:
            return {
                "found": False,
                "message": "Student not found in short-term memory.",
                "student_id": student_id
            }

        if long_term.empty:
            return {
                "found": False,
                "message": "Student not found in long-term memory.",
                "student_id": student_id
            }

        if concept_records.empty:
            return {
                "found": False,
                "message": "Student not found in concept-based memory.",
                "student_id": student_id
            }

        short_record = short_term.iloc[0].to_dict()
        long_record = long_term.iloc[0].to_dict()

        if target_concept is None:
            target_concept = (
                concept_records.sort_values("total_interactions", ascending=False)
                .iloc[0]["concept_name"]
            )

        concept_result = self.get_concept_memory(student_id, target_concept)

        return {
            "found": True,
            "student_id": student_id,
            "target_concept": target_concept,
            "short_term_memory": {
                "session_id": self._safe_int(short_record.get("session_id")),
                "current_concept": short_record.get("current_concept"),
                "recent_interaction_count": self._safe_int(short_record.get("recent_interaction_count")),
                "recent_accuracy": self._safe_float(short_record.get("recent_accuracy")),
                "average_attempts": self._safe_float(short_record.get("average_attempts")),
                "recent_hint_usage": self._safe_int(short_record.get("recent_hint_usage")),
                "session_status": short_record.get("session_status")
            },
            "long_term_memory": {
                "total_interactions": self._safe_int(long_record.get("total_interactions")),
                "total_sessions": self._safe_int(long_record.get("total_sessions")),
                "total_concepts": self._safe_int(long_record.get("total_concepts")),
                "overall_accuracy": self._safe_float(long_record.get("overall_accuracy")),
                "average_attempts": self._safe_float(long_record.get("average_attempts")),
                "average_hint_count": self._safe_float(long_record.get("average_hint_count")),
                "total_hint_count": self._safe_int(long_record.get("total_hint_count")),
                "average_response_time_ms": self._safe_float(long_record.get("average_response_time_ms")),
                "preferred_support_style": long_record.get("preferred_support_style")
            },
            "concept_based_memory": concept_result.get("concept_based_memory", {}),
            "integration_note": {
                "for_meta_agent": "Use this stored interaction history to derive mastery, knowledge graph updates, regression flags, and learning paths.",
                "for_fapr_lb": "Use this memory context as input features for struggle prediction and repair strategy selection.",
                "for_tutor_agent": "Use this context to personalize explanations without treating the student as new."
            }
        }

    def get_student_interactions(self, student_id: int, limit: int = 20) -> Dict[str, Any]:
        records = self.interaction_df[self.interaction_df["student_id"] == student_id]

        if records.empty:
            return {
                "found": False,
                "message": "No interactions found for this student.",
                "student_id": student_id
            }

        records = records.sort_values("interaction_order").tail(limit)

        return {
            "found": True,
            "student_id": student_id,
            "interaction_count_returned": len(records),
            "interactions": records.to_dict(orient="records")
        }