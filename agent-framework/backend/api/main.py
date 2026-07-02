from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import HTTPException as StarletteHTTPException
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import time
import logging
import os
import json
import uuid
from datetime import datetime

from agent_framework.core.agent import Agent
from api.routes import agents as agents_router

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("agent-framework")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

app = FastAPI(title="Agent Framework API")
# track process start for uptime
START_TIME = time.time()
agent = Agent()

# CORS
origins = os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# simple auth middleware: if API_AUTH_TOKEN set, require Bearer token for /api/*
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    token = os.getenv("API_AUTH_TOKEN")
    if token and request.url.path.startswith("/api"):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or auth.split(" ", 1)[1] != token:
            return JSONResponse(status_code=401, content={"error": "unauthorized"})
    return await call_next(request)



@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = time.time()
    try:
        response = await call_next(request)
    except Exception as exc:
        # let exception handlers handle formatting
        raise
    duration_ms = int((time.time() - start) * 1000)
    logger.info(json.dumps({
        "method": request.method,
        "path": str(request.url.path),
        "status_code": getattr(response, "status_code", None),
        "duration_ms": duration_ms,
    }))
    return response


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    try:
        response = await call_next(request)
    except Exception as exc:
        # Let exception handler deal with it
        raise
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time-Ms"] = str(int(process_time))
    # security headers
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    return response


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"error": "internal_server_error", "detail": str(exc)})


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # ensure consistent JSON error format for HTTPException
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.get("/health")
def health():
    uptime_s = int(time.time() - START_TIME)
    return {"status": "ok", "uptime": f"{uptime_s}s"}


@app.get("/ready")
def ready():
    # basic readiness: ensure core package importable and agent present
    try:
        ok = agent is not None
        return {"ready": bool(ok)}
    except Exception as e:
        logger.exception("readiness check failed: %s", e)
        raise HTTPException(status_code=500, detail="not ready")


# include routers
app.include_router(agents_router.router, prefix="/api/agents", tags=["agents"])

# include optional routers if present
try:
    from api.routes import tools as tools_router
    app.include_router(tools_router.router, prefix="/api/tools", tags=["tools"])
except Exception:
    logger.info("tools router not present; skipping")

try:
    from api.routes import memory as memory_router
    app.include_router(memory_router.router, prefix="/api/memory", tags=["memory"])
except Exception:
    logger.info("memory router not present; skipping")


# monitoring router (polling) + websocket endpoint (real-time)
try:
    from api.routes import monitoring as monitoring_router
    app.include_router(monitoring_router.router, prefix="/api/monitoring", tags=["monitoring"])
except Exception:
    logger.info("monitoring router not present; skipping")


@app.websocket("/ws/monitoring")
async def websocket_monitoring(ws: WebSocket):
    await ws.accept()
    try:
        # send a few initial events then keep the connection alive
        for i in range(5):
            payload = {
                "type": "metric",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "value": i,
                "timeline": [],
            }
            await ws.send_json(payload)
            await asyncio.sleep(1)
        # heartbeat loop
        while True:
            await ws.send_json({"type": "heartbeat", "timestamp": datetime.utcnow().isoformat() + "Z"})
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        logger.info("monitoring websocket disconnected")


@app.post('/run')
def run(payload: dict):
    return {"result": "ok"}
