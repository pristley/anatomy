from typing import Callable, Optional

import uuid
import time
import json

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from backend.agent_framework.observability import logger as obs_logger
from backend.agent_framework.observability.context import request_id_var, correlation_id_var
import os


def _json_log(obj: dict):
    try:
        obs_logger.info(json.dumps(obj))
    except Exception:
        # Fallback to printing
        print(obj)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware that ensures each request has a request_id available in scope and contextvars."""

    async def dispatch(self, request: Request, call_next: Callable):
        incoming = request.headers.get("X-Request-ID")
        request_id = incoming or str(uuid.uuid4())
        request.scope["request_id"] = request_id
        request_id_var.set(request_id)
        response: Response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


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
        _json_log({"event": "request_start", "method": request.method, "path": request.url.path, "user_id": user_id, "request_id": request_id, "correlation_id": correlation, "timestamp": time.time()})
        try:
            response = await call_next(request)
        except Exception as exc:
            # Let ErrorHandlerMiddleware handle mapping; re-raise to let it catch
            raise
        duration_ms = int((time.time() - start) * 1000)
        _json_log({"event": "request_end", "method": request.method, "path": request.url.path, "status_code": getattr(response, "status_code", None), "duration_ms": duration_ms, "user_id": user_id, "request_id": request_id, "correlation_id": correlation})
        return response


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Catches exceptions thrown by route handlers and converts them to safe JSON responses."""

    async def dispatch(self, request: Request, call_next: Callable):
        try:
            return await call_next(request)
        except ValueError as exc:
            request_id = request.scope.get("request_id", "")
            user_id = request.scope.get("user_id")
            _json_log({"event": "error", "type": "ValueError", "error": str(exc), "method": request.method, "path": request.url.path, "user_id": user_id, "request_id": request_id})
            resp = Response(status_code=400, content=json.dumps({"error": str(exc), "request_id": request_id}), media_type="application/json")
            resp.headers["X-Request-ID"] = request_id
            return resp
        except KeyError as exc:
            request_id = request.scope.get("request_id", "")
            user_id = request.scope.get("user_id")
            _json_log({"event": "error", "type": "KeyError", "error": str(exc), "method": request.method, "path": request.url.path, "user_id": user_id, "request_id": request_id})
            resp = Response(status_code=404, content=json.dumps({"error": str(exc), "request_id": request_id}), media_type="application/json")
            resp.headers["X-Request-ID"] = request_id
            return resp
        except Exception as exc:
            # Log stacktrace but avoid exposing internals to client
            request_id = request.scope.get("request_id", "")
            user_id = request.scope.get("user_id")
            _json_log({"event": "error", "type": "Exception", "error": "internal error", "detail": str(exc), "method": request.method, "path": request.url.path, "user_id": user_id, "request_id": request_id})
            resp = Response(status_code=500, content=json.dumps({"error": "internal error", "request_id": request_id}), media_type="application/json")
            resp.headers["X-Request-ID"] = request_id
            return resp



class ResponseHeaderMiddleware(BaseHTTPMiddleware):
    """Adds security headers and ensures X-Request-ID is present on every response."""

    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        # security headers
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'")
        # ensure X-Request-ID propagated
        if not response.headers.get("X-Request-ID"):
            rid = request.scope.get("request_id") or request_id_var.get()
            if rid:
                response.headers["X-Request-ID"] = rid
        # Rate limit headers (best-effort placeholders configurable via env)
        try:
            rl_limit = int(os.getenv("RATE_LIMIT_REQUESTS", "1000"))
            rl_window = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
            response.headers.setdefault("X-RateLimit-Limit", str(rl_limit))
            response.headers.setdefault("X-RateLimit-Remaining", str(rl_limit))
            response.headers.setdefault("X-RateLimit-Reset", str(int(time.time()) + rl_window))
        except Exception:
            pass
        return response


class AuthMiddleware(BaseHTTPMiddleware):
    """Validate JWT token from Authorization header or cookies and set `user_id` in request.scope.

    This implementation performs a lightweight JWT payload extraction (no signature verification).
    Replace `_validate_token` with a proper verifier (PyJWT) in production.
    """

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path
        public = path.startswith("/health") or path.startswith("/docs") or path.startswith("/openapi.json") or path.startswith("/metrics")
        if public:
            return await call_next(request)

        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
        elif "access_token" in request.cookies:
            token = request.cookies.get("access_token")

        user_id = None
        if token:
            user_id = self._validate_token(token)

        if not user_id:
            return Response(status_code=401, content=json.dumps({"error": "unauthorized", "request_id": request.scope.get("request_id")}), media_type="application/json")

        request.scope["user_id"] = user_id
        return await call_next(request)

    def _validate_token(self, token: str) -> Optional[str]:
        """Validate JWT using PyJWT if a verification key/secret is configured.

        Environment variables supported:
        - `JWT_SECRET` (HMAC shared secret)
        - `JWT_PUBLIC_KEY` (PEM public key for RSA/EC)
        - `JWT_ALGORITHM` (default `HS256`)

        Returns the `sub` or `user_id` claim when valid, otherwise None.
        """
        try:
            import os
            import jwt
            options = {"verify_signature": True}
            alg = os.getenv("JWT_ALGORITHM", "HS256")
            secret = os.getenv("JWT_SECRET")
            pub = os.getenv("JWT_PUBLIC_KEY")
            key = pub or secret
            if not key:
                # no verification key configured; reject token for safety
                return None
            payload = jwt.decode(token, key=key, algorithms=[alg])
            return payload.get("sub") or payload.get("user_id")
        except Exception:
            return None


def add_cors(app, production_origin: Optional[str] = None):
    allowed = ["http://localhost:3000", "http://localhost:5173"]
    if production_origin:
        allowed.append(production_origin)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
        expose_headers=["X-Total-Count"],
    )
