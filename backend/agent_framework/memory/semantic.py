from __future__ import annotations

import time
import uuid
from typing import Dict, List

from .base import AbstractSemantic


class SemanticMemory(AbstractSemantic):
    def __init__(self) -> None:
        self._patterns: Dict[str, Dict] = {}

    def store(self, key: str, value) -> None:
        self._patterns[key] = value

    def retrieve(self, key: str):
        return self._patterns.get(key)

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        # naive search by substring match
        out = [v for v in self._patterns.values() if query.lower() in v.get("pattern", "").lower()]
        return out[:top_k]

    def store_pattern(self, category: str, pattern: str, confidence: float) -> None:
        pid = str(uuid.uuid4())
        self._patterns[pid] = {"pattern_id": pid, "category": category, "pattern": pattern, "confidence": float(confidence), "created_at": int(time.time())}

    def retrieve_patterns(self, category: str, min_confidence: float = 0.7) -> List[Dict]:
        now = int(time.time())
        # auto-clean: remove patterns older than 30 days with low confidence
        cutoff = now - 30 * 24 * 60 * 60
        to_delete = [k for k, v in self._patterns.items() if v.get("created_at", 0) < cutoff and v.get("confidence", 0) < min_confidence]
        for k in to_delete:
            del self._patterns[k]

        return [v for v in self._patterns.values() if v.get("category") == category and v.get("confidence", 0) >= min_confidence]


__all__ = ["SemanticMemory"]
