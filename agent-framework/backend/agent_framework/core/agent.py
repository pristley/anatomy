import asyncio
import importlib
import time
from typing import Dict, Any

from .types import AgentInput, AgentState
from .interfaces.claude_client import ClaudeClient

# dynamic import helper for numeric-prefixed modules
def _import_layer(name: str):
    module_path = f"{__package__}.layers.{name}"
    return importlib.import_module(module_path)

input_layer = _import_layer("01_input")
understanding_layer = _import_layer("02_understanding")
reasoning_layer = _import_layer("03_reasoning")
planning_layer = _import_layer("04_planning")
state_layer = _import_layer("05_state")
decision_layer = _import_layer("06_decision")


class Agent:
    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022", max_iterations: int = 10):
        self.model_name = model_name
        self.max_iterations = max_iterations
        self.llm = ClaudeClient()
        self.input = input_layer.InputLayer()
        self.understand = understanding_layer.UnderstandingLayer()
        self.reasoner = reasoning_layer.ReasoningCore(self.llm)
        self.planner = planning_layer.PlanningDecomposition()
        self.state_mgr = state_layer.StateManager()
        self.decider = decision_layer.DecisionEngine()

    def run(self, query: str, user_id: str = None) -> Dict[str, Any]:
        timeline = []
        try:
            t0 = time.time()
            inp = self.input.process(query, user_id)
            timeline.append({"layer": "input", "time": time.time() - t0})

            u = self.understand.understand(inp)
            timeline.append({"layer": "understanding"})

            # call reasoner (async)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            reasoning = loop.run_until_complete(self.reasoner.reason(u, memory=None))
            loop.close()
            timeline.append({"layer": "reasoning", "tokens": reasoning.get("tokens_used")})

            tasks = self.planner.decompose(reasoning.get("reasoning_output", ""))
            state = self.state_mgr.initialize_state(goal=inp.query, tasks=tasks)
            timeline.append({"layer": "planning", "tasks": len(tasks)})

            # simple execution loop
            iterations = 0
            outputs = []
            while iterations < self.max_iterations and state.active_tasks:
                action = self.decider.decide_next_action(state)
                if action is None:
                    break
                action_type, params = action
                if action_type == "call_llm":
                    # call reasoning again for the task prompt
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    resp = loop.run_until_complete(self.reasoner.reason({"task": params}, memory=None))
                    loop.close()
                    outputs.append(resp)
                    # mark task complete
                    state = self.state_mgr.mark_task_complete(state, params.get("task_id"), resp)
                iterations += 1

            t1 = time.time()
            return {"success": True, "output": outputs, "metrics": {"duration_ms": int((t1 - t0) * 1000)}, "timeline": timeline}
        except Exception as e:
            return {"success": False, "error": str(e)}
