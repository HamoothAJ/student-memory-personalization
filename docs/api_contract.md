# Memory Component API Contract

## Component

**Component 3: Memory (Student Personalization)**

Formal title: **Three-Layer Student Memory Architecture for Personalized Academic Support**

## Boundary

The Memory Component stores, updates, retrieves, and packages student learning context.

It does not generate tutoring responses, calculate mastery probability, run BKT, build knowledge graphs, predict struggle, or choose repair strategies. Those responsibilities remain with Tutor, Planner, Evaluator, Meta-Agent, and FAPR-LB.

## Implemented Endpoints

```http
GET /
GET /memory/student/{student_id}
GET /memory/context/{student_id}
GET /memory/student/{student_id}/concept/{concept_name}
GET /memory/student/{student_id}/interactions
POST /memory/update
GET /memory/fapr-context/{student_id}
GET /memory/meta-session/{student_id}/{session_id}
POST /memory/question-context
```

## POST /memory/question-context

Semantic topic-aware memory retrieval for a new student question.

### Request

```json
{
  "student_id": 999001,
  "session_id": 7001,
  "question": "Can you explain how to find 25 percent of 80?"
}
```

### Response

```json
{
  "student_id": 999001,
  "session_id": 7001,
  "question": "Can you explain how to find 25 percent of 80?",
  "detected_topic": {
    "skill_id": 312,
    "skill_name": "Percent Of",
    "canonical_skill_name": "Percent Of",
    "confidence": 0.78,
    "method": "hybrid_keyword_tfidf",
    "needs_review": false
  },
  "topic_memory": {
    "skill_id": 312,
    "skill_name": "Percent Of",
    "total_interactions": 8,
    "correct_count": 3,
    "wrong_count": 5,
    "accuracy": 0.38,
    "total_hints": 7,
    "avg_hints": 0.88,
    "avg_attempts": 2.1,
    "avg_response_time_ms": 42000.0
  },
  "recommendation_context": {
    "support_need": "needs_support",
    "suggested_tutor_style": "step_by_step_support",
    "reason": "Student has low accuracy or repeated hint usage in this topic."
  },
  "integration_hint": {
    "for_fapr_lb": "Use skill_id and skill_name as current_skill_id/current_skill_name.",
    "for_meta_agent": "Use canonical_skill_name as the skill field.",
    "for_tutor_planner_evaluator": "Use topic_memory and recommendation_context to personalize the next tutoring turn."
  }
}
```

### Topic Detection

The current detector uses a local hybrid method:

- keyword matching over canonical skill names and descriptions
- TF-IDF cosine similarity fallback
- `needs_review = true` when confidence is below the low-confidence threshold
- low-confidence results return `skill_id`, `skill_name`, and `canonical_skill_name` as `null`
- low-confidence results do not retrieve topic memory

The starter skill map lives at:

```text
models/canonical_skills.json
```

This file is intentionally replaceable by the Meta-Agent official 95-skill list later.

### Unclear Question Response

When the question does not contain enough topic information, Memory asks the caller to clarify the topic instead of returning guessed memory.

```json
{
  "student_id": 999001,
  "session_id": 7001,
  "question": "Can you help me understand this?",
  "detected_topic": {
    "skill_id": null,
    "skill_name": null,
    "canonical_skill_name": null,
    "confidence": 0,
    "method": "hybrid_keyword_tfidf",
    "needs_review": true
  },
  "topic_memory": null,
  "recommendation_context": {
    "support_need": "topic_clarification_needed",
    "suggested_tutor_style": "ask_clarifying_question",
    "reason": "The question does not contain enough topic information to retrieve topic-specific memory."
  },
  "integration_hint": {
    "for_fapr_lb": "Do not call repair strategy until skill is clarified.",
    "for_meta_agent": "No canonical skill should be emitted for this unclear question.",
    "for_tutor_planner_evaluator": "Ask the student to specify the topic or provide the question."
  }
}
```

## GET /memory/fapr-context/{student_id}

Returns recent interaction context for FAPR-LB.

### Query Parameters

```text
session_id optional integer
current_skill_id optional integer
current_skill_name optional string
limit optional integer, default 10, max 20
```

### Response

Memory returns the FAPR-LB repair-turn payload shape:

```json
{
  "student_id": "999951",
  "session_id": "8101",
  "current_skill_id": 312,
  "current_skill_name": "Percent Of",
  "recent_interactions": [
    {
      "order_id": 1001,
      "skill_id": 312,
      "correct": 0,
      "hint_count": 1,
      "attempt_count": 2,
      "ms_first_response": 18000.0
    }
  ],
  "current_attempt": {
    "skill_id": 312,
    "correct": 1,
    "hint_count": 0,
    "attempt_count": 1,
    "ms_first_response": 9000.0
  },
  "previous_repair": null,
  "last_student_utterance": null
}
```

Memory provides context only. FAPR-LB performs struggle prediction, failure type detection, and repair action selection.

If the SQLite row does not contain `skill_id`, Memory maps from `concept_name` or `canonical_skill_name` using `models/canonical_skills.json` when possible. If no mapping exists, `skill_id` is returned as `null` rather than crashing.

`previous_repair` is `null` until repair outcomes are stored. Store-repair-outcome is a next-step TODO.

## GET /memory/meta-session/{student_id}/{session_id}

Compatibility endpoint for the older Meta-Agent attempt format.

```json
{
  "student_id": "999892",
  "session_id": "7001",
  "attempts": [
    {
      "skill": "Percent Of",
      "correct": 0
    }
  ],
  "misconceptions": []
}
```

The newer Meta-Agent signal endpoint is still pending. Future signal records should use canonical skill names and one of the approved signal types.

## POST /memory/update

Stores a structured student interaction and updates short-term, long-term, and concept-based memory.

If migration columns exist in SQLite, the backend also stores mapped `skill_id` and `canonical_skill_name` when the concept is known in the canonical skill file.

## SQLite Migration

Run this once when using the existing SQLite database:

```bash
python scripts/migrate_add_integration_fields.py
```

The migration is idempotent and safely skips columns that already exist.

## Question Context Test Script

Start the FastAPI backend, then run:

```bash
python scripts/test_question_context.py
```

The script checks percent, fraction, equation, and low-confidence unclear-question examples.

To test the FAPR-LB payload contract, start the backend and run:

```bash
python scripts/test_fapr_context_contract.py
```

The script seeds test interactions through `POST /memory/update`, calls `GET /memory/fapr-context/{student_id}`, checks the required FAPR-LB fields, and verifies oldest-to-newest ordering.
