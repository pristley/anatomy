import pytest

from agent_framework.core.agent import Agent
from agent_framework.core.types import TaskDef


@pytest.mark.asyncio
async def test_run_with_subagents_simple():
    agent = Agent()
    # two independent tasks
    t1 = TaskDef(id="t1", name="task one", dependencies=[])
    t2 = TaskDef(id="t2", name="task two", dependencies=[])
    state = agent.state_manager.initialize_state(goal="g", tasks=[t1, t2])

    new_state, results = await agent.run_with_subagents(state, "user-x")
    assert isinstance(results, dict)
    assert "t1" in results and "t2" in results
    assert new_state.status in ("succeeded", "running")


@pytest.mark.asyncio
async def test_run_with_dependencies():
    agent = Agent()
    # t2 depends on t1
    t1 = TaskDef(id="t1", name="task one", dependencies=[])
    t2 = TaskDef(id="t2", name="task two", dependencies=["t1"])
    state = agent.state_manager.initialize_state(goal="g", tasks=[t1, t2])

    new_state, results = await agent.run_with_subagents(state, "user-x")
    # both tasks should be present in results
    assert set(results.keys()) == {"t1", "t2"}
    assert new_state.status == "succeeded"
