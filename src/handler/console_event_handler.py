from typing import List
from ..entities.patient import Patient
from ..entities.doctor import Doctor
from ..entities.sub_entities.triage_assessment import TriageAssessment
from ..entities.sub_entities.preemption_decision import PreemptionDecision

class ConsoleEventHandler:
    """Console-based event handler for logging"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.events = []
    
    def _log(self, message: str, timestamp: float = 0.0):
        event = f"Time {timestamp:6.1f}: {message}"
        self.events.append(event)
        if self.verbose:
            print(event)
    
    def on_patient_arrival(self, patient: Patient):
        self._log(f"Patient {patient.id} arrives - {patient.condition}", patient.arrival_time)
    
    def on_triage_complete(self, patient: Patient, assessment: TriageAssessment):
        self._log(f"Patient {patient.id} triaged as {assessment.priority.name} - {assessment.reason}", 
                 assessment.timestamp)
    
    def on_treatment_start(self, patient: Patient, doctor: Doctor):
        self._log(f"{doctor.name} starts treating Patient {patient.id} ({patient.priority.name})",
                 patient.treatment_start_time or 0.0)
    
    def on_treatment_complete(self, patient: Patient, doctor: Doctor):
        self._log(f"{doctor.name} completed Patient {patient.id}")
    
    def on_preemption(self, decision: PreemptionDecision, affected_patients: List[Patient]):
        self._log(f"PREEMPTION: {decision.reason} - Affected: {[p.id for p in affected_patients]}")
