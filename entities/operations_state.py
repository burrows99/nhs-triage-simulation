from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
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

    # New: Summarize the current operations state for decision-making (agent, logging, etc.)
    def get_summary(self) -> Dict[str, Any]:
        # Resources summary with capacity, usage, free slots, utilization and queue length
        resources_summary: Dict[str, Dict[str, float | int]] = {}
        for rt, rs in self.resources.items():
            qlen = len(self.queues.get(rt, []))
            free = max(0, int(rs.capacity) - int(rs.in_use))
            util = (float(rs.in_use) / float(rs.capacity)) if int(rs.capacity) > 0 else 0.0
            resources_summary[rt.name] = {
                "capacity": int(rs.capacity),
                "in_use": int(rs.in_use),
                "free": int(free),
                "utilization": float(util),
                "queue_len": int(qlen),
            }
        # Patients summary by status and by priority
        total_patients = len(self.patients)
        by_status: Dict[str, int] = {}
        by_priority: Dict[str, int] = {}
        for pst in self.patients.values():
            sname = getattr(pst.status, "name", str(pst.status))
            by_status[sname] = by_status.get(sname, 0) + 1
            pr = getattr(pst, "priority", None)
            if pr is not None:
                pname = getattr(pr, "name", str(pr))
                by_priority[pname] = by_priority.get(pname, 0) + 1
        # Queues summary with ordered entries (patient_id, priority, arrival_time)
        queues_summary: Dict[str, List[Dict[str, int | float | str]]] = {}
        for rt, q in self.queues.items():
            queues_summary[rt.name] = [
                {
                    "patient_id": int(e.patient_id),
                    "priority": getattr(e.priority, "name", str(e.priority)),
                    "arrival_time": float(e.arrival_time),
                }
                for e in q
            ]
        return {
            "time": float(self.time),
            "resources": resources_summary,
            "patients": {
                "total": int(total_patients),
                "by_status": by_status,
                "by_priority": by_priority,
            },
            "queues": queues_summary,
        }