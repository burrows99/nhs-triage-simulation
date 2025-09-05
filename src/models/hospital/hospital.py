import attr
import random
from functools import wraps
from typing import Dict, List, Optional
from ..entities.entity import Entity
from ..entities.patient import Patient
from ..entities.resources.resource import Resource
from ..simulation.snapshot import Snapshot
from ..systems.triage_system import TriageSystem
from ..agents.preemption_agent import PreemptionAgent
from ...enums import HospitalAction
from ...services.plotting_service import PlottingService
from ...utils.constants import STEP_COUNTER


def action(func):
    """Decorator for hospital actions that handles step counting and snapshot creation."""
    @wraps(func)
    def wrapper(self: "Hospital", *args, **kwargs):  # type: ignore
        step = next(STEP_COUNTER)

        patient = kwargs.get("patient") or (args[0] if args and isinstance(args[0], Patient) else None)
        resource = kwargs.get("resource") or (args[0] if args and isinstance(args[0], Resource) else None)
        action_type = kwargs.get("action_type") or HospitalAction[func.__name__.upper()]

        # Strict checks
        if func.__name__ in ["admit_patient", "assign_patient"] and not patient:
            raise ValueError(f"[Strict] Action '{func.__name__}' requires a Patient object")
        if func.__name__ in ["release_patient"] and not resource:
            raise ValueError(f"[Strict] Action '{func.__name__}' requires a Resource object")

        # Execute action
        result = func(self, *args, step=step, duration=action_type.random_duration(), **kwargs)

        # Take snapshot and append to history
        snap = Snapshot.take(self, step)
        self.history.append(snap)

        return result
    return wrapper


@attr.s(auto_attribs=True)
class Hospital(Entity):
    """Main hospital class that manages resources, patients, and simulation."""
    resources: Dict[str, List[Resource]] = attr.ib(factory=lambda: {"Doctor": [], "Bed": [], "MRI": []})
    history: List[Snapshot] = attr.ib(factory=list)
    triage_system: TriageSystem = attr.ib(factory=lambda: TriageSystem(0, "MTS Triage"))
    preemption_agent: PreemptionAgent = attr.ib(factory=lambda: PreemptionAgent(0, "Random Preemption"))
    plotting_service: Optional[PlottingService] = None

    def add_resource(self, resource: Resource):
        """Add a resource to the hospital."""
        self.resources[resource.resource_type].append(resource)

    def _get_resource_by_id(self, resource_id: int) -> Optional[Resource]:
        """Get a resource by its ID."""
        for reslist in self.resources.values():
            for r in reslist:
                if r.entity_id == resource_id:
                    return r
        return None

    def execute_preemption(self, patient: Patient, step: int) -> bool:
        """Execute preemption logic for a patient."""
        decision = self.preemption_agent.should_preempt(self.resources, patient)
        if not decision["preempt"]:
            return False
        target_res = self._get_resource_by_id(decision["target_resource_id"])
        if target_res is None:
            return False
        if target_res.current_patient:
            preempted = target_res.current_patient
            target_res.add_patient_to_queue(preempted, target_priority=decision["target_queue"], bumped=True)
        target_res.assign_patient(patient, current_time=step)
        return True

    @action
    def admit_patient(self, patient: Patient, step: int, duration: int, **kwargs):
        """Admit a patient to the hospital."""
        patient.arrival_time = step
        self.triage_system.assign_priority(patient)
        preempted = self.execute_preemption(patient, step)
        if not preempted:
            rtype = random.choice(list(self.resources.keys()))
            target_res = random.choice(self.resources[rtype])
            target_res.add_patient_to_queue(patient)

    @action
    def allocate_resources(self, step: int, duration: int, **kwargs):
        """Allocate resources to waiting patients."""
        for reslist in self.resources.values():
            for res in reslist:
                next_patient = res.get_next_patient_from_queue()
                if next_patient:
                    res.assign_patient(next_patient, current_time=step)

    @action
    def release_patient(self, resource: Resource, step: int, duration: int, **kwargs):
        """Release a patient from a resource."""
        return resource.release_current_patient()