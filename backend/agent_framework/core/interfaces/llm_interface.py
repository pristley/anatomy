"""Abstract LLM client interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Tuple


class LLMClient(ABC):
    """Abstract language model client.

    Implementations should return a tuple of (text, metrics).
    Metrics is a dict containing at least `tokens_used` and optionally `cost` and `latency_ms`.
    """

    @abstractmethod
    async def infer(
        self, system_prompt: str, user_msg: str, max_tokens: int = 512
    ) -> Tuple[str, Dict]:
        raise NotImplementedError()


__all__ = ["LLMClient"]
