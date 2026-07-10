"""Layer 11: Cost tracking and budget enforcement."""

from __future__ import annotations

from typing import Dict


class CostTracker:
    # pricing per 1k tokens
    PRICING = {
        "claude": {"input_per_1k": 0.003, "output_per_1k": 0.015},
    }

    @classmethod
    def track(
        cls, action_type: str, tokens: int | Dict[str, int], model: str = "claude"
    ) -> float:
        pricing = cls.PRICING.get(model, cls.PRICING.get("claude"))
        # tokens may be an int (total) or dict {"input": x, "output": y}
        if isinstance(tokens, dict):
            inp = tokens.get("input", 0)
            out = tokens.get("output", 0)
        else:
            inp = tokens
            out = 0

        cost = (inp / 1000.0) * pricing["input_per_1k"] + (out / 1000.0) * pricing[
            "output_per_1k"
        ]
        return float(cost)


class BudgetEnforcer:
    def __init__(self) -> None:
        # simple in-memory budgets
        self._budgets: Dict[str, float] = {}
        self._used: Dict[str, float] = {}

    def set_budget(self, user_id: str, amount: float) -> None:
        self._budgets[user_id] = float(amount)

    def check_budget(self, user_id: str, cost: float) -> Dict[str, float | int]:
        budget = self._budgets.get(user_id)
        used = self._used.get(user_id, 0.0)
        total_cost = used + cost

        if budget is None:
            remaining = float("inf")
            ok = True
        else:
            remaining = max(0.0, budget - total_cost)
            ok = total_cost <= budget

        if ok:
            self._used[user_id] = total_cost

        return {
            "total_cost": total_cost,
            "tokens_used": 0,
            "remaining_budget": remaining,
        }


__all__ = ["CostTracker", "BudgetEnforcer"]
