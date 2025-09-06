from enum import Enum
from typing import Final


class ResourceType(Enum):
    """
    Types of hospital resources available in the simulation.
    
    Each resource type has different characteristics:
    - DOCTOR: Preemptive resource - can interrupt current patient for higher priority
    - MRI_MACHINE: Preemptive resource - can interrupt scans for emergencies
    - BED: Non-preemptive resource - patient must complete stay before release
    - TRIAGE_NURSE: Special resource for initial patient assessment
    
    Preemption policies based on NHS emergency care protocols.
    Reference: NHS Emergency Care Standards
    """
    DOCTOR = "doctor"
    MRI_MACHINE = "mri_machine"
    BED = "bed"
    TRIAGE_NURSE = "triage_nurse"
    
    @property
    def is_preemptive(self) -> bool:
        """Whether this resource type supports preemption."""
        preemptive_resources: Final[set[str]] = {
            "doctor", 
            "mri_machine"
        }
        return self.value in preemptive_resources
    
    @property
    def typical_service_time_minutes(self) -> tuple[float, float]:
        """Typical service time range (min, max) in minutes for this resource."""
        service_times: Final[dict[str, tuple[float, float]]] = {
            "doctor": (15.0, 45.0),        # Consultation time
            "mri_machine": (30.0, 90.0),   # MRI scan duration
            "bed": (120.0, 480.0),         # Bed occupancy time
            "triage_nurse": (5.0, 15.0)    # Triage assessment time
        }
        return service_times[self.value]
    
    def __str__(self) -> str:
        return self.value.replace('_', ' ').title()