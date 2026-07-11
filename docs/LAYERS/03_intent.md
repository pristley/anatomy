# Layer 3: Intent (Intent Extraction)

## Overview
The Intent layer isolates the user's primary goal from the understood text
and produces a normalized intent representation for planning and execution.
Intent extraction in this project is split between the Understanding layer
and refinement from the Reasoning Core.

## Responsibilities
- Identify the primary actionable intent.
- Map free-form text to canonical intent labels.
- Provide intent metadata for planner heuristics.

## Data Flow

`Understood` (intent candidates) → `IntentExtractor` → `Intent` (label, args)

## Key Classes

### `IntentExtractor`
Identifies and normalizes intent labels from parsed understanding.

````python
class IntentExtractor:
	def extract(self, understood: Dict[str, Any]) -> Dict[str, Any]:
		"""Return canonical intent and normalized args."""
````

## Example

````python
from agent_framework.core.layers._03_intent import IntentExtractor

ie = IntentExtractor()
intent = ie.extract(understood)
````

## Testing
See `backend/tests/` for intent-related integration tests.

## Common Issues & Fixes
- Ambiguous intents: use reasoning to disambiguate or prompt for clarification.
- Unknown intent labels: add mappings to the capability registry.

## See Also
- Layer 2: Understanding
- Layer 3 (Reasoning): `docs/LAYERS/03_reasoning.md`
