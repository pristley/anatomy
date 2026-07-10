# Quickstart

5-minute quickstart to run examples locally.

Requirements:
- Python 3.12 (recommended)
- `git` and a local shell

Steps:

```bash
# clone the repo
git clone https://github.com/pristley/anatomy.git
cd anatomy

# create a venv and install backend deps
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# run tests
PYTHONPATH=.:backend .venv/bin/pytest backend/tests/ -q

# run an example
PYTHONPATH=.:backend .venv/bin/python3 examples/simple_query_agent.py
```

If you prefer Docker compose, see `agent-framework/docker-compose.yml` for
an example deployment stack used by the project maintainers.
