import time

from agent_framework.tools.base import ToolDefinition, ToolRegistry, ToolExecutor


def test_tool_registry_and_executor():
    def echo(params):
        return {"echo": params}

    reg = ToolRegistry()
    td = ToolDefinition(
        name="echo", description="echo", params_schema=None, execute_fn=echo
    )
    reg.register(td)
    assert reg.get("echo") is td

    exec = ToolExecutor(registry=reg, max_workers=2)
    out = exec.execute("echo", {"a": 1})
    assert out["status"] == "ok"
    assert out["output"]["echo"]["a"] == 1


def test_tool_not_found():
    exec = ToolExecutor(registry=ToolRegistry())
    out = exec.execute("missing")
    assert out["status"] == "not_found"


def test_tool_timeout_and_error():
    def long_running(_: dict):
        time.sleep(0.2)
        return "done"

    def raises(_: dict):
        raise ValueError("fail")

    reg = ToolRegistry()
    reg.register(ToolDefinition("slow", "slow", None, long_running))
    reg.register(ToolDefinition("bad", "bad", None, raises))
    exec = ToolExecutor(registry=reg, max_workers=2)

    out = exec.execute("slow", timeout_sec=0)
    assert out["status"] in ("timeout", "error")

    out2 = exec.execute("bad")
    assert out2["status"] == "error"
