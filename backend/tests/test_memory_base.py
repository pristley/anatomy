import pytest

from agent_framework.memory.base import (
    AbstractMemory,
    AbstractEpisodic,
    AbstractSemantic,
    AbstractRetriever,
)


def test_abstract_classes_require_implementation():
    with pytest.raises(TypeError):
        AbstractMemory()


class DummyMemory(AbstractMemory):
    def __init__(self):
        self._store = {}

    def store(self, key: str, value):
        self._store[key] = value

    def retrieve(self, key: str):
        return self._store.get(key)

    def search(self, query: str, top_k: int = 5):
        return [{"k": k, "v": v} for k, v in self._store.items() if query in str(v)]


def test_dummy_memory():
    d = DummyMemory()
    d.store("a", "apple")
    assert d.retrieve("a") == "apple"
    assert d.search("app")
