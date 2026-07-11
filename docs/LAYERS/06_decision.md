# Layer 6: Decision

## Overview
The Decision layer selects the next action(s) to run from the plan given the
current `AgentState`, policy, and resource constraints. It bridges planning
with execution.

## Responsibilities
- Choose next task(s) to schedule.
- Enforce policies such as concurrency limits and priorities.
- Validate task inputs against schemas and skip invalid tasks.

## Data Flow

`TaskPlan` + `AgentState` -> `DecisionEngine` -> next `TaskDef`(s)

## Key Classes

### `DecisionEngine`
Applies policies and heuristics to select runnable tasks.

````python
class DecisionEngine:
	def select_next(self, state: AgentState, plan: List[TaskDef]) -> List[TaskDef]:
		"""Return tasks to execute next."""
````

## Example

````python
from agent_framework.core.layers._06_decision import DecisionEngine

de = DecisionEngine()
next_tasks = de.select_next(state, plan)
````

## Testing
See `backend/tests/test_layers/test_layer_6.py` for decision path tests.

## Common Issues & Fixes
- Invalid task parameters: schema-validate before scheduling and log/skips.
- Starvation of low-priority tasks: use fairness policies or aging.

## See Also
- Layer 4: Planning
- Layer 7: Execution
