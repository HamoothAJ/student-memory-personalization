# Student Memory Personalization Component

## Research Component

This repository contains the implementation of **Component 3: Memory (Student Personalization)** for a personalized AI academic support system.

The Memory Component stores, updates, and retrieves student-specific learning information so that other agents can provide personalized academic support.

---

## Component Title

**Three-Layer Student Memory System for Personalized Academic Support**

---

## Component Overview

The Memory Component is the **student personalization and context storage layer** of the tutoring system.

It records student learning interactions and maintains structured student memory that can be reused by other components such as:

- Tutor Agent
- Planner Agent
- Evaluator Agent
- Meta-Agent
- FAPR-LB Self-Improvement Component

The component remembers:

- current session context
- student interaction logs
- weak areas
- strong areas
- past mistakes
- repeated learning behavior
- hint usage patterns
- attempt behavior
- response behavior
- preferred learning support style
- concept-level interaction history

The Memory Component does **not** perform high-level learning analysis such as mastery prediction, Bayesian Knowledge Tracing, knowledge graph generation, regression detection, learning path generation, struggle prediction, or repair strategy selection.

Those responsibilities belong to other components such as the Meta-Agent and FAPR-LB.

In simple terms:

```text
Memory Component = stores and retrieves student learning data
Meta-Agent = analyzes memory data for mastery and learning paths
FAPR-LB = uses memory context to predict struggle and select repair strategies
```

---

## Memory Types

The Memory Component is divided into three memory layers.

---

### 1. Short-Term Memory

Short-Term Memory stores the current tutoring session context.

It includes:

- current student question or activity
- current concept
- recent interactions
- recent correct/wrong answers
- hint usage in the current session
- average attempts in the current session
- current confusion or support need
- current session status

Purpose:

Short-Term Memory helps live agents maintain continuity during the session instead of treating every message as a new conversation.

---

### 2. Long-Term Memory

Long-Term Memory stores persistent student behavior across multiple sessions.

It includes:

- total interactions
- total sessions
- total concepts attempted
- overall student accuracy
- average attempt count
- average hint usage
- total hint count
- average response time
- preferred support style

Purpose:

Long-Term Memory helps the system understand the student as a learner and personalize future sessions based on previous learning history.

---

### 3. Concept-Based Memory

Concept-Based Memory stores student interaction history at the concept level.

For each concept attempted by the student, it stores:

- concept name
- total interactions
- correct count
- wrong count
- accuracy
- total hint usage
- average hint usage
- average attempts
- average response time
- last interaction information

Purpose:

Concept-Based Memory stores concept-level learning history. This data can later be used by the Meta-Agent for mastery tracking, knowledge graph updates, regression detection, and learning path generation.

Important boundary:

The Memory Component stores the concept-level history, but it does **not** calculate final mastery probability, BKT output, knowledge graph state, or learning path categories.

---

## Relationship with Other Components

The Memory Component acts as the **student data and context layer**.

```text
Student Interaction
        ↓
Memory Component stores and updates student memory
        ↓
Tutor / Planner / Evaluator / Meta-Agent / FAPR-LB retrieve memory context
        ↓
Other components provide personalized academic support
```

---

## Component Separation

| Component | Responsibility |
|---|---|
| Memory Component | Stores, updates, and retrieves student learning memory |
| Tutor Agent | Generates personalized explanations |
| Planner Agent | Breaks questions into suitable learning steps |
| Evaluator Agent | Checks student answers and gives feedback |
| Meta-Agent | Analyzes memory data, tracks mastery, detects regression, and generates learning paths |
| FAPR-LB | Predicts turn-level struggle and selects repair strategies |

---

## What the Memory Component Does

The Memory Component:

- stores current session context
- stores student interaction logs
- stores long-term student behavior
- stores concept-level interaction history
- stores hint usage, attempt count, response time, and correctness
- generates structured memory context for other components
- provides APIs for memory retrieval and update

---

## What the Memory Component Does Not Do

The Memory Component does not:

- generate lesson explanations
- act as the Tutor Agent
- evaluate final answers independently
- calculate final mastery probability
- train or run a BKT model
- generate the knowledge graph
- detect learning regression
- generate learning paths
- predict turn-level struggle
- detect tutoring failure type
- select repair strategies
- score tutor responses
- update bandit policies
- orchestrate the complete multi-agent workflow

---

## Relationship with Meta-Agent

The Meta-Agent uses data stored in the Memory Component.

Memory stores:

- raw interaction logs
- session context
- long-term learner behavior
- concept-level attempt history
- hint usage
- attempt behavior
- response time behavior

Meta-Agent analyzes this data to produce:

- mastery probability
- BKT-based mastery state
- knowledge graph updates
- regression flags
- personalized learning path
- revise / learn next / already strong categories

So the relationship is:

```text
Memory stores the data.
Meta-Agent analyzes the data.
```

---

## Relationship with FAPR-LB

FAPR-LB uses the Memory Component as a data provider.

Memory provides:

- recent correctness
- hint count
- attempt count
- response time
- session status
- preferred support style
- concept-level interaction history

FAPR-LB uses this context to produce:

- repair need score
- effort cost score
- disengagement risk
- failure type
- selected repair strategy

So the relationship is:

```text
Memory Component = data/context provider
FAPR-LB = adaptive repair decision-maker
```

---

## Dataset

The selected dataset is the **ASSISTments Skill Builder Dataset**.

This dataset is suitable because it contains real student learning interaction records with information such as:

- student ID
- assignment/session ID
- problem ID
- skill/concept name
- correctness
- attempt count
- hint count
- total available hints
- response time
- opportunity count

These fields are useful for creating memory records about student behavior, past mistakes, support needs, and concept-level learning history.

---

## Dataset Columns Used

Original dataset columns used:

```text
order_id
assignment_id
user_id
problem_id
correct
attempt_count
skill_id
skill_name
hint_count
hint_total
ms_first_response
opportunity
```

After preprocessing, the selected columns are renamed as:

```text
interaction_order
student_id
session_id
problem_id
concept_name
correct
attempt_count
hint_count
hint_total
response_time_ms
opportunity
```

---

## Project Structure

```text
student-memory-personalization/
│
├── data/
│   ├── raw/
│   │   └── skill_builder_data.csv
│   ├── processed/
│   │   ├── processed_interactions.csv
│   │   ├── short_term_memory.csv
│   │   ├── long_term_memory.csv
│   │   └── concept_based_memory.csv
│   └── memory_component.db
│
├── notebooks/
│   ├── 01_dataset_exploration.ipynb
│   ├── 02_memory_modeling.ipynb
│   ├── 03_generate_memory_tables.ipynb
│   ├── 04_memory_evaluation.ipynb
│   └── 05_dynamic_memory_api_testing.ipynb
│
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── schemas.py
│   ├── memory_service.py
│   ├── database.py
│   ├── db_init.py
│   └── dynamic_memory_service.py
│
├── outputs/
│   ├── graphs/
│   ├── tables/
│   └── api_results/
│
├── docs/
│   └── api_contract.md
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Implementation Progress

### Implemented in Notebook 01

`notebooks/01_dataset_exploration.ipynb`

This notebook performs:

- dataset loading
- column inspection
- missing value checking
- student count analysis
- concept count analysis
- correct/wrong answer distribution
- top concept analysis
- processed dataset creation

---

### Implemented in Notebook 02

`notebooks/02_memory_modeling.ipynb`

This notebook creates sample memory outputs for one student:

- short-term memory
- long-term memory
- concept-based memory
- structured memory context JSON for other agents

---

### Implemented in Notebook 03

`notebooks/03_generate_memory_tables.ipynb`

This notebook generates memory tables for all students using the processed ASSISTments dataset.

Generated tables:

- `short_term_memory.csv`
- `long_term_memory.csv`
- `concept_based_memory.csv`

---

### Implemented in Notebook 04

`notebooks/04_memory_evaluation.ipynb`

This notebook evaluates the generated memory tables by checking:

- student coverage across all memory layers
- short-term session status distribution
- long-term support style distribution
- concept-level interaction summaries
- clean memory context generation
- comparison of memory context between different students

This notebook also clarifies the component boundary by keeping analytical outputs such as mastery prediction, knowledge graph generation, regression detection, and learning path generation outside the Memory Component.

---

### Implemented in Notebook 05

`notebooks/05_dynamic_memory_api_testing.ipynb`

This notebook validates the SQLite-based dynamic memory update API.

It tests:

- first student interaction creation
- short-term memory update
- long-term memory update
- concept-based memory update
- repeated interaction update
- multiple concept handling
- memory context retrieval after dynamic updates

The notebook confirms that `POST /memory/update` successfully stores new student interactions and updates all three memory layers.

---

## Implemented Backend API

The FastAPI backend provides memory retrieval and memory update services.

Implemented endpoints:

```text
GET /
GET /memory/student/{student_id}
GET /memory/context/{student_id}
GET /memory/fapr-context/{student_id}
GET /memory/meta-session/{student_id}/{session_id}
GET /memory/student/{student_id}/concept/{concept_name}
GET /memory/student/{student_id}/interactions
POST /memory/update
POST /memory/question-context
POST /memory/store-repair-outcome
```

---

## CSV-Based Memory Retrieval

The first backend prototype loads generated CSV memory tables and returns:

- student long-term profile
- concept-level interaction history
- full memory context
- recent interaction history

CSV files used:

```text
data/processed/short_term_memory.csv
data/processed/long_term_memory.csv
data/processed/concept_based_memory.csv
data/processed/processed_interactions.csv
```

---

## Dynamic Memory Update Prototype

The backend now includes an SQLite-based dynamic memory update prototype.

Implemented dynamic update flow:

```text
POST /memory/update
        ↓
Stores new interaction in SQLite
        ↓
Updates short-term memory
        ↓
Updates long-term memory
        ↓
Updates concept-based memory
        ↓
Returns updated memory context
```

This allows the Memory Component to support live tutoring interactions instead of only retrieving pre-generated CSV memory records.

---

## API Contract

The integration API contract is documented in:

```text
docs/api_contract.md
```

This document defines how Tutor Agent, Planner Agent, Evaluator Agent, Meta-Agent, and FAPR-LB can read from and write to the Memory Component.

---

## Example Memory Context Output

```json
{
  "found": true,
  "student_id": 14,
  "target_concept": "Percent Of",
  "short_term_memory": {
    "session_id": 263599,
    "current_concept": "Percent Of",
    "recent_interaction_count": 3,
    "recent_accuracy": 0.67,
    "average_attempts": 1.33,
    "recent_hint_usage": 1,
    "session_status": "moderate_progress"
  },
  "long_term_memory": {
    "total_interactions": 120,
    "total_sessions": 15,
    "total_concepts": 8,
    "overall_accuracy": 0.62,
    "average_attempts": 1.8,
    "average_hint_count": 1.2,
    "total_hint_count": 144,
    "average_response_time_ms": 42000.0,
    "preferred_support_style": "step_by_step_support"
  },
  "concept_based_memory": {
    "total_interactions": 10,
    "correct_count": 4,
    "wrong_count": 6,
    "accuracy": 0.4,
    "total_hints": 8,
    "avg_hints": 0.8,
    "avg_attempts": 2.1,
    "avg_response_time_ms": 45000.0,
    "last_interaction_order": 34891
  },
  "integration_note": {
    "for_meta_agent": "Use this stored interaction history to derive mastery, knowledge graph updates, regression flags, and learning paths.",
    "for_fapr_lb": "Use this memory context as input features for struggle prediction and repair strategy selection.",
    "for_tutor_agent": "Use this context to personalize explanations without treating the student as new."
  }
}
```

---

## How to Run the Project

### 1. Create a virtual environment

```bash
python -m venv .venv
```

### 2. Activate the virtual environment

Windows PowerShell:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Jupyter Notebook

```bash
jupyter notebook
```

Run the notebooks in order:

```text
01_dataset_exploration.ipynb
02_memory_modeling.ipynb
03_generate_memory_tables.ipynb
04_memory_evaluation.ipynb
05_dynamic_memory_api_testing.ipynb
```

---

## How to Run the FastAPI Backend

Go to the backend folder:

```bash
cd backend
```

Run the API:

```bash
uvicorn app:app --reload
```

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

---

## Example API Calls

### Health Check

```text
GET http://127.0.0.1:8000/
```

### Get Student Profile

```text
GET http://127.0.0.1:8000/memory/student/14
```

### Get Full Memory Context

```text
GET http://127.0.0.1:8000/memory/context/14
```

### Get Concept-Based Memory

```text
GET http://127.0.0.1:8000/memory/student/14/concept/Percent%20Of
```

### Get Student Interactions

```text
GET http://127.0.0.1:8000/memory/student/14/interactions?limit=20
```

### Update Memory Dynamically

```text
POST http://127.0.0.1:8000/memory/update
```

Example request body:

```json
{
  "student_id": 999001,
  "session_id": 5001,
  "problem_id": 101,
  "concept_name": "Percent Of",
  "correct": 0,
  "attempt_count": 2,
  "hint_count": 1,
  "hint_total": 3,
  "response_time_ms": 45000
}
```

### Get Semantic Topic-Aware Question Context

```text
POST http://127.0.0.1:8000/memory/question-context
```

Example request body:

```json
{
  "student_id": 999001,
  "session_id": 7001,
  "question": "Can you explain how to find 25 percent of 80?"
}
```

This endpoint maps the student question to a starter canonical skill record with:

- numeric `skill_id` for FAPR-LB
- `skill_name` and `canonical_skill_name` for Meta-Agent compatibility
- topic-specific memory history for Tutor, Planner, Evaluator, Meta-Agent, and FAPR-LB

The topic detector uses local keyword matching first and TF-IDF cosine similarity as a fallback. It does not call external APIs and does not perform mastery prediction.

After starting the backend, run:

```bash
python scripts/test_question_context.py
```

to verify percent, fraction, equation, and low-confidence unclear-question cases.

### Get FAPR-LB Repair-Turn Context

```text
GET http://127.0.0.1:8000/memory/fapr-context/999951?session_id=8101&current_skill_id=312&current_skill_name=Percent%20Of&limit=10
```

Example response:

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

Memory provides context only. FAPR-LB uses this payload for struggle prediction and repair action selection. `previous_repair` remains `null` until a repair outcome is stored.

### Store FAPR-LB Repair Outcome

```text
POST http://127.0.0.1:8000/memory/store-repair-outcome
```

Example request body:

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

Example response:

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

Memory stores the FAPR-LB repair outcome on the latest matching interaction row. The next `GET /memory/fapr-context/{student_id}` call can then return it as `previous_repair`.

After starting the backend, run:

```bash
python scripts/test_fapr_context_contract.py
python scripts/test_store_repair_outcome.py
```

to verify the FAPR-LB payload fields, oldest-to-newest recent interaction order, and repair outcome persistence.

---

## Requirements

Main libraries used:

```text
pandas
numpy
matplotlib
seaborn
scikit-learn
jupyter
notebook
fastapi
uvicorn
pydantic
requests
python-multipart
```

---

## Research Contribution

The main contribution of this component is a structured three-layer memory system that converts raw student interaction records into reusable personalization context.

The component supports personalized academic assistance by remembering:

- what the student is doing now
- how the student behaved in previous sessions
- what support style the student may need
- which concepts have interaction history
- how the student performed in each concept
- how other agents can retrieve and use this memory context

Final one-line summary:

**The Memory Component is a three-layer student personalization memory system that stores current session context, long-term learner behavior, and concept-level interaction history, then provides structured memory context to other agents for personalized academic support.**

---

## Current Status

Implemented:

- GitHub project structure
- ASSISTments dataset preprocessing
- short-term memory table generation
- long-term memory table generation
- concept-based memory table generation
- memory evaluation notebook
- CSV-based FastAPI retrieval service
- SQLite-based dynamic memory update service
- dynamic API testing notebook
- API integration contract document
- semantic topic-aware memory retrieval with numeric `skill_id` support
- starter canonical skill mapping in `models/canonical_skills.json`

Pending:

- final integration testing with other components
- PP1 evidence pack
- optional frontend/dashboard display
- replacement of starter canonical skills with the Meta-Agent official 95-skill list
- optional BERT/DistilBERT concept extractor after the TF-IDF baseline
- final research evaluation documentation
- final report and presentation preparation


### Implemented in Notebook 06

`notebooks/06_integration_context_testing.ipynb`

This notebook validates integration-ready memory outputs for other components.

It tests:

- FAPR-LB context endpoint
- Meta-Agent session export endpoint
- recent interaction schema compatibility
- chronological attempt order
- binary correctness format
- integration output completeness

Generated outputs:

```text
outputs/tables/integration_context_test_results.csv
outputs/tables/integration_context_test_summary.csv
outputs/api_results/fapr_context_sample.json
outputs/api_results/meta_session_sample.json
