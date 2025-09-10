from dataclasses import dataclass
from ..patient.patient import Patient
from ...enums.priority import Priority

@dataclass
class RoutingAgent:
    """Simple rule-based routing agent for patient resource assignment"""
    
    def should_assign_to_doctor(self, patient: Patient, priority: Priority) -> bool:
        """Determine if patient should be assigned to doctor (default: always true)"""
        return True
    
    def should_assign_urgent_bed(self, patient: Patient, priority: Priority) -> bool:
        """Determine if urgent patient should also get a bed"""
        return priority in [Priority.RED, Priority.ORANGE]