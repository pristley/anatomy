from typing import Optional
from starlette.middleware.cors import CORSMiddleware


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
