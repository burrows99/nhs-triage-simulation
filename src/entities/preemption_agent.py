import random
from typing import List
from .sub_entities.preemption_decision import PreemptionDecision

class PreemptionAgent:
    """AI agent for making preemption decisions (randomized)"""
    
    def __init__(self):
        self.decision_history = []
    
    def should_preempt(self, new_patient: 'Patient', busy_doctors: List['Doctor']) -> 'PreemptionDecision':
        """Randomly decide whether to preempt a doctor for a higher priority patient"""
        
        possible_responses = [
            PreemptionDecision(False, None, "No preemption needed", 0.0),
            PreemptionDecision(True, random.choice([doc.id for doc in busy_doctors]) 
                               if busy_doctors else None,
                               "Random preemption suggested", random.uniform(0.5, 0.95))
        ]
        
        decision = random.choice(possible_responses)
        
        self.decision_history.append({
            'timestamp': 0,  # Could hook into simpy env if needed
            'decision': decision,
            'new_patient_id': getattr(new_patient, 'id', None),
            'preempted_patient_id': decision.doctor_to_preempt
        })
        
        return decision
