# Layer 1: Input

## Overview
Layer 1 handles input normalization, validation, and early sanitization. It
transforms raw user requests (HTTP payloads, CLI inputs, or example scripts)
into the canonical `Goal` / `AgentInput` structures consumed by downstream
layers.

## Responsibilities
- Validate incoming payloads and reject malformed requests.
- Normalize encoding and whitespace, strip unsafe content.
- Attach metadata (user id, request id, timestamp) and produce `AgentInput`.

## Data Flow

User input → `InputLayer.process()` → `AgentInput` (text, user_id, meta)

## Key Classes

### `InputLayer`
Responsible for parsing and normalizing raw input and producing the
canonical `AgentInput`.

````python
class InputLayer:
	def process(self, raw_text: str, user_id: str) -> AgentInput:
		"""Normalize, validate and return AgentInput."""
````

## Example

````python
from agent_framework.core.layers._01_input import InputLayer

layer = InputLayer()
inp = layer.process("  How do I write unit tests?  ", "user1")
````

## Testing
See `backend/tests/test_layers/test_layer_1.py` for unit tests that exercise
validation, trimming, and metadata attachment.

## Common Issues & Fixes
- Empty input: raise `ValueError` and return a helpful error message.
- Non-UTF8 payloads: normalize to UTF-8 and reject invalid bytes.

## See Also
- Layer 2: Understanding
