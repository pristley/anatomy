"""Tests for Layer 2: Understanding."""

import importlib.util
import sys
from pathlib import Path
import pytest


def _load_mod():
    backend_root = Path(__file__).resolve().parents[2]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))
    path = backend_root / "agent_framework" / "core" / "layers" / "02_understanding.py"
    pkg = "agent_framework.core.layers"
    mod_name = f"{pkg}.02_understanding"
    spec = importlib.util.spec_from_file_location(mod_name, str(path))
    mod = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    mod.__package__ = pkg
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_parse_query_and_understand():
    mod = _load_mod()
    pe = mod.PerceptionEngine
    parsed = pe.parse_query("What is Python?")
    assert parsed["intent"] == "question"

    # UnderstandingLayer uses AgentInput model; construct minimal object
    from agent_framework.core.types import AgentInput

    ai = AgentInput(query="What is Python?", user_id="u1")
    ul = mod.UnderstandingLayer()
    out = ul.understand(ai)
    assert "parsed_query" in out
    assert isinstance(out.get("kb_results"), list)


def test_knowledge_retriever_returns_empty():
    mod = _load_mod()
    kr = mod.KnowledgeRetriever
    res = kr.retrieve("anything")
    assert isinstance(res, list)
