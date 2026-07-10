from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import json

from backend.agent_framework.observability import logger as obs_logger
from backend.agent_framework.observability.context import request_id_var


def _json_log(obj: dict):
    try:
        obs_logger.info(json.dumps(obj))
    except Exception:
        print(obj)


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
