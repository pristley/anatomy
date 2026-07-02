import asyncio
import importlib
import time
from typing import Dict, Any

from .types import AgentInput, AgentState
from .interfaces.claude_client import ClaudeClient
from agent_framework.memory.episodic import EpisodicMemory
from agent_framework.memory.semantic import SemanticMemory
from agent_framework.tools.base import ToolExecutor
from agent_framework.guardrails.orchestrator import GuardrailOrchestrator

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
    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022", max_iterations: int = 10, episodic_memory: EpisodicMemory | None = None, semantic_memory: SemanticMemory | None = None):
        self.model_name = model_name
        self.max_iterations = max_iterations
        self.llm = ClaudeClient()
        self.input = input_layer.InputLayer()
        self.understand = understanding_layer.UnderstandingLayer()
        self.reasoner = reasoning_layer.ReasoningCore(self.llm)
        self.planner = planning_layer.PlanningDecomposition()
        self.state_mgr = state_layer.StateManager()
        self.decider = decision_layer.DecisionEngine()
        self.tool_executor = ToolExecutor()
        self.guardrails = GuardrailOrchestrator()
        # memory
        self.episodic = episodic_memory or EpisodicMemory()
        self.semantic = semantic_memory or SemanticMemory()

    def run(self, query: str, user_id: str = None) -> Dict[str, Any]:
        timeline = []
        try:
            t0 = time.time()
            inp = self.input.process(query, user_id)
            timeline.append({"layer": "input", "time": time.time() - t0})

            u = self.understand.understand(inp)
            timeline.append({"layer": "understanding"})

            # call reasoner (async) with memory context from episodic/semantic
            # create a dedicated event loop for synchronous invocation without
            # modifying the global loop (avoids closing the test runner loop)
            loop = asyncio.new_event_loop()
            # fetch similar experiences to enrich context
            try:
                prior = self.episodic.retrieve_similar(u.get("parsed_query", ""))
            except Exception:
                prior = []
            mem_ctx = {"prior_experiences": prior, "semantic": self.semantic.search(u.get("parsed_query", ""))}
            reasoning = loop.run_until_complete(self.reasoner.reason(u, memory=mem_ctx))
            loop.close()
            timeline.append({"layer": "reasoning", "tokens": reasoning.get("tokens_used")})

            tasks = self.planner.decompose(reasoning.get("reasoning_output", ""))
            state = self.state_mgr.initialize_state(goal=inp.query, tasks=tasks)
            timeline.append({"layer": "planning", "tasks": len(tasks)})

            metrics: Dict[str, Any] = {"tokens_used": 0, "cost": 0.0}

            # simple execution loop
            iterations = 0
            outputs = []
            while iterations < self.max_iterations and state.active_tasks:
                action = self.decider.decide_next_action(state)
                if action is None:
                    break
                # support decider returning (action_type, params) or (action_type, params, confidence)
                if isinstance(action, tuple) and len(action) == 3:
                    action_type, params, confidence = action
                elif isinstance(action, tuple) and len(action) >= 2:
                    action_type, params = action[0], action[1]
                    confidence = 0.0
                else:
                    # unexpected shape
                    break
                if action_type == "call_llm":
                    # call reasoning again for the task prompt
                    loop = asyncio.new_event_loop()
                    resp = loop.run_until_complete(self.reasoner.reason({"task": params}, memory=None))
                    loop.close()
                    outputs.append(resp)
                    # mark task complete
                    state = self.state_mgr.mark_task_complete(state, params.get("task_id"), resp)
                # guardrails check
                allowed, failed = self.guardrails.check_all(state.__dict__ if hasattr(state, "__dict__") else {}, {"tool": action_type, "params": params}, cost=0.0)
                if not allowed:
                    # log and mark task failed
                    from agent_framework.observability import logger

                    logger.info(f"guardrails blocked action={action} failures={failed}")
                    if state.active_tasks:
                        tid = state.active_tasks[0].id
                        state = self.state_mgr.mark_task_complete(state, tid, result={"error": "guardrails_blocked", "details": failed})
                    continue

                # execute tool via executor
                exec_res = self.tool_executor.execute(action_type, params or {}, timeout_sec=30)
                metrics["tokens_used"] += exec_res.get("execution_time_ms", 0)
                metrics["cost"] += 0.0

                r = {"reasoning_output": exec_res.get("output"), "tokens_used": 0, "cost": 0.0}
                # store experience
                try:
                    self.episodic.store_experience(inp.query, f"{action_type}:{params}", str(r.get("reasoning_output")), score=1.0)
                except Exception:
                    pass
                iterations += 1

            t1 = time.time()
            return {"success": True, "output": outputs, "metrics": {"duration_ms": int((t1 - t0) * 1000)}, "timeline": timeline}
        except Exception as e:
            return {"success": False, "error": str(e)}
