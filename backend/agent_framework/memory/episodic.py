"""Episodic memory: session history and past outcomes."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Dict


@dataclass
class Episode:
    """Single episode from memory."""
    query: str
    reasoning: str
    tasks: List[Dict[str, Any]]
    outcome: str  # success, partial, failure
    cost: float
    tokens_used: int
    timestamp: datetime


class EpisodicMemory:
    """Stores and retrieves session history."""

    def __init__(self):
        self.episodes: List[Episode] = []

    def store(self, episode: Episode) -> None:
        """Store an episode.

        TODO: Replace in-memory list with durable database storage.
        """
        self.episodes.append(episode)

    def retrieve(self, query: str, limit: int = 5) -> List[Episode]:
        """Retrieve similar episodes.

        TODO: Implement similarity search; currently returns most recent.
        """
        return list(self.episodes)[-limit:]

