# Layer 7: Execution

## Overview
Execution performs the actual work of running tasks: calling tool adapters,
running external APIs, and collecting raw results for evaluation.

## Responsibilities
- Invoke tool adapters and external services.
- Enforce timeouts and collect execution metrics (latency, cost, tokens).
- Surface errors to Resilience layer for retries or circuit-breaking.

## Data Flow

`TaskDef` -> `ExecutionEngine.execute()` -> `ExecutionResult` -> Resilience/Evaluation

## Key Classes

### `ExecutionEngine`
Handles task invocation and result normalization.

````python
class ExecutionEngine:
	async def execute(self, task: TaskDef) -> ExecutionResult:
		"""Run a task and return its result."""
````

## Example

````python
from agent_framework.core.layers._07_execution import ExecutionEngine

ee = ExecutionEngine()
res = await ee.execute(task)
````

## Testing
Unit and integration tests should mock external tool adapters; see `backend/tests/` for examples.

## Common Issues & Fixes
- Hanging external calls: set per-tool timeouts and use Resilience wrappers.
- Non-deterministic results: log full response and add schema validation.

## See Also
- Layer 8: Resilience
- Tools: `backend/agent_framework/tools/`
