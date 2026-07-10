"""Tool system: definitions, registry, and executor."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ToolDefinition:
    name: str
    description: str
    params_schema: Dict[str, Any] | None
    execute_fn: Callable[[Dict[str, Any]], Any]


class ToolRegistry:
    _default: "ToolRegistry" | None = None

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_all(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    @classmethod
    def get_default(cls) -> "ToolRegistry":
        if cls._default is None:
            cls._default = ToolRegistry()
        return cls._default


class ToolExecutor:
    def __init__(
        self, registry: ToolRegistry | None = None, max_workers: int = 4
    ) -> None:
        self.registry = registry or ToolRegistry.get_default()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def execute(
        self,
        tool_name: str,
        params: Dict[str, Any] | None = None,
        timeout_sec: int = 30,
    ) -> Dict[str, Any]:
        params = params or {}
        tool = self.registry.get(tool_name)
        if tool is None:
            return {
                "output": None,
                "status": "not_found",
                "error": f"tool {tool_name} not registered",
                "execution_time_ms": 0,
            }

        start = time.monotonic()
        future = self.executor.submit(tool.execute_fn, params)
        try:
            res = future.result(timeout=timeout_sec)
            elapsed = int((time.monotonic() - start) * 1000)
            return {
                "output": res,
                "status": "ok",
                "error": None,
                "execution_time_ms": elapsed,
            }
        except FuturesTimeout:
            future.cancel()
            elapsed = int((time.monotonic() - start) * 1000)
            return {
                "output": None,
                "status": "timeout",
                "error": "timeout",
                "execution_time_ms": elapsed,
            }
        except Exception as exc:  # pragma: no cover - runtime
            elapsed = int((time.monotonic() - start) * 1000)
            return {
                "output": None,
                "status": "error",
                "error": str(exc),
                "execution_time_ms": elapsed,
            }


__all__ = ["ToolDefinition", "ToolRegistry", "ToolExecutor"]
