"""Layer 2: Perception and knowledge retrieval (mocked)."""

from __future__ import annotations

from typing import Any, Dict, List


class PerceptionEngine:
    @staticmethod
    def parse_query(query: str) -> Dict[str, Any]:
        """Very small mock parser that extracts intent and simple entities.

        This is a placeholder for an NLP parser.
        """
        text = (query or "").strip()
        intent = "unknown"
        entities: List[Dict[str, str]] = []

        if text.endswith("?"):
            intent = "question"
        elif text.lower().startswith("create"):
            intent = "create"

        # naive entity extraction: look for words starting with capital letter
        for tok in text.split():
            if tok.istitle():
                entities.append({"text": tok})

        return {"intent": intent, "entities": entities, "constraints": {}}


class KnowledgeRetriever:
    @staticmethod
    def retrieve(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Mock KB retriever — returns empty list for now.
        Replace with real vector DB / DB lookup later.
        """
        return []


class UnderstandingLayer:
    @staticmethod
    def understand(agent_input) -> Dict[str, Any]:
        parsed = PerceptionEngine.parse_query(agent_input.query)
        kb_results = KnowledgeRetriever.retrieve(agent_input.query)
        # confidence placeholder
        confidence = 0.5 if parsed.get("intent") != "unknown" else 0.2

        return {
            "parsed_query": parsed,
            "kb_results": kb_results,
            "confidence": confidence,
        }


__all__ = ["PerceptionEngine", "KnowledgeRetriever", "UnderstandingLayer"]
