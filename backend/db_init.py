from database import get_connection


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interaction_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        session_id INTEGER NOT NULL,
        problem_id INTEGER NOT NULL,
        concept_name TEXT NOT NULL,
        correct INTEGER NOT NULL,
        attempt_count INTEGER NOT NULL,
        hint_count INTEGER NOT NULL,
        hint_total INTEGER DEFAULT 0,
        response_time_ms REAL DEFAULT 0,
        skill_id INTEGER,
        canonical_skill_name TEXT,
        student_utterance TEXT,
        tutor_response TEXT,
        repair_action TEXT,
        repair_outcome_correct INTEGER,
        repair_hint_used INTEGER,
        pps_score REAL,
        reward REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS short_term_memory (
        student_id INTEGER NOT NULL,
        session_id INTEGER NOT NULL,
        current_concept TEXT,
        recent_interaction_count INTEGER,
        recent_accuracy REAL,
        average_attempts REAL,
        recent_hint_usage INTEGER,
        session_status TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (student_id, session_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS long_term_memory (
        student_id INTEGER PRIMARY KEY,
        total_interactions INTEGER,
        total_sessions INTEGER,
        total_concepts INTEGER,
        overall_accuracy REAL,
        average_attempts REAL,
        average_hint_count REAL,
        total_hint_count INTEGER,
        average_response_time_ms REAL,
        preferred_support_style TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS concept_based_memory (
        student_id INTEGER NOT NULL,
        concept_name TEXT NOT NULL,
        total_interactions INTEGER,
        correct_count INTEGER,
        wrong_count INTEGER,
        accuracy REAL,
        total_hints INTEGER,
        avg_hints REAL,
        avg_attempts REAL,
        avg_response_time_ms REAL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (student_id, concept_name)
    )
    """)

    conn.commit()
    conn.close()

    print("SQLite memory tables created successfully.")


if __name__ == "__main__":
    create_tables()
