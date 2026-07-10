from fastapi import APIRouter
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import asyncio
import os
import time
from typing import Dict

router = APIRouter()
startup_time = datetime.now(timezone.utc)

# Simple in-memory cache for health results (cached for 5 seconds)
_cached_health: Dict = {"ts": 0, "result": None}


async def _check_database() -> str:
    """Attempt a lightweight DB check. Tries a SELECT 1 if SQLAlchemy session is available.

    Returns "ok" or "error".
    """
    try:
        # Try to import the project's DB session
        try:
            from agent_framework.database.session import engine
        except Exception:
            try:
                from database.session import engine
            except Exception:
                engine = None

        if engine is None:
            return "error"

        def _sync_check():
            with engine.connect() as conn:
                conn.execute("SELECT 1")

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _sync_check)
        return "ok"
    except Exception:
        return "error"


async def _check_memory() -> str:
    """Attempt store & retrieve using an in-process memory backend if available."""
    try:
        # Try to find a semantic retrieval implementation
        try:
            from agent_framework.memory.retrieval import SemanticRetrieval, MemoryEntry
        except Exception:
            try:
                from agent_framework.agent_framework.memory.retrieval import (
                    SemanticRetrieval,
                    MemoryEntry,
                )
            except Exception:
                SemanticRetrieval = None

        if SemanticRetrieval is None:
            return "error"

        retr = SemanticRetrieval(embedding_provider=None)
        entry = MemoryEntry(id="hc-1", content="health-check")

        # store and retrieve with timeout
        await asyncio.wait_for(retr.store_memory(entry), timeout=1.0)
        res = await asyncio.wait_for(
            retr.retrieve_similar("health-check", top_k=1), timeout=1.0
        )
        return "ok" if res else "error"
    except Exception:
        return "error"


async def _check_llm() -> str:
    """Check LLM connectivity (Anthropic/Claude) if API key provided. Skips if no key."""
    try:
        key = os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            return "ok"
        import httpx

        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(
                "https://api.anthropic.com/health", headers={"x-api-key": key}
            )
            return "ok" if r.status_code == 200 else "error"
    except Exception:
        return "error"


def _compute_status(checks: Dict[str, str]) -> str:
    # If any critical check is error, return unhealthy
    critical = [checks.get("database")]
    if any(c == "error" for c in critical):
        return "unhealthy"
    # degraded if any non-critical fail
    if any(v == "error" for v in checks.values()):
        return "degraded"
    return "healthy"


def _security_headers() -> Dict[str, str]:
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
    }


@router.get("/health")
async def health():
    """Return aggregate health information.

    Runs database, memory, and LLM checks concurrently with individual timeouts.
    Results are cached for 5 seconds to avoid overloading downstream systems.
    """
    now = time.time()
    if _cached_health["ts"] and now - _cached_health["ts"] < 5:
        result = _cached_health["result"]
        return JSONResponse(content=result, headers=_security_headers())

    # run checks with per-check timeouts
    tasks = {
        "database": asyncio.create_task(
            asyncio.wait_for(_check_database(), timeout=2.0)
        ),
        "memory_backend": asyncio.create_task(
            asyncio.wait_for(_check_memory(), timeout=1.0)
        ),
        "llm_connection": asyncio.create_task(
            asyncio.wait_for(_check_llm(), timeout=2.0)
        ),
    }

    checks = {}
    for name, task in tasks.items():
        try:
            checks[name] = await task
        except asyncio.TimeoutError:
            checks[name] = "error"
        except Exception:
            checks[name] = "error"

    status = _compute_status(checks)
    uptime = int((datetime.now(timezone.utc) - startup_time).total_seconds())

    # version lookup
    version = "unknown"
    try:
        try:
            from agent_framework.version import __version__ as v

            version = v
        except Exception:
            try:
                from agent_framework.agent_framework.version import __version__ as v2

                version = v2
            except Exception:
                version = "unknown"
    except Exception:
        version = "unknown"

    result = {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": uptime,
        "version": version,
        "checks": checks,
    }

    _cached_health["ts"] = now
    _cached_health["result"] = result
    return JSONResponse(content=result, headers=_security_headers())


@router.get("/health/ready")
async def readiness():
    """Kubernetes readiness probe — 200 if healthy, 503 otherwise."""
    res = await health()
    # If we returned a JSONResponse, inspect the body for health status
    if isinstance(res, JSONResponse):
        data = res.body
        try:
            import json as _json

            data_dict = (
                _json.loads(data.decode())
                if isinstance(data, (bytes, bytearray))
                else data
            )
        except Exception:
            data_dict = None
        if data_dict and data_dict.get("status") == "healthy":
            return res
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy"},
            headers=_security_headers(),
        )

    return JSONResponse(
        status_code=503, content={"status": "unhealthy"}, headers=_security_headers()
    )
