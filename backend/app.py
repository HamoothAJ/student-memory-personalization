from fastapi import FastAPI, Query
from typing import Optional
from memory_service import MemoryService
from schemas import MemoryUpdateRequest

app = FastAPI(
    title="Student Memory Personalization API",
    description="Three-layer student memory service for personalized academic support.",
    version="1.0.0"
)

memory_service = MemoryService()


@app.get("/")
def root():
    return {
        "message": "Student Memory Personalization API is running.",
        "component": "Component 3: Memory (Student Personalization)",
        "memory_layers": [
            "short-term memory",
            "long-term memory",
            "concept-based memory"
        ]
    }


@app.get("/memory/student/{student_id}")
def get_student_profile(student_id: int):
    return memory_service.get_student_profile(student_id)


@app.get("/memory/student/{student_id}/concept/{concept_name}")
def get_student_concept_memory(student_id: int, concept_name: str):
    return memory_service.get_concept_memory(student_id, concept_name)


@app.get("/memory/context/{student_id}")
def get_memory_context(
    student_id: int,
    concept_name: Optional[str] = Query(default=None)
):
    return memory_service.get_memory_context(student_id, concept_name)


@app.get("/memory/student/{student_id}/interactions")
def get_student_interactions(
    student_id: int,
    limit: int = Query(default=20, ge=1, le=100)
):
    return memory_service.get_student_interactions(student_id, limit)


@app.post("/memory/update")
def update_memory(request: MemoryUpdateRequest):
    return {
        "message": "Memory update endpoint placeholder.",
        "note": "CSV-based prototype currently supports retrieval. Full dynamic update will be implemented in the next stage with SQLite/PostgreSQL.",
        "received_interaction": request.dict()
    }