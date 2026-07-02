"""Layer 1: Input normalization and validation."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from ..types import AgentInput


class InputLayer:
    @staticmethod
    def process(query: str, user_id: str, session_id: Optional[str] = None) -> AgentInput:
        """Validate and normalize raw input into an `AgentInput`.

        - Ensures `query` is non-empty.
        - Adds a timestamp (UTC) and a `context` containing `session_id`.
        - Returns an `AgentInput` instance with defaults filled.
        """
        q = (query or "").strip()
        if not q:
            raise ValueError("query must not be empty")

        if session_id is None:
            session_id = str(uuid.uuid4())

        context = {"session_id": session_id}

        return AgentInput(query=q, user_id=user_id, context=context, timestamp=datetime.now(timezone.utc))


__all__ = ["InputLayer"]
