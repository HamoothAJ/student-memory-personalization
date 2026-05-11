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
    student_utterance: Optional[str] = None


class MemoryContextResponse(BaseModel):
    student_id: int
    target_concept: Optional[str] = None


class QuestionContextRequest(BaseModel):
    student_id: int
    session_id: int
    question: str


class RepairOutcome(BaseModel):
    correct: int
    hint_used: int
    pps_score: Optional[float] = None
    reward: Optional[float] = None


class StoreRepairOutcomeRequest(BaseModel):
    student_id: int
    session_id: int
    skill_id: Optional[int] = None
    chosen_action: str
    after_outcome: RepairOutcome
