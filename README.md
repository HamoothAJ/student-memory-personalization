# Student Memory Personalization Component

## Research Component

This repository contains the implementation of **Component 3: Memory (Student Personalization)** for a personalized AI academic support system.

The Memory Component stores and updates student-specific learning information so that other agents can provide personalized academic support.

## Component Title

**Three-Layer Student Memory System for Personalized Academic Support**

## Component Overview

The Memory Component is the **storage and personalization layer** of the tutoring system. It records student learning interactions and maintains structured student memory that can be reused by the Tutor Agent, Planner Agent, Evaluator Agent, and Meta-Agent.

The component remembers:

- current session context
- weak areas
- strong areas
- past mistakes
- repeated learning behavior
- hint usage patterns
- response behavior
- preferred learning support style
- concept-level interaction history

The Memory Component does **not** perform high-level learning analysis such as mastery prediction, Bayesian Knowledge Tracing, knowledge graph generation, regression detection, or learning path generation. Those responsibilities belong to the Meta-Agent.

## Memory Types

The Memory Component is divided into three memory layers.

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

### 2. Long-Term Memory

Long-Term Memory stores persistent student behavior across multiple sessions.

It includes:

- overall student accuracy
# Student Memory Personalization Component

## Research Component

This repository contains the implementation of **Component 3: Memory (Student Personalization)** for a personalized AI academic support system.

## Component Title

**Three-Layer Student Memory System for Personalized Academic Support**

## Component Overview

The Memory Component is the **storage and personalization layer** of the tutoring system. It records student learning interactions and maintains structured student memory that can be reused by the Tutor Agent, Planner Agent, Evaluator Agent, and Meta-Agent.

The component remembers:

- current session context
- weak areas
- strong areas
- past mistakes
- repeated learning behavior
- hint usage patterns
- response behavior
- preferred learning support style
- concept-level interaction history

The Memory Component does **not** perform high-level learning analysis such as mastery prediction, Bayesian Knowledge Tracing, knowledge graph generation, regression detection, or learning path generation. Those responsibilities belong to the Meta-Agent.

## Memory Types

The Memory Component is divided into three memory layers.

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

### 2. Long-Term Memory

Long-Term Memory stores persistent student behavior across multiple sessions.

It includes:

- overall student accuracy
- average attempt count
- average hint usage
- average response time
- repeated weak areas
- strong areas
- learning behavior patterns
- preferred support style

Purpose:

Long-Term Memory helps the system understand the student as a learner and personalize future sessions based on previous learning history.

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
- observed behavior
- memory note for personalization

Purpose:

Concept-Based Memory helps identify concept-level learning patterns such as repeated difficulty, hint dependence, or consistent strength. This stored history can later be analyzed by the Meta-Agent for mastery tracking and learning path generation.

## Relationship with Other Components

The Memory Component acts as the **student data and context layer**.

```text
Student Interaction
        ↓
Memory Component stores and updates student memory
        ↓
Tutor / Planner / Evaluator / Meta-Agent retrieve memory context
        ↓
Agents provide personalized academic support

                Component Separation


| Component        | Responsibility                                                                         |
| ---------------- | -------------------------------------------------------------------------------------- |
| Memory Component | Stores and updates student memory                                                      |
| Tutor Agent      | Generates personalized explanations                                                    |
| Planner Agent    | Breaks questions into suitable learning steps                                          |
| Evaluator Agent  | Checks student answers and gives feedback                                              |
| Meta-Agent       | Analyzes memory data, tracks mastery, detects regression, and generates learning paths |
```

What the Memory Component Does

The Memory Component:

- stores current session context
- stores student interaction logs
- stores long-term student behavior
- stores weak and strong areas
- stores past mistakes and repeated patterns
- stores concept-level interaction history
- generates structured memory context for other agents

The selected dataset is the ASSISTments Skill Builder Dataset.

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

These fields are useful for creating memory records about student behavior, weak areas, past mistakes, and concept-level learning history.

## Dataset Columns Used

Original dataset columns used:
- order_id
- assignment_id
- user_id
- problem_id
- correct
- attempt_count
- skill_id
- skill_name
- hint_count
- hint_total
- ms_first_response
- opportunity

After preprocessing, the selected columns are renamed as:
- interaction_order
- student_id
- session_id
- problem_id
- concept_name
- correct
- attempt_count
- hint_count
- hint_total
- response_time_ms
- opportunity

## Project Structure

```
student-memory-personalization/
│
├── data/
│   ├── raw/
│   │   └── skill_builder_data.csv
│   └── processed/
│       └── processed_interactions.csv
│
├── notebooks/
│   ├── 01_dataset_exploration.ipynb
│   └── 02_memory_modeling.ipynb
│
├── backend/
│   ├── app.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── memory_service.py
│
├── outputs/
│   ├── graphs/
│   ├── tables/
│   └── api_results/
│
├── docs/
│
├── requirements.txt
├── README.md
└── .gitignore
``` 

### Implemented in Notebook 04

`notebooks/04_memory_evaluation.ipynb`

This notebook evaluates the generated memory tables by checking:

- student coverage across all memory layers
- short-term session status distribution
- long-term support style distribution
- concept-level interaction summaries
- clean memory context generation
- comparison of memory context between different students

This notebook also clarifies the component boundary by keeping analytical outputs such as mastery prediction, knowledge graph generation, and learning path generation outside the Memory Component.

## Implemented Backend API

The first FastAPI prototype has been implemented using generated CSV memory tables.

Implemented endpoints:

```text
GET /
GET /memory/student/{student_id}
GET /memory/context/{student_id}
GET /memory/student/{student_id}/concept/{concept_name}
GET /memory/student/{student_id}/interactions
POST /memory/update

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