from enum import Enum


class PatientStatus(Enum):
    """
    Patient status throughout the hospital journey.
    
    Status progression typically follows:
    ARRIVED -> WAITING_TRIAGE -> IN_TRIAGE -> WAITING_RESOURCE -> 
    IN_SERVICE -> PREEMPTED (optional) -> COMPLETED -> DISCHARGED
    
    Based on NHS patient flow tracking standards.
    Reference: NHS Patient Flow and Capacity Planning
    """
    ARRIVED = "arrived"                    # Just arrived at hospital
    WAITING_TRIAGE = "waiting_triage"      # Waiting for triage assessment
    IN_TRIAGE = "in_triage"                # Being assessed by triage nurse
    WAITING_RESOURCE = "waiting_resource"  # Waiting for assigned resource
    IN_SERVICE = "in_service"              # Currently receiving service
    PREEMPTED = "preempted"                # Service interrupted for higher priority
    COMPLETED = "completed"                # Service completed
    DISCHARGED = "discharged"              # Left the hospital
    
    @property
    def is_active(self) -> bool:
        """Whether patient is still active in the system."""
        return self != PatientStatus.DISCHARGED
    
    @property
    def is_waiting(self) -> bool:
        """Whether patient is in a waiting state."""
        waiting_states = {
            PatientStatus.WAITING_TRIAGE,
            PatientStatus.WAITING_RESOURCE
        }
        return self in waiting_states
    
    @property
    def is_receiving_service(self) -> bool:
        """Whether patient is currently receiving service."""
        service_states = {
            PatientStatus.IN_TRIAGE,
            PatientStatus.IN_SERVICE
        }
        return self in service_states
    
    def __str__(self) -> str:
        return self.value.replace('_', ' ').title()