from .types import AgentState, AgentInput

class Agent:
    """Minimal Agent orchestrator placeholder."""
    def __init__(self, config=None):
        self.config = config

    def run(self, agent_input: AgentInput) -> AgentState:
        return AgentState()
