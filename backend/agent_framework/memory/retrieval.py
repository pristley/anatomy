from __future__ import annotations

import asyncio
import math
import time
import hashlib
import random
from typing import Any, Dict, List, Optional, Sequence
import os
import httpx


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


class SimpleEmbeddings:
    """Deterministic, lightweight embedding generator for testing and local use.

    Produces a fixed-dimension vector derived from a hash of the input text.
    Provides both sync `embed` and async `aembed` for compatibility.
    """

    def __init__(self, dim: int = 128):
        self.dim = dim

    def embed(self, text: str) -> List[float]:
        h = hashlib.sha256(text.encode("utf-8")).digest()
        out: List[float] = []
        for i in range(self.dim):
            byte = h[i % len(h)]
            out.append(((byte / 255.0) * 2.0) - 1.0)
        return out

    async def aembed(self, text: str) -> List[float]:
        # mimic async latency
        await asyncio.sleep(0)
        return self.embed(text)


class OpenAIEmbeddings:
    """Async OpenAI embeddings client using `httpx`. Requires `OPENAI_API_KEY` env var or api_key param."""

    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-3-small", base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"

    async def aembed(self, text: str) -> List[float]:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY not configured")
        url = f"{self.base_url}/embeddings"
        payload = {"model": self.model, "input": text}
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]

    def embed(self, text: str) -> List[float]:
        # synchronous wrapper
        return asyncio.get_event_loop().run_until_complete(self.aembed(text))


def _is_coroutine_fn(fn: Any) -> bool:
    return asyncio.iscoroutinefunction(fn)


def _retry_backoff(max_retries: int = 3, base_delay: float = 0.05):
    def deco(fn):
        async def wrapper(*args, **kwargs):
            attempt = 0
            while True:
                try:
                    return await fn(*args, **kwargs)
                except Exception as exc:
                    attempt += 1
                    if attempt > max_retries:
                        raise
                    await asyncio.sleep(base_delay * (2 ** (attempt - 1)) + random.random() * 0.01)

        return wrapper

    return deco


class Retriever:
    """Simple synchronous retriever used by in-memory episodic stores.

    Expects documents as list of dicts with `embedding` field (list of floats) and optional `id`.
    """

    def __init__(self, embedding_model: SimpleEmbeddings):
        self.embedding_model = embedding_model

    def retrieve(self, query: str, docs: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        q_emb = self.embedding_model.embed(query)
        scored = []
        for d in docs:
            emb = d.get("embedding")
            if not emb:
                # fallback to exact match
                score = 1.0 if query.lower() in d.get("input", "").lower() else 0.0
            else:
                score = _cosine(q_emb, emb)
            scored.append({"doc": d, "score": float(score)})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return [{**s["doc"], "similarity_score": s["score"]} for s in scored[:top_k]]


class SemanticRetrieval:
    """Async semantic retrieval interface backed by a simple in-memory backend.

    Backend should expose a mapping of id -> dict at attribute `_store` (legacy) or
    implement `list_entries()` and `store_entry(entry)` async methods. This class
    is intentionally lightweight for local development and tests.
    """

    def __init__(
        self,
        embedding_model: Optional[Any] = None,
        backend: Optional[Any] = None,
        similarity_threshold: float = 0.7,
        embedding_batch_size: int = 32,
        cache_embeddings: bool = False,
        cache_ttl: int = 3600,
    ) -> None:
        # prefer a real provider when configured
        if embedding_model:
            self.embedding_model = embedding_model
        else:
            if os.getenv("OPENAI_API_KEY"):
                self.embedding_model = OpenAIEmbeddings()
            else:
                self.embedding_model = SimpleEmbeddings()
        self.backend = backend
        self.similarity_threshold = similarity_threshold
        self.embedding_batch_size = embedding_batch_size
        self.cache_embeddings = cache_embeddings
        self.cache_ttl = cache_ttl
        self._embed_cache: Dict[str, Dict[str, Any]] = {}

    async def _embed(self, text: str) -> List[float]:
        # Support both sync and async embedding models
        if hasattr(self.embedding_model, "aembed") and _is_coroutine_fn(getattr(self.embedding_model, "aembed")):
            return await self.embedding_model.aembed(text)
        if _is_coroutine_fn(getattr(self.embedding_model, "embed", None)):
            return await self.embedding_model.embed(text)
        # sync call
        return self.embedding_model.embed(text)

    @_retry_backoff()
    async def store_memory(self, memory_entry: Dict[str, Any], embedding: Optional[List[float]] = None) -> Dict[str, Any]:
        if not embedding:
            try:
                embedding = await self._embed(memory_entry.get("content") or memory_entry.get("input", ""))
            except Exception:
                embedding = None

        entry = dict(memory_entry)
        entry["embedding"] = embedding
        entry.setdefault("timestamp", int(time.time()))

        # store using backend api if available
        if self.backend is None:
            # fallback: keep local store
            if not hasattr(self, "_local_store"):
                self._local_store = {}
            eid = entry.get("id") or str(hashlib.sha256(str(time.time()).encode()).hexdigest())
            entry["id"] = eid
            self._local_store[eid] = entry
            return entry

        # if backend exposes async store_entry
        if hasattr(self.backend, "store_entry") and _is_coroutine_fn(getattr(self.backend, "store_entry")):
            return await self.backend.store_entry(entry)

        # sync store interface
        if hasattr(self.backend, "store"):
            try:
                self.backend.store(entry.get("id") or str(time.time()), entry)
                return entry
            except Exception:
                raise

        # fallback attempt to set into _store mapping
        if hasattr(self.backend, "_store"):
            eid = entry.get("id") or str(time.time())
            entry["id"] = eid
            self.backend._store[eid] = entry
            return entry

        raise RuntimeError("Backend does not support store operations")

    async def retrieve_similar(self, query: str, agent_id: Optional[str] = None, top_k: int = 5, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        if threshold is None:
            threshold = self.similarity_threshold
        if not query:
            return []

        try:
            q_emb = await self._embed(query)
        except Exception:
            q_emb = None

        # gather entries
        entries: List[Dict[str, Any]] = []
        if self.backend is None:
            entries = list(getattr(self, "_local_store", {}).values())
        elif hasattr(self.backend, "list_entries") and _is_coroutine_fn(getattr(self.backend, "list_entries")):
            entries = await self.backend.list_entries()
        elif hasattr(self.backend, "_store"):
            entries = [dict(v, id=k) for k, v in self.backend._store.items()]
        else:
            # try to call sync list_entries
            if hasattr(self.backend, "list_entries"):
                entries = self.backend.list_entries()

        scored: List[Dict[str, Any]] = []
        for e in entries:
            if agent_id and e.get("agent_id") != agent_id:
                continue
            emb = e.get("embedding")
            if q_emb is None or emb is None:
                # fallback to substring match
                score = 1.0 if query.lower() in (e.get("content") or e.get("input", "")).lower() else 0.0
            else:
                score = _cosine(q_emb, emb)
            if score >= threshold:
                scored.append({"entry": e, "score": float(score)})

        scored.sort(key=lambda x: x["score"], reverse=True)
        out = []
        for item in scored[:top_k]:
            ent = dict(item["entry"])
            ent["similarity_score"] = item["score"]
            out.append(ent)
        return out

    async def retrieve_by_metadata(self, agent_id: Optional[str], filters: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        # Support filters: tags (subset), start_ts, end_ts
        entries = []
        if self.backend and hasattr(self.backend, "_store"):
            entries = list(self.backend._store.values())
        else:
            entries = list(getattr(self, "_local_store", {}).values())

        def match(e: Dict[str, Any]) -> bool:
            if agent_id and e.get("agent_id") != agent_id:
                return False
            tags = filters.get("tags")
            if tags:
                etags = set(e.get("metadata", {}).get("tags", []))
                if not set(tags).issubset(etags):
                    return False
            start = filters.get("start_ts")
            end = filters.get("end_ts")
            ts = e.get("timestamp", 0)
            if start and ts < start:
                return False
            if end and ts > end:
                return False
            return True

        matched = [e for e in entries if match(e)]
        matched.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        return matched[:limit]

    async def retrieve_recent(self, agent_id: Optional[str], limit: int = 10) -> List[Dict[str, Any]]:
        entries = []
        if self.backend and hasattr(self.backend, "_store"):
            entries = list(self.backend._store.values())
        else:
            entries = list(getattr(self, "_local_store", {}).values())
        if agent_id:
            entries = [e for e in entries if e.get("agent_id") == agent_id]
        entries.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        return entries[:limit]

    async def batch_retrieve(self, queries: List[str], agent_id: Optional[str], top_k: int = 5) -> Dict[int, List[Dict[str, Any]]]:
        # Batch embedding generation
        q_embs = []
        for q in queries:
            try:
                q_embs.append(await self._embed(q))
            except Exception:
                q_embs.append(None)

        # gather entries once
        entries = list(getattr(self.backend, "_store", {}).values()) if self.backend and hasattr(self.backend, "_store") else list(getattr(self, "_local_store", {}).values())

        results: Dict[int, List[Dict[str, Any]]] = {}
        for idx, q in enumerate(queries):
            q_emb = q_embs[idx]
            scored = []
            for e in entries:
                if agent_id and e.get("agent_id") != agent_id:
                    continue
                emb = e.get("embedding")
                if q_emb is None or emb is None:
                    score = 1.0 if q.lower() in (e.get("content") or e.get("input", "")).lower() else 0.0
                else:
                    score = _cosine(q_emb, emb)
                scored.append({"entry": e, "score": float(score)})
            scored.sort(key=lambda x: x["score"], reverse=True)
            results[idx] = [dict(item["entry"], similarity_score=item["score"]) for item in scored[:top_k]]

        return results


__all__ = ["SimpleEmbeddings", "Retriever", "SemanticRetrieval"]
from typing import List, Dict, Any, Optional
import asyncio
import math


class MemoryEntry:
    def __init__(self, id: str, content: str, embedding: Optional[List[float]] = None, metadata: Optional[Dict[str, Any]] = None):
        self.id = id
        self.content = content
        self.embedding = embedding
        self.metadata = metadata or {}


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norma = math.sqrt(sum(x * x for x in a))
    normb = math.sqrt(sum(y * y for y in b))
    if norma == 0 or normb == 0:
        return 0.0
    return dot / (norma * normb)


class SemanticRetrieval:
    def __init__(self, embedding_provider=None, backend=None, similarity_threshold: float = 0.7):
        self.embedding_provider = embedding_provider
        self.backend = backend or {}
        self.similarity_threshold = similarity_threshold

    async def store_memory(self, memory_entry: MemoryEntry, embedding: Optional[List[float]] = None) -> MemoryEntry:
        if embedding is None and self.embedding_provider:
            embedding = await self.embedding_provider.embed([memory_entry.content])
            embedding = embedding[0]
        memory_entry.embedding = embedding
        # Use in-memory backend dict for now
        self.backend[memory_entry.id] = memory_entry
        return memory_entry

    async def retrieve_similar(self, query: str, agent_id: Optional[str] = None, top_k: int = 5, threshold: Optional[float] = None):
        threshold = threshold or self.similarity_threshold
        if self.embedding_provider:
            q_emb = await self.embedding_provider.embed([query])
            q_emb = q_emb[0]
        else:
            return []
        results = []
        for entry in self.backend.values():
            if entry.embedding:
                score = _cosine(q_emb, entry.embedding)
                if score >= threshold:
                    results.append((score, entry))
        results.sort(key=lambda x: x[0], reverse=True)
        return [{"score": float(s), "entry": e.content, "id": e.id} for s, e in results[:top_k]]

    async def retrieve_recent(self, agent_id: Optional[str] = None, limit: int = 10):
        # Return recent by insertion order (backend is dict) — placeholder
        items = list(self.backend.values())[-limit:]
        return items[::-1]
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
