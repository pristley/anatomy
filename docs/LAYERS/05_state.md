# Layer 5: State

## Overview
The State layer tracks execution progress for goals and tasks and exposes a
`StateManager` API used by Decision and Execution layers to persist status,
retries, and checkpoints.

## Responsibilities
- Initialize and update task/goal state snapshots.
- Track retries, failure counts, and backoff windows.
- Expose checkpointing and recovery interfaces.

## Data Flow

Planner produces `TaskDef` → StateManager initializes `AgentState` → Decision/Execution update statuses

## Key Classes

### `StateManager`
Manages `AgentState` lifecycle and snapshots.

````python
class StateManager:
	def initialize(self, goal: Goal) -> AgentState: ...
	def mark_complete(self, task_id: str): ...
````

## Example

````python
from agent_framework.core.layers._05_state import StateManager

sm = StateManager()
state = sm.initialize(goal)
sm.mark_complete(task_id)
````

## Testing
See `backend/tests/test_layers/test_layer_5.py`.

## Common Issues & Fixes
- In-memory state lost after restart: use pluggable durable store.
- Conflicting updates: use optimistic locking or sequence numbers on state updates.

## See Also
- Layer 4: Planning
- Layer 6: Decision
