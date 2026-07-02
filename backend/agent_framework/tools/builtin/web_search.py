"""Mock web search tool."""
from __future__ import annotations

from typing import List, Dict


def search(query: str) -> List[Dict[str, str]]:
    # simple hardcoded mock results
    return [
        {"title": "Example result 1", "url": "https://example.com/1", "snippet": f"Result for {query} - 1"},
        {"title": "Example result 2", "url": "https://example.com/2", "snippet": f"Result for {query} - 2"},
    ]


__all__ = ["search"]
