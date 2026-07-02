"""Layer 7: Execution engine (tool invocation)."""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from typing import Any

from ...tools.registry import ToolRegistry


class ExecutionEngine:
    def __init__(self, registry: ToolRegistry | None = None, max_workers: int = 4) -> None:
        self.registry = registry or ToolRegistry.get_default()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def execute(self, tool_name: str, params: dict | None = None, timeout: int = 30) -> dict[str, Any]:
        params = params or {}
        tool = self.registry.get(tool_name)
        if tool is None:
            return {"output": None, "status": "not_found", "time_ms": 0}

        start = time.monotonic()
        future = self.executor.submit(tool.handler, params)
        try:
            result = future.result(timeout=timeout)
            elapsed = int((time.monotonic() - start) * 1000)
            return {"output": result, "status": "ok", "time_ms": elapsed}
        except FuturesTimeout:
            future.cancel()
            elapsed = int((time.monotonic() - start) * 1000)
            return {"output": None, "status": "timeout", "time_ms": elapsed}
        except Exception as exc:  # pragma: no cover - runtime error cases
            elapsed = int((time.monotonic() - start) * 1000)
            return {"output": str(exc), "status": "error", "time_ms": elapsed}


__all__ = ["ExecutionEngine"]
