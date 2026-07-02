from typing import Tuple, Dict, Any, Optional
from ..types import AgentState


class DecisionEngine:
    def __init__(self, cost_limit: float = 1.0):
        self.cost_limit = cost_limit

    def decide_next_action(self, state: AgentState) -> Optional[Tuple[str, Dict[str, Any]]]:
        # take first incomplete task from active_tasks
        if not state.active_tasks:
            return None
        task = state.active_tasks[0]
        # simple heuristic: map action_type to action
        if task.action_type == "infer":
            return ("call_llm", {"task_id": task.id, "prompt": task.name})
        return ("noop", {})
