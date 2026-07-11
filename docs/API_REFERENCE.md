# API Reference

The public HTTP API is implemented under `api/` (top-level). The main
application entrypoint for the backend API server is `api/main.py` which
mounts route modules under `api/routes/`.

Key files:

- `api/main.py` — FastAPI (or similar) application startup and middleware.
- `api/routes/agents.py` — agent-related endpoints (create/run/list).

If you are extending the HTTP API, add route handlers under `api/routes/`
and update the OpenAPI schema as part of the PR.

Quick examples

Start the backend API locally (from repo root):

```bash
cd backend
python -m api.main
# or with venv: .venv/bin/python -m api.main
```

Call the REST API with `httpx`:

```python
import httpx

resp = httpx.post('http://localhost:8000/agents/run', json={'query': 'Summarize this code'})
print(resp.json())
```

Python client usage (programmatic agent run):

```python
from agent_framework.core.agent import Agent

agent = Agent()
result = agent.run_sync('What is the time complexity of quicksort?', user_id='tester')
print(result)
```

Extending routes

- Add a new module under `api/routes/` and include it in `api/main.py`.
- Use Pydantic models for request/response schemas so the OpenAPI spec updates automatically.

Debugging tips

- Enable debug logging with `export LOG_LEVEL=DEBUG`.
- Use `httpx` or `curl` to exercise endpoints and inspect request/response JSON.
