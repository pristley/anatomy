# Layer 2: Understanding

## Overview
The Understanding layer turns canonical input (`AgentInput` / `Goal`) into a
structured representation: intents, entities, and contextual fields used by
the planner and reasoner.

## Responsibilities
- Parse natural language to extract intent and entities.
- Normalize synonyms and map expressions to known tool capabilities.
- Retrieve initial context (KB hits) and attach to the understanding result.

## Data Flow

`AgentInput` → `PerceptionEngine` / `UnderstandingLayer` → `Understood` (intent, entities, context)

## Key Classes

### `UnderstandingLayer`
Coordinates NLP parsing and optional knowledge retrieval.

````python
class UnderstandingLayer:
	def understand(self, agent_input: AgentInput) -> Dict[str, Any]:
		"""Return structured understanding for planner and reasoner."""
````

## Implementation Details
- Supports pluggable parsers (rule-based or model-backed).
- Optionally calls a `KnowledgeRetriever` to enrich context.

## Example

````python
from agent_framework.core.layers._02_understanding import UnderstandingLayer

layer = UnderstandingLayer()
understood = layer.understand(agent_input)
````

## Testing
See `backend/tests/test_layers/test_layer_2.py`.

## Common Issues & Fixes
- Overly broad intent: tighten parser rules or prompt engineering for model-backed parsers.
- Missing context: ensure `KnowledgeRetriever` is configured and available.

## See Also
- Layer 1: Input
- Layer 3: Reasoning
