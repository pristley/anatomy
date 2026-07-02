from .llm_interface import LLMInterface

class ClaudeClient(LLMInterface):
    def generate(self, prompt: str) -> str:
        return "claude response"
