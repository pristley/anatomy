# Intent - Layer 03

## Overview
The Intent layer extracts the user's primary objective and maps it to a
concise internal intent representation. In this codebase intent parsing is a
collaboration between the Understanding and Reasoning layers.

## Responsibilities
- Identify the primary actionable intent from user input.
- Normalize intent labels and map to known capabilities or tools.
- Pass intent metadata to planning and reasoning components.

## Implementation Status
Partially implemented across the Understanding and Reasoning layers; intent
extraction logic is present in `02_understanding.py` and refined via the
reasoning client in `03_reasoning.py`.

## Code Reference
- [backend/agent_framework/core/layers/02_understanding.py](backend/agent_framework/core/layers/02_understanding.py)
- [backend/agent_framework/core/layers/03_reasoning.py](backend/agent_framework/core/layers/03_reasoning.py)
