from database import get_connection


class DynamicMemoryService:
    def add_interaction(self, request):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO interaction_logs (
            student_id,
            session_id,
            problem_id,
            concept_name,
            correct,
            attempt_count,
            hint_count,
            hint_total,
            response_time_ms
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.student_id,
            request.session_id,
            request.problem_id,
            request.concept_name,
            request.correct,
            request.attempt_count,
            request.hint_count,
            request.hint_total,
            request.response_time_ms
        ))

        conn.commit()
        conn.close()

        self.update_short_term_memory(request.student_id, request.session_id)
        self.update_long_term_memory(request.student_id)
        self.update_concept_based_memory(request.student_id, request.concept_name)

        return self.get_dynamic_memory_context(request.student_id, request.concept_name)

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
        average_response_time_ms = sum(row["response_time_ms"] for row in rows) / total_interactions

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
        avg_response_time_ms = sum(row["response_time_ms"] for row in rows) / total_interactions

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

    def get_dynamic_memory_context(self, student_id, concept_name):
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

        concept_memory = cursor.execute("""
        SELECT *
        FROM concept_based_memory
        WHERE student_id = ? AND LOWER(concept_name) = LOWER(?)
        """, (student_id, concept_name)).fetchone()

        conn.close()

        return {
            "message": "Memory updated successfully.",
            "student_id": student_id,
            "target_concept": concept_name,
            "short_term_memory": dict(short_term) if short_term else {},
            "long_term_memory": dict(long_term) if long_term else {},
            "concept_based_memory": dict(concept_memory) if concept_memory else {},
            "integration_note": {
                "for_meta_agent": "Use this stored interaction history to derive mastery, knowledge graph updates, regression flags, and learning paths.",
                "for_fapr_lb": "Use this memory context as input features for struggle prediction and repair strategy selection.",
                "for_tutor_agent": "Use this context to personalize explanations without treating the student as new."
            }
        }