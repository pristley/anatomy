import os
import logging
from fastapi import FastAPI
from fastapi import HTTPException
from starlette.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from .middleware import (
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    ErrorHandlerMiddleware,
    AuthMiddleware,
    add_cors,
)
from .middleware import ResponseHeaderMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware


def create_app() -> FastAPI:
    # Load environment from .env
    load_dotenv()

    # Build basic config
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    PORT = int(os.getenv("PORT", "8000"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DATABASE_URL = os.getenv("DATABASE_URL")
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

    logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    @asynccontextmanager
    async def lifespan(app):
        # Startup: validate config, init DB, load tool registry, warm caches
        logging.info("startup: validating environment variables")
        # Validate required env vars
        if not DATABASE_URL:
            logging.error("DATABASE_URL is not set")
            raise RuntimeError("DATABASE_URL is required")
        # In production ensure critical keys are present
        if ENVIRONMENT.lower() == "production":
            if not CLAUDE_API_KEY:
                logging.error("CLAUDE_API_KEY is required in production")
                raise RuntimeError("CLAUDE_API_KEY is required in production")

        logging.info("startup: initialize database and registries")
        # Try to initialize database if session module exists
        try:
            from agent_framework.database import session as db_session

            # attempt a quick connect; engines create lazily
            _ = getattr(db_session, "engine", None)
        except Exception:
            try:
                from database import session as db_session
            except Exception:
                db_session = None

        # Try to initialize tool registry if available
        try:
            from agent_framework.tools import registry as tools_registry

            if hasattr(tools_registry, "init_registry"):
                tools_registry.init_registry()
        except Exception:
            pass

        # warm caches placeholder
        logging.info("startup: warm caches (placeholder)")
        try:
            yield
        finally:
            logging.info("shutdown: cleanup resources")
            # Close DB connections if present
            try:
                if db_session and hasattr(db_session, "engine"):
                    db_session.engine.dispose()
            except Exception:
                pass

    # Create app with lifespan hooks
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

    app = FastAPI(
        title="Anatomy Agent Framework API",
        description="Agent Framework API",
        version=version,
        docs_url="/docs",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Register middleware in required order
    # Order: RequestID -> ErrorHandler -> RequestLogging -> CORS -> ResponseHeader -> Auth
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    # CORS
    add_cors(app, production_origin=os.getenv("PRODUCTION_ORIGIN"))
    # Response headers (security + X-Request-ID)
    app.add_middleware(ResponseHeaderMiddleware)
    # HTTPS redirect in production
    if ENVIRONMENT.lower() == "production":
        app.add_middleware(HTTPSRedirectMiddleware)
    # Auth should be last in middleware order
    app.add_middleware(AuthMiddleware)

    # Include routers (import locally to avoid circular imports)
    try:
        from .routes import health as health_mod
        from .routes import agents as agents_mod
        from .routes import chat as chat_mod
        from .routes import tools as tools_mod
        from .routes import memory as memory_mod
        # monitoring is optional
        try:
            from .routes import monitoring as monitoring_mod
        except Exception:
            monitoring_mod = None

        app.include_router(health_mod.router, prefix="", tags=["health"])
        app.include_router(agents_mod.router, prefix="/agents", tags=["agents"])
        app.include_router(chat_mod.router, prefix="/agents/{agent_id}/messages", tags=["chat"])
        app.include_router(tools_mod.router, prefix="/tools", tags=["tools"])
        app.include_router(memory_mod.router, prefix="/agents/{agent_id}/memory", tags=["memory"])
        if monitoring_mod is not None:
            app.include_router(monitoring_mod.router, prefix="/monitoring", tags=["monitoring"])
    except Exception:
        # Routers may not be present during initial scaffolding — ignore for now
        pass

    @app.exception_handler(Exception)
    async def generic_exception_handler(request, exc):
        request_id = getattr(request.state, "request_id", "")
        return JSONResponse(status_code=500, content={"error": "internal error", "request_id": request_id})

    # HTTP exceptions (e.g. 404) should also include request_id
    from fastapi import HTTPException

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request, exc: HTTPException):
        request_id = getattr(request.state, "request_id", "")
        content = {"error": exc.detail if exc.detail else exc.status_code, "request_id": request_id}
        return JSONResponse(status_code=exc.status_code, content=content)

    return app


app = create_app()
