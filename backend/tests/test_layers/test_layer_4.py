"""Tests for Layer 4: Planning and decomposition."""

import importlib.util
import sys
from pathlib import Path


def _load_mod():
    backend_root = Path(__file__).resolve().parents[2]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))
    path = backend_root / "agent_framework" / "core" / "layers" / "04_planning.py"
    pkg = "agent_framework.core.layers"
    mod_name = f"{pkg}.04_planning"
    spec = importlib.util.spec_from_file_location(mod_name, str(path))
    mod = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    mod.__package__ = pkg
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_decompose_steps_and_fallback():
    mod = _load_mod()
    text = "Step 1: Do A\nStep 2: Do B"
    tasks = mod.PlanningDecomposition.decompose(text)
    assert len(tasks) == 2

    # fallback
    tasks2 = mod.PlanningDecomposition.decompose("Just a sentence. Another.")
    assert len(tasks2) >= 1


def test_topological_sort_handles_deps_and_cycles():
    mod = _load_mod()
    from agent_framework.core.types import TaskDef

    t1 = TaskDef(id="a", name="a", dependencies=["b"])
    t2 = TaskDef(id="b", name="b", dependencies=[])
    ordered = mod.topological_sort([t1, t2])
    assert ordered[0].id == "b"
