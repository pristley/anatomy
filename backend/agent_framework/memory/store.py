"""Abstract memory store interface."""

from abc import ABC, abstractmethod
from typing import Any


class MemoryStore(ABC):
    """Base class for memory storage backends."""

    @abstractmethod
    async def store(self, key: str, value: Any) -> None:
        """Store value."""
        pass

    @abstractmethod
    async def retrieve(self, key: str) -> Any:
        """Retrieve value."""
        pass
