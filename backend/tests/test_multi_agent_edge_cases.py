"""Edge case tests for multi-agent scenarios."""

import pytest
import asyncio
from agent_framework.core.agent import Agent
from agent_framework.core.types import TaskDef


@pytest.mark.asyncio
async def test_cyclic_dependencies_handled():
    agent = Agent()
    t1 = TaskDef(id="t1", name="task 1", dependencies=["t2"])
    t2 = TaskDef(id="t2", name="task 2", dependencies=["t1"])

    state = agent.state_manager.initialize_state(goal="cyclic", tasks=[t1, t2])
    final_state, results = await agent.run_with_subagents(state, "user1")
    # cycle should avoid infinite loop; final_state returned
    assert final_state is not None


@pytest.mark.asyncio
async def test_duplicate_task_ids():
    agent = Agent()
    t1 = TaskDef(id="t1", name="task 1", dependencies=[])
    t2 = TaskDef(id="t1", name="task 1 copy", dependencies=[])

    state = agent.state_manager.initialize_state(goal="duplicates", tasks=[t1, t2])
    final_state, results = await agent.run_with_subagents(state, "user1")
    assert final_state is not None


@pytest.mark.asyncio
async def test_large_task_graph_quick():
    agent = Agent()
    tasks = []
    for i in range(20):
        deps = [f"t{i-1}"] if i > 0 else []
        tasks.append(TaskDef(id=f"t{i}", name=f"task {i}", dependencies=deps))

    state = agent.state_manager.initialize_state(goal="large", tasks=tasks)
    final_state, results = await agent.run_with_subagents(state, "user1")
    assert isinstance(results, dict)
