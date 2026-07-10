"""Multi-agent demo script.

Demonstrates AgentCoordinator, spawning subagents, and parallel execution
using `run_with_subagents()`.
"""

import asyncio
import json

from agent_framework.core.agent import Agent, AgentCoordinator
from agent_framework.core.types import TaskDef


async def demo_run():
    print("Starting multi-agent demo...\n")

    # Coordinator with two agents
    coord = AgentCoordinator()
    a1 = Agent(model_name="agent-one")
    a2 = Agent(model_name="agent-two")
    coord.register("agent-one", a1)
    coord.register("agent-two", a2)

    # Run both agents concurrently via coordinator
    print("Running two agents concurrently via AgentCoordinator...")
    r1_task = asyncio.create_task(coord.run_agent("agent-one", "top-level query A", "user-a"))
    r2_task = asyncio.create_task(coord.run_agent("agent-two", "top-level query B", "user-b"))
    r1, r2 = await asyncio.gather(r1_task, r2_task)

    print("Coordinator run results:")
    print(json.dumps({"agent-one": r1, "agent-two": r2}, default=str, indent=2))

    # Demonstrate run_with_subagents for parallel task execution
    print("\nDemonstrating run_with_subagents with dependent tasks...")
    agent = Agent(model_name="parent-agent")
    t1 = TaskDef(id="t1", name="task one", dependencies=[])
    t2 = TaskDef(id="t2", name="task two", dependencies=[])
    t3 = TaskDef(id="t3", name="task three", dependencies=["t1", "t2"])  # depends on both

    # initialize state and run parallel execution
    state = agent.state_manager.initialize_state(goal="demo-goal", tasks=[t1, t2, t3])
    final_state, results = await agent.run_with_subagents(state, "demo-user")

    print("run_with_subagents results:")
    print(json.dumps({"results": results, "final_status": final_state.status}, default=str, indent=2))


if __name__ == "__main__":
    asyncio.run(demo_run())
