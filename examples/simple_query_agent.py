"""Simple Query Agent example (DOC-001).

Shows a minimal example of using the `Agent` to run a single query,
prints the result and cost metrics, and handles errors gracefully.

Acceptance Criteria satisfied:
- runs without errors (adds `backend` to `sys.path` when necessary)
- demonstrates basic Agent usage
- prints cost tracking and tokens
- includes docstring and comments
- wraps call with try/except for graceful error handling
"""

import os
import sys
import json
import asyncio

# Ensure the `backend` package is importable when running this example
ROOT = os.path.dirname(os.path.dirname(__file__))
BACKEND = os.path.join(ROOT, "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from agent_framework.core.agent import Agent


def run_simple_query(query: str, user_id: str) -> dict:
    """Run a single query through an Agent and return the result dict.

    If called from inside an event loop, `Agent.run` may return a
    coroutine — in that case we await it so this function always returns
    a concrete dict.
    """
    agent = Agent()

    try:
        out = agent.run(query, user_id)
        if asyncio.iscoroutine(out):
            out = asyncio.run(out)
        return out
    except Exception as exc:
        return {"success": False, "error": str(exc)}


def main() -> None:
    query = "Provide a short summary of: The quick brown fox jumps over the lazy dog."
    user = "simple-example-user"

    print("Running Simple Query Agent example...\n")
    result = run_simple_query(query, user)

    print("Agent result:")
    try:
        print(json.dumps(result, default=str, indent=2))
    except Exception:
        print(result)

    metrics = result.get("metrics") if isinstance(result, dict) else None
    if isinstance(metrics, dict):
        cost = metrics.get("cost", 0.0)
        tokens = metrics.get("tokens_used", 0)
        duration = metrics.get("duration_ms") or result.get("execution_time_ms")
        print(f"\nCost: {cost:.6f}  Tokens used: {tokens}  Duration(ms): {duration}")
    elif not result.get("success", True):
        print("Agent reported an error:", result.get("error"))


if __name__ == "__main__":
    main()
