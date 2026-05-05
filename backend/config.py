from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SHORT_TERM_MEMORY_PATH = BASE_DIR / "data" / "processed" / "short_term_memory.csv"
LONG_TERM_MEMORY_PATH = BASE_DIR / "data" / "processed" / "long_term_memory.csv"
CONCEPT_MEMORY_PATH = BASE_DIR / "data" / "processed" / "concept_based_memory.csv"
INTERACTION_LOG_PATH = BASE_DIR / "data" / "processed" / "processed_interactions.csv"