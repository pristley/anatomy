from ..types import AgentInput
from datetime import datetime
import uuid


class InputLayer:
    def process(self, query: str, user_id: str = None) -> AgentInput:
        if not query or not query.strip():
            raise ValueError("query must not be empty")

        ctx = {
            "session_id": str(uuid.uuid4()),
            "timezone": "UTC",
        }

        return AgentInput(query=query.strip(), user_id=user_id, context=ctx, timestamp=datetime.utcnow())
