from __future__ import annotations
from dataclasses import dataclass, field
import logging
from typing import Optional
import numpy as np
from enums.resource_type import ResourceType
from enums.priority import Priority
from entities.patient import Patient
from services.logger_service import LoggerService

@dataclass(slots=True)
class PreemptionDecision:
    should_preempt: bool
    resource_type: Optional[ResourceType]
    target_index: Optional[int]

    def __post_init__(self) -> None:
        if self.should_preempt:
            if self.resource_type is None or self.target_index is None:
                raise ValueError("resource_type and target_index required when should_preempt is True")

@dataclass(slots=True)
class PreemptionAgent:
    logger: logging.Logger = field(init=False, repr=False, compare=False)
    def __post_init__(self) -> None:
        self.logger = LoggerService.get_logger(__name__)

    def mock_fetch(self, patient: Patient, ops_state: object) -> float:
        # stand-in for remote model score; returns 0..1
        score = float(np.random.rand())
        self.logger.debug(
            "Preemption mock score=%.3f for patient=%s (priority=%s, resource=%s)",
            score, patient.id, getattr(patient.priority, "name", str(patient.priority)), getattr(patient.required_resource, "name", str(patient.required_resource))
        )
        return score

    def decide(self, patient: Patient, ops_state: object) -> PreemptionDecision:
        # Randomized policy for now; later integrate AI policy
        score = self.mock_fetch(patient, ops_state)
        if score > 0.7 and patient.priority in (Priority.IMMEDIATE, Priority.VERY_URGENT):
            # choose a resource type matching patient's need, and a placeholder index 0
            rtype = ResourceType.DOCTOR if patient.required_resource == ResourceType.DOCTOR else (
                ResourceType.MRI if patient.required_resource == ResourceType.MRI else ResourceType.BED
            )
            decision = PreemptionDecision(True, rtype, 0)
            self.logger.info("Preemption decided: %s on %s (target_index=%d)", decision.should_preempt, rtype.name, decision.target_index)
            return decision
        decision = PreemptionDecision(False, None, None)
        self.logger.debug("Preemption decided: %s", decision.should_preempt)
        return decision

    # New: initial resource recommendation to guide first-stage assignment at triage
    def recommend_initial_resource(self, patient: Patient) -> Optional[ResourceType]:
        """Heuristic initial resource recommendation.
        Returns a ResourceType when a strong signal exists, else None to allow default (DOCTOR).
        """
        s = getattr(patient, "symptoms", None)
        pr: Optional[Priority] = getattr(patient, "priority", None)
        try:
            # If life-threatening indicators, see a doctor immediately
            if s is not None:
                if s.consciousness_impairment >= 0.9 or s.respiration_distress >= 0.9 or s.bleeding >= 0.9:
                    self.logger.debug("Initial resource recommended=DOCTOR for patient=%s due to critical vital signal", patient.id)
                    return ResourceType.DOCTOR
                # Significant trauma with high pain -> prioritize MRI imaging first
                if s.trauma_severity >= 0.85 and (pr in (Priority.VERY_URGENT, Priority.URGENT, Priority.IMMEDIATE)):
                    self.logger.debug("Initial resource recommended=MRI for patient=%s due to high trauma severity", patient.id)
                    return ResourceType.MRI
            # Priority alone can force DOCTOR
            if pr in (Priority.IMMEDIATE, Priority.VERY_URGENT):
                self.logger.debug("Initial resource recommended=DOCTOR for patient=%s due to high priority=%s", patient.id, getattr(pr, "name", pr))
                return ResourceType.DOCTOR
        except Exception as e:
            self.logger.debug("Initial resource recommendation error for patient=%s: %s", patient.id, e)
        # No strong signal; allow default path
        return None