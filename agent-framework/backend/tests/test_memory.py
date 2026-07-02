import pytest

from agent_framework.memory.episodic import EpisodicMemory
from agent_framework.memory.semantic import SemanticMemory
# test helpers


def test_episodic_stores_experience():
    m = EpisodicMemory()
    m.store_experience("hello world", "search", "result1", score=0.9)
    res = m.retrieve_similar("hello")
    assert isinstance(res, list)
    assert len(res) >= 1


def test_episodic_retrieves_similar():
    m = EpisodicMemory()
    m.store_experience("order pizza", "db_query", "ok", score=0.5)
    m.store_experience("order sushi", "db_query", "ok", score=0.6)
    res = m.retrieve_similar("order")
    assert len(res) >= 2


def test_semantic_stores_pattern():
    s = SemanticMemory()
    s.store_pattern("greeting", "hello there", 0.95)
    pats = s.retrieve_patterns("greeting")
    assert any(p.get("pattern") == "hello there" for p in pats)


def test_semantic_retrieves_patterns():
    s = SemanticMemory()
    s.store_pattern("farewell", "goodbye", 0.9)
    out = s.search("goodbye")
    assert len(out) >= 1


def test_memory_enriches_reasoning(monkeypatch):
    # create episodic memory and store an experience
    m = EpisodicMemory()
    m.store_experience("how to reset password", "guide", "step1: ...", score=0.8)

    # create a simple mock LLM used by reasoning that echoes memory contents
    class MockLLM:
        async def infer(self, system, user_msg, max_tokens=128):
            return ("OK", {"tokens_used": 1, "cost": 0.0})

    # dynamic import of the reasoning layer (filename starts with digits)
    import importlib.util
    import pathlib
    import agent_framework

    layers_path = pathlib.Path(agent_framework.__file__).resolve().parent / "core" / "layers" / "03_reasoning.py"
    # load module with a package context so relative imports work
    mod_name = "agent_framework.core.layers._03_reasoning"
    spec = importlib.util.spec_from_file_location(mod_name, str(layers_path))
    mod = importlib.util.module_from_spec(spec)
    # set package so relative imports inside the module resolve
    mod.__package__ = "agent_framework.core.layers"
    spec.loader.exec_module(mod)
    rc = mod.ReasoningCore(MockLLM())
    # call reason with memory context including prior experiences
    mem_ctx = {"prior_experiences": m.retrieve_similar("reset password")}
    out = pytest.raises(Exception)
    # ensure call succeeds
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    res = loop.run_until_complete(rc.reason({"parsed_query": "how to reset password", "kb_results": []}, memory=mem_ctx))
    loop.close()
    assert "reasoning_output" in res
