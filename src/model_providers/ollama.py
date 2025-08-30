import json
from .base import ModelProvider
from typing import Dict, Any

class OllamaProvider(ModelProvider):
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.system_prompt = ""
    
    def setup(self, system_prompt: str):
        self.system_prompt = f"""{system_prompt}
        Always respond with VALID JSON format containing:
        - priority (integer 1-5)
        - rationale (string)
        - recommended_actions (array of strings)
        """
    
    def generate_triage_decision(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Actual Ollama API call would go here
            mock_response = '''{
                "priority": 2,
                "rationale": "Moderate respiratory distress",
                "recommended_actions": ["Oxygen therapy", "Chest X-ray"]
            }'''
            return json.loads(mock_response)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response"}
    
    def validate_response(self, response: Dict) -> bool:
        required_keys = {"priority", "rationale", "recommended_actions"}
        return all(key in response for key in required_keys)