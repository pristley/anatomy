SHELL := /bin/bash
VENV ?= .venv
PY = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
NPM = npm

.PHONY: init install-backend install-frontend lint format build test test-backend test-frontend deploy clean

init: ## Create virtualenv and install dependencies (backend + frontend)
	@test -d $(VENV) || python -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools
	@if [ -f backend/requirements.txt ]; then $(PIP) install -r backend/requirements.txt; fi
	@if [ -d frontend ]; then (cd frontend && $(NPM) install); fi
	@if [ -d frontend ] && [ "$(INSTALL_FRONTEND)" = "1" ]; then (cd frontend && $(NPM) install) || echo "frontend install failed, continuing"; else echo "skipping frontend install (set INSTALL_FRONTEND=1 to enable)"; fi

install-backend: ## Install backend dependencies into venv
	@test -d $(VENV) || python -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools
	@if [ -f backend/requirements.txt ]; then $(PIP) install -r backend/requirements.txt; fi

install-frontend: ## Install frontend deps (if frontend exists)
	@if [ -d frontend ]; then (cd frontend && $(NPM) install); else echo "no frontend directory"; fi
	@if [ -d frontend ]; then (cd frontend && $(NPM) install) || echo "frontend install failed, continuing"; else echo "no frontend directory"; fi

lint: ## Run linting (ruff + black) — requires tools installed in venv
	@echo "Running lints..."
	@$(VENV)/bin/ruff check . || true
	@$(VENV)/bin/black --check . || true

format: ## Format code (ruff + black)
	@$(VENV)/bin/ruff format . || true
	@$(VENV)/bin/black . || true

test: test-backend test-frontend

test-backend: ## Run backend tests
	PYTHONPATH=.:backend pytest backend/tests/

test-frontend: ## Run frontend tests
	@if [ -d frontend ]; then (cd frontend && $(NPM) test); else echo "no frontend tests"; fi

build: ## Build backend package and frontend app (if present)
	@echo "Building artifacts..."
	@if [ -f backend/pyproject.toml ]; then $(PY) -m build backend || true; fi
	@if [ -d frontend ]; then (cd frontend && $(NPM) run build) || true; fi

deploy: ## Run deploy script if present
	@if [ -f ./infrastructure/scripts/deploy.sh ]; then bash ./infrastructure/scripts/deploy.sh; \
	elif [ -f ./scripts/deploy.sh ]; then bash ./scripts/deploy.sh; \
	else echo "No deploy script found. Provide ./infrastructure/scripts/deploy.sh or ./scripts/deploy.sh"; fi

clean: ## Cleanup build artifacts and virtualenv
	rm -rf $(VENV) dist build *.egg-info
	-find . -name "__pycache__" -type d -print0 | xargs -0 rm -rf || true

# help target
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | awk 'BEGIN {print "Usage:"} {printf "  %-20s %s\n", $$1, substr($$0, index($$0, "##")+3)}'
