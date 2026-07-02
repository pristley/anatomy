from abc import ABC, abstractmethod

class ToolInterface(ABC):
    @abstractmethod
    def run(self, params: dict) -> dict:
        pass
