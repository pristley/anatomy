"""Multi-Agent example (DOC-002).

Demonstrates using `AgentCoordinator` to run two agents concurrently,
shows cost/tokens metrics per agent, handles errors gracefully, and
prints a combined summary.

Run with:
    PYTHONPATH=.:backend .venv/bin/python3 examples/multi_agent_example.py

"""

import os
import sys
import json
import asyncio
from typing import Any, Dict

# Ensure backend package is importable when running directly
ROOT = os.path.dirname(os.path.dirname(__file__))
BACKEND = os.path.join(ROOT, "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from agent_framework.core.agent import Agent, AgentCoordinator


async def run_coordinator_demo() -> Dict[str, Any]:
    """Create two agents, run them concurrently, and return results."""
    coord = AgentCoordinator()
    a1 = Agent(model_name="agent-one")
    a2 = Agent(model_name="agent-two")
    coord.register("agent-one", a1)
    coord.register("agent-two", a2)

    # prepare two queries
    q1 = "Summarize: Cats are curious animals."
    q2 = "Explain briefly: How photosynthesis works."

    # run both agents concurrently and capture errors per-agent
    async def run_agent(id: str, query: str, user: str) -> Dict[str, Any]:
        try:
            out = coord.run_agent(id, query, user)
            if asyncio.iscoroutine(out):
                out = await out
            return out
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    t1 = asyncio.create_task(run_agent("agent-one", q1, "user-a"))
    t2 = asyncio.create_task(run_agent("agent-two", q2, "user-b"))

    r1, r2 = await asyncio.gather(t1, t2)

    # collect metrics and produce a summary
    def summarize(name: str, res: Dict[str, Any]) -> Dict[str, Any]:
        metrics = res.get("metrics") if isinstance(res, dict) else None
        return {
            "agent": name,
            "success": bool(res.get("success", False)),
            "cost": metrics.get("cost", 0.0) if isinstance(metrics, dict) else 0.0,
            "tokens": metrics.get("tokens_used", 0) if isinstance(metrics, dict) else 0,
            "error": res.get("error") if not res.get("success", True) else None,
        }

    summary = {"agent-one": summarize("agent-one", r1), "agent-two": summarize("agent-two", r2)}
    return {"results": {"agent-one": r1, "agent-two": r2}, "summary": summary}


def main() -> None:
    print("Running Multi-Agent example...\n")
    try:
        out = asyncio.run(run_coordinator_demo())
    except Exception as exc:
        print("Unexpected failure when running coordinator demo:", exc)
        raise

    # pretty print results and summary
    print("Full results:")
    try:
        print(json.dumps(out["results"], default=str, indent=2))
    except Exception:
        print(out.get("results"))

    print("\nSummary:")
    print(json.dumps(out.get("summary"), indent=2))


if __name__ == "__main__":
    main()
"""Example: Multi-Agent Parallelization

This example demonstrates:
- Spawning subagents for parallel tasks
- Aggregating results

Usage:
    python examples/multi_agent_example.py

Expected output:
    Placeholder run (no-op)

Status:
    TODO: Implement after core layers are complete
"""

import asyncio


async def main():
    # TODO: Implement example
    print("multi_agent_example: placeholder")


if __name__ == "__main__":
    asyncio.run(main())
