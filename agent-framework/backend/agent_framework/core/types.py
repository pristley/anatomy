from typing import Any

class AgentInput:
    def __init__(self, query: str, user_id: str = None):
        self.query = query
        self.user_id = user_id

class AgentState:
    def __init__(self, result: Any = None):
        self.result = result
