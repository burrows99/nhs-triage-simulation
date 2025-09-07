from __future__ import annotations
from dataclasses import dataclass
from enums.resource_type import ResourceType
from enums.priority import Priority
from entities.base import BaseResource
from entities.patient import Patient


@dataclass(slots=True)
class Doctor(BaseResource):
    def __post_init__(self) -> None:
        BaseResource.__post_init__(self)

    def decide_required_resource(self, patient: Patient) -> ResourceType:
        """
        Legacy compatibility: Do not assign DOCTOR here to avoid self-selection.
        Caller should set DOCTOR pre-visit (triage does this). If invoked, fall back to DOCTOR
        only when no required_resource yet; otherwise return the current requirement.
        """
        if patient.required_resource is None:
            return ResourceType.DOCTOR
        return patient.required_resource

    def decide_next_after_doctor(self, patient: Patient) -> ResourceType:
        """After consultation, use triage symptoms and priority to route to MRI or Bed.
        Simplified rules:
        - If severe trauma or neurological impairment or very high pain -> MRI
        - Else -> Bed (observation/ward)
        """
        # Safe defaults if symptoms missing
        if getattr(patient, "symptoms", None) is None:
            # Use priority fallback: high acuity more likely to need imaging
            pr: Priority = patient.priority
            if pr in (Priority.IMMEDIATE, Priority.VERY_URGENT):
                return ResourceType.MRI
            return ResourceType.BED
        s = patient.symptoms
        assert s is not None
        red_flag = (s.trauma_severity >= 0.7) or (s.consciousness_impairment >= 0.6) or (s.pain >= 0.85)
        if red_flag:
            return ResourceType.MRI
        # otherwise bed/observation
        return ResourceType.BED