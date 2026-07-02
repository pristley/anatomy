from typing import List, Any


class SemanticMemory:
    def __init__(self):
        self._items = []

    def index(self, key: str, value: Any):
        self._items.append({"key": key, "value": value})

    def search(self, query: str, limit: int = 5) -> List[Any]:
        return [i for i in self._items if query in i.get("key", "")][:limit]


__all__ = ["SemanticMemory"]
