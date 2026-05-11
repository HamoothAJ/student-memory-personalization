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
GET /memory/meta-signals/{student_id}/{session_id}
POST /memory/question-context
POST /memory/store-repair-outcome
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
    "confidence": 0.95,
    "method": "keyword_rule",
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

### Pre-trained Topic Detection

The topic detector maps student questions to canonical skills from `models/canonical_skills.json`.

Detection order:

- strong keyword rule match for obvious skill mentions
- pre-trained sentence embedding similarity using `sentence-transformers/all-MiniLM-L6-v2`
- TF-IDF cosine fallback if `sentence-transformers` is unavailable or the model fails to load

For embedding similarity, `needs_review = true` when confidence is below `0.35`. For TF-IDF fallback, `needs_review = true` when confidence is below `0.25`.

Low-confidence results return `skill_id`, `skill_name`, and `canonical_skill_name` as `null`, and low-confidence results do not retrieve topic memory. Memory does not default unclear questions to the first skill.

Signal extraction remains rule-based for now. This topic detector is not BKT, mastery prediction, or BERT fine-tuning.

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
    "confidence": 0.0,
    "method": "pretrained_embedding_similarity",
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

If the pre-trained model is unavailable, the same unclear response may use `"method": "tfidf_cosine_fallback"`.

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

`previous_repair` is `null` until repair outcomes are stored through `POST /memory/store-repair-outcome`.

## POST /memory/store-repair-outcome

Stores a FAPR-LB response on the latest matching interaction row so the next FAPR context call can include it as `previous_repair`.

### Request

```json
{
  "student_id": 999001,
  "session_id": 5001,
  "skill_id": 220,
  "chosen_action": "prerequisite_review",
  "after_outcome": {
    "correct": 1,
    "hint_used": 0,
    "pps_score": 0.51,
    "reward": 0.65
  }
}
```

### Response

```json
{
  "stored": true,
  "student_id": "999001",
  "session_id": "5001",
  "skill_id": 220,
  "repair_action": "prerequisite_review",
  "after_outcome": {
    "correct": 1,
    "hint_used": 0,
    "pps_score": 0.51,
    "reward": 0.65
  },
  "message": "Repair outcome stored successfully."
}
```

If no interaction row exists for the student/session, Memory returns:

```json
{
  "stored": false,
  "message": "No matching interaction found for repair outcome storage."
}
```

The endpoint prefers the latest interaction matching `student_id`, `session_id`, and `skill_id`. If that row does not exist, it falls back to the latest interaction for the student/session.

On the next FAPR context call, Memory returns:

```json
{
  "prev_action": "prerequisite_review",
  "prev_outcome": {
    "correct": 1,
    "hint_used": 0
  }
}
```

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

## GET /memory/meta-signals/{student_id}/{session_id}

Signal-based session export for the Meta-Agent.

Memory provides structured evidence signals only. The Meta-Agent performs BKT, mastery analysis, knowledge graph updates, and learning path logic.

### Request

```http
GET /memory/meta-signals/{student_id}/{session_id}
```

Example:

```http
GET /memory/meta-signals/999001/5001
```

### Response

```json
{
  "session_id": "5001",
  "student_id": "999001",
  "signals": [
    {
      "skill": "Percent Of",
      "signal_type": "incorrect_answer"
    },
    {
      "skill": "Percent Of",
      "signal_type": "repeated_misunderstanding"
    },
    {
      "skill": "Percent Of",
      "signal_type": "correct_answer"
    }
  ],
  "misconceptions": []
}
```

The full SQLite response also includes `found`, `source`, `signal_count`, and an `integration_note` describing downstream usage constraints.

### Signal Rules

Allowed positive evidence signal types:

- `correct_answer`
- `correct_explanation`
- `partial_correct`
- `evaluator_positive`

Allowed negative evidence signal types:

- `incorrect_answer`
- `repeated_misunderstanding`
- `confusion`
- `clarification_request`
- `evaluator_negative`

Current deterministic extraction rules:

- `correct_answer`: `correct = 1`, `hint_count = 0`, and `attempt_count = 1`
- `partial_correct`: `correct = 1` with hints or multiple attempts
- `incorrect_answer`: `correct = 0`
- `confusion`: clear confusion phrases in stored `student_utterance`
- `clarification_request`: clear explanation or repeat requests in stored `student_utterance`
- `repeated_misunderstanding`: same canonical skill has at least two `incorrect_answer` signals in the session

Skills are canonical names from `models/canonical_skills.json`. Unknown or unmapped skills are skipped. Unknown signal types are skipped.

Future work: train a text model for signal extraction from MathDial and emit `correct_explanation`, `evaluator_positive`, and `evaluator_negative` when explicit stored evidence exists.

## POST /memory/update

Stores a structured student interaction and updates short-term, long-term, and concept-based memory.

If migration columns exist in SQLite, the backend also stores mapped `skill_id` and `canonical_skill_name` when the concept is known in the canonical skill file.

`student_utterance` is optional. When provided, it is stored for downstream signal extraction rules such as `confusion` and `clarification_request`.

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
python scripts/test_pretrained_topic_extractor.py
python scripts/test_question_context_pretrained.py
```

The scripts check direct TopicExtractor predictions, the running `/memory/question-context` endpoint, and low-confidence unclear-question examples.

To test the FAPR-LB payload contract, start the backend and run:

```bash
python scripts/test_fapr_context_contract.py
python scripts/test_store_repair_outcome.py
python scripts/test_meta_signals_contract.py
```

The scripts seed test interactions through `POST /memory/update`, call `GET /memory/fapr-context/{student_id}` and `GET /memory/meta-signals/{student_id}/{session_id}`, check the required fields, verify oldest-to-newest ordering where applicable, verify that stored repair outcomes appear as `previous_repair`, and verify the Meta-Agent signal contract.

## Final Integration Evidence Test

Run the backend:

```bash
cd backend
..\.venv\Scripts\python.exe -m uvicorn app:app --reload
```

Run the final evidence test from the repository root:

```bash
.\.venv\Scripts\python.exe scripts\test_final_memory_integration.py
```

The final script uses `requests` against `http://127.0.0.1:8000` and validates the running Memory Component end to end:

- topic-aware question understanding
- skill ID and canonical skill support
- FAPR-LB repair-turn context
- repair outcome storage
- previous repair retrieval
- Meta-Agent signal export
- safe unclear-question handling

Evidence outputs:

```text
outputs/api_results/final_question_context_clear.json
outputs/api_results/final_question_context_unclear.json
outputs/api_results/final_fapr_before_repair.json
outputs/api_results/final_store_repair_outcome.json
outputs/api_results/final_fapr_after_repair.json
outputs/api_results/final_meta_signals.json
outputs/tables/final_integration_test_results.csv
```
