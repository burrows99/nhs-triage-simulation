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
        Caller must ensure patient.required_resource is set by triage before doctor interaction.
        """
        if patient.required_resource is None:
            raise ValueError("Doctor cannot determine required_resource when none is set; triage must assign it")
        return patient.required_resource

    def decide_next_after_doctor(self, patient: Patient) -> ResourceType:
        """After consultation, use triage symptoms to route to MRI or Bed.
        Simplified rules:
        - If severe trauma or neurological impairment or very high pain -> MRI
        - Else -> Bed (observation/ward)
        """
        # Require symptoms to be present (set during triage)
        if getattr(patient, "symptoms", None) is None:
            raise ValueError("Patient has no triage symptoms; cannot determine next resource after doctor")
        s = patient.symptoms
        assert s is not None
        red_flag = (s.trauma_severity >= 0.7) or (s.consciousness_impairment >= 0.6) or (s.pain >= 0.85)
        if red_flag:
            return ResourceType.MRI
        # otherwise bed/observation
        return ResourceType.BED