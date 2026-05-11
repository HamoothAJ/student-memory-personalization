from database import get_connection
from signal_extractor import SignalExtractor
from topic_extractor import TopicExtractor


class DynamicMemoryService:
    def __init__(self):
        self.topic_extractor = TopicExtractor()
        self.signal_extractor = SignalExtractor(self.topic_extractor)

    def add_interaction(self, request):
        conn = get_connection()
        cursor = conn.cursor()

        columns = [
            "student_id",
            "session_id",
            "problem_id",
            "concept_name",
            "correct",
            "attempt_count",
            "hint_count",
            "hint_total",
            "response_time_ms"
        ]
        values = [
            request.student_id,
            request.session_id,
            request.problem_id,
            request.concept_name,
            request.correct,
            request.attempt_count,
            request.hint_count,
            request.hint_total,
            request.response_time_ms
        ]

        interaction_columns = self._get_table_columns(cursor, "interaction_logs")
        skill = self.topic_extractor.get_skill_by_name(request.concept_name)

        if skill and "skill_id" in interaction_columns:
            columns.append("skill_id")
            values.append(int(skill["skill_id"]))

        if skill and "canonical_skill_name" in interaction_columns:
            columns.append("canonical_skill_name")
            values.append(skill["canonical_skill_name"])

        if request.student_utterance and "student_utterance" in interaction_columns:
            columns.append("student_utterance")
            values.append(request.student_utterance)

        placeholders = ", ".join(["?"] * len(columns))
        column_names = ", ".join(columns)

        cursor.execute(
            f"INSERT INTO interaction_logs ({column_names}) VALUES ({placeholders})",
            values
        )

        conn.commit()
        conn.close()

        self.update_short_term_memory(request.student_id, request.session_id)
        self.update_long_term_memory(request.student_id)
        self.update_concept_based_memory(request.student_id, request.concept_name)

        return self.get_dynamic_memory_context(
            request.student_id,
            request.concept_name
        )

    def add_interaction_from_text(self, request):
        """
        Store a text-based tutoring interaction after detecting its topic.

        This path supports live frontend or Tutor Agent messages. It keeps the
        original structured add_interaction path unchanged.
        """
        detected_topic = self.topic_extractor.detect_topic(request.student_utterance)

        if detected_topic["needs_review"]:
            self._insert_text_interaction(
                request=request,
                concept_name="Unknown",
                skill_id=None,
                canonical_skill_name=None
            )
            return {
                "updated": False,
                "reason": "topic_clarification_needed",
                "detected_topic": detected_topic,
                "message": (
                    "Topic could not be confidently detected. Ask the student "
                    "to clarify the topic."
                )
            }

        concept_name = detected_topic["canonical_skill_name"]
        self._insert_text_interaction(
            request=request,
            concept_name=concept_name,
            skill_id=detected_topic["skill_id"],
            canonical_skill_name=detected_topic["canonical_skill_name"]
        )

        self.update_short_term_memory(request.student_id, request.session_id)
        self.update_long_term_memory(request.student_id)
        self.update_concept_based_memory(request.student_id, concept_name)

        return {
            "updated": True,
            "student_id": request.student_id,
            "session_id": request.session_id,
            "detected_topic": detected_topic,
            "memory_context": self.get_dynamic_memory_context(
                request.student_id,
                concept_name
            ),
            "integration_note": {
                "for_fapr_lb": (
                    "Stored skill_id and student_utterance are available in "
                    "FAPR context."
                ),
                "for_meta_agent": (
                    "Stored canonical skill and utterance are available for "
                    "signal export."
                )
            }
        }

    def _insert_text_interaction(
        self,
        request,
        concept_name,
        skill_id=None,
        canonical_skill_name=None
    ):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            interaction_columns = self._get_table_columns(cursor, "interaction_logs")
            columns = [
                "student_id",
                "session_id",
                "problem_id",
                "concept_name",
                "correct",
                "attempt_count",
                "hint_count",
                "hint_total",
                "response_time_ms"
            ]
            values = [
                request.student_id,
                request.session_id,
                request.problem_id,
                concept_name,
                request.correct,
                request.attempt_count,
                request.hint_count,
                request.hint_total,
                request.response_time_ms
            ]

            optional_values = {
                "skill_id": skill_id,
                "canonical_skill_name": canonical_skill_name,
                "student_utterance": request.student_utterance,
                "tutor_response": request.tutor_response,
            }

            for column_name, value in optional_values.items():
                if column_name in interaction_columns:
                    columns.append(column_name)
                    values.append(value)

            placeholders = ", ".join(["?"] * len(columns))
            column_names = ", ".join(columns)

            cursor.execute(
                f"INSERT INTO interaction_logs ({column_names}) VALUES ({placeholders})",
                values
            )
            conn.commit()
        finally:
            conn.close()

    def _get_table_columns(self, cursor, table_name):
        rows = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {row["name"] for row in rows}

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

    def _safe_float(self, value, default=0.0):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def update_short_term_memory(self, student_id, session_id):
        conn = get_connection()
        cursor = conn.cursor()

        rows = cursor.execute("""
        SELECT *
        FROM interaction_logs
        WHERE student_id = ? AND session_id = ?
        ORDER BY id
        """, (student_id, session_id)).fetchall()

        if not rows:
            conn.close()
            return

        total = len(rows)
        correct_sum = sum(row["correct"] for row in rows)
        recent_accuracy = correct_sum / total
        average_attempts = sum(row["attempt_count"] for row in rows) / total
        recent_hint_usage = sum(row["hint_count"] for row in rows)
        current_concept = rows[-1]["concept_name"]

        if recent_accuracy >= 0.75:
            session_status = "good_progress"
        elif recent_accuracy >= 0.50:
            session_status = "moderate_progress"
        else:
            session_status = "needs_support"

        cursor.execute("""
        INSERT OR REPLACE INTO short_term_memory (
            student_id,
            session_id,
            current_concept,
            recent_interaction_count,
            recent_accuracy,
            average_attempts,
            recent_hint_usage,
            session_status,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            student_id,
            session_id,
            current_concept,
            total,
            round(recent_accuracy, 2),
            round(average_attempts, 2),
            recent_hint_usage,
            session_status
        ))

        conn.commit()
        conn.close()

    def update_long_term_memory(self, student_id):
        conn = get_connection()
        cursor = conn.cursor()

        rows = cursor.execute("""
        SELECT *
        FROM interaction_logs
        WHERE student_id = ?
        """, (student_id,)).fetchall()

        if not rows:
            conn.close()
            return

        total_interactions = len(rows)
        total_sessions = len(set(row["session_id"] for row in rows))
        total_concepts = len(set(row["concept_name"] for row in rows))

        overall_accuracy = sum(row["correct"] for row in rows) / total_interactions
        average_attempts = sum(row["attempt_count"] for row in rows) / total_interactions
        average_hint_count = sum(row["hint_count"] for row in rows) / total_interactions
        total_hint_count = sum(row["hint_count"] for row in rows)
        average_response_time_ms = (
            sum(row["response_time_ms"] for row in rows) / total_interactions
        )

        if average_hint_count >= 2:
            preferred_support_style = "guided_support"
        elif average_attempts >= 2:
            preferred_support_style = "step_by_step_support"
        elif overall_accuracy >= 0.75:
            preferred_support_style = "independent_practice"
        else:
            preferred_support_style = "basic_explanation_support"

        cursor.execute("""
        INSERT OR REPLACE INTO long_term_memory (
            student_id,
            total_interactions,
            total_sessions,
            total_concepts,
            overall_accuracy,
            average_attempts,
            average_hint_count,
            total_hint_count,
            average_response_time_ms,
            preferred_support_style,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            student_id,
            total_interactions,
            total_sessions,
            total_concepts,
            round(overall_accuracy, 2),
            round(average_attempts, 2),
            round(average_hint_count, 2),
            total_hint_count,
            round(average_response_time_ms, 2),
            preferred_support_style
        ))

        conn.commit()
        conn.close()

    def update_concept_based_memory(self, student_id, concept_name):
        conn = get_connection()
        cursor = conn.cursor()

        rows = cursor.execute("""
        SELECT *
        FROM interaction_logs
        WHERE student_id = ? AND LOWER(concept_name) = LOWER(?)
        """, (student_id, concept_name)).fetchall()

        if not rows:
            conn.close()
            return

        total_interactions = len(rows)
        correct_count = sum(row["correct"] for row in rows)
        wrong_count = total_interactions - correct_count
        accuracy = correct_count / total_interactions
        total_hints = sum(row["hint_count"] for row in rows)
        avg_hints = total_hints / total_interactions
        avg_attempts = sum(row["attempt_count"] for row in rows) / total_interactions
        avg_response_time_ms = (
            sum(row["response_time_ms"] for row in rows) / total_interactions
        )

        cursor.execute("""
        INSERT OR REPLACE INTO concept_based_memory (
            student_id,
            concept_name,
            total_interactions,
            correct_count,
            wrong_count,
            accuracy,
            total_hints,
            avg_hints,
            avg_attempts,
            avg_response_time_ms,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            student_id,
            concept_name,
            total_interactions,
            correct_count,
            wrong_count,
            round(accuracy, 2),
            total_hints,
            round(avg_hints, 2),
            round(avg_attempts, 2),
            round(avg_response_time_ms, 2)
        ))

        conn.commit()
        conn.close()

    def student_exists_in_dynamic_memory(self, student_id):
        """
        Check whether a student exists in the SQLite dynamic memory tables.

        This is used by app.py to decide whether /memory/context/{student_id}
        should return SQLite dynamic memory or fallback to CSV-generated memory.
        """
        conn = get_connection()
        cursor = conn.cursor()

        row = cursor.execute("""
        SELECT student_id
        FROM long_term_memory
        WHERE student_id = ?
        """, (student_id,)).fetchone()

        conn.close()

        return row is not None

    def get_dynamic_memory_context(self, student_id, concept_name=None):
        """
        Return memory context from SQLite dynamic memory.

        If concept_name is not provided, the latest updated concept for the
        student is selected automatically.
        """
        conn = get_connection()
        cursor = conn.cursor()

        short_term = cursor.execute("""
        SELECT *
        FROM short_term_memory
        WHERE student_id = ?
        ORDER BY updated_at DESC
        LIMIT 1
        """, (student_id,)).fetchone()

        long_term = cursor.execute("""
        SELECT *
        FROM long_term_memory
        WHERE student_id = ?
        """, (student_id,)).fetchone()

        if concept_name is None:
            latest_concept = cursor.execute("""
            SELECT concept_name
            FROM concept_based_memory
            WHERE student_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
            """, (student_id,)).fetchone()

            if latest_concept:
                concept_name = latest_concept["concept_name"]

        concept_memory = None

        if concept_name is not None:
            concept_memory = cursor.execute("""
            SELECT *
            FROM concept_based_memory
            WHERE student_id = ? AND LOWER(concept_name) = LOWER(?)
            """, (student_id, concept_name)).fetchone()

        conn.close()

        if short_term is None or long_term is None:
            return {
                "found": False,
                "source": "sqlite",
                "message": "Student not found in dynamic SQLite memory.",
                "student_id": student_id
            }

        return {
            "found": True,
            "source": "sqlite",
            "student_id": student_id,
            "target_concept": concept_name,
            "short_term_memory": dict(short_term) if short_term else {},
            "long_term_memory": dict(long_term) if long_term else {},
            "concept_based_memory": dict(concept_memory) if concept_memory else {},
            "integration_note": {
                "for_meta_agent": (
                    "Use this stored interaction history to derive mastery, "
                    "knowledge graph updates, regression flags, and learning paths."
                ),
                "for_fapr_lb": (
                    "Use this memory context as input features for struggle "
                    "prediction and repair strategy selection."
                ),
                "for_tutor_agent": (
                    "Use this context to personalize explanations without "
                    "treating the student as new."
                )
            }
        }

    def get_question_context(self, student_id, session_id, question):
        """
        Detect the academic topic in a student question and return the
        student's topic-specific memory for downstream tutoring agents.
        """
        detected_topic = self.topic_extractor.detect_topic(question)

        if detected_topic["needs_review"]:
            return self._build_unclear_question_context(
                student_id=student_id,
                session_id=session_id,
                question=question,
                detected_topic=detected_topic
            )

        topic_memory = self._get_topic_memory(student_id, detected_topic)
        recommendation_context = self._build_recommendation_context(topic_memory)

        return {
            "student_id": student_id,
            "session_id": session_id,
            "question": question,
            "detected_topic": detected_topic,
            "topic_memory": topic_memory,
            "recommendation_context": recommendation_context,
            "integration_hint": {
                "for_fapr_lb": "Use skill_id and skill_name as current_skill_id/current_skill_name.",
                "for_meta_agent": "Use canonical_skill_name as the skill field.",
                "for_tutor_planner_evaluator": (
                    "Use topic_memory and recommendation_context to personalize "
                    "the next tutoring turn."
                )
            }
        }

    def _build_unclear_question_context(
        self,
        student_id,
        session_id,
        question,
        detected_topic
    ):
        return {
            "student_id": student_id,
            "session_id": session_id,
            "question": question,
            "detected_topic": detected_topic,
            "topic_memory": None,
            "recommendation_context": {
                "support_need": "topic_clarification_needed",
                "suggested_tutor_style": "ask_clarifying_question",
                "reason": (
                    "The question does not contain enough topic information "
                    "to retrieve topic-specific memory."
                )
            },
            "integration_hint": {
                "for_fapr_lb": "Do not call repair strategy until skill is clarified.",
                "for_meta_agent": "No canonical skill should be emitted for this unclear question.",
                "for_tutor_planner_evaluator": (
                    "Ask the student to specify the topic or provide the question."
                )
            }
        }

    def _get_topic_memory(self, student_id, detected_topic):
        conn = get_connection()
        cursor = conn.cursor()

        try:
            row = cursor.execute("""
            SELECT *
            FROM concept_based_memory
            WHERE student_id = ?
              AND (
                LOWER(concept_name) = LOWER(?)
                OR LOWER(concept_name) = LOWER(?)
              )
            LIMIT 1
            """, (
                student_id,
                detected_topic["canonical_skill_name"],
                detected_topic["skill_name"]
            )).fetchone()
        finally:
            conn.close()

        if row is None:
            return {
                "skill_id": detected_topic["skill_id"],
                "skill_name": detected_topic["skill_name"],
                "total_interactions": 0,
                "correct_count": 0,
                "wrong_count": 0,
                "accuracy": 0.0,
                "total_hints": 0,
                "avg_hints": 0.0,
                "avg_attempts": 0.0,
                "avg_response_time_ms": 0.0
            }

        return {
            "skill_id": detected_topic["skill_id"],
            "skill_name": detected_topic["skill_name"],
            "total_interactions": self._safe_int(row["total_interactions"]),
            "correct_count": self._safe_int(row["correct_count"]),
            "wrong_count": self._safe_int(row["wrong_count"]),
            "accuracy": self._safe_float(row["accuracy"]),
            "total_hints": self._safe_int(row["total_hints"]),
            "avg_hints": self._safe_float(row["avg_hints"]),
            "avg_attempts": self._safe_float(row["avg_attempts"]),
            "avg_response_time_ms": self._safe_float(row["avg_response_time_ms"])
        }

    def _build_recommendation_context(self, topic_memory):
        total_interactions = topic_memory["total_interactions"]
        accuracy = topic_memory["accuracy"]
        avg_hints = topic_memory["avg_hints"]
        avg_attempts = topic_memory["avg_attempts"]

        if total_interactions == 0:
            return {
                "support_need": "new_topic",
                "suggested_tutor_style": "introductory_explanation",
                "reason": "No previous memory exists for this topic."
            }

        if accuracy < 0.5:
            return {
                "support_need": "needs_support",
                "suggested_tutor_style": "step_by_step_support",
                "reason": "Student has low accuracy or repeated hint usage in this topic."
            }

        if avg_hints >= 1.5:
            return {
                "support_need": "guided_support",
                "suggested_tutor_style": "guided_support",
                "reason": "Student has used multiple hints in this topic."
            }

        if avg_attempts >= 2:
            return {
                "support_need": "step_by_step_support",
                "suggested_tutor_style": "step_by_step_support",
                "reason": "Student usually needs multiple attempts in this topic."
            }

        return {
            "support_need": "normal_support",
            "suggested_tutor_style": "normal_support",
            "reason": "Student has sufficient prior performance in this topic."
        }

    def _skill_for_interaction(self, row):
        skill_id = self._row_get(row, "skill_id")
        if skill_id is not None:
            skill = self.topic_extractor.get_skill_by_id(skill_id)
            if skill:
                return {
                    "skill_id": int(skill["skill_id"]),
                    "skill_name": skill["skill_name"],
                    "canonical_skill_name": skill["canonical_skill_name"]
                }

        concept_name = (
            self._row_get(row, "canonical_skill_name")
            or self._row_get(row, "concept_name")
        )
        skill = self.topic_extractor.get_skill_by_name(concept_name)

        if skill:
            return {
                "skill_id": int(skill["skill_id"]),
                "skill_name": skill["skill_name"],
                "canonical_skill_name": skill["canonical_skill_name"]
            }

        return {
            "skill_id": self._safe_int(skill_id, default=None),
            "skill_name": concept_name,
            "canonical_skill_name": concept_name
        }

    def _resolve_skill_identifier(self, current_skill_id, current_skill_name, latest_row):
        if current_skill_id is not None:
            skill = (
                self.topic_extractor.get_skill_by_id(current_skill_id)
                or self.topic_extractor.get_skill_by_name(current_skill_id)
            )
            if skill:
                return {
                    "skill_id": int(skill["skill_id"]),
                    "skill_name": skill["skill_name"],
                    "canonical_skill_name": skill["canonical_skill_name"]
                }

            return {
                "skill_id": self._safe_int(current_skill_id, default=None),
                "skill_name": current_skill_name or self._row_get(latest_row, "concept_name"),
                "canonical_skill_name": current_skill_name or self._row_get(latest_row, "concept_name")
            }

        if current_skill_name is not None:
            skill = self.topic_extractor.get_skill_by_name(current_skill_name)
            if skill:
                return {
                    "skill_id": int(skill["skill_id"]),
                    "skill_name": skill["skill_name"],
                    "canonical_skill_name": skill["canonical_skill_name"]
                }

            return {
                "skill_id": None,
                "skill_name": current_skill_name,
                "canonical_skill_name": current_skill_name
            }

        return self._skill_for_interaction(latest_row)

    def _format_fapr_attempt(self, row):
        skill = self._skill_for_interaction(row)
        response_time_ms = self._safe_float(row["response_time_ms"])

        return {
            "order_id": self._safe_int(self._row_get(row, "id")),
            "skill_id": skill["skill_id"],
            "correct": self._safe_int(row["correct"]),
            "hint_count": self._safe_int(row["hint_count"]),
            "attempt_count": self._safe_int(row["attempt_count"]),
            "ms_first_response": response_time_ms
        }

    def _format_fapr_current_attempt(self, row):
        formatted_attempt = self._format_fapr_attempt(row)
        return {
            "skill_id": formatted_attempt["skill_id"],
            "correct": formatted_attempt["correct"],
            "hint_count": formatted_attempt["hint_count"],
            "attempt_count": formatted_attempt["attempt_count"],
            "ms_first_response": formatted_attempt["ms_first_response"]
        }

    def _build_previous_repair(self, rows):
        for row in reversed(rows):
            repair_action = self._row_get(row, "repair_action")
            if repair_action:
                outcome_correct = self._row_get(row, "repair_outcome_correct")
                hint_used = self._row_get(row, "repair_hint_used")

                return {
                    "prev_action": repair_action,
                    "prev_outcome": {
                        "correct": outcome_correct,
                        "hint_used": hint_used
                    }
                }

        return None

    def _get_previous_repair_for_session(self, cursor, student_id, session_id):
        interaction_columns = self._get_table_columns(cursor, "interaction_logs")
        required_columns = {
            "repair_action",
            "repair_outcome_correct",
            "repair_hint_used"
        }

        if not required_columns.issubset(interaction_columns):
            return None

        row = cursor.execute("""
        SELECT repair_action, repair_outcome_correct, repair_hint_used
        FROM interaction_logs
        WHERE student_id = ?
          AND session_id = ?
          AND repair_action IS NOT NULL
        ORDER BY id DESC
        LIMIT 1
        """, (student_id, session_id)).fetchone()

        if row is None:
            return None

        return {
            "prev_action": row["repair_action"],
            "prev_outcome": {
                "correct": row["repair_outcome_correct"],
                "hint_used": row["repair_hint_used"]
            }
        }

    def store_repair_outcome(self, request):
        """
        Store the FAPR-LB repair outcome on the latest matching interaction row.

        The stored values are later exposed as previous_repair by
        /memory/fapr-context/{student_id}.
        """
        conn = get_connection()
        cursor = conn.cursor()

        try:
            interaction_columns = self._get_table_columns(cursor, "interaction_logs")
            required_columns = {
                "repair_action",
                "repair_outcome_correct",
                "repair_hint_used",
                "pps_score",
                "reward"
            }
            missing_columns = required_columns.difference(interaction_columns)

            if missing_columns:
                return {
                    "stored": False,
                    "message": (
                        "Repair outcome columns are missing. Run "
                        "scripts/migrate_add_integration_fields.py first."
                    ),
                    "missing_columns": sorted(missing_columns)
                }

            row = None

            if request.skill_id is not None and "skill_id" in interaction_columns:
                row = cursor.execute("""
                SELECT *
                FROM interaction_logs
                WHERE student_id = ?
                  AND session_id = ?
                  AND skill_id = ?
                ORDER BY id DESC
                LIMIT 1
                """, (
                    request.student_id,
                    request.session_id,
                    request.skill_id
                )).fetchone()

            if row is None:
                row = cursor.execute("""
                SELECT *
                FROM interaction_logs
                WHERE student_id = ?
                  AND session_id = ?
                ORDER BY id DESC
                LIMIT 1
                """, (
                    request.student_id,
                    request.session_id
                )).fetchone()

            if row is None:
                return {
                    "stored": False,
                    "message": "No matching interaction found for repair outcome storage."
                }

            cursor.execute("""
            UPDATE interaction_logs
            SET repair_action = ?,
                repair_outcome_correct = ?,
                repair_hint_used = ?,
                pps_score = ?,
                reward = ?
            WHERE id = ?
            """, (
                request.chosen_action,
                request.after_outcome.correct,
                request.after_outcome.hint_used,
                request.after_outcome.pps_score,
                request.after_outcome.reward,
                row["id"]
            ))

            conn.commit()

            stored_skill_id = request.skill_id
            if stored_skill_id is None:
                stored_skill_id = self._skill_for_interaction(row)["skill_id"]

            return {
                "stored": True,
                "student_id": str(request.student_id),
                "session_id": str(request.session_id),
                "skill_id": stored_skill_id,
                "repair_action": request.chosen_action,
                "after_outcome": {
                    "correct": request.after_outcome.correct,
                    "hint_used": request.after_outcome.hint_used,
                    "pps_score": request.after_outcome.pps_score,
                    "reward": request.after_outcome.reward
                },
                "message": "Repair outcome stored successfully."
            }

        finally:
            conn.close()

    def get_fapr_context(
        self,
        student_id,
        session_id=None,
        current_skill_id=None,
        current_skill_name=None,
        limit=10
    ):
        """
        Return recent turn-by-turn learning context for the FAPR-LB component.

        FAPR-LB uses this output for:
        - TSRP struggle prediction
        - failure type detection
        - LinTS repair strategy selection
        - later reward/policy update

        Current version:
        - Reads from SQLite interaction_logs
        - Returns previous_repair as null values
        - Returns last_student_utterance when text interactions have been stored
        """
        conn = get_connection()
        cursor = conn.cursor()

        try:
            if session_id is None:
                latest_session = cursor.execute("""
                SELECT session_id
                FROM interaction_logs
                WHERE student_id = ?
                ORDER BY id DESC
                LIMIT 1
                """, (student_id,)).fetchone()

                if latest_session is None:
                    return {
                        "found": False,
                        "source": "sqlite",
                        "message": "No interaction records found for this student.",
                        "student_id": str(student_id)
                    }

                session_id = latest_session["session_id"]

            rows = cursor.execute("""
            SELECT *
            FROM interaction_logs
            WHERE student_id = ? AND session_id = ?
            ORDER BY id DESC
            LIMIT ?
            """, (student_id, session_id, limit)).fetchall()

            if not rows:
                return {
                    "found": False,
                    "source": "sqlite",
                    "message": "No interaction records found for this student and session.",
                    "student_id": str(student_id),
                    "session_id": str(session_id)
                }

            rows = list(reversed(rows))
            latest_row = rows[-1]
            current_skill = self._resolve_skill_identifier(
                current_skill_id,
                current_skill_name,
                latest_row
            )
            recent_interactions = [
                self._format_fapr_attempt(row)
                for row in rows
            ]
            current_attempt = self._format_fapr_current_attempt(latest_row)

            return {
                "student_id": str(student_id),
                "session_id": str(session_id),
                "current_skill_id": current_skill["skill_id"],
                "current_skill_name": current_skill["skill_name"],
                "recent_interactions": recent_interactions,
                "current_attempt": current_attempt,
                "previous_repair": self._get_previous_repair_for_session(
                    cursor,
                    student_id,
                    session_id
                ),
                "last_student_utterance": self._row_get(latest_row, "student_utterance")
            }

        finally:
            conn.close()

    def get_meta_signals_export(self, student_id, session_id):
        """
        Return deterministic evidence signals for the Meta-Agent.

        This endpoint exports structured evidence only. Meta-Agent owns BKT,
        mastery estimation, knowledge graph updates, and learning paths.
        """
        conn = get_connection()
        cursor = conn.cursor()

        try:
            rows = cursor.execute("""
            SELECT *
            FROM interaction_logs
            WHERE student_id = ? AND session_id = ?
            ORDER BY id ASC
            """, (student_id, session_id)).fetchall()

            if not rows:
                return {
                    "found": False,
                    "source": "sqlite",
                    "message": "No session interactions found for this student and session.",
                    "session_id": str(session_id),
                    "student_id": str(student_id),
                    "signals": [],
                    "misconceptions": []
                }

            signals = self.signal_extractor.extract_session_signals(rows)

            return {
                "found": True,
                "source": "sqlite",
                "session_id": str(session_id),
                "student_id": str(student_id),
                "signals": signals,
                "signal_count": len(signals),
                "misconceptions": [],
                "integration_note": {
                    "target_component": "Meta-Agent",
                    "purpose": (
                        "Structured evidence signals for BKT/mastery analysis, "
                        "knowledge graph updates, and learning path generation."
                    ),
                    "important_constraints": [
                        "Skills are canonical skill names.",
                        "Signal types are restricted to the 9 allowed values.",
                        "Memory exports evidence only and does not calculate mastery."
                    ]
                }
            }

        finally:
            conn.close()

    def get_meta_session_export(self, student_id, session_id):
        """
        Return chronological session attempts for the Meta-Agent.

        The Meta-Agent uses this output for:
        - BKT mastery tracking
        - knowledge graph updates
        - learning path generation
        - regression detection

        Current version:
        - Reads from SQLite interaction_logs.
        - Returns attempts in chronological order.
        - Uses concept_name as skill.
        - Returns binary correct value only.
        - Misconceptions are returned as an empty list for now.
        """
        conn = get_connection()
        cursor = conn.cursor()

        try:
            rows = cursor.execute("""
            SELECT *
            FROM interaction_logs
            WHERE student_id = ? AND session_id = ?
            ORDER BY id ASC
            """, (student_id, session_id)).fetchall()

            if not rows:
                return {
                    "found": False,
                    "source": "sqlite",
                    "message": "No session attempts found for this student and session.",
                    "student_id": str(student_id),
                    "session_id": str(session_id),
                    "attempts": [],
                    "misconceptions": []
                }

            attempts = []

            for row in rows:
                skill = self._skill_for_interaction(row)
                attempts.append({
                    "skill": skill["canonical_skill_name"],
                    "correct": int(row["correct"])
                })

            return {
                "found": True,
                "source": "sqlite",
                "student_id": str(student_id),
                "session_id": str(session_id),
                "attempt_count": len(attempts),
                "attempts": attempts,
                "misconceptions": [],
                "integration_note": {
                    "target_component": "Meta-Agent",
                    "purpose": (
                        "Chronological session attempts for BKT mastery tracking, "
                        "knowledge graph updates, and learning path generation."
                    ),
                    "important_constraints": [
                        "Skill names should match the canonical ASSISTments skill list.",
                        "correct must be binary: 0 or 1.",
                        "Attempts are returned in chronological order.",
                        "Misconceptions are optional and currently returned as an empty list."
                    ]
                }
            }

        finally:
            conn.close()
