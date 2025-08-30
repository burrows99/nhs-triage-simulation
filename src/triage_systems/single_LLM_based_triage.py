from triage_systems.base_triage import BaseTriageSystem
from model_providers.base import ModelProvider

class SingleLLMBasedTriage(BaseTriageSystem):
    def __init__(self, provider: ModelProvider):
        self.provider = provider
        
    def perform_triage(self, patient_data):
        self.provider.setup("""
        You are an emergency triage system. Analyze patient vital signs, 
        symptoms and medical history to determine priority level (1-5).
        """)
        decision = self.provider.generate_triage_decision(patient_data)
        if self.provider.validate_response(decision):
            return decision
        return {"error": "Invalid triage response"}