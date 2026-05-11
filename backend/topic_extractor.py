import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class TopicExtractor:
    """
    Lightweight academic topic detector for memory retrieval.

    The extractor uses deterministic keyword matching first, then falls back to
    TF-IDF cosine similarity over the canonical skill descriptions.
    """

    LOW_CONFIDENCE_THRESHOLD = 0.45

    def __init__(self, skills_path: Optional[Path] = None):
        base_dir = Path(__file__).resolve().parent.parent
        self.skills_path = skills_path or base_dir / "models" / "canonical_skills.json"
        self.skills = self._load_skills()
        self._skill_lookup = self._build_skill_lookup()
        self._keyword_index = self._build_keyword_index()
        self._documents = [self._skill_document(skill) for skill in self.skills]
        self._vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self._skill_matrix = self._vectorizer.fit_transform(self._documents)

    def detect_topic(self, question: str) -> Dict[str, Any]:
        normalized_question = self._normalize(question)

        keyword_match = self._detect_with_keywords(normalized_question)
        if keyword_match is not None:
            return keyword_match

        return self._detect_with_tfidf(question)

    def get_skill_by_name(self, skill_name: Optional[str]) -> Optional[Dict[str, Any]]:
        if skill_name is None:
            return None

        return self._skill_lookup.get(self._normalize(skill_name))

    def get_skill_by_id(self, skill_id: Optional[Any]) -> Optional[Dict[str, Any]]:
        if skill_id is None:
            return None

        try:
            normalized_id = int(skill_id)
        except (TypeError, ValueError):
            return None

        for skill in self.skills:
            if int(skill["skill_id"]) == normalized_id:
                return skill

        return None

    def _load_skills(self) -> List[Dict[str, Any]]:
        with self.skills_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _build_skill_lookup(self) -> Dict[str, Dict[str, Any]]:
        lookup = {}
        for skill in self.skills:
            lookup[self._normalize(skill["skill_name"])] = skill
            lookup[self._normalize(skill["canonical_skill_name"])] = skill
        return lookup

    def _build_keyword_index(self) -> List[Dict[str, Any]]:
        keyword_index = []
        stop_words = {
            "a", "an", "and", "are", "by", "can", "do", "does", "for", "from",
            "how", "i", "in", "is", "me", "of", "or", "please", "the", "to",
            "what", "when", "where", "with", "you"
        }

        for skill in self.skills:
            source_text = self._skill_document(skill)
            tokens = {
                token for token in self._tokenize(source_text)
                if len(token) >= 3 and token not in stop_words
            }
            phrases = {
                self._normalize(skill["skill_name"]),
                self._normalize(skill["canonical_skill_name"]),
            }
            keyword_index.append({
                "skill": skill,
                "tokens": tokens,
                "phrases": {phrase for phrase in phrases if phrase}
            })

        return keyword_index

    def _detect_with_keywords(self, normalized_question: str) -> Optional[Dict[str, Any]]:
        question_tokens = set(self._tokenize(normalized_question))
        best_skill = None
        best_hits = 0
        best_phrase_match = False

        for entry in self._keyword_index:
            token_hits = len(question_tokens.intersection(entry["tokens"]))
            phrase_match = any(
                phrase in normalized_question
                for phrase in entry["phrases"]
                if len(phrase) >= 5
            )

            score_hits = token_hits + (2 if phrase_match else 0)
            if score_hits > best_hits:
                best_skill = entry["skill"]
                best_hits = score_hits
                best_phrase_match = phrase_match

        if best_skill is None or best_hits == 0:
            return None

        confidence = 0.55 + min(best_hits, 4) * 0.08
        if best_phrase_match:
            confidence += 0.15
        confidence = round(min(confidence, 0.95), 2)

        return self._format_result(
            best_skill,
            confidence=confidence,
            method="hybrid_keyword_tfidf"
        )

    def _detect_with_tfidf(self, question: str) -> Dict[str, Any]:
        question_vector = self._vectorizer.transform([question])
        similarities = cosine_similarity(question_vector, self._skill_matrix)[0]

        best_index = int(similarities.argmax())
        best_skill = self.skills[best_index]
        confidence = round(float(similarities[best_index]), 2)

        return self._format_result(
            best_skill,
            confidence=confidence,
            method="hybrid_keyword_tfidf"
        )

    def _format_result(
        self,
        skill: Dict[str, Any],
        confidence: float,
        method: str
    ) -> Dict[str, Any]:
        needs_review = confidence < self.LOW_CONFIDENCE_THRESHOLD

        if needs_review:
            return {
                "skill_id": None,
                "skill_name": None,
                "canonical_skill_name": None,
                "confidence": 0,
                "method": method,
                "needs_review": True
            }

        return {
            "skill_id": int(skill["skill_id"]),
            "skill_name": skill["skill_name"],
            "canonical_skill_name": skill["canonical_skill_name"],
            "confidence": confidence,
            "method": method,
            "needs_review": False
        }

    def _skill_document(self, skill: Dict[str, Any]) -> str:
        return " ".join([
            str(skill.get("skill_name", "")),
            str(skill.get("canonical_skill_name", "")),
            str(skill.get("description", ""))
        ])

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[a-z0-9]+", self._normalize(text))

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", str(text).lower()).strip()
