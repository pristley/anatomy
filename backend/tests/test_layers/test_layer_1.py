"""Tests for Layer 1: Input Processing."""

import importlib.util
import sys
from pathlib import Path
import pytest


def _load_mod():
    backend_root = Path(__file__).resolve().parents[2]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))
    path = backend_root / "agent_framework" / "core" / "layers" / "01_input.py"
    pkg = "agent_framework.core.layers"
    mod_name = f"{pkg}.01_input"
    spec = importlib.util.spec_from_file_location(mod_name, str(path))
    mod = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    mod.__package__ = pkg
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_process_simple_query():
    mod = _load_mod()
    layer = mod.InputLayer()
    res = layer.process("What is 2+2?", user_id="u1")
    assert res is not None
    assert hasattr(res, "query")
    assert res.user_id == "u1"


def test_process_empty_query_raises():
    mod = _load_mod()
    layer = mod.InputLayer()
    with pytest.raises(ValueError):
        layer.process("  ", user_id="u1")


def test_process_long_and_special_chars():
    mod = _load_mod()
    layer = mod.InputLayer()
    long_q = "x" * 5000 + " @#$%^&*()"
    res = layer.process(long_q, user_id="u2")
    assert res.query.startswith("x")
    assert res.user_id == "u2"
