"""Abstract guardrails and simple enforcers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple
import time


class AbstractGuardrail(ABC):
    @abstractmethod
    def check(self, state: Dict[str, Any], action: Dict[str, Any]) -> Tuple[bool, str]:
        """Return (allowed, reason)"""


class BudgetEnforcer:
    def __init__(self) -> None:
        # simple in-memory budgets per user
        self._budgets: Dict[str, float] = {}

    def set_budget(self, user_id: str, amount: float) -> None:
        self._budgets[user_id] = amount

    def check_budget(self, user_id: str, cost: float) -> bool:
        remaining = self._budgets.get(user_id)
        if remaining is None:
            return True
        if cost > remaining:
            return False
        self._budgets[user_id] = remaining - cost
        return True


class RateLimiter:
    def __init__(self, max_per_minute: int = 60) -> None:
        self.max = max_per_minute
        self._calls: Dict[str, List[float]] = {}

    def check_rate_limit(self, user_id: str) -> bool:
        now = time.time()
        window = 60.0
        calls = self._calls.setdefault(user_id, [])
        # purge old
        calls[:] = [t for t in calls if now - t < window]
        if len(calls) >= self.max:
            return False
        calls.append(now)
        return True


__all__ = ["AbstractGuardrail", "BudgetEnforcer", "RateLimiter"]
