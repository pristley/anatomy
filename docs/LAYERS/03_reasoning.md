# Layer 3: Reasoning Core

## Overview
The Reasoning Core uses the LLM to perform chain-of-thought reasoning over the
understood query and context.

## Responsibilities
- Invoke LLM with reasoning prompt
- Generate reasoning trace
- Track tokens and cost
- Return structured reasoning output

## Data Flow

Input (understood query + context)
↓
ReasoningCore.reason()
├─ Build prompt with CoT instructions
├─ Call LLM API
├─ Parse response
└─ Return reasoning trace + metrics
↓
Output (reasoning_output, tokens_used, cost)


## Key Classes

### ReasoningCore
Handles LLM-based reasoning with chain-of-thought.

````python
class ReasoningCore:
	async def reason(self, understood: Dict[str, Any]) -> Dict[str, Any]:
		"""Perform reasoning over understood query."""
		# Implementation details
````

## Implementation Details

### Reasoning Prompt Strategy
- Uses chain-of-thought (CoT) prompting
- Includes examples for in-context learning
- Tracks token usage and cost

### Error Handling
- LLM API timeouts → retry with backoff
- Invalid responses → fallback to simple response
- Token limits → truncate context as needed

## Performance Characteristics
- Typical latency: 500-2000ms (depends on LLM)
- Token usage: 200-2000 tokens per query
- Cost: $0.001-$0.01 per query

## Example Usage

````python
from agent_framework.core.layers.reasoning import ReasoningCore

reasoning = ReasoningCore(llm_client)
result = await reasoning.reason({
	"parsed_query": "How to optimize Python?",
	"kb_results": ["Python docs", "Best practices"]
})

print(result["reasoning_output"])  # Reasoning trace
print(result["tokens_used"])       # Token count
print(result["cost"])              # Cost in USD
````

## Testing

See `backend/tests/test_layers/test_layer_3.py` for comprehensive tests.

## Common Issues & Fixes

### Issue: Reasoning timeout
**Cause:** LLM is slow or API is overloaded
**Fix:** Increase timeout in config or use faster model

### Issue: Nonsensical reasoning output
**Cause:** Poor prompt or LLM confusion
**Fix:** Refine prompt, provide better context examples

## See Also
- Layer 2: Understanding (context preparation)
- Layer 4: Planning (uses reasoning output)
- docs/GLOSSARY.md (terminology)
