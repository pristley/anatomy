"""Layer 6: Decision engine."""
from __future__ import annotations

from typing import Tuple, Optional, Any

from ..types import AgentState, TaskDef
from agent_framework.tools.base import ToolRegistry
from agent_framework.tools.validator import SchemaValidator


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
        registry = ToolRegistry.get_default()
        for task in state.active_tasks:
            if task.status == "completed":
                continue
            if not self._dependencies_satisfied(task, state):
                continue

            # if task specifies a tool name in parameters, prefer that
            params = task.parameters or {}
            tool_name = params.get("tool") or task.action_type
            if not tool_name:
                continue

            tool = registry.get(tool_name)
            if tool is None:
                continue

            # validate params against tool schema if available
            schema = tool.params_schema
            valid, errors, sanitized = SchemaValidator.validate_params(params, schema)
            if not valid:
                # skip invalid tool invocation
                continue

            confidence = 0.8
            return tool_name, sanitized, confidence

        return None, None, 0.0


__all__ = ["DecisionEngine"]
