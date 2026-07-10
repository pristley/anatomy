import re

from agent_framework.tools.validator import SchemaValidator


def test_is_safe_string():
    assert SchemaValidator._is_safe_string("hello world")
    assert not SchemaValidator._is_safe_string("rm -rf /;")


def test_validate_params_basic():
    valid, errors, sanitized = SchemaValidator.validate_params({"a": 1}, None)
    assert valid and not errors


def test_validate_params_required_and_type():
    schema = {"x": {"required": True, "type": int}, "y": float}
    valid, errors, sanitized = SchemaValidator.validate_params({"y": 2}, schema)
    assert not valid
    assert any("missing required x" in e for e in errors)

    valid2, errors2, san2 = SchemaValidator.validate_params({"y": 2}, {"y": float})
    assert valid2
    assert isinstance(san2["y"], float)


def test_validate_params_unsafe_string():
    schema = {"cmd": str}
    val = {"cmd": "rm -rf /; echo hi;"}
    valid, errors, sanitized = SchemaValidator.validate_params(val, schema)
    assert not valid
    assert "unsafe value" in errors[0] or any("unsafe" in e for e in errors)
    assert ";" not in sanitized["cmd"]
