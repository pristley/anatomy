# Examples

This repository includes runnable examples under the top-level `examples/`
directory. Examples use the `backend` package on `PYTHONPATH` so they can be
run from the repository root.

Notable examples:

- `examples/simple_query_agent.py` — minimal single-agent usage (DOC-001).
- `examples/multi_agent_example.py` — demonstrates `AgentCoordinator` and
	concurrent agent runs (DOC-002).
- `examples/tool_integration_example.py` — shows invoking builtin tools
	such as `math_eval` (DOC-003).
- `examples/memory_usage_example.py` — shows episodic and semantic memory
	usage (DOC-004).
- `examples/multi_agent_demo.py` — additional coordinator/demo script.

Run examples with:

```bash
PYTHONPATH=.:backend .venv/bin/python3 examples/<example>.py
```

When adding examples: keep them small, deterministic, and ensure they
document any required environment variables (API keys, whitelists) at the
top of the script.
