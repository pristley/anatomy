"""Tests for Layer 5: State management."""

import importlib.util
import sys
from pathlib import Path


def _load_mod():
    backend_root = Path(__file__).resolve().parents[2]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))
    path = backend_root / "agent_framework" / "core" / "layers" / "05_state.py"
    pkg = "agent_framework.core.layers"
    mod_name = f"{pkg}.05_state"
    spec = importlib.util.spec_from_file_location(mod_name, str(path))
    mod = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    mod.__package__ = pkg
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_state_initialize_and_mark_complete():
    mod = _load_mod()
    from agent_framework.core.types import TaskDef

    sm = mod.StateManager(agent_id="agent-x")
    tasks = [TaskDef(id="t1", name="one"), TaskDef(id="t2", name="two")]
    st = sm.initialize_state(goal="g", tasks=tasks)
    assert st.agent_id == "agent-x"
    new = sm.mark_task_complete(st, "t1")
    assert len(new.completed_tasks) == 1
    assert new.status in ("running", "succeeded")
    summary = sm.get_state_summary()
    assert "Agent" in summary
