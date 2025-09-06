from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from enums.priority import Priority
from enums.resource_type import ResourceType
from enums.patient_status import PatientStatus
from entities.base import BaseEntity

@dataclass(slots=True)
class Patient(BaseEntity):
    required_resource: ResourceType
    arrival_time: float
    priority: Priority = field(default=Priority.NON_URGENT)
    status: PatientStatus = field(default=PatientStatus.ARRIVED)
    start_wait_time: Optional[float] = field(default=None)
    service_start_time: Optional[float] = field(default=None)
    service_end_time: Optional[float] = field(default=None)

    def __post_init__(self) -> None:
        BaseEntity.__post_init__(self)
        if self.arrival_time < 0:
            raise ValueError("arrival_time must be >= 0 to preserve simulation causality")

    def wait_duration(self) -> Optional[float]:
        if self.service_start_time is None:
            return None
        if self.start_wait_time is None:
            return 0.0
        return float(self.service_start_time - self.start_wait_time)

    def service_duration(self) -> Optional[float]:
        if self.service_start_time is None or self.service_end_time is None:
            return None
        return float(self.service_end_time - self.service_start_time)