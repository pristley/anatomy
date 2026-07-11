# Observability - Layer 10

## Overview
Observability adds structured logging, context propagation, and simple
tracing helpers so other layers can emit consistent telemetry and debug
information.

## Responsibilities
- Propagate request and run-level context to logs.
- Provide structured logging and metrics helpers.
- Integrate optional telemetry backends (exporters) when configured.

## Data Flow

Layers emit logs/metrics → Observability helpers enrich and forward to backends

## Key Classes & Helpers

- `context` helpers — attach `request_id`, `user_id`, `trace_id` to logs
- `logger` — masked logging helpers to avoid exposing secrets

## Example

````python
from agent_framework.observability.logger import get_logger

log = get_logger(__name__)
log.info("Starting task", extra={"task_id": tid})
````

## Testing
Verify logs include expected context fields and secrets are masked.

## Common Issues & Fixes
- Sensitive data in logs: use masking utilities before emitting messages.
- Missing context: ensure middlewares populate context for API requests.

## See Also
- Layer 9: Evaluation (metrics)
