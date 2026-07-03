from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Any, Dict, List, Optional
import time
import io
import json
import csv
from datetime import datetime, timedelta

router = APIRouter()


class MemoryService:
    def __init__(self) -> None:
        # try to use existing implementations
        try:
            from backend.agent_framework.memory.episodic import EpisodicMemory
            from backend.agent_framework.memory.semantic import SemanticMemory
        except Exception:
            try:
                from agent_framework.memory.episodic import EpisodicMemory
                from agent_framework.memory.semantic import SemanticMemory
            except Exception:
                EpisodicMemory = None
                SemanticMemory = None

        self.episodic = EpisodicMemory() if EpisodicMemory is not None else None
        self.semantic = SemanticMemory() if SemanticMemory is not None else None
        # retrieval wrapper
        try:
            from backend.agent_framework.memory.retrieval import SemanticRetrieval, SimpleEmbeddings
        except Exception:
            try:
                from agent_framework.memory.retrieval import SemanticRetrieval, SimpleEmbeddings
            except Exception:
                SemanticRetrieval = None
                SimpleEmbeddings = None

        if SemanticRetrieval is not None:
            emb = SimpleEmbeddings() if SimpleEmbeddings is not None else None
            self.retriever = SemanticRetrieval(embedding_model=emb, backend=self.episodic)
        else:
            self.retriever = None

    async def search(self, agent_id: str, q: str, type_: str = "all", limit: int = 10, threshold: float = 0.7, include_score: bool = True, skip: int = 0):
        start = time.time()
        results: List[Dict[str, Any]] = []
        if type_ in ("episodic", "all") and self.episodic:
            # naive episodic search: use episodic.retrieve_similar if available
            try:
                if hasattr(self.episodic, "retrieve_similar"):
                    ep = await maybe_await(self.episodic.retrieve_similar(q, top_k=limit))
                else:
                    ep = []
            except Exception:
                ep = []
            for e in ep:
                e_copy = dict(e)
                if not include_score:
                    e_copy.pop("similarity_score", None)
                results.append({"source": "episodic", **e_copy})

        if type_ in ("semantic", "all") and self.retriever:
            try:
                sem = await self.retriever.retrieve_similar(q, agent_id=agent_id, top_k=limit, threshold=threshold)
            except Exception:
                sem = []
            for s in sem:
                s_copy = dict(s)
                if not include_score:
                    s_copy.pop("similarity_score", None)
                results.append({"source": "semantic", **s_copy})

        # combine & rank by similarity_score if present
        def score_key(x: Dict[str, Any]):
            return x.get("similarity_score", 0.0)

        results.sort(key=score_key, reverse=True)
        total = len(results)
        elapsed_ms = int((time.time() - start) * 1000)
        return {"query": q, "results": results[skip: skip + limit], "count": total, "query_time_ms": elapsed_ms}

    async def recent(self, agent_id: str, limit: int = 20, type_: str = "all", days: Optional[int] = None, skip: int = 0):
        out = []
        cutoff = None
        if days:
            cutoff = int((datetime.utcnow() - timedelta(days=days)).timestamp())
        if type_ in ("episodic", "all") and self.episodic:
            try:
                if hasattr(self.episodic, "retrieve_recent"):
                    ep = await maybe_await(self.episodic.retrieve_recent(agent_id, limit=limit))
                else:
                    ep = []
            except Exception:
                ep = []
            out.extend(ep)
        if type_ in ("semantic", "all") and self.semantic:
            # semantic memory may not have recent; fallback to patterns
            try:
                # try to list stored patterns
                pats = list(getattr(self.semantic, "_patterns", {}).values())
            except Exception:
                pats = []
            out.extend(pats[:limit])

        # filter by cutoff
        if cutoff:
            out = [m for m in out if m.get("timestamp", m.get("created_at", 0)) >= cutoff]
        # sort desc
        out.sort(key=lambda x: x.get("timestamp", x.get("created_at", 0)), reverse=True)
        total = len(out)
        return {"memories": out[skip: skip + limit], "count": total}

    async def stats(self, agent_id: str) -> Dict[str, Any]:
        episodic_count = len(getattr(self.episodic, "_store", {}).get(agent_id, {}) if self.episodic else {})
        semantic_count = len(getattr(self.semantic, "_patterns", {}) if self.semantic else {})
        total_size_bytes = 0
        # crude size estimate
        if self.episodic:
            for v in getattr(self.episodic, "_store", {}).get(agent_id, {}).values():
                total_size_bytes += len(json.dumps(v).encode())
        if self.semantic:
            for v in getattr(self.semantic, "_patterns", {}).values():
                total_size_bytes += len(json.dumps(v).encode())
        top_tags = []
        return {"episodic_count": episodic_count, "semantic_count": semantic_count, "total_size_bytes": total_size_bytes, "memory_usage": {}, "created_date_range": {}, "top_tags": top_tags}

    async def delete(self, agent_id: str, memory_id: str) -> None:
        # soft delete from episodic if present
        if self.episodic and hasattr(self.episodic, "_store"):
            store = getattr(self.episodic, "_store")
            if memory_id in store:
                store[memory_id]["deleted"] = True
                return
        raise KeyError("not found")

    async def clear(self, agent_id: str, type_: Optional[str] = None, older_than_days: Optional[int] = None) -> Dict[str, Any]:
        cutoff = None
        if older_than_days:
            cutoff = int((datetime.utcnow() - timedelta(days=older_than_days)).timestamp())
        cleared = 0
        freed = 0
        if type_ in (None, "episodic") and self.episodic:
            store = getattr(self.episodic, "_store", {})
            keys = list(store.keys())
            for k in keys:
                v = store[k]
                ts = v.get("timestamp", v.get("created_at", 0))
                if cutoff and ts < cutoff:
                    freed += len(json.dumps(v).encode())
                    del store[k]
                    cleared += 1
                elif not cutoff:
                    freed += len(json.dumps(v).encode())
                    del store[k]
                    cleared += 1
        if type_ in (None, "semantic") and self.semantic:
            pats = getattr(self.semantic, "_patterns", {})
            keys = list(pats.keys())
            for k in keys:
                v = pats[k]
                ts = v.get("created_at", 0)
                if cutoff and ts < cutoff:
                    freed += len(json.dumps(v).encode())
                    del pats[k]
                    cleared += 1
                elif not cutoff:
                    freed += len(json.dumps(v).encode())
                    del pats[k]
                    cleared += 1
        return {"cleared_count": cleared, "freed_bytes": freed}

    async def patterns(self, agent_id: str) -> Dict[str, Any]:
        pats = list(getattr(self.semantic, "_patterns", {}).values()) if self.semantic else []
        return {"patterns": pats, "count": len(pats)}

    async def timeline(self, agent_id: str, granularity: str = "day", limit: int = 30) -> Dict[str, Any]:
        # build timeline over episodic store
        store = getattr(self.episodic, "_store", {}) if self.episodic else {}
        items = list(store.values())
        periods: Dict[str, Dict[str, Any]] = {}
        now = datetime.utcnow()
        for it in items:
            ts = datetime.utcfromtimestamp(it.get("timestamp", it.get("created_at", now.timestamp())))
            if granularity == "day":
                period = ts.strftime("%Y-%m-%d")
            elif granularity == "week":
                y, w, _ = ts.isocalendar()
                period = f"{y}-W{w}"
            else:
                period = ts.strftime("%Y-%m")
            entry = periods.setdefault(period, {"period": period, "count": 0, "preview": ""})
            entry["count"] += 1
            if not entry["preview"]:
                entry["preview"] = it.get("input") or it.get("content") or ""
        timeline = sorted(list(periods.values()), key=lambda x: x["period"], reverse=True)[:limit]
        return {"timeline": timeline}

    async def export(self, agent_id: str, fmt: str = "json", include: List[str] | None = None):
        include = include or ["content", "metadata", "scores"]
        # collect memories
        items = []
        if self.episodic:
            items.extend(list(getattr(self.episodic, "_store", {}).values()))
        if self.semantic:
            items.extend(list(getattr(self.semantic, "_patterns", {}).values()))
        # format
        if fmt == "csv":
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["id", "type", "content", "metadata", "score"])
            for it in items:
                writer.writerow([it.get("id"), it.get("type", "episodic"), it.get("content") or it.get("input"), json.dumps(it.get("metadata", {})), it.get("similarity_score")])
            buf.seek(0)
            return StreamingResponse(iter([buf.getvalue().encode()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=memory_export_{agent_id}.csv"})
        else:
            payload = []
            for it in items:
                rec = {}
                if "content" in include:
                    rec["content"] = it.get("content") or it.get("input")
                if "metadata" in include:
                    rec["metadata"] = it.get("metadata") or {}
                if "scores" in include and it.get("similarity_score") is not None:
                    rec["score"] = it.get("similarity_score")
                payload.append(rec)
            body = json.dumps({"agent_id": agent_id, "count": len(payload), "items": payload})
            return StreamingResponse(iter([body.encode()]), media_type="application/json", headers={"Content-Disposition": f"attachment; filename=memory_export_{agent_id}.json"})


async def maybe_await(v):
    if hasattr(v, "__await__"):
        return await v
    return v


_svc = MemoryService()


@router.get("/search")
async def search(agent_id: str, q: str = Query(...), type: str = Query("all"), limit: int = Query(10, le=50), threshold: float = Query(0.7, ge=0.0, le=1.0), include_score: bool = Query(True), skip: int = Query(0, ge=0)):
    if not q:
        raise HTTPException(status_code=400, detail="q is required")
    res = await _svc.search(agent_id, q, type_=type, limit=limit, threshold=threshold, include_score=include_score, skip=skip)
    return JSONResponse(content=res)


@router.get("/recent")
async def recent(agent_id: str, limit: int = Query(20, le=200), type: str = Query("all"), days: Optional[int] = Query(None), skip: int = Query(0, ge=0)):
    res = await _svc.recent(agent_id, limit=limit, type_=type, days=days, skip=skip)
    return JSONResponse(content=res)


@router.get("/stats")
async def stats(agent_id: str):
    res = await _svc.stats(agent_id)
    return JSONResponse(content=res)


@router.delete("/{memory_id}", status_code=204)
async def delete(agent_id: str, memory_id: str):
    try:
        await _svc.delete(agent_id, memory_id)
        return ""
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")


@router.post("/clear")
async def clear(agent_id: str, confirm: bool = Query(False), type: Optional[str] = Query(None), older_than_days: Optional[int] = Query(None)):
    if not confirm:
        raise HTTPException(status_code=400, detail="confirm=true required")
    res = await _svc.clear(agent_id, type_=type, older_than_days=older_than_days)
    return JSONResponse(content=res)


@router.get("/patterns")
async def patterns(agent_id: str):
    res = await _svc.patterns(agent_id)
    return JSONResponse(content=res)


@router.get("/timeline")
async def timeline(agent_id: str, granularity: str = Query("day"), limit: int = Query(30, le=365)):
    res = await _svc.timeline(agent_id, granularity=granularity, limit=limit)
    return JSONResponse(content=res)


@router.post("/export")
async def export(agent_id: str, format: str = Query("json"), include: Optional[str] = Query(None)):
    inc = include.split(",") if include else None
    return await _svc.export(agent_id, fmt=format, include=inc)
from fastapi import APIRouter, Query, HTTPException
from typing import List

router = APIRouter()


@router.get("/search")
async def search_memory(agent_id: str, q: str = Query(...), limit: int = 10):
    # Placeholder: wiring into retrieval layer
    return {"query": q, "results": [], "count": 0}


@router.get("/recent")
async def recent(agent_id: str, limit: int = 20):
    return {"memories": [], "count": 0}
