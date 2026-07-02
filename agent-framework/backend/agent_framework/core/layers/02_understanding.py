from typing import Dict, List, Any
from datetime import datetime


class PerceptionEngine:
    def parse_query(self, query: str) -> Dict[str, Any]:
        # very small heuristic parser
        tokens = query.lower().split()
        intent = "unknown"
        if tokens and tokens[0] in ("get", "list", "what", "who"):
            intent = "retrieve"
        elif "calculate" in tokens or any(t.isdigit() for t in tokens):
            intent = "compute"

        entities = []
        return {"intent": intent, "entities": entities, "raw": query, "parsed_at": datetime.utcnow()}


class KnowledgeRetriever:
    def __init__(self):
        # mock KB for Phase 1
        self.kb = []

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        # return empty list or simple mock results
        return []


class UnderstandingLayer:
    def __init__(self):
        self.perceptor = PerceptionEngine()
        self.retriever = KnowledgeRetriever()

    def understand(self, agent_input) -> Dict[str, Any]:
        parsed = self.perceptor.parse_query(agent_input.query)
        kb = self.retriever.retrieve(agent_input.query)
        return {"parsed_query": parsed, "kb_results": kb, "timestamp": datetime.utcnow()}
