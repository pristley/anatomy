from typing import Callable
import time
import json
import os

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from backend.agent_framework.observability import logger as obs_logger
from backend.agent_framework.observability.context import (
    request_id_var,
    correlation_id_var,
)


def _json_log(obj: dict):
    try:
        obs_logger.info(json.dumps(obj))
    except Exception:
        print(obj)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs structured JSON at request start and end, including correlation id if present."""

    async def dispatch(self, request: Request, call_next: Callable):
        start = time.time()
        request_id = request.scope.get("request_id")
        user_id = request.scope.get("user_id")
        correlation = request.scope.get("correlation_id")
        # set correlation context var for use in logging
        if request_id:
            request_id_var.set(request_id)
        if correlation:
            correlation_id_var.set(correlation)
        _json_log(
            {
                "event": "request_start",
                "method": request.method,
                "path": request.url.path,
                "user_id": user_id,
                "request_id": request_id,
                "correlation_id": correlation,
                "timestamp": time.time(),
            }
        )
        try:
            response = await call_next(request)
        except Exception:
            # Let ErrorHandlerMiddleware handle mapping; re-raise to let it catch
            raise
        duration_ms = int((time.time() - start) * 1000)
        _json_log(
            {
                "event": "request_end",
                "method": request.method,
                "path": request.url.path,
                "status_code": getattr(response, "status_code", None),
                "duration_ms": duration_ms,
                "user_id": user_id,
                "request_id": request_id,
                "correlation_id": correlation,
            }
        )
        return response


class ResponseHeaderMiddleware(BaseHTTPMiddleware):
    """Adds security headers and ensures X-Request-ID is present on every response."""

    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        # security headers
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'")
        # ensure X-Request-ID propagated
        if not response.headers.get("X-Request-ID"):
            try:
                rid = request.scope.get("request_id") or request_id_var.get()
            except Exception:
                rid = None
            if rid:
                response.headers["X-Request-ID"] = rid
        # Rate limit headers (best-effort placeholders configurable via env)
        try:
            rl_limit = int(os.getenv("RATE_LIMIT_REQUESTS", "1000"))
            rl_window = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
            response.headers.setdefault("X-RateLimit-Limit", str(rl_limit))
            response.headers.setdefault("X-RateLimit-Remaining", str(rl_limit))
            response.headers.setdefault(
                "X-RateLimit-Reset", str(int(time.time()) + rl_window)
            )
        except Exception:
            pass
        return response
