from typing import Callable, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import json


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
