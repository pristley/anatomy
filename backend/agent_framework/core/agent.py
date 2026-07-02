"""Agent orchestrator that runs the layer pipeline end-to-end."""
from __future__ import annotations

import os
import time
from typing import Any, Dict

from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path


def _load_from_layers(filename: str, attr: str):
    base = Path(__file__).resolve().parent
    path = base / "layers" / filename
    spec = spec_from_file_location(f"agent_framework.core.layers.{filename}", str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {filename}")
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, attr)


_InputLayer = _load_from_layers("01_input.py", "InputLayer")
_UnderstandingLayer = _load_from_layers("02_understanding.py", "UnderstandingLayer")
_ReasoningCore = _load_from_layers("03_reasoning.py", "ReasoningCore")
PlanningDecomposition = _load_from_layers("04_planning.py", "PlanningDecomposition")
_topological_sort = _load_from_layers("04_planning.py", "topological_sort")
_StateManager = _load_from_layers("05_state.py", "StateManager")
_DecisionEngine = _load_from_layers("06_decision.py", "DecisionEngine")
ClaudeClient = _load_from_layers("../interfaces/claude_client.py", "ClaudeClient")


class Agent:
    def __init__(self, model_name: str = "claude", max_iterations: int = 10) -> None:
        self.model_name = model_name
        self.max_iterations = max_iterations
        # pick LLM client
        self.llm_client = ClaudeClient()
        self.reasoner = _ReasoningCore(self.llm_client)
        self.input_layer = _InputLayer()
        self.understanding = _UnderstandingLayer()
        self.planner = PlanningDecomposition()
        self.state_manager = None
        self.decision_engine = _DecisionEngine()

    async def run(self, query: str, user_id: str) -> Dict[str, Any]:
        start_all = time.monotonic()
        metrics: Dict[str, Any] = {"tokens_used": 0, "cost": 0.0}
        try:
            agent_input = self.input_layer.process(query, user_id)
            understood = self.understanding.understand(agent_input)

            reasoning_res = await self.reasoner.reason(understood)
            metrics["tokens_used"] += reasoning_res.get("tokens_used", 0)
            metrics["cost"] += reasoning_res.get("cost", 0.0)

            # planning
            tasks = self.planner.decompose(reasoning_res.get("reasoning_output", ""))
            tasks = _topological_sort(tasks)

            # state
            self.state_manager = _StateManager(agent_id=user_id)
            state = self.state_manager.initialize_state(goal=understood.get("parsed_query", {}).get("intent"), tasks=tasks)

            # execution loop
            iteration = 0
            last_output = None
            while iteration < self.max_iterations and state.active_tasks:
                iteration += 1
                action, params, confidence = self.decision_engine.decide_next_action(state)
                if action is None:
                    break

                # Mock execution: call reasoner again to simulate tool call/LLM reasoning for the task
                task_text = f"Execute {action} with params {params} (confidence={confidence})"
                r = await self.reasoner.reason({"parsed_query": task_text, "kb_results": [], "confidence": confidence})
                metrics["tokens_used"] += r.get("tokens_used", 0)
                metrics["cost"] += r.get("cost", 0.0)

                # assume first active task is the one
                if state.active_tasks:
                    tid = state.active_tasks[0].id
                    state = self.state_manager.mark_task_complete(state, tid, result={"output": r.get("reasoning_output")})
                    last_output = r.get("reasoning_output")

            total_ms = int((time.monotonic() - start_all) * 1000)
            return {"success": True, "output": last_output, "metrics": metrics, "cost": metrics.get("cost", 0.0), "execution_time_ms": total_ms}

        except Exception as exc:  # pragma: no cover - orchestration error handling
            return {"success": False, "error": str(exc)}


__all__ = ["Agent"]
