"""Abstract memory store interface."""

from abc import ABC, abstractmethod
from typing import Any


def create_engine_with_pool(database_url: str, **kwargs):
    """Create a SQLAlchemy engine with a QueuePool if SQLAlchemy is installed.

    This helper is optional; it will raise ImportError if SQLAlchemy is not
    available. Use it to enable connection pooling for durable memory stores.
    """
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.pool import QueuePool
    except Exception as exc:  # pragma: no cover - optional dependency
        raise ImportError("SQLAlchemy is required for create_engine_with_pool") from exc

    engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=kwargs.get("pool_size", 10),
        max_overflow=kwargs.get("max_overflow", 20),
        pool_pre_ping=kwargs.get("pool_pre_ping", True),
    )
    return engine


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
