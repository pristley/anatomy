# Glossary

- **Agent**: an orchestrator that runs the layered pipeline to satisfy a
	user goal. Core implementation: `backend/agent_framework/core/agent.py`.
- **Layer**: a focused module implementing a stage in the pipeline. Layers
	live in `backend/agent_framework/core/layers/` (01..11).
- **ExecutionEngine**: executes tools and external actions. See
	`backend/agent_framework/core/layers/07_execution.py` and tests under
	`backend/tests/`.
- **StateManager**: tracks goal/task state between iterations
	(`backend/agent_framework/core/layers/05_state.py`).
- **Tool**: pluggable piece of functionality invoked by the agent; builtin
	tools are in `backend/agent_framework/tools/builtin/`.
- **Episodic memory / Semantic memory**: stores past episodes and semantic
	patterns (`backend/agent_framework/memory/`).
