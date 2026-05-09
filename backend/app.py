from typing import Optional

from fastapi import FastAPI, Query

from memory_service import MemoryService
from dynamic_memory_service import DynamicMemoryService
from schemas import MemoryUpdateRequest


app = FastAPI(
    title="Student Memory Personalization API",
    description="Three-layer student memory service for personalized academic support.",
    version="1.0.0"
)

# CSV-based memory retrieval service
memory_service = MemoryService()

# SQLite-based dynamic memory update/retrieval service
dynamic_memory_service = DynamicMemoryService()


@app.get("/")
def root():
    return {
        "message": "Student Memory Personalization API is running.",
        "component": "Component 3: Memory (Student Personalization)",
        "memory_layers": [
            "short-term memory",
            "long-term memory",
            "concept-based memory"
        ],
        "storage_modes": {
            "csv_memory": "Pre-generated memory tables from ASSISTments dataset",
            "sqlite_memory": "Dynamic memory updates from live interactions"
        }
    }


@app.get("/memory/student/{student_id}")
def get_student_profile(student_id: int):
    """
    Return long-term student memory.

    Current version:
    - Uses CSV-generated memory for existing dataset students.
    - Dynamic SQLite long-term profile is returned through /memory/context/{student_id}
      after POST /memory/update.
    """
    return memory_service.get_student_profile(student_id)


@app.get("/memory/student/{student_id}/concept/{concept_name}")
def get_student_concept_memory(student_id: int, concept_name: str):
    """
    Return concept-level memory for a student and concept.

    Current version:
    - Uses CSV-generated concept memory for existing dataset students.
    """
    return memory_service.get_concept_memory(student_id, concept_name)


@app.get("/memory/context/{student_id}")
def get_memory_context(
    student_id: int,
    concept_name: Optional[str] = Query(default=None)
):
    """
    Return full memory context.

    Logic:
    1. Check SQLite dynamic memory first.
       This supports new students added through POST /memory/update.
    2. If the student is not available in SQLite, fallback to CSV-generated memory.
       This supports original ASSISTments dataset students.
    """

    if dynamic_memory_service.student_exists_in_dynamic_memory(student_id):
        return dynamic_memory_service.get_dynamic_memory_context(
            student_id=student_id,
            concept_name=concept_name
        )

    return memory_service.get_memory_context(
        student_id=student_id,
        target_concept=concept_name
    )


@app.get("/memory/student/{student_id}/interactions")
def get_student_interactions(
    student_id: int,
    limit: int = Query(default=20, ge=1, le=100)
):
    """
    Return recent raw interaction records for a student.

    Current version:
    - Uses CSV-generated processed interaction records.
    """
    return memory_service.get_student_interactions(student_id, limit)


@app.post("/memory/update")
def update_memory(request: MemoryUpdateRequest):
    """
    Store a new student interaction and dynamically update memory.

    This endpoint updates:
    - interaction_logs
    - short_term_memory
    - long_term_memory
    - concept_based_memory

    Data is stored in SQLite.
    """
    return dynamic_memory_service.add_interaction(request)