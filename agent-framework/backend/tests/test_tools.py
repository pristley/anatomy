import time
import pytest

from agent_framework.tools.base import ToolDefinition, ToolRegistry, ToolExecutor
from agent_framework.tools.validator import SchemaValidator


def test_tool_registry_registers():
    reg = ToolRegistry()

    def fn(p):
        return p

    td = ToolDefinition(name="echo", description="echo", params_schema=None, execute_fn=fn)
    reg.register(td)
    got = reg.get("echo")
    assert got is not None and got.name == "echo"


def test_tool_executor_runs_tool():
    reg = ToolRegistry()

    def add(params):
        return params.get("a", 0) + params.get("b", 0)

    td = ToolDefinition(name="add", description="add", params_schema=None, execute_fn=add)
    reg.register(td)
    exec = ToolExecutor(registry=reg)
    r = exec.execute("add", {"a": 2, "b": 3}, timeout_sec=1)
    assert r["status"] == "ok"
    assert r["output"] == 5


def test_tool_executor_timeout():
    reg = ToolRegistry()

    def slow(params):
        time.sleep(2)
        return "done"

    td = ToolDefinition(name="slow", description="slow", params_schema=None, execute_fn=slow)
    reg.register(td)
    exec = ToolExecutor(registry=reg)
    r = exec.execute("slow", {}, timeout_sec=0.5)
    assert r["status"] == "timeout"


def test_schema_validator_validates():
    schema = {"q": {"type": str, "required": True}}
    valid, errors, sanitized = SchemaValidator.validate_params({"q": "hello"}, schema)
    assert valid and not errors


def test_tool_prevents_injection():
    schema = {"sql": {"type": str, "required": True}}
    params = {"sql": "SELECT * FROM users; DROP TABLE users;"}
    valid, errors, sanitized = SchemaValidator.validate_params(params, schema)
    assert not valid or any("unsafe" in e for e in errors) or sanitized.get("sql") != params["sql"]
