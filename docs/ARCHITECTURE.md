# Architecture

This repository implements a small layered agent framework. The core
orchestration and layering are implemented in `backend/agent_framework/core`.

High-level components:

- **Agent orchestrator**: `backend/agent_framework/core/agent.py` — coordinates
	input, understanding, planning, decision, execution, resilience, and
	evaluation layers.
- **Layers**: implemented under `backend/agent_framework/core/layers/` as
	modular components (`01_input.py` .. `11_infrastructure.py`). Each layer
	encapsulates a focused responsibility (see `docs/LAYERS/` for per-layer
	descriptions).
- **Tools**: builtin tools and tool adapters live in
	`backend/agent_framework/tools/` (see `tools/builtin/` for implementations
	such as `math_eval.py`, `api_call.py`).
- **Memory**: episodic and semantic memory implementations are in
	`backend/agent_framework/memory/` (`episodic.py`, `semantic.py`,
	`retrieval.py`).
- **Observability**: logging and context helpers are in
	`backend/agent_framework/observability/`.

Data flow summary:

1. Incoming query processed by `01_input.py`.
2. `02_understanding.py` parses and normalizes intent.
3. `04_planning.py` decomposes goals into `TaskDef`s and topologically sorts
	 dependencies.
4. The `Agent` loop (see `Agent._run_async` in `core/agent.py`) uses the
	 `DecisionEngine` and `ExecutionEngine` to execute tasks, invoking tools
	 and the reasoner as needed.
5. `08_resilience.py` wraps tool execution with circuit-breaking and
	 recovery strategies.
6. `09_evaluation.py` computes `TaskOutcome` and `GoalEvaluation` summaries.

See `docs/LAYERS/` for layer-level details and code references.
