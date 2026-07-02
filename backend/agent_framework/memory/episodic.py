from __future__ import annotations

import time
import uuid
from typing import Dict, List

from .base import AbstractEpisodic
from .retrieval import SimpleEmbeddings, Retriever


class EpisodicMemory(AbstractEpisodic):
    def __init__(self) -> None:
        self._store: Dict[str, Dict] = {}
        self._emb = SimpleEmbeddings()
        self._retriever = Retriever(self._emb)

    def store(self, key: str, value) -> None:
        self._store[key] = value

    def retrieve(self, key: str):
        return self._store.get(key)

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        return self.retrieve_similar(query, top_k)

    def store_experience(self, input: str, action: str, output: str, score: float | None = None) -> None:
        eid = str(uuid.uuid4())
        embedding = self._emb.embed(input)
        self._store[eid] = {"timestamp": int(time.time()), "input": input, "action": action, "output": output, "score": score or 0.0, "embedding": embedding}

    def retrieve_similar(self, query: str, top_k: int = 5) -> List[Dict]:
        docs = [{"id": k, **v} for k, v in self._store.items()]
        return self._retriever.retrieve(query, docs, top_k=top_k)


__all__ = ["EpisodicMemory"]
