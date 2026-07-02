"""Tool registry and built-in tools."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Tool:
    name: str
    description: str
    params_schema: Dict[str, Any] | None
    handler: Callable[[Dict[str, Any]], Any]


class ToolRegistry:
    _default: "ToolRegistry" | None = None

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_all(self) -> List[Tool]:
        return list(self._tools.values())

    @classmethod
    def get_default(cls) -> "ToolRegistry":
        if cls._default is None:
            cls._default = ToolRegistry()
            _register_builtins(cls._default)
        return cls._default


def _register_builtins(reg: ToolRegistry) -> None:
    def print_text(params: Dict[str, Any]) -> str:
        text = params.get("text", "")
        print(text)
        return text

    def add_numbers(params: Dict[str, Any]) -> float:
        nums = params.get("numbers", [])
        return float(sum(nums))

    def return_string(params: Dict[str, Any]) -> str:
        return params.get("value", "")

    reg.register(Tool(name="print_text", description="Print text to stdout", params_schema={"text": "str"}, handler=print_text))
    reg.register(Tool(name="add_numbers", description="Add a list of numbers", params_schema={"numbers": "List[float]"}, handler=add_numbers))
    reg.register(Tool(name="return_string", description="Return the given string", params_schema={"value": "str"}, handler=return_string))


__all__ = ["Tool", "ToolRegistry"]
