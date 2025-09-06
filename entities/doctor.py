from __future__ import annotations
from dataclasses import dataclass
from enums.resource_type import ResourceType
from entities.base import BaseResource
from entities.patient import Patient

@dataclass(slots=True)
class Doctor(BaseResource):
    def __post_init__(self) -> None:
        BaseResource.__post_init__(self)

    def decide_required_resource(self, patient: Patient) -> ResourceType:
        """
        Decide which resource the patient should receive next.
        Simple deterministic policy based on patient id to distribute load across
        Doctor -> MRI -> Bed in a round-robin fashion.
        """
        pid = int(patient.id)
        mod = pid % 3
        if mod == 0:
            return ResourceType.DOCTOR
        elif mod == 1:
            return ResourceType.MRI
        else:
            return ResourceType.BED