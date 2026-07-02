"""Layer 9: Evaluation & scoring of outcomes."""
from __future__ import annotations

from typing import Any, Dict


class EvaluationEngine:
    def __init__(self) -> None:
        pass

    def evaluate(self, outcome: Dict[str, Any], criteria: Dict[str, Any] | None = None) -> float:
        """Return a score between 0.0 and 1.0 for the given outcome.

        Simple heuristic: prefer status 'ok' and non-empty output.
        """
        criteria = criteria or {}
        status = outcome.get("status")
        output = outcome.get("output")

        if status != "ok":
            return 0.0

        if output is None:
            return 0.0

        # length-based signal
        try:
            length = len(str(output))
        except Exception:
            length = 0

        score = min(1.0, max(0.0, length / 200.0))
        return float(score)


__all__ = ["EvaluationEngine"]
