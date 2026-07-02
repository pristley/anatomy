import importlib
import asyncio


def test_full_agent_cycle(monkeypatch):
    # import Agent dynamically
    agent_mod = importlib.import_module("agent_framework.core.agent")
    # mock ClaudeClient to return deterministic response
    claude_mod = importlib.import_module("agent_framework.core.interfaces.claude_client")

    class MockClaude:
        async def infer(self, s, u, max_tokens=0):
            return "Step 1: The answer is 4"

    monkeypatch.setattr(claude_mod, "ClaudeClient", lambda *a, **k: MockClaude())

    Agent = agent_mod.Agent
    agent = Agent()
    res = agent.run("What is 2+2?", "test_user")
    assert res.get("success") is True
    assert res.get("output") is not None
    assert res.get("metrics") and res["metrics"]["duration_ms"] >= 0