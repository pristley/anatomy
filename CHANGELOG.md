# Changelog

## Unreleased

### Added
- `docs/ARCHITECTURE.md`: appended a text data-flow diagram describing the 11-layer pipeline.
- `docs/asserts/img/architecture.svg`: static SVG rendering of the architecture diagram.
- `docs/asserts/img/architecture.mmd`: mermaid source for the architecture diagram.
- `docs/TROUBLESHOOTING.md`: troubleshooting guide with common issues and fixes.
- `docs/LAYERS/README.md`: landing page for per-layer documentation.
- `backend/tests/test_agents_service.py`: additional unit test for `AgentService` CRUD flows.

### Chore
- Pre-commit and lint fixes applied to tests and docs (formatting, trailing whitespace, ruff fixes).

### Notes
- CI steps were run locally via `make ci` and now pass: lints and tests all green.
# Changelog

All notable changes to this project are documented here. This file follows
the "Keep a Changelog" style with an **Unreleased** section for ongoing
work.

## [Unreleased]

### Added
- GitHub Actions CI workflow: `.github/workflows/ci.yml` — sets up Python
  3.12, installs backend deps, runs `pre-commit`, `ruff` and `black` checks,
  and runs the backend test suite via `pytest`.
- Pre-commit configuration: `.pre-commit-config.yaml` — runs `black`, `ruff`,
  and common hygiene hooks (`end-of-file-fixer`, `trailing-whitespace`, `check-yaml`).
- Execution engine: `backend/agent_framework/core/layers/07_execution.py` —
  `ExecutionEngine`, `ExecutionResult`, and `ExecutionStatus` for running
  tools with timeout, retry/backoff, and cost/latency metrics.
- Execution engine integration: `backend/agent_framework/core/agent.py` now
  instantiates and uses the `ExecutionEngine` in the main orchestration loop.
- Comprehensive unit tests for Layer 7 execution: `backend/tests/test_layers/test_layer_7.py`.

### Changed
- Switched CI to use direct venv/python commands (no `make` dependency).
- Linting/formatting: ran `ruff --fix` and `black` across the repository; fixed
  multiple style and import-order issues. Many files were reformatted for
  consistency.
- Replaced local layer types star-import shim with explicit exports to avoid
  linter warnings: `backend/agent_framework/core/layers/types.py`.
- Migrated Pydantic `@validator` usages to `@field_validator` (Pydantic v2).

### Fixed
- Removed duplicate placeholder endpoints and fixed import-order issues that
  caused spurious linter errors and test failures.
- Resolved a number of ruff errors (E402, F841, F403, F405, E721, etc.) by
  moving imports, removing unused variables, and replacing comparisons where
  appropriate.

### Documentation
- Added `CHANGELOG.md` (this file).
- Added CI and pre-commit instructions implicitly via `.github/workflows/ci.yml`
  and `.pre-commit-config.yaml`.

### Notes / Next Steps
- Consider adding a `CONTRIBUTING.md` recommending `pre-commit install`.
- Consider adding a coverage upload step in CI for test coverage monitoring.
- Consider reviewing `ruff` rules and making `ruff` check-only in CI if you
  prefer to avoid auto-fixes in machine pipelines.

## [0.1.0-alpha-cleanup] - 2026-07-10
- Repository cleanup and restructure; added middleware package, memory module skeleton, agent config, and Makefile.
## [0.1.1] - 2026-07-10
- Released changes merged to `main`:
  - Added `ExecutionEngine` and integrated it into the agent orchestrator.
  - Added CI workflow and pinned formatting/linting tools (`black`, `ruff`).
  - Applied repository-wide lint/format fixes and migrated Pydantic validators to v2.
  - Added unit tests for the execution layer and updated docs (`CHANGELOG.md`).
  - Triggered remote CI run to validate the branch protection and CI checks.
