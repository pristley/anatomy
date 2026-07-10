"""Tool Integration example (DOC-003).

Demonstrates invoking a built-in tool (`math_eval`) safely from examples,
shows result handling, basic cost tracking (simulated), and error handling.

Run with:
    PYTHONPATH=.:backend .venv/bin/python3 examples/tool_integration_example.py

"""

import os
import sys
import json
from typing import Any, Dict

# Ensure backend package is importable when running this example
ROOT = os.path.dirname(os.path.dirname(__file__))
BACKEND = os.path.join(ROOT, "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

# Import the safe math evaluator tool
from agent_framework.tools.builtin.math_eval import evaluate_expression


def run_expressions(exprs: list[str]) -> Dict[str, Any]:
    """Run a list of math expressions through the safe evaluator.

    Returns a structured dict with per-expression results and simple
    aggregated cost/tokens metrics (simulated for the example).
    """
    results = {}
    total_cost = 0.0
    total_tokens = 0

    for i, expr in enumerate(exprs, start=1):
        try:
            val = evaluate_expression(expr)
            # Simulate cost/tokens proportional to expression length
            tokens = max(1, len(expr) // 4)
            cost = tokens * 0.00001
            results[f"expr_{i}"] = {"expression": expr, "result": val, "success": True}
            total_tokens += tokens
            total_cost += cost
        except Exception as exc:
            results[f"expr_{i}"] = {"expression": expr, "success": False, "error": str(exc)}

    return {"results": results, "metrics": {"tokens_used": total_tokens, "cost": total_cost}}


def main() -> None:
    examples = [
        "2 + 2",
        "3 * (4 + 5)",
        "2 ** 10",
        "invalid + expr",
    ]

    print("Running Tool Integration example (math_eval)...\n")
    out = run_expressions(examples)

    print("Per-expression results:")
    print(json.dumps(out["results"], indent=2))

    print("\nMetrics:")
    print(json.dumps(out["metrics"], indent=2))


if __name__ == "__main__":
    main()
