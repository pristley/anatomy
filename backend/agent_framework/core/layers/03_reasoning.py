"""Layer 3: Reasoning core that uses an LLM client."""
from __future__ import annotations

import os
import time
from typing import Any, Dict

from ..interfaces.llm_interface import LLMClient


class ReasoningCore:
    def __init__(self, llm_client: LLMClient) -> None:
        self.llm = llm_client

    async def reason(self, understanding: Dict[str, Any], memory: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Run reasoning by calling the LLM client and returning output + metrics."""
        system_prompt = os.getenv("REASONER_SYSTEM_PROMPT", "You are agent reasoning engine. Answer concisely.")
        user_msg = f"Parsed: {understanding.get('parsed_query')}\nKB: {understanding.get('kb_results')}\nConfidence: {understanding.get('confidence')}"
        max_tokens = int(os.getenv("MAX_TOKENS_PER_REQUEST", "512"))

        start = time.monotonic()
        result = await self.llm.infer(system_prompt, user_msg, max_tokens=max_tokens)
        # support clients that return either (text, metrics) or just text
        if isinstance(result, tuple) and len(result) == 2:
            text, metrics = result
        else:
            text = result
            metrics = {}

        latency_ms = int((time.monotonic() - start) * 1000)
        metrics.setdefault("latency_ms", latency_ms)

        return {"reasoning_output": text, **metrics}


__all__ = ["ReasoningCore"]
