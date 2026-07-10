# Resilience - Layer 08

## Overview
Resilience implements circuit-breaking and retry strategies around tool and
external service calls. It prevents cascading failures by tracking recent
error rates and short-circuiting failing components.

## Responsibilities
- Wrap execution calls with circuit-breaker logic.
- Track failure counts and apply exponential backoff for retries.
- Provide hooks to the State and Decision layers for degraded-mode behavior.

## Implementation Status
Implemented: `CircuitBreaker` and resilience wrappers are available in the
resilience layer and used by the execution pipeline.

## Code Reference
- Implementation: [backend/agent_framework/core/layers/08_resilience.py](backend/agent_framework/core/layers/08_resilience.py)
