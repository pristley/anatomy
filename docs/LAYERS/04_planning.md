# Layer 4: Planning

## Overview
Planning decomposes a normalized intent into actionable `TaskDef`s, resolves
dependencies, and produces an ordered plan used by the Decision layer.

## Responsibilities
- Decompose goals into tasks.
- Resolve task dependencies and produce a topologically-sorted plan.
- Annotate tasks with resource hints and estimated costs.

## Data Flow

`Intent` → `PlanningDecomposition.decompose()` → List[`TaskDef`] → `DecisionEngine`

## Key Classes

### `PlanningDecomposition`
Breaks reasoning output or intent into tasks and returns a DAG of tasks.

````python
class PlanningDecomposition:
	def decompose(self, reasoning_output: str) -> List[TaskDef]:
		"""Return list of task definitions from reasoning output."""
````

### `topological_sort`
Utility to order tasks based on dependency graph.

## Example

````python
from agent_framework.core.layers._04_planning import PlanningDecomposition

planner = PlanningDecomposition()
tasks = planner.decompose(reasoning_output)
ordered = topological_sort(tasks)
````

## Testing
See `backend/tests/test_layers/test_layer_4.py` for decomposition and sorting tests.

## Common Issues & Fixes
- Cyclic dependencies: fallback to heuristic ordering or prompt user to clarify.
- Over-decomposition: limit number of tasks or merge trivial tasks.

## Performance
- Consider caching decomposition results for identical reasoning outputs.

## See Also
- Layer 3: Reasoning
- Layer 6: Decision
