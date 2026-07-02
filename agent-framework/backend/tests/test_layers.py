import importlib
import pytest

def _mod(name: str):
    return importlib.import_module(f"agent_framework.core.layers.{name}")

input_mod = _mod("01_input")
u_mod = _mod("02_understanding")
r_mod = _mod("03_reasoning")
p_mod = _mod("04_planning")
s_mod = _mod("05_state")
d_mod = _mod("06_decision")


def test_input_layer_normalizes_query():
    layer = input_mod.InputLayer()
    inp = layer.process(" Hello world ", "user1")
    assert inp.query == "Hello world"
    assert inp.user_id == "user1"


def test_understanding_extracts_intent():
    u = u_mod.UnderstandingLayer()
    class Dummy:
        query = "What is my top product"
    out = u.understand(Dummy())
    assert "parsed_query" in out


def test_reasoning_calls_llm(monkeypatch):
    class MockLLM:
        async def infer(self, s, u, max_tokens=0):
            return "Step 1: do something"

    rc = r_mod.ReasoningCore(MockLLM())
    import asyncio

    res = asyncio.get_event_loop().run_until_complete(rc.reason({"parsed_query": {}}))
    assert "reasoning_output" in res


def test_planning_decomposes_tasks():
    planner = p_mod.PlanningDecomposition()
    tasks = planner.decompose("Step 1: a\nStep 2: b")
    assert len(tasks) >= 1


def test_state_tracks_progress():
    sm = s_mod.StateManager()
    from agent_framework.core.types import TaskDef

    tasks = [TaskDef(id="t1", name="do", dependencies=[])]
    state = sm.initialize_state("goal", tasks)
    new_state = sm.mark_task_complete(state, "t1", {"out": 1})
    assert len(new_state.completed_tasks) == 1


def test_decision_selects_action():
    dec = d_mod.DecisionEngine()
    from agent_framework.core.types import AgentState, TaskDef

    tasks = [TaskDef(id="t1", name="do", dependencies=[])]
    s = AgentState(agent_id="a", goal="g", active_tasks=tasks)
    action = dec.decide_next_action(s)
    assert action is not None
