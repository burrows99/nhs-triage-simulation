import attr
from collections import deque
from typing import Dict, Deque, Optional
from ..entity import Entity
from ..patient import Patient
from ....enums import HospitalAction
from ....utils.constants import TRIAGE_PRIORITIES, STEP_COUNTER, priority_rank


@attr.s(auto_attribs=True)
class Resource(Entity):
    """Base resource class for hospital resources like doctors, beds, and MRI machines."""
    allow_preemption: bool = True
    current_patient: Optional[Patient] = None
    queues: Dict[str, Deque[Patient]] = attr.ib(factory=lambda: {p: deque() for p in TRIAGE_PRIORITIES})
    bumped_patients: set[int] = attr.ib(factory=set)
    resource_type: str = "Generic"

    def assign_service_time(self, patient: Patient, current_time: int):
        """Assign service time to a patient."""
        duration = HospitalAction.ASSIGN_PATIENT.random_duration()
        patient.start_service_time = current_time
        patient.service_time = duration
        patient.finish_service_time = patient.start_service_time + duration

    def add_patient_to_queue(self, patient: Patient, target_priority: Optional[str] = None, bumped: bool = False):
        """Add a patient to the appropriate priority queue."""
        queue_priority = target_priority or patient.priority
        if queue_priority is None:
            queue_priority = TRIAGE_PRIORITIES[0]  # Default to highest priority
        if bumped and patient.priority:
            idx = max(priority_rank(patient.priority) - 1, 0)
            queue_priority = TRIAGE_PRIORITIES[idx]
            self.bumped_patients.add(patient.entity_id)
        self.queues[queue_priority].append(patient)

    def get_next_patient_from_queue(self) -> Optional[Patient]:
        """Get the next patient from the highest priority queue."""
        for p in TRIAGE_PRIORITIES:
            if self.queues[p]:
                return self.queues[p].popleft()
        return None

    def assign_patient(self, patient: Patient, current_time: int):
        """Assign a patient to this resource, handling preemption if necessary."""
        if self.current_patient is None:
            self._start_service(patient, current_time)
        else:
            self._maybe_preempt(patient, current_time)

    def _start_service(self, patient: Patient, current_time: int):
        """Start service for a patient."""
        self.assign_service_time(patient, current_time)
        self.current_patient = patient

    def _maybe_preempt(self, patient: Patient, current_time: int):
        """Check if current patient should be preempted by incoming patient."""
        if self.current_patient is None or self.current_patient.priority is None or patient.priority is None:
            self.add_patient_to_queue(patient)
            return
        curr_rank = priority_rank(self.current_patient.priority)
        incoming_rank = priority_rank(patient.priority)
        if self.allow_preemption and incoming_rank < curr_rank:
            preempted = self.current_patient
            self.add_patient_to_queue(preempted, bumped=True)
            self._start_service(patient, current_time)
        else:
            self.add_patient_to_queue(patient)

    def release_current_patient(self) -> Optional[Patient]:
        """Release the current patient and start service for the next patient in queue."""
        finished = self.current_patient
        self.current_patient = None
        next_patient = self.get_next_patient_from_queue()
        if next_patient:
            self._start_service(next_patient, current_time=next(STEP_COUNTER))
        return finished

    def status(self) -> str:
        """Get a string representation of the resource's current status."""
        qs = {p: list(q) for p, q in self.queues.items() if q}
        return f"{self.name} | Current: {self.current_patient} | Queues: {qs}"