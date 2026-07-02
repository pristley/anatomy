from abc import ABC, abstractmethod
from typing import Optional


class LLMClient(ABC):
    @abstractmethod
    async def infer(self, system_prompt: str, user_message: str, max_tokens: int = 1024) -> str:
        """Infer from the configured LLM and return text output."""
        raise NotImplementedError


class SyncLLMAdapter(LLMClient):
    """Compatibility shim: implement sync infer via asyncio.run if needed."""
    def __init__(self, async_client: LLMClient):
        self._async = async_client

    async def infer(self, system_prompt: str, user_message: str, max_tokens: int = 1024) -> str:
        return await self._async.infer(system_prompt, user_message, max_tokens)
