# Layer 9: Evaluation

## Overview
The Evaluation layer scores task outcomes and aggregates metrics to produce
goal-level evaluations. It informs learning signals, success rates, and
feedback to users or upstream components.

## Responsibilities
- Score individual task outcomes and compute aggregate metrics.
- Produce structured `TaskOutcome` and `GoalEvaluation` objects.
- Provide hooks to store evaluation results for telemetry and training.

## Data Flow

ExecutionResult -> EvaluationLayer.score() -> TaskOutcome -> GoalEvaluation

## Key Classes

### `EvaluationLayer`
Scores and aggregates results.

````python
class EvaluationLayer:
	def score(self, exec_result: ExecutionResult) -> TaskOutcome: ...
````

## Example

````python
from agent_framework.core.layers._09_evaluation import EvaluationLayer

el = EvaluationLayer()
outcome = el.score(exec_result)
````

## Testing
Test scoring logic with synthetic execution results and verify aggregated metrics.

## Common Issues & Fixes
- Misleading scores: normalize metrics and ensure consistent baselines.
- Missing telemetry: ensure evaluation results are persisted or emitted.

## See Also
- Layer 7: Execution
- Observability: Layer 10
