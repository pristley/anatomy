"""Tests for Claude client in interfaces (mocked network)."""

import importlib.util
import sys
from pathlib import Path
import asyncio
import os


def _load_mod():
    backend_root = Path(__file__).resolve().parents[2]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))
    path = backend_root / "agent_framework" / "core" / "interfaces" / "claude_client.py"
    pkg = "agent_framework.core.interfaces"
    mod_name = f"{pkg}.claude_client"
    spec = importlib.util.spec_from_file_location(mod_name, str(path))
    mod = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    mod.__package__ = pkg
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_mocked_response_when_no_key():
    mod = _load_mod()
    # ensure env var not set
    os.environ.pop("CLAUDE_API_KEY", None)
    c = mod.ClaudeClient(api_key=None)

    res, metrics = asyncio.get_event_loop().run_until_complete(c.infer("sys", "user"))
    assert "mocked claude response" in res
    assert metrics["tokens_used"] > 0


def test_calls_httpx_when_key_present(monkeypatch):
    mod = _load_mod()
    async def fake_post(url, json, headers):
        class R:
            def raise_for_status(self):
                return None

            def json(self):
                return {"completion": "ok from api"}

        return R()

    class FakeClient:
        def __init__(self, timeout=30.0):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json, headers):
            return await fake_post(url, json, headers)

    monkeypatch.setenv("CLAUDE_API_KEY", "dummy")
    monkeypatch.setattr(mod, "httpx", mod.httpx)
    # patch AsyncClient to our FakeClient
    monkeypatch.setattr(mod.httpx, "AsyncClient", lambda timeout=30.0: FakeClient())

    c = mod.ClaudeClient(api_key="dummy")
    res, metrics = asyncio.get_event_loop().run_until_complete(c.infer("s", "u"))
    assert "ok from api" in res
