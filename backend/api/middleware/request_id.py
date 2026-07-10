from typing import Callable
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from backend.agent_framework.observability.context import (
    request_id_var,
)


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


def get_request_id() -> str:
    try:
        return request_id_var.get()
    except Exception:
        return ""
