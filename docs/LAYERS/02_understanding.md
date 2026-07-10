# Understanding - Layer 02

## Overview
The Understanding layer parses and extracts structured intent from the
canonical `Goal` produced by the input layer. It performs NLP parsing,
entity extraction, and maps user language to internal task templates.

## Responsibilities
- Parse natural language to determine intents and entities.
- Enrich the `Goal` with structured fields used by the planner and reasoner.
- Normalize synonyms and map to known tool or capability names.

## Data Flow
TODO: Add data flow diagram

## Implementation Status
Implemented: basic parsing and normalization; extendable with custom
parsers or model-backed analyzers.

## Code Reference
- File: `backend/agent_framework/core/layers/02_understanding.py`
- Implementation: [backend/agent_framework/core/layers/02_understanding.py](backend/agent_framework/core/layers/02_understanding.py)
