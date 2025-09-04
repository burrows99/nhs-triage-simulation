from typing import Protocol
from ..entities.patient import Patient
from ..entities.sub_entities.triage_assessment import TriageAssessment

class TriageSystem(Protocol):
    """Interface for triage assessment systems"""
    def assess_patient(self, patient: Patient) -> TriageAssessment: ...
