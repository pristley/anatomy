import time
from typing import Dict, Any
from ..interfaces.llm_interface import LLMClient


class ReasoningCore:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def reason(self, understanding: Dict[str, Any], memory: Dict[str, Any] = None, max_tokens: int = 512) -> Dict[str, Any]:
        system_prompt = "You are an agent reasoning engine. Be concise and return steps."
        user_msg = f"Understanding: {understanding}\nMemory: {memory or {}}"
        t0 = time.time()
        res = await self.llm.infer(system_prompt, user_msg, max_tokens=max_tokens)
        t1 = time.time()
        # support LLMs that return either a plain string or a (text, meta) tuple
        text = None
        meta = None
        if isinstance(res, tuple) and len(res) >= 1:
            text = res[0]
            if len(res) > 1:
                meta = res[1]
        else:
            text = res

        tokens_used = None
        if isinstance(meta, dict) and "tokens_used" in meta:
            tokens_used = int(meta.get("tokens_used", 0))
        else:
            tokens_used = len(text.split()) if text else 0

        return {"reasoning_output": text, "tokens_used": tokens_used, "latency_ms": int((t1 - t0) * 1000)}
