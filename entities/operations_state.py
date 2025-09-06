from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enums.resource_type import ResourceType
from enums.priority import Priority
from enums.patient_status import PatientStatus

@dataclass(slots=True)
class ResourceState:
    resource_type: ResourceType
    capacity: int
    in_use: int = 0

@dataclass(slots=True)
class QueueEntry:
    patient_id: int
    priority: Priority
    arrival_time: float
    required_resource: ResourceType

@dataclass(slots=True)
class PatientState:
    id: int
    status: PatientStatus
    required_resource: Optional[ResourceType]
    arrival_time: float
    priority: Optional[Priority] = None
    service_start_time: Optional[float] = None
    preemptions: int = 0

@dataclass(slots=True)
class OperationsState:
    time: float
    resources: Dict[ResourceType, ResourceState] = field(default_factory=dict)
    queues: Dict[ResourceType, List[QueueEntry]] = field(default_factory=dict)
    patients: Dict[int, PatientState] = field(default_factory=dict)

    def copy(self) -> 'OperationsState':
        # Manual deep copy to keep dataclasses with slots lightweight
        new_resources = {k: ResourceState(v.resource_type, v.capacity, v.in_use) for k, v in self.resources.items()}
        new_queues = {k: [QueueEntry(e.patient_id, e.priority, e.arrival_time, e.required_resource) for e in v] for k, v in self.queues.items()}
        new_patients = {
            k: PatientState(v.id, v.status, v.required_resource, v.arrival_time, v.priority, v.service_start_time, v.preemptions)
            for k, v in self.patients.items()
        }
        return OperationsState(self.time, new_resources, new_queues, new_patients)