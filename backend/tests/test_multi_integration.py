import asyncio
import pytest

from agent_framework.core.agent import Agent, AgentCoordinator
from agent_framework.core.types import TaskDef


@pytest.mark.asyncio
async def test_coordinator_runs_multiple_agents_concurrently():
    coord = AgentCoordinator()
    a1 = Agent()
    a2 = Agent()
    coord.register("a1", a1)
    coord.register("a2", a2)

    # run two agents concurrently via coordinator
    res1_coro = coord.run_agent("a1", "hello a1", "user1")
    res2_coro = coord.run_agent("a2", "hello a2", "user2")
    r1, r2 = await asyncio.gather(res1_coro, res2_coro)

    assert isinstance(r1, dict) and r1.get("success") is True
    assert isinstance(r2, dict) and r2.get("success") is True


@pytest.mark.asyncio
async def test_subagent_instances_are_independent():
    parent = Agent(model_name="parent-model")
    child = parent.spawn_subagent("s1")
    # child inherits initial config
    assert child.model_name == "parent-model"

    # mutate child and ensure parent unaffected
    child.model_name = "child-model"
    assert parent.model_name == "parent-model"
    assert child.model_name == "child-model"


@pytest.mark.asyncio
async def test_nested_parallel_via_run_with_subagents():
    agent = Agent()
    # t1 and t2 independent, t3 depends on both
    t1 = TaskDef(id="t1", name="task one", dependencies=[])
    t2 = TaskDef(id="t2", name="task two", dependencies=[])
    t3 = TaskDef(id="t3", name="task three", dependencies=["t1", "t2"])
    state = agent.state_manager.initialize_state(goal="nested", tasks=[t1, t2, t3])

    final_state, results = await agent.run_with_subagents(state, "user-n")
    assert set(results.keys()) == {"t1", "t2", "t3"}
    assert final_state.status == "succeeded"
