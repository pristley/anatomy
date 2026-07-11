# Layer 8: Resilience

## Overview
Resilience provides fault-tolerance primitives (circuit-breakers, retries,
backoff) that protect the system from cascading external failures.

## Responsibilities
- Wrap tool execution with retry and circuit-breaker policies.
- Track recent error rates and short-circuit failing components.
- Expose hooks for degraded-mode behavior to Decision and State layers.

## Data Flow

Execution call -> Resilience wrappers -> (retry/circuit-break) -> Execution

## Key Classes

### `CircuitBreaker`
Tracks failure counts and decides when to open/close the breaker.

````python
class CircuitBreaker:
	def __init__(self, threshold: int, window_seconds: int): ...
````

## Example

````python
from agent_framework.core.layers._08_resilience import CircuitBreaker

cb = CircuitBreaker(threshold=5, window_seconds=60)
````

## Testing
Simulate failing tool adapters and verify breakers open and retries occur with backoff.

## Common Issues & Fixes
- Too aggressive breaking: tune thresholds and window lengths.
- Retry storms: use jitter and exponential backoff to reduce synchronized retries.

## See Also
- Layer 7: Execution
