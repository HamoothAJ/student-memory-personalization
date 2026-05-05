from pydantic import BaseModel
from typing import Optional


class MemoryUpdateRequest(BaseModel):
    student_id: int
    session_id: int
    problem_id: int
    concept_name: str
    correct: int
    attempt_count: int
    hint_count: int
    hint_total: Optional[int] = 0
    response_time_ms: Optional[float] = 0.0


class MemoryContextResponse(BaseModel):
    student_id: int
    target_concept: Optional[str] = None