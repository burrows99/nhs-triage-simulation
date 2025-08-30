from triage_systems.base_triage import BaseTriageSystem
from typing import List
from model_providers.base import ModelProvider
import statistics

class MultiLLMBasedTriage(BaseTriageSystem):
    def __init__(self, providers: List[ModelProvider]):
        self.providers = providers
        
    def perform_triage(self, patient_data):
        system_prompt = """
        You are part of a multi-agent emergency triage system. 
        Analyze patient data and reach consensus on priority level (1-5).
        Provide detailed rationale and recommended actions.
        """
        
        decisions = []
        for provider in self.providers:
            provider.setup(system_prompt)
            decision = provider.generate_triage_decision(patient_data)
            if provider.validate_response(decision):
                decisions.append(decision)
        
        if not decisions:
            return {"error": "No valid responses from providers"}
        
        return {
            "consensus_priority": self._calculate_consensus(decisions),
            "rationales": [d.get('rationale', '') for d in decisions],
            "recommended_actions": list({action for d in decisions for action in d.get('recommended_actions', [])})
        }
    
    def _calculate_consensus(self, decisions):
        try:
            priorities = [d['priority'] for d in decisions if isinstance(d.get('priority'), int)]
            return round(statistics.mean(priorities))
        except statistics.StatisticsError:
            return 3