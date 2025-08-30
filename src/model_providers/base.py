from abc import ABC, abstractmethod
from typing import Dict, Any

class ModelProvider(ABC):
    @abstractmethod
    def setup(self, system_prompt: str) -> None:
        """Initialize the model with system prompt"""
        pass

    @abstractmethod
    def get_model_response(self, prompt: str) -> str:
        """Get raw model response"""
        pass