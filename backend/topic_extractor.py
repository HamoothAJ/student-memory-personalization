import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class TopicExtractor:
    """
    Academic topic detector for memory retrieval.

    Detection order:
    1. Strong keyword rule match for obvious skill mentions.
    2. Pre-trained sentence embedding similarity when sentence-transformers is
       installed and the model loads successfully.
    3. TF-IDF cosine fallback when embeddings are unavailable.
    """

    EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_LOW_CONFIDENCE_THRESHOLD = 0.35
    TFIDF_LOW_CONFIDENCE_THRESHOLD = 0.25

    def __init__(self, skills_path: Optional[Path] = None):
        base_dir = Path(__file__).resolve().parent.parent
        self.skills_path = skills_path or base_dir / "models" / "canonical_skills.json"
        self.skills = self._load_skills()
        self._skill_lookup = self._build_skill_lookup()
        self._keyword_index = self._build_keyword_index()
        self._documents = [self._skill_document(skill) for skill in self.skills]
        self._vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self._skill_matrix = self._vectorizer.fit_transform(self._documents)
        self._embedding_model = None
        self._skill_embeddings = None
        self.embedding_status = {
            "available": False,
            "model_name": self.EMBEDDING_MODEL_NAME,
            "error": None,
        }
        self._load_embedding_model()

    def detect_topic(self, question: str) -> Dict[str, Any]:
        normalized_question = self._normalize(question)

        keyword_match = self._detect_with_keyword_rules(normalized_question)
        if keyword_match is not None:
            return keyword_match

        if self._is_generic_unclear_question(normalized_question):
            return self._format_unclear_result(
                confidence=0.0,
                method=self._semantic_method_name(),
            )

        if self._embedding_model is not None and self._skill_embeddings is not None:
            return self._detect_with_embeddings(question)

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

    def _load_embedding_model(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer

            try:
                self._embedding_model = SentenceTransformer(
                    self.EMBEDDING_MODEL_NAME,
                    local_files_only=True,
                )
            except TypeError:
                self._embedding_model = SentenceTransformer(self.EMBEDDING_MODEL_NAME)
            except Exception as local_error:
                if os.getenv("MEMORY_TOPIC_ALLOW_MODEL_DOWNLOAD") != "1":
                    raise local_error
                self._embedding_model = SentenceTransformer(self.EMBEDDING_MODEL_NAME)

            if self._embedding_model is not None:
                self._skill_embeddings = self._encode_texts(self._documents)
                self.embedding_status["available"] = True
        except Exception as error:
            self._embedding_model = None
            self._skill_embeddings = None
            self.embedding_status["available"] = False
            self.embedding_status["error"] = str(error)

    def _encode_texts(self, texts: List[str]):
        try:
            return self._embedding_model.encode(
                texts,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        except TypeError:
            return self._embedding_model.encode(texts)

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
            "how", "i", "in", "is", "me", "of", "or", "please", "the", "this",
            "to", "what", "when", "where", "with", "you"
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

    def _detect_with_keyword_rules(
        self,
        normalized_question: str
    ) -> Optional[Dict[str, Any]]:
        question_tokens = set(self._tokenize(normalized_question))
        best_entry = None
        best_score = 0

        for entry in self._keyword_index:
            phrase_match = any(
                self._phrase_in_text(phrase, normalized_question)
                for phrase in entry["phrases"]
                if len(phrase) >= 5
            )
            token_hits = len(question_tokens.intersection(entry["tokens"]))
            score = token_hits + (3 if phrase_match else 0)

            if (phrase_match or token_hits >= 2) and score > best_score:
                best_entry = entry
                best_score = score

        if best_entry is not None:
            return self._format_skill_result(
                best_entry["skill"],
                confidence=0.95,
                method="keyword_rule",
                threshold=self.EMBEDDING_LOW_CONFIDENCE_THRESHOLD,
            )

        return None

    def _detect_with_embeddings(self, question: str) -> Dict[str, Any]:
        question_embedding = self._encode_texts([question])
        similarities = cosine_similarity(question_embedding, self._skill_embeddings)[0]

        best_index = int(similarities.argmax())
        best_skill = self.skills[best_index]
        confidence = round(float(similarities[best_index]), 4)

        return self._format_skill_result(
            best_skill,
            confidence=confidence,
            method="pretrained_embedding_similarity",
            threshold=self.EMBEDDING_LOW_CONFIDENCE_THRESHOLD,
        )

    def _detect_with_tfidf(self, question: str) -> Dict[str, Any]:
        question_vector = self._vectorizer.transform([question])
        similarities = cosine_similarity(question_vector, self._skill_matrix)[0]

        best_index = int(similarities.argmax())
        best_skill = self.skills[best_index]
        confidence = round(float(similarities[best_index]), 4)

        return self._format_skill_result(
            best_skill,
            confidence=confidence,
            method="tfidf_cosine_fallback",
            threshold=self.TFIDF_LOW_CONFIDENCE_THRESHOLD,
        )

    def _format_skill_result(
        self,
        skill: Dict[str, Any],
        confidence: float,
        method: str,
        threshold: float,
    ) -> Dict[str, Any]:
        if confidence < threshold:
            return self._format_unclear_result(confidence=confidence, method=method)

        return {
            "skill_id": int(skill["skill_id"]),
            "skill_name": skill["skill_name"],
            "canonical_skill_name": skill["canonical_skill_name"],
            "confidence": round(float(confidence), 4),
            "method": method,
            "needs_review": False,
        }

    def _format_unclear_result(self, confidence: float, method: str) -> Dict[str, Any]:
        return {
            "skill_id": None,
            "skill_name": None,
            "canonical_skill_name": None,
            "confidence": round(float(confidence), 4),
            "method": method,
            "needs_review": True,
        }

    def _semantic_method_name(self) -> str:
        if self._embedding_model is not None and self._skill_embeddings is not None:
            return "pretrained_embedding_similarity"

        return "tfidf_cosine_fallback"

    def _skill_document(self, skill: Dict[str, Any]) -> str:
        return " ".join([
            str(skill.get("skill_name", "")),
            str(skill.get("canonical_skill_name", "")),
            str(skill.get("description", ""))
        ])

    def _is_generic_unclear_question(self, normalized_question: str) -> bool:
        if not normalized_question:
            return True

        generic_phrases = (
            "can you help me understand this",
            "help me understand this",
            "can you help me with this",
            "i need help with this",
            "i do not understand this",
            "i don't understand this",
            "i dont understand this",
            "this problem is confusing",
        )

        if any(phrase in normalized_question for phrase in generic_phrases):
            return True

        return False

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[a-z0-9]+", self._normalize(text))

    def _phrase_in_text(self, phrase: str, text: str) -> bool:
        pattern = r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])"
        return re.search(pattern, text) is not None

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", str(text).lower()).strip()
