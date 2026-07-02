import os
import time
from typing import Optional
import httpx

from .llm_interface import LLMClient


class ClaudeClient(LLMClient):
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key or os.getenv("CLAUDE_API_KEY")
        self.model = model

    async def infer(self, system_prompt: str, user_message: str, max_tokens: int = 1024) -> str:
        # If no API key, return a mock response for local testing
        start = time.time()
        if not self.api_key:
            await self._async_sleep(0.01)
            return f"[mocked claude response] {user_message}"

        # Basic httpx call structure (user must configure real endpoint)
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "prompt": system_prompt + "\n" + user_message,
            "max_tokens": max_tokens,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post("https://api.anthropic.example/v1/complete", json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                # assume API returns {'text': '...'}
                return data.get("text", "")
            except Exception:
                return ""

    async def _async_sleep(self, delay: float):
        # small helper to allow await
        import asyncio

        await asyncio.sleep(delay)
