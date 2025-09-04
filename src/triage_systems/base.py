from abc import ABC, abstractmethod
from ..entities.patient import Patient
from ..entities.sub_entities.triage_assessment import TriageAssessment

class BaseTriageSystem(ABC):
    """Abstract base class for triage assessment systems"""
    
    @abstractmethod
    def assess_patient(self, patient: Patient, current_time: float = 0.0) -> TriageAssessment:
        """Assess patient and return triage assessment with priority and treatment time"""
        pass
