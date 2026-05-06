# Memory Component API Contract

## Component

**Component 3: Memory (Student Personalization)**

## Purpose

The Memory Component stores, updates, and retrieves student-specific learning memory for the AI academic support system.

It provides structured memory context to other components, including:

- Tutor Agent
- Planner Agent
- Evaluator Agent
- Meta-Agent
- FAPR-LB Self-Improvement Component

The Memory Component does not generate tutoring responses, calculate mastery probabilities, run BKT, generate learning paths, detect regression, predict struggle, or select repair strategies.

Its role is to act as the student data and context provider.

---

## Component Boundary

### Memory Component Responsibilities

The Memory Component stores:

- student interaction logs
- current session context
- long-term learner behavior
- concept-level interaction history
- hint usage
- attempt behavior
- response time behavior
- weak/strong area records if written by other components
- persisted personalization records

### Not Memory Component Responsibilities

The Memory Component does not perform:

- lesson generation
- answer evaluation
- BKT mastery prediction
- knowledge graph generation
- regression detection
- learning path generation
- turn-level struggle prediction
- repair strategy selection
- tutor response scoring
- bandit policy update

---

## Relationship with Other Components

| Component | How It Uses Memory |
|---|---|
| Tutor Agent | Reads memory context to personalize explanations |
| Planner Agent | Reads memory context to break tasks into suitable steps |
| Evaluator Agent | Reads memory context to understand previous mistakes and support needs |
| Meta-Agent | Reads memory records to calculate mastery, update knowledge graph, detect regression, and generate learning paths |
| FAPR-LB | Reads memory context as features for struggle prediction and repair strategy selection |

---

## Main API Endpoints

### 1. Health Check

```http
GET /

