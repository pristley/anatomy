from copy import deepcopy
from typing import List
from ..types import AgentState, TaskDef


class StateManager:
    def __init__(self):
        self._history: List[AgentState] = []
        self._current: AgentState = AgentState(agent_id=None, goal=None)

    def initialize_state(self, goal: str, tasks: List[TaskDef]) -> AgentState:
        state = AgentState(agent_id=None, goal=goal, active_tasks=tasks, completed_tasks=[])
        self._current = state
        self._history.append(deepcopy(state))
        return deepcopy(state)

    def mark_task_complete(self, state: AgentState, task_id: str, result) -> AgentState:
        new_state = deepcopy(state)
        # find task in active_tasks
        remaining = []
        completed = new_state.completed_tasks[:]
        for t in new_state.active_tasks:
            if t.id == task_id:
                t.status = "completed"
                completed.append(t)
            else:
                remaining.append(t)
        new_state.active_tasks = remaining
        new_state.completed_tasks = completed
        self._current = new_state
        self._history.append(deepcopy(new_state))
        return deepcopy(new_state)

    def get_current_state(self) -> AgentState:
        return deepcopy(self._current)
