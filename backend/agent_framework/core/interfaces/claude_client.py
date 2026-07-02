"""Claude LLM client implementation (minimal)."""
from __future__ import annotations

import os
import time
from typing import Dict, Tuple

import httpx

from .llm_interface import LLMClient


class ClaudeClient(LLMClient):
    def __init__(self, api_key: str | None = None, model: str = "claude-3-5-sonnet-20241022") -> None:
        self.api_key = api_key or os.getenv("CLAUDE_API_KEY")
        self.model = model

    async def infer(self, system_prompt: str, user_msg: str, max_tokens: int = 512) -> Tuple[str, Dict]:
        metrics: Dict = {"tokens_used": 0, "cost": 0.0, "latency_ms": 0}
        start = time.monotonic()

        if not self.api_key:
            # Return a mocked response when API key is not available
            text = f"[mocked claude response] system: {system_prompt[:80]} user: {user_msg[:80]}"
            metrics["tokens_used"] = len(text.split())
            metrics["latency_ms"] = int((time.monotonic() - start) * 1000)
            return text, metrics

        # Example: call Anthropic/Claude-style API; endpoint may vary by provider.
        url = os.getenv("CLAUDE_API_URL", "https://api.anthropic.com/v1/complete")
        headers = {"x-api-key": self.api_key, "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "prompt": system_prompt + "\n" + user_msg,
            "max_tokens_to_sample": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()

                # Attempt to extract text (best-effort; providers differ)
                text = data.get("completion") or data.get("text") or ""

                metrics["tokens_used"] = len(text.split())
                metrics["latency_ms"] = int((time.monotonic() - start) * 1000)
                # cost estimation is not implemented here
                return text, metrics
        except Exception as exc:  # pragma: no cover - network/error handling
            latency = int((time.monotonic() - start) * 1000)
            return f"[error calling Claude API] {exc}", {"tokens_used": 0, "cost": 0.0, "latency_ms": latency}


__all__ = ["ClaudeClient"]
