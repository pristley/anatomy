from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class AbstractMemory(ABC):
    @abstractmethod
    def store(self, key: str, value: Any) -> None:
        raise NotImplementedError()

    @abstractmethod
    def retrieve(self, key: str) -> Any:
        raise NotImplementedError()

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        raise NotImplementedError()


class AbstractEpisodic(AbstractMemory):
    @abstractmethod
    def store_experience(
        self, input: str, action: str, output: str, score: float | None = None
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    def retrieve_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        raise NotImplementedError()


class AbstractSemantic(AbstractMemory):
    @abstractmethod
    def store_pattern(self, category: str, pattern: str, confidence: float) -> None:
        raise NotImplementedError()

    @abstractmethod
    def retrieve_patterns(
        self, category: str, min_confidence: float = 0.7
    ) -> List[Dict[str, Any]]:
        raise NotImplementedError()


class AbstractRetriever(ABC):
    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        raise NotImplementedError()


__all__ = [
    "AbstractMemory",
    "AbstractEpisodic",
    "AbstractSemantic",
    "AbstractRetriever",
]
