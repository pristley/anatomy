# Contributing

Thanks for contributing! This project uses `pre-commit`, `ruff`, and `black` to
keep the codebase consistent. Please follow the steps below when working on
changes.

Local setup
1. Create and activate a Python virtual environment (recommended):

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install development dependencies and `pre-commit`:

```bash
.venv/bin/pip install -r backend/requirements.txt || true
.venv/bin/pip install pre-commit ruff black
```

Install pre-commit hooks

Run the following once to install the Git hooks locally:

```bash
.venv/bin/pre-commit install
```

If you'd like to run the hooks across the entire repository (useful before
opening a PR):

```bash
.venv/bin/pre-commit run --all-files
```

Working on changes
- Run tests locally before committing: `export PYTHONPATH=.:backend && .venv/bin/pytest backend/tests/`
- Format and lint: pre-commit hooks will run on commit, but you can also run
  `ruff` and `black` manually: `.venv/bin/ruff check . --fix` and `.venv/bin/black .`.

CI
- The CI workflow runs `pre-commit` checks, `ruff`, `black --check`, and the
  backend tests. Ensure your branch passes these locally before creating a PR.

Thank you for helping keep the project healthy!
