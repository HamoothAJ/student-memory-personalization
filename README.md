# Student Memory Personalization Component

## Research Component

This repository contains the implementation of the Memory Component for a personalized AI academic support system.

## Component Title

Three-Layer Student Memory System for Personalized Academic Support

## Memory Types

1. Short-Term Memory  
   Stores current session-level learning context.

2. Long-Term Memory  
   Stores student-level learning behavior across sessions.

3. Concept-Based Memory  
   Tracks student mastery, weaknesses, and progress for each concept.

## Dataset

The project uses the ASSISTments Skill Builder dataset, which contains student problem-solving interaction records including student ID, problem ID, skill/concept name, correctness, attempt count, hint usage, and response time.

## Current Implementation Stage

- Dataset exploration
- Dataset preprocessing
- Memory-ready interaction dataset creation

## Planned Modules

- Short-term memory generator
- Long-term memory profile generator
- Concept mastery tracker
- BKT-style mastery updater
- Memory context generator
- FastAPI backend for memory retrieval