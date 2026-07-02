from typing import List, Any


class SemanticMemory:
    def __init__(self):
        self._patterns = []  # list of dicts: {namespace, pattern, score}

    def store_pattern(self, namespace: str, pattern: str, score: float = 1.0):
        self._patterns.append({"namespace": namespace, "pattern": pattern, "score": float(score)})

    def retrieve_patterns(self, namespace: str) -> List[dict]:
        return [p for p in self._patterns if p.get("namespace") == namespace]

    def retrieve_similar(self, query: str, limit: int = 5) -> List[Any]:
        return [p for p in self._patterns if query in p.get("pattern", "")][:limit]

    def search(self, query: str, limit: int = 5) -> List[Any]:
        return self.retrieve_similar(query, limit=limit)


__all__ = ["SemanticMemory"]
