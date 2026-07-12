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

## Data Flow Diagram

```mermaid
flowchart TB
	A[User Query] --> B[Layer 1: Input]\n
	subgraph L2 [Layer 2: Understanding]
		B2[Parse & normalize intent]\n  end
	B --> L2

	subgraph L3 [Layer 3: Reasoning]
		C[LLM chain-of-thought reasoning]
	end
	L2 --> L3

	subgraph L4 [Layer 4: Planning]
		D[Decompose into task DAG]
	end
	L3 --> L4

	subgraph L5 [Layer 5: State]
		E[Initialize task state]
	end
	L4 --> L5

	subgraph Exec [Execution Loop]
		F[Layer 6: Decision]
		G[Layer 7: Execution]
		H[Layer 8: Resilience]
		I[Layer 9: Evaluation]
	end
	L5 --> Exec
	Exec --> J[Layer 10: Observability]
	J --> K[Layer 11: Infrastructure]

	K --> L[Final Output]
```

Loop back if more tasks or continue to next task.

## Data Flow Diagram (Text)

User Query
↓
┌─────────────────────────────────────────┐
│ Layer 1: Input                          │
│ Parse & normalize query                 │
└──────────────┬──────────────────────────┘
↓
┌─────────────────────────────────────────┐
│ Layer 2: Understanding                  │
│ Extract intent, retrieve context        │
└──────────────┬──────────────────────────┘
↓
┌─────────────────────────────────────────┐
│ Layer 3: Reasoning                      │
│ LLM chain-of-thought reasoning          │
└──────────────┬──────────────────────────┘
↓
┌─────────────────────────────────────────┐
│ Layer 4: Planning                       │
│ Decompose into task DAG                 │
└──────────────┬──────────────────────────┘
↓
┌─────────────────────────────────────────┐
│ Layer 5: State                          │
│ Initialize task state                   │
└──────────────┬──────────────────────────┘
↓
┌──────────────┐
│ Execution    │
│ Loop         │
└──────────────┘
↓
┌─────────────────────────────────────────┐
│ Layer 6: Decision                       │
│ Select next action                      │
└──────────────┬──────────────────────────┘
↓
┌─────────────────────────────────────────┐
│ Layer 7: Execution                      │
│ Run tool with timeout                   │
└──────────────┬──────────────────────────┘
↓
┌─────────────────────────────────────────┐
│ Layer 8: Resilience                     │
│ Error recovery & circuit breaker        │
└──────────────┬──────────────────────────┘
↓
┌─────────────────────────────────────────┐
│ Layer 9: Evaluation                     │
│ Score outcome & feedback                │
└──────────────┬──────────────────────────┘
↓
Loop back (if more tasks)
or
Continue to next task
↓
┌───────────────────────┐
│ Layer 10: Observability
│ Log all metrics       │
└───────────────────────┘
↓
┌───────────────────────┐
│ Layer 11: Infrastructure
│ Track cost & budget   │
└───────────────────────┘
↓
Final Output


#### Step 4: README Links Check

Run the link-check snippet in the repo root to verify internal docs links.
