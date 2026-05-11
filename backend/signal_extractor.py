import re
from collections import Counter


class SignalExtractor:
    """
    Deterministic evidence signal extractor for Meta-Agent integration.

    The extractor emits observed evidence only. It does not estimate mastery,
    run BKT, or predict future performance.
    """

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

    CONFUSION_PHRASES = (
        "i don't understand",
        "i dont understand",
        "i'm confused",
        "im confused",
        "confused",
        "lost",
        "i don't get it",
        "i dont get it",
    )

    CLARIFICATION_PHRASES = (
        "can you explain",
        "explain again",
        "what does that mean",
        "repeat",
        "can you show",
        "how do i",
    )

    def __init__(self, topic_extractor):
        self.topic_extractor = topic_extractor

    def extract_session_signals(self, rows):
        signals = []
        incorrect_counts = Counter()
        skill_order = []

        for row in rows:
            skill = self._canonical_skill_for_row(row)
            if skill is None:
                continue

            correctness_signal = self._correctness_signal_for_row(row)
            if correctness_signal:
                self._append_signal(signals, skill, correctness_signal)
                if correctness_signal == "incorrect_answer":
                    incorrect_counts[skill] += 1
                    if skill not in skill_order:
                        skill_order.append(skill)

            utterance = self._row_get(row, "student_utterance")
            if utterance:
                normalized_utterance = self._normalize_text(utterance)
                if self._contains_phrase(normalized_utterance, self.CONFUSION_PHRASES):
                    self._append_signal(signals, skill, "confusion")
                if self._contains_phrase(normalized_utterance, self.CLARIFICATION_PHRASES):
                    self._append_signal(signals, skill, "clarification_request")

            # TODO: Emit evaluator_positive/evaluator_negative when evaluator
            # fields are added to interaction_logs.
            # TODO: Emit correct_explanation when explicit explanation quality
            # text or labels are stored.

        for skill in skill_order:
            if incorrect_counts[skill] >= 2:
                self._append_signal(signals, skill, "repeated_misunderstanding")

        return signals

    def _append_signal(self, signals, skill, signal_type):
        if signal_type not in self.ALLOWED_SIGNAL_TYPES:
            return

        signals.append({
            "skill": skill,
            "signal_type": signal_type,
        })

    def _canonical_skill_for_row(self, row):
        canonical_skill_name = self._row_get(row, "canonical_skill_name")
        if canonical_skill_name:
            skill = self.topic_extractor.get_skill_by_name(canonical_skill_name)
            if skill:
                return skill["canonical_skill_name"]
            return None

        concept_name = self._row_get(row, "concept_name")
        skill = self.topic_extractor.get_skill_by_name(concept_name)
        if skill:
            return skill["canonical_skill_name"]

        return None

    def _correctness_signal_for_row(self, row):
        correct = self._safe_int(self._row_get(row, "correct"), default=None)
        hint_count = self._safe_int(self._row_get(row, "hint_count"), default=0)
        attempt_count = self._safe_int(self._row_get(row, "attempt_count"), default=0)

        if correct == 1 and hint_count == 0 and attempt_count == 1:
            return "correct_answer"

        if correct == 1 and (hint_count > 0 or attempt_count > 1):
            return "partial_correct"

        if correct == 0:
            return "incorrect_answer"

        return None

    def _contains_phrase(self, text, phrases):
        return any(phrase in text for phrase in phrases)

    def _normalize_text(self, text):
        return re.sub(r"\s+", " ", str(text).lower()).strip()

    def _row_get(self, row, key, default=None):
        if row is None:
            return default

        if key not in row.keys():
            return default

        value = row[key]
        if value is None:
            return default

        return value

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
