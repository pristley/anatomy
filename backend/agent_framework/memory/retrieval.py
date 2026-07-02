from __future__ import annotations

import math
from typing import Dict, List


class Embeddings:
    def embed(self, text: str) -> List[float]:
        raise NotImplementedError()


class SimpleEmbeddings(Embeddings):
    def embed(self, text: str) -> List[float]:
        # deterministic mock embedding: map chars to small vector
        v = [float((ord(c) % 23) - 11) for c in text[:128]]
        # pad/truncate to length 32
        if len(v) < 32:
            v += [0.0] * (32 - len(v))
        return v[:32]


def _dot(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _norm(a: List[float]) -> float:
    return math.sqrt(sum(x * x for x in a))


def cosine_similarity(a: List[float], b: List[float]) -> float:
    na = _norm(a)
    nb = _norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(_dot(a, b) / (na * nb))


class Retriever:
    def __init__(self, emb: Embeddings) -> None:
        self.emb = emb

    def retrieve(self, query: str, docs: List[Dict], top_k: int = 5) -> List[Dict]:
        qv = self.emb.embed(query)
        scored = []
        for d in docs:
            dv = d.get("embedding") or self.emb.embed(d.get("input", ""))
            score = cosine_similarity(qv, dv)
            scored.append({"id": d.get("id"), "text": d.get("input") or d.get("output"), "score": score, "metadata": d})

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]


__all__ = ["Embeddings", "SimpleEmbeddings", "Retriever", "cosine_similarity"]
