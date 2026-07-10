"""Agent orchestrator that runs the layer pipeline end-to-end."""

from __future__ import annotations

import time
import asyncio
from typing import Any, Dict, Optional, List

from importlib.util import spec_from_file_location, module_from_spec
import sys
from pathlib import Path


def _load_from_layers(filename: str, attr: str):
    base = Path(__file__).resolve().parent
    path = base / "layers" / filename
    real_path = path.resolve()
    # derive package relative to the agent_framework root so relative imports work
    relative = real_path.parent.relative_to(base.parent)
    pkg = "agent_framework." + ".".join(relative.parts)
    mod_name = f"{pkg}.{real_path.stem}"
    spec = spec_from_file_location(mod_name, str(real_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {filename}")
    mod = module_from_spec(spec)
    mod.__package__ = pkg
    # register module so decorators and dataclasses can find the module entry
    sys.modules[mod_name] = mod
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
_ExecutionEngine = _load_from_layers("07_execution.py", "ExecutionEngine")
_ExecutionStatus = _load_from_layers("07_execution.py", "ExecutionStatus")
_ResilienceLayer = _load_from_layers("08_resilience.py", "ResilienceLayer")
_EvaluationEngine = _load_from_layers("09_evaluation.py", "EvaluationEngine")


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
        # state manager available for orchestration and tests
        try:
            self.state_manager = _StateManager(agent_id=None)
        except Exception:
            self.state_manager = None
        self.decision_engine = _DecisionEngine()
        # Execution engine for tool invocation
        try:
            self.execution_engine = _ExecutionEngine()
        except Exception:
            # fallback if layer not available
            self.execution_engine = None
        # Resilience layer for fault isolation and recovery
        try:
            self.resilience = _ResilienceLayer()
        except Exception:
            self.resilience = None
        # Evaluation engine for outcome assessment (Layer 9)
        try:
            self.evaluator = _EvaluationEngine()
        except Exception:
            self.evaluator = None
        # Subagent management
        self._subagents: Dict[str, Agent] = {}
        self._subagent_tasks: Dict[str, List[asyncio.Task]] = {}
        self._subagent_counter = 0

    async def _run_async(self, query: str, user_id: str) -> Dict[str, Any]:
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
            state = self.state_manager.initialize_state(
                goal=understood.get("parsed_query", {}).get("intent"), tasks=tasks
            )

            # execution loop
            iteration = 0
            last_output = None
            while iteration < self.max_iterations and state.active_tasks:
                iteration += 1
                action, params, confidence = self.decision_engine.decide_next_action(
                    state
                )
                if action is None:
                    break
                # Prepare task execution. Prefer executing via ExecutionEngine.
                task_text = (
                    f"Execute {action} with params {params} (confidence={confidence})"
                )

                # small internal tool wrapper that delegates to the reasoner
                class _ReasonerTool:
                    def __init__(self, reasoner, text, conf):
                        self._reasoner = reasoner
                        self._text = text
                        self._conf = conf

                    def validate_params(self, p):
                        return None

                    async def run_async(self, **p):
                        return await self._reasoner.reason(
                            {
                                "parsed_query": self._text,
                                "kb_results": [],
                                "confidence": self._conf,
                            }
                        )

                    def estimated_cost(self, **p):
                        return 0.0

                tool = _ReasonerTool(self.reasoner, task_text, confidence)

                if self.execution_engine is not None:
                    # Prefer executing under resilience coordination so circuit
                    # breakers can isolate failing services and suggest recovery.
                    if self.resilience is not None:
                        res = await self.resilience.execute_with_resilience(
                            self.execution_engine.execute,
                            action or "tool",
                            tool,
                            {},
                            request_id=user_id,
                        )
                        if res.get("success"):
                            result = res.get("output")
                        else:
                            # recovery strategy handling: try a single retry for transient errors
                            strategy = res.get("recovery_strategy")
                            if strategy == "retry_with_backoff":
                                await asyncio.sleep(0.05)
                                try:
                                    result = await self.execution_engine.execute(
                                        tool, {}, request_id=user_id
                                    )
                                except Exception:
                                    result = None
                            else:
                                result = None
                    else:
                        result = await self.execution_engine.execute(
                            tool, {}, request_id=user_id
                        )

                    if (
                        result is not None
                        and getattr(result, "status", None) == _ExecutionStatus.SUCCESS
                    ):
                        r = result.output
                        metrics["tokens_used"] += getattr(
                            result.metrics, "tokens_used", 0
                        )
                        metrics["cost"] += getattr(result.metrics, "cost", 0.0)
                    else:
                        # on error or timeout, record and continue
                        r = {"reasoning_output": None, "tokens_used": 0, "cost": 0.0}
                else:
                    # fallback to previous behavior
                    r = await self.reasoner.reason(
                        {
                            "parsed_query": task_text,
                            "kb_results": [],
                            "confidence": confidence,
                        }
                    )
                metrics["tokens_used"] += r.get("tokens_used", 0)
                metrics["cost"] += r.get("cost", 0.0)

                # assume first active task is the one
                if state.active_tasks:
                    tid = state.active_tasks[0].id
                    state = self.state_manager.mark_task_complete(
                        state, tid, result={"output": r.get("reasoning_output")}
                    )
                    # Evaluate outcome if evaluation engine is available
                    try:
                        if self.evaluator is not None:
                            expected = ""
                            # try to infer expected from params if provided
                            if isinstance(params, dict):
                                expected = params.get("expected", "") or ""
                            actual = r.get("reasoning_output") or ""
                            # collect per-task outcomes for goal-level aggregation
                            if not hasattr(self, "_task_outcomes"):
                                self._task_outcomes = []
                            to = await self.evaluator.evaluate_task(
                                tid, expected, actual, goal_id=state.goal
                            )
                            self._task_outcomes.append(to)
                    except Exception:
                        # non-fatal; continue without evaluation
                        pass
                    last_output = r.get("reasoning_output")

            total_ms = int((time.monotonic() - start_all) * 1000)
            metrics["duration_ms"] = total_ms
            # produce goal-level evaluation if available
            goal_evaluation = None
            try:
                if self.evaluator is not None and hasattr(self, "_task_outcomes"):
                    goal_evaluation = await self.evaluator.evaluate_goal(
                        state.goal or "", self._task_outcomes
                    )
            except Exception:
                goal_evaluation = None
            return {
                "success": True,
                "output": last_output,
                "metrics": metrics,
                "cost": metrics.get("cost", 0.0),
                "execution_time_ms": total_ms,
                "evaluation": goal_evaluation,
            }

        except Exception as exc:  # pragma: no cover - orchestration error handling
            return {"success": False, "error": str(exc)}

    def run(self, query: str, user_id: str) -> Dict[str, Any]:
        """Synchronous wrapper around the async pipeline for convenience in tests."""
        import asyncio

        loop = asyncio.get_event_loop()
        if loop.is_running():
            # if already in an event loop, return coroutine for caller to await
            return self._run_async(query, user_id)
        return loop.run_until_complete(self._run_async(query, user_id))

    def spawn_subagent(
        self,
        agent_id: str,
        model_name: Optional[str] = None,
        max_iterations: Optional[int] = None,
    ) -> "Agent":
        """Create and register a subagent inheriting parent config.

        Subagents are independent instances but inherit parent `model_name`
        and `max_iterations` unless overridden.
        """
        if agent_id in self._subagents:
            raise KeyError(f"subagent already exists: {agent_id}")

        child = Agent(
            model_name=model_name or self.model_name,
            max_iterations=max_iterations or self.max_iterations,
        )
        # keep a backref to parent for context if needed
        child.parent = self
        self._subagents[agent_id] = child
        self._subagent_tasks[agent_id] = []
        return child

    def list_subagents(self) -> List[str]:
        return list(self._subagents.keys())

    def run_subagent_async(
        self, agent_id: str, query: str, user_id: str
    ) -> asyncio.Task:
        """Start a subagent run concurrently and return the asyncio.Task."""
        if agent_id not in self._subagents:
            raise KeyError(f"unknown subagent: {agent_id}")
        task = asyncio.create_task(self._subagents[agent_id]._run_async(query, user_id))
        self._subagent_tasks.setdefault(agent_id, []).append(task)
        return task

    async def run_with_subagents(self, state, user_id: str):
        """Run tasks in the provided `state` using subagents for parallelizable tasks.

        Simple dependency resolution: tasks with no unmet dependencies run concurrently.
        Returns final state and a mapping of task_id -> result.
        """
        results: Dict[str, Any] = {}

        # Ensure there is a state manager available for marking task completion
        if self.state_manager is None:
            self.state_manager = _StateManager(agent_id=user_id)

        def completed_ids(s):
            return {t.id for t in s.completed_tasks}

        current_state = state

        while current_state.active_tasks:
            # find runnable tasks (all dependencies satisfied)
            runnable = [
                t
                for t in current_state.active_tasks
                if set(t.dependencies).issubset(completed_ids(current_state))
            ]
            if not runnable:
                # cyclic dependency or blocked; break to avoid infinite loop
                break

            tasks_map = {}
            for t in runnable:
                # spawn a unique subagent per task
                self._subagent_counter += 1
                sid = f"sub-{t.id}-{self._subagent_counter}"
                self.spawn_subagent(sid)
                # start it; use task.name as query for simplicity
                task = self.run_subagent_async(sid, t.name, user_id)
                tasks_map[t.id] = (t, sid, task)

            # wait for all runnable tasks to complete
            awaited = [v[2] for v in tasks_map.values()]
            completed = await asyncio.gather(*awaited)

            # aggregate results and mark tasks complete
            for task_id, (task_def, sid, _t) in tasks_map.items():
                # find the corresponding completed result from gathered outputs
                # mapping order preserved
                out = completed.pop(0)
                results[task_id] = out
                # mark complete on state manager
                current_state = self.state_manager.mark_task_complete(
                    current_state,
                    task_id,
                    result={
                        "output": out.get("output") if isinstance(out, dict) else out
                    },
                )

        return current_state, results


__all__ = ["Agent"]

__all__.append("ExecutionEngine")


class AgentCoordinator:
    """Lightweight coordinator for managing multiple Agent instances.

    This is a small helper for tests and lightweight orchestration. Replace
    with a more featureful implementation as needed.
    """

    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}

    def register(self, agent_id: str, agent: Agent) -> None:
        self._agents[agent_id] = agent

    def run_agent(self, agent_id: str, query: str, user_id: str):
        agent = self._agents.get(agent_id)
        if agent is None:
            raise KeyError(f"agent not registered: {agent_id}")
        return agent.run(query, user_id)


__all__.append("AgentCoordinator")
