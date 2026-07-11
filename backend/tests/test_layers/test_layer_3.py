"""Tests for Layer 3: Reasoning (LLM client integration)."""

import importlib.util
import sys
from pathlib import Path
import pytest
import asyncio


def _load_mod():
    backend_root = Path(__file__).resolve().parents[2]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))
    path = backend_root / "agent_framework" / "core" / "layers" / "03_reasoning.py"
    pkg = "agent_framework.core.layers"
    mod_name = f"{pkg}.03_reasoning"
    spec = importlib.util.spec_from_file_location(mod_name, str(path))
    mod = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    mod.__package__ = pkg
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


class DummyLLM:
    async def infer(self, system, user, max_tokens=0):
        return "simple reply"


class DummyLLM2:
    async def infer(self, system, user, max_tokens=0):
        return ("tuple reply", {"tokens_used": 3})


@pytest.mark.asyncio
async def test_reasoning_returns_text_and_metrics():
    mod = _load_mod()
    rc = mod.ReasoningCore(DummyLLM())
    out = await rc.reason({"parsed_query": {}, "kb_results": [], "confidence": 0.5})
    assert "reasoning_output" in out

    rc2 = mod.ReasoningCore(DummyLLM2())
    out2 = await rc2.reason({"parsed_query": {}, "kb_results": [], "confidence": 0.5})
    assert out2.get("reasoning_output") == "tuple reply"
    assert out2.get("tokens_used", 0) >= 0
