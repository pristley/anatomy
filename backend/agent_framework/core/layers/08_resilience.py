"""Layer 8: Resilience & error handling with retries/backoff."""

from __future__ import annotations

from typing import Any, Dict


class ResilienceLayer:
    RETRIABLE = "retriable"
    TERMINAL = "terminal"

    def __init__(self, max_retries: int = 3, backoff_base: float = 2.0) -> None:
        self.max_retries = max_retries
        self.backoff_base = backoff_base

    def classify(self, error: Exception) -> str:
        name = error.__class__.__name__.lower()
        if "timeout" in name or "tempor" in name or "connection" in name:
            return self.RETRIABLE
        return self.TERMINAL

    def handle_error(self, error: Exception, task: Dict[str, Any]) -> Dict[str, Any]:
        """Decide whether to retry or abort.

        Expects `task` to be a dict that may contain `retry_count`.
        """
        kind = self.classify(error)
        retry_count = int(task.get("retry_count", 0))

        if kind == self.RETRIABLE and retry_count < self.max_retries:
            retry_count += 1
            retry_time = int((self.backoff_base**retry_count) * 1)
            return {
                "recovered": True,
                "action": "retry",
                "retry_time": retry_time,
                "retry_count": retry_count,
            }

        return {
            "recovered": False,
            "action": "abort",
            "retry_time": None,
            "retry_count": retry_count,
        }


__all__ = ["ResilienceLayer"]
