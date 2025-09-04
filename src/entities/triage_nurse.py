import random
from ..enums.Triage import Priority
from .sub_entities.triage_assessment import TriageAssessment

class TriageNurse:
    """MTS (Manchester Triage System) implementation with random responses"""
    
    def assess_patient(self, patient) -> TriageAssessment:
        """Randomly assess patient using MTS priorities"""
        priority = random.choice(list(Priority))
        reason_text = f"Randomly assigned priority {priority.name}"
        
        # Estimate treatment time based on priority with some random factor
        base_time = priority.value * 10  # Simple mapping
        treatment_time = base_time * random.uniform(0.8, 1.2)
        
        return TriageAssessment(
            priority=priority,
            reason=reason_text,
            estimated_treatment_time=treatment_time
        )