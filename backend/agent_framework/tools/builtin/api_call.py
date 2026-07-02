"""Mock API call tool."""
from __future__ import annotations

from typing import Any, Dict


def call_api(method: str, url: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {"status": 200, "method": method, "url": url, "params": params or {}, "body": {"mock": True}}


__all__ = ["call_api"]
