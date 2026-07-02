"""Layer 6: Decision engine."""
from __future__ import annotations

from typing import Tuple, Optional

from ..types import AgentState, TaskDef


class DecisionEngine:
    def __init__(self, cost_limit_per_user: float | None = None) -> None:
        self.cost_limit_per_user = cost_limit_per_user

    def _dependencies_satisfied(self, task: TaskDef, state: AgentState) -> bool:
        completed_ids = {t.id for t in state.completed_tasks}
        return all(d in completed_ids for d in task.dependencies)

    def decide_next_action(self, state: AgentState) -> Tuple[Optional[str], Optional[dict], float]:
        """Return next (action_type/tool_name, parameters, confidence).

        Chooses the first incomplete task whose dependencies are satisfied.
        """
        for task in state.active_tasks:
            if task.status == "completed":
                continue
            if not self._dependencies_satisfied(task, state):
                continue

            # budget/compliance checks would go here; assume OK
            confidence = 0.8
            return task.action_type, task.parameters or {}, confidence

        return None, None, 0.0


__all__ = ["DecisionEngine"]
