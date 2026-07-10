import importlib
import pytest

mod = importlib.import_module("agent_framework.core.layers.09_evaluation")
EvaluationEngine = mod.EvaluationEngine
TaskOutcome = mod.TaskOutcome
GoalEvaluation = mod.GoalEvaluation


@pytest.mark.asyncio
async def test_similarity_and_empty_cases():
    # exact match
    assert EvaluationEngine.similarity("hello", "hello") == 1.0
    # both empty
    assert EvaluationEngine.similarity("", "") == 1.0
    # one empty
    assert EvaluationEngine.similarity("", "nonempty") == 0.0


@pytest.mark.asyncio
async def test_evaluate_task_success_and_failure():
    engine = EvaluationEngine(success_threshold=0.8)
    good = await engine.evaluate_task("t1", "The cat sat on the mat.", "The cat sat on the mat.")
    assert good.success is True
    assert pytest.approx(good.similarity, rel=1e-6) == 1.0

    bad = await engine.evaluate_task("t2", "The cat sat on the mat.", "Completely unrelated output.")
    assert bad.success is False


@pytest.mark.asyncio
async def test_evaluate_goal_and_feedback():
    engine = EvaluationEngine(success_threshold=0.75)
    t1 = await engine.evaluate_task("t1", "A B C D E", "A B C D E")
    t2 = await engine.evaluate_task("t2", "foo bar baz", "foo baz bar")
    goal = await engine.evaluate_goal("g1", [t1, t2])
    assert 0.0 <= goal.overall_score <= 1.0
    assert "Goal 'g1' overall score" in goal.feedback
    # When at least one task is below threshold, feedback should include suggested actions
    if goal.overall_score < 0.8:
        assert "Suggested actions" in goal.feedback
