import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "memory_component.db"

INTEGRATION_COLUMNS = {
    "skill_id": "INTEGER",
    "canonical_skill_name": "TEXT",
    "student_utterance": "TEXT",
    "tutor_response": "TEXT",
    "repair_action": "TEXT",
    "repair_outcome_correct": "INTEGER",
    "repair_hint_used": "INTEGER",
    "pps_score": "REAL",
    "reward": "REAL",
}


def get_existing_columns(cursor, table_name):
    rows = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row[1] for row in rows}


def add_missing_columns():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    existing_columns = get_existing_columns(cursor, "interaction_logs")
    added_columns = []

    for column_name, column_type in INTEGRATION_COLUMNS.items():
        if column_name in existing_columns:
            continue

        cursor.execute(
            f"ALTER TABLE interaction_logs ADD COLUMN {column_name} {column_type}"
        )
        added_columns.append(column_name)

    conn.commit()
    conn.close()

    if added_columns:
        print("Added columns:", ", ".join(added_columns))
    else:
        print("No migration needed. All integration columns already exist.")


if __name__ == "__main__":
    add_missing_columns()
