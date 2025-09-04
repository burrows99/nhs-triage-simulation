import random
from .base import BaseTriageSystem
from ..entities.patient import Patient
from ..entities.sub_entities.triage_assessment import TriageAssessment
from ..enums.Triage import Priority

class RandomTriageSystem(BaseTriageSystem):
    """Simple random triage system with purely random priority assignment"""
    
    def __init__(self, system_id: str = "RANDOM_TRIAGE_001"):
        self.system_id = system_id
        self.assessments_completed = 0
    
    def assess_patient(self, patient: Patient, current_time: float = 0.0) -> TriageAssessment:
        """Assess patient using completely random priority assignment"""
        # Randomly assign priority
        priority = random.choice(list(Priority))
        
        # Generate simple reason
        reason = f"Random triage assessment: {patient.condition} assigned {priority.name} priority"
        
        # Random treatment time based on priority
        base_time = priority.value * 10
        treatment_time = base_time * random.uniform(0.8, 1.2)
        
        # Create assessment
        assessment = TriageAssessment(
            priority=priority,
            reason=reason,
            estimated_treatment_time=treatment_time,
            timestamp=current_time
        )
        
        self.assessments_completed += 1
        return assessment