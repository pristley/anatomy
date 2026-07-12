"""Tests for Layer 6: Decision engine."""

import importlib.util
import sys
from pathlib import Path


def _load_mod():
    backend_root = Path(__file__).resolve().parents[2]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))
    path = backend_root / "agent_framework" / "core" / "layers" / "06_decision.py"
    pkg = "agent_framework.core.layers"
    mod_name = f"{pkg}.06_decision"
    spec = importlib.util.spec_from_file_location(mod_name, str(path))
    mod = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    mod.__package__ = pkg
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_decision_engine_with_registered_tool():
    mod = _load_mod()
    from agent_framework.core.types import TaskDef, AgentState
    from agent_framework.tools.base import ToolDefinition, ToolRegistry

    # register a dummy tool
    reg = ToolRegistry.get_default()
    reg._tools.clear()

    def exec_fn(p):
        return {"ok": True}

    td = ToolDefinition(
        name="tool", description="d", params_schema=None, execute_fn=exec_fn
    )
    reg.register(td)

    t = TaskDef(id="t1", name="do", action_type="tool", parameters={})
    state = AgentState(
        agent_id="a",
        active_tasks=[t],
        completed_tasks=[],
        status="running",
        memory_refs=[],
    )
    de = mod.DecisionEngine()
    tool_name, params, conf = de.decide_next_action(state)
    assert tool_name == "tool"
    assert conf > 0


def test_decision_skips_invalid_params():
    mod = _load_mod()
    from agent_framework.core.types import TaskDef, AgentState
    from agent_framework.tools.base import ToolDefinition, ToolRegistry

    reg = ToolRegistry.get_default()
    reg._tools.clear()

    td = ToolDefinition(
        name="tool2",
        description="d",
        params_schema={"x": {"type": int, "required": True}},
        execute_fn=lambda p: p,
    )
    reg.register(td)

    t = TaskDef(id="t2", name="do", action_type="tool2", parameters={})
    state = AgentState(
        agent_id="a",
        active_tasks=[t],
        completed_tasks=[],
        status="running",
        memory_refs=[],
    )
    de = mod.DecisionEngine()
    tool_name, params, conf = de.decide_next_action(state)
    # missing required param -> should skip and return None
    assert tool_name is None
