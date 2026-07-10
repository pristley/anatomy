import asyncio
import pytest

from agent_framework.core.agent import Agent


@pytest.mark.asyncio
async def test_spawn_and_run_subagents():
    parent = Agent()
    child1 = parent.spawn_subagent("s1")
    child2 = parent.spawn_subagent("s2", max_iterations=2)

    assert child1 is not parent
    assert child1.model_name == parent.model_name
    assert child2.max_iterations == 2

    # run both subagents concurrently
    t1 = parent.run_subagent_async("s1", "hello from s1", "user1")
    t2 = parent.run_subagent_async("s2", "hello from s2", "user2")

    res1, res2 = await asyncio.gather(t1, t2)
    assert isinstance(res1, dict) and res1.get("success") is True
    assert isinstance(res2, dict) and res2.get("success") is True


def test_list_subagents():
    parent = Agent()
    parent.spawn_subagent("s-a")
    parent.spawn_subagent("s-b")
    ids = parent.list_subagents()
    assert set(ids) == {"s-a", "s-b"}
