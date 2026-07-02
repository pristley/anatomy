"""Layer 5: State management (immutable snapshots)."""
from __future__ import annotations

from copy import deepcopy
from typing import List, Optional

from ..types import AgentState, TaskDef


class StateManager:
    def __init__(self, agent_id: str) -> None:
        self.agent_id = agent_id
        self.state_history: List[AgentState] = []

    def initialize_state(self, goal: str | None, tasks: List[TaskDef]) -> AgentState:
        st = AgentState(agent_id=self.agent_id, goal=goal or "", active_tasks=deepcopy(tasks), completed_tasks=[], status="running", memory_refs=[])
        self.state_history.append(st)
        return st

    def mark_task_complete(self, state: AgentState, task_id: str, result: Optional[dict] = None) -> AgentState:
        # produce a new AgentState (immutable snapshot)
        new_state = deepcopy(state)
        # move task from active to completed
        active = [t for t in new_state.active_tasks if t.id != task_id]
        completed = new_state.completed_tasks[:]
        moved = [t for t in state.active_tasks if t.id == task_id]
        if moved:
            task = moved[0]
            task.status = "completed"
            completed.append(task)

        new_state.active_tasks = active
        new_state.completed_tasks = completed
        if not new_state.active_tasks:
            new_state.status = "succeeded"

        self.state_history.append(new_state)
        return new_state

    def get_state_summary(self) -> str:
        if not self.state_history:
            return "no state"
        s = self.state_history[-1]
        return f"Agent {s.agent_id}: status={s.status}, active={len(s.active_tasks)}, completed={len(s.completed_tasks)}"


__all__ = ["StateManager"]
