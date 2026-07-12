# Troubleshooting Guide

## Common Issues

### Issue 1: "CLAUDE_API_KEY is not set"
**Symptom:** `RuntimeError: CLAUDE_API_KEY is required in production`
**Cause:** Environment variable not configured
**Solution:**
```bash
export CLAUDE_API_KEY="sk-ant-..."
# or add to .env file:
echo "CLAUDE_API_KEY=sk-ant-..." >> .env
```

### Issue 2: Queries timeout after 30 seconds
**Symptom:** Task execution times out
**Cause:** Complex query or slow LLM
**Solution:**
```python
from agent_framework.config import AgentConfig

config = AgentConfig(timeout_ms=60000)  # 60 seconds
agent = Agent(config=config)
```

### Issue 3: Memory grows unbounded
**Symptom:** Process uses more RAM over time
**Cause:** Memory system not evicting old entries
**Solution:**
```python
# Clear old memory entries periodically
agent.memory.cleanup(max_age_hours=24)
```

### Issue 4: Subagent doesn't return result
**Symptom:** `run_with_subagents` hangs or times out
**Cause:** Subagent error not propagated
**Solution:**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python your_script.py  # Now see subagent errors
```

## Performance Tuning

### Slow Queries
1. Check layer latencies: `scripts/benchmark.py`
2. Most likely: Layer 3 (Reasoning - LLM call)
3. Solutions:
   - Use faster LLM model
   - Increase LLM timeout
   - Reduce context size

### High Memory Usage
1. Check episodic memory size
2. Implement memory cleanup
3. Use semantic memory filtering

### High API Costs
1. Monitor token usage per layer
2. Reduce max_tokens in config
3. Batch LLM requests

## Testing

### Run All Tests
```bash
cd backend
pytest tests/ -v
```

### Run Specific Test
```bash
pytest tests/test_layers/test_layer_7.py -v
```

### Check Coverage
```bash
pytest tests/ --cov=agent_framework --cov-report=html
```

## Getting Help

- Documentation: `docs/ARCHITECTURE.md`
- Examples: `examples/` directory
- Issues: GitHub issues
- API docs: `http://localhost:8000/docs` (after starting server)
