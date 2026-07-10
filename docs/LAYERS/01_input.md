# Input - Layer 01

## Overview
Layer 01 is responsible for ingesting and normalizing external inputs (HTTP
requests, CLI arguments, or example scripts) into the internal `Query`/`Goal`
structures used by the pipeline.

## Responsibilities
- Validate and sanitize incoming payloads.
- Map external fields into the agent's internal goal/task model.
- Attach request metadata (user id, request id) to the processing context.

## Data Flow
- Receives raw input -> performs schema validation and normalization -> emits
	a canonical `Goal` object for downstream layers.

## Implementation Status
Implemented: see code reference for the current behavior and examples.

## Code Reference
- Implementation: [backend/agent_framework/core/layers/01_input.py](backend/agent_framework/core/layers/01_input.py)
