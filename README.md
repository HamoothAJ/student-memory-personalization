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