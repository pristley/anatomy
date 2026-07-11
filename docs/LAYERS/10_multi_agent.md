# Multi-Agent / Parallelism - Layer 10

## Overview
Multi-agent capabilities enable spawning subagents, parallel task execution,
and aggregation of results. The runtime provides APIs to create and manage
subagents and coordinate work across them.

## Responsibilities
- Spawn and manage subagents and coordinators.
- Execute tasks in parallel and merge results.
- Provide APIs for lifecycle management and result aggregation.

## Data Flow

Parent Agent -> spawn subagent(s) -> subagent executes tasks -> aggregate results

## Key Behaviors

- `Agent.spawn_subagent()` — create subagent instance
- `Agent.run_with_subagents()` — orchestrate cooperative execution

## Example

````python
from agent_framework.core.agent import Agent

parent = Agent()
result = await parent.run_with_subagents(query)
````

## Testing
See `backend/tests/test_agent_subagents.py` for multi-agent edge-case tests.

## Common Issues & Fixes
- Deadlocks in awaits: ensure subagents use proper timeouts and handle cancellations.
- Resource contention: use ResourceManager or limit concurrency per user.

## See Also
- Layer 7: Execution
