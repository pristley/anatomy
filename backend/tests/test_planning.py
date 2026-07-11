from agent_framework.core.agent import (
    PlanningDecomposition,
    _topological_sort as topological_sort,
)
from agent_framework.core.types import TaskDef


def test_decompose_steps():
    text = "Step 1: Do A\nStep 2: Do B"
    tasks = PlanningDecomposition.decompose(text, max_tasks=5)
    assert len(tasks) == 2
    assert tasks[0].name.startswith("Step 1")


def test_decompose_fallback():
    text = "Do A. Do B."
    tasks = PlanningDecomposition.decompose(text, max_tasks=2)
    assert len(tasks) == 2
    assert tasks[0].name


def test_decompose_empty():
    assert PlanningDecomposition.decompose("") == []


def test_topological_sort():
    a = TaskDef(id="a", name="a", dependencies=[])
    b = TaskDef(id="b", name="b", dependencies=["a"])
    c = TaskDef(id="c", name="c", dependencies=["b"])
    ordered = topological_sort([c, b, a])
    assert [t.id for t in ordered][:3] == ["a", "b", "c"]


def test_topological_cycle():
    a = TaskDef(id="a", name="a", dependencies=["c"])
    b = TaskDef(id="b", name="b", dependencies=["a"])
    c = TaskDef(id="c", name="c", dependencies=["b"])
    ordered = topological_sort([a, b, c])
    # cycle: ensure all tasks are returned
    assert set(t.id for t in ordered) == {"a", "b", "c"}
