from typing import List, Any


class EpisodicMemory:
    def __init__(self):
        self._store = []

    def store_experience(self, query: str, action: str, result: str, score: float = 1.0):
        self._store.append({"query": query, "action": action, "result": result, "score": score})

    def retrieve_similar(self, query: str, limit: int = 5) -> List[Any]:
        # naive substring match
        return [s for s in self._store if query in s.get("query", "")][:limit]


__all__ = ["EpisodicMemory"]
