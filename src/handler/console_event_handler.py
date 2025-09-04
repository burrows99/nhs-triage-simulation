from typing import List
from ..entities.patient import Patient
from ..entities.doctor import Doctor
from ..entities.sub_entities.triage_assessment import TriageAssessment
from ..entities.sub_entities.preemption_decision import PreemptionDecision
from ..utils.logger import get_logger, EventType

class ConsoleEventHandler:
    """Event handler using centralized logging system"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.events = []
        self.logger = get_logger()
    
    def _log(self, message: str, timestamp: float = 0.0, event_type: EventType = EventType.SYSTEM_STATE, data: dict = None):
        """Log event using centralized logger"""
        event = f"Time {timestamp:6.1f}: {message}"
        self.events.append(event)
        
        if self.verbose:
            self.logger.log_event(
                timestamp=timestamp,
                event_type=event_type,
                message=message,
                data=data or {},
                source="console_event_handler"
            )
    
    def on_patient_arrival(self, patient: Patient):
        self._log(
            f"Patient {patient.id} arrives - {patient.condition}", 
            patient.arrival_time,
            EventType.PATIENT_ARRIVAL,
            {"patient_id": patient.id, "condition": patient.condition}
        )
    
    def on_triage_complete(self, patient: Patient, assessment: TriageAssessment, current_time: float = None):
        timestamp = current_time if current_time is not None else assessment.timestamp
        self._log(
            f"Patient {patient.id} triaged as {assessment.priority.name} - {assessment.reason}", 
            timestamp,
            EventType.TRIAGE_COMPLETE,
            {
                "patient_id": patient.id, 
                "priority": assessment.priority.name, 
                "reason": assessment.reason
            }
        )
    
    def on_treatment_start(self, patient: Patient, doctor: Doctor):
        self._log(
            f"{doctor.name} starts treating Patient {patient.id} ({patient.priority.name})",
            patient.treatment_start_time or 0.0,
            EventType.TREATMENT_START,
            {
                "patient_id": patient.id, 
                "doctor_id": doctor.id, 
                "doctor_name": doctor.name,
                "priority": patient.priority.name
            }
        )
    
    def on_treatment_complete(self, patient: Patient, doctor: Doctor, current_time: float = None):
        timestamp = current_time if current_time is not None else 0.0
        wait_time = getattr(patient, 'wait_time', 0.0)
        self._log(
            f"Treatment completed: Doctor {doctor.id} finished Patient {patient.id} (wait: {wait_time:.1f}min)", 
            timestamp,
            EventType.TREATMENT_COMPLETE,
            {
                "patient_id": patient.id, 
                "doctor_id": doctor.id, 
                "doctor_name": doctor.name,
                "wait_time": wait_time
            }
        )
    
    def on_preemption(self, decision: PreemptionDecision, affected_patients: List[Patient]):
        self._log(
            f"PREEMPTION: {decision.reason} - Affected: {[p.id for p in affected_patients]}",
            decision.timestamp,
            EventType.PREEMPTION_EXECUTED,
            {
                "decision_reason": decision.reason,
                "affected_patient_ids": [p.id for p in affected_patients],
                "doctor_to_preempt": decision.doctor_to_preempt,
                "confidence": decision.confidence
            }
        )
