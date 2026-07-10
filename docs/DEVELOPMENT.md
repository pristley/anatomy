# Development

Quick setup for local development (uses the repository `backend` package):

1. Create and activate a Python 3.12 virtualenv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

2. Run pre-commit and linters locally:

```bash
.venv/bin/pre-commit run --all-files
```

3. Run tests:

```bash
PYTHONPATH=.:backend .venv/bin/pytest backend/tests/ -q
```

4. Examples can be executed with the backend on the PYTHONPATH, for example:

```bash
PYTHONPATH=.:backend .venv/bin/python3 examples/simple_query_agent.py
```

Development notes:
- The project uses `black` and `ruff` via `pre-commit`.
- The core orchestrator is `backend/agent_framework/core/agent.py` — changes
	here impact most examples and tests.
