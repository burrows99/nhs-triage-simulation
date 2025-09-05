import attr
from typing import Optional, Dict, Any
from .entity import Entity
from ...enums import TriagePriority, PresentingComplaint, ArrivalMode


@attr.s(auto_attribs=True)
class Patient(Entity):
    """Patient entity with triage priority and service time tracking, extended for Manchester Triage System."""
    priority: Optional[str] = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.in_(TriagePriority.get_values()))
    )
    service_time: Optional[int] = None
    arrival_time: Optional[int] = None
    start_service_time: Optional[int] = None
    finish_service_time: Optional[int] = None

    # --- MTS-specific fields ---
    presenting_complaint: Optional[str] = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.in_([c.value for c in PresentingComplaint]))
    )
    vital_signs: Optional[Dict[str, Any]] = attr.ib(factory=dict)  # e.g., {"HR": 80, "BP": "120/80"}
    age: Optional[int] = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.and_(attr.validators.instance_of(int), attr.validators.in_(range(0, 151))))
    )
    arrival_mode: Optional[str] = attr.ib(
        default=None,
        validator=attr.validators.optional(attr.validators.in_([m.value for m in ArrivalMode]))
    )
    preempted_count: int = 0

    history: str = ""

    @property
    def wait_time(self) -> Optional[int]:
        """Calculate wait time from arrival to start of service."""
        if self.arrival_time is not None and self.start_service_time is not None:
            return self.start_service_time - self.arrival_time
        return None

    @property
    def actual_service_time(self) -> Optional[int]:
        """Calculate actual service time from start to finish."""
        if self.start_service_time is not None and self.finish_service_time is not None:
            return self.finish_service_time - self.start_service_time
        return None

    @property
    def length_of_stay(self) -> Optional[int]:
        """Calculate total length of stay from arrival to finish."""
        if self.arrival_time is not None and self.finish_service_time is not None:
            return self.finish_service_time - self.arrival_time
        return None
