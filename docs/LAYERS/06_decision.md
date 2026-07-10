# Decision - Layer 06

## Overview
Decision layer selects which tasks to run next based on the current state and
policy. It mediates between planning and execution and may implement simple
heuristics or policy lookups.

## Responsibilities
- Choose next tasks to schedule from the plan.
- Apply policies (concurrency limits, priority overrides).
- Coordinate with `StateManager` to avoid duplicate work.

## Implementation Status
Implemented: core decision heuristics exist; policy engine is pluggable.

## Code Reference
- Implementation: [backend/agent_framework/core/layers/06_decision.py](backend/agent_framework/core/layers/06_decision.py)
