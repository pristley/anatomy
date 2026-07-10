# API Reference

The public HTTP API is implemented under `api/` (top-level). The main
application entrypoint for the backend API server is `api/main.py` which
mounts route modules under `api/routes/`.

Key files:

- `api/main.py` — FastAPI (or similar) application startup and middleware.
- `api/routes/agents.py` — agent-related endpoints (create/run/list).

If you are extending the HTTP API, add route handlers under `api/routes/`
and update the OpenAPI schema as part of the PR.
