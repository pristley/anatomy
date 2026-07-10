"""Layer 9: Evaluation Engine.

Spec: EVAL-001

Provides an `EvaluationEngine` for simple outcome assessment, similarity
scoring, and feedback generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class TaskOutcome:
    """Represents the evaluation result for a single task.

    Attributes:
        task_id: Unique identifier for the task
        goal_id: Optional goal this task contributes to
        success: Whether the task is considered successful
        similarity: Similarity score (0..1) between expected and actual
        summary: Human-readable summary of the outcome
        timestamp: When the outcome was evaluated
        metadata: Additional evaluation metrics
    """

    task_id: str
    goal_id: Optional[str]
    success: bool
    similarity: float
    summary: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GoalEvaluation:
    """Aggregated evaluation for a goal composed of multiple task outcomes."""

    goal_id: str
    overall_score: float
    feedback: str
    task_outcomes: List[TaskOutcome]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EvaluationEngine:
    """Engine to evaluate task outcomes and goals.

    Uses a lightweight similarity function to compare expected vs actual
    outputs and produces feedback messages based on scores.
    """

    def __init__(self, success_threshold: float = 0.8) -> None:
        self.success_threshold = float(success_threshold)

    @staticmethod
    def similarity(a: str, b: str) -> float:
        """Return a normalized similarity score between two strings (0..1).

        Uses difflib.SequenceMatcher which is dependency-free and deterministic
        for testing purposes.
        """
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        return float(SequenceMatcher(None, a, b).ratio())

    async def evaluate_task(
        self,
        task_id: str,
        expected: str,
        actual: str,
        goal_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TaskOutcome:
        """Evaluate a single task's outcome.

        Returns a `TaskOutcome` with similarity and success flag.
        """
        sim = self.similarity(expected, actual)
        success = sim >= self.success_threshold
        summary = f"success={success}; similarity={sim:.3f}; expected_len={len(expected)}; actual_len={len(actual)}"
        return TaskOutcome(
            task_id=task_id,
            goal_id=goal_id,
            success=success,
            similarity=sim,
            summary=summary,
            metadata=metadata or {},
        )

    async def evaluate_goal(
        self, goal_id: str, task_outcomes: Sequence[TaskOutcome]
    ) -> GoalEvaluation:
        """Aggregate multiple `TaskOutcome`s into a `GoalEvaluation`.

        Computes an overall score as the mean similarity, and generates
        actionable feedback.
        """
        outcomes = list(task_outcomes)
        if not outcomes:
            return GoalEvaluation(
                goal_id=goal_id,
                overall_score=0.0,
                feedback="No tasks evaluated.",
                task_outcomes=[],
            )

        overall_score = float(sum(o.similarity for o in outcomes) / len(outcomes))
        feedback = self.generate_feedback(goal_id, overall_score, outcomes)
        return GoalEvaluation(
            goal_id=goal_id,
            overall_score=overall_score,
            feedback=feedback,
            task_outcomes=outcomes,
        )

    def generate_feedback(
        self, goal_id: str, overall_score: float, outcomes: Sequence[TaskOutcome]
    ) -> str:
        """Create human-friendly feedback based on the overall score and outcomes."""
        low = [o for o in outcomes if o.similarity < self.success_threshold]
        parts: List[str] = []
        parts.append(f"Goal '{goal_id}' overall score: {overall_score:.3f}")

        if overall_score >= 0.95:
            parts.append("Excellent — the task outputs closely match expectations.")
        elif overall_score >= 0.8:
            parts.append(
                "Good — minor discrepancies detected. Consider small prompt or configuration tweaks."
            )
        else:
            parts.append(
                "Below expectations — review the following tasks for improvement:"
            )
            for o in low:
                parts.append(
                    f" - {o.task_id}: similarity={o.similarity:.3f}; summary={o.summary}"
                )
            parts.append(
                "Suggested actions: refine prompts, increase examples/contexts, or add validation checks."
            )

        return "\n".join(parts)


__all__ = ["EvaluationEngine", "TaskOutcome", "GoalEvaluation"]
