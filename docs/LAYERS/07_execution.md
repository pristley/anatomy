# Execution - Layer 07

## Overview
The Execution layer invokes tools and external actions. It wraps tool calls
with scheduling and basic error handling.

## Responsibilities
- Execute tasks by invoking tool adapters or the reasoning core.
- Collect execution results, tokens, and cost metrics.
- Surface errors back to the resilience and decision layers for handling.

## Implementation Status
Implemented: integrates with builtin tools and external adapters under
`backend/agent_framework/tools/`.

## Code Reference
- Implementation: [backend/agent_framework/core/layers/07_execution.py](backend/agent_framework/core/layers/07_execution.py)
