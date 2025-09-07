from __future__ import annotations
from dataclasses import dataclass, field
import logging
from typing import Optional, Any, Dict, List, cast
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

    def _compute_rule_based_decision(self, patient: Patient, ops_state_summary: Dict[str, Any]) -> PreemptionDecision:
        # Deterministic rule-based policy using current state summary
        pr: Optional[Priority] = getattr(patient, "priority", None)
        rtype: Optional[ResourceType] = getattr(patient, "required_resource", None)
        if pr is None or rtype is None:
            return PreemptionDecision(False, None, None)
        # Only consider preemption for preemptible resources
        if not rtype.preemptible:
            return PreemptionDecision(False, None, None)
        # Extract queue information for the patient's required resource
        queues: Dict[str, List[Dict[str, Any]]] = cast(Dict[str, List[Dict[str, Any]]], ops_state_summary.get("queues", {}))
        q_list: List[Dict[str, Any]] = queues.get(rtype.name, [])
        # For high priority patients, preempt if queue is non-empty and all servers are busy
        resources: Dict[str, Dict[str, Any]] = cast(Dict[str, Dict[str, Any]], ops_state_summary.get("resources", {}))
        res_info: Dict[str, Any] = resources.get(rtype.name, {})
        in_use = int((res_info.get("in_use", 0) or 0))
        capacity = int((res_info.get("capacity", 0) or 0))
        queue_len = int((res_info.get("queue_len", len(q_list)) or len(q_list)))
        # Rule thresholds: IMMEDIATE always, VERY_URGENT when heavily loaded
        if pr == Priority.IMMEDIATE:
            # pick the lowest-priority target in queue (last position)
            if queue_len > 0 and in_use >= capacity and capacity > 0:
                target_idx = queue_len - 1
                return PreemptionDecision(True, rtype, target_idx)
            return PreemptionDecision(False, None, None)
        if pr == Priority.VERY_URGENT:
            # preempt only if load > 90% and queue exists
            util = float(in_use) / float(capacity) if capacity > 0 else 0.0
            if queue_len > 0 and util >= 0.9 and capacity > 0:
                target_idx = queue_len - 1
                return PreemptionDecision(True, rtype, target_idx)
            return PreemptionDecision(False, None, None)
        # Lower priorities do not trigger preemption in this baseline
        return PreemptionDecision(False, None, None)

    def decide(self, patient: Patient, ops_state: object) -> PreemptionDecision:
        # If ops_state exposes get_summary, use it for deterministic decision; otherwise fallback to random mock
        summary: Optional[Dict[str, Any]]
        try:
            summary_raw = ops_state.get_summary()  # type: ignore[attr-defined]
            summary = cast(Optional[Dict[str, Any]], summary_raw if isinstance(summary_raw, dict) else None)
        except Exception:
            summary = None
        if isinstance(summary, dict):
            decision = self._compute_rule_based_decision(patient, summary)
            rname = getattr(getattr(patient, "required_resource", None), "name", "")
            resources = cast(Dict[str, Dict[str, Any]], (summary.get("resources", {}) or {}))
            self.logger.debug(
                "Rule-based preemption decision for patient=%s: %s %s idx=%s (resource load=%s)",
                patient.id,
                decision.should_preempt,
                getattr(decision.resource_type, "name", None),
                decision.target_index,
                resources.get(rname, {}),
            )
            return decision
        # Fallback to stochastic mock policy
        score = self.mock_fetch(patient, ops_state)
        if score > 0.7 and patient.priority in (Priority.IMMEDIATE, Priority.VERY_URGENT):
            rtype = patient.required_resource or ResourceType.DOCTOR
            if not rtype.preemptible:
                return PreemptionDecision(False, None, None)
            return PreemptionDecision(True, rtype, 0)
        return PreemptionDecision(False, None, None)

    # New: initial resource recommendation to guide first-stage assignment at triage
    def recommend_initial_resource(self, patient: Patient) -> ResourceType:
        """Heuristic initial resource recommendation.
        Returns a ResourceType when a strong signal exists; defaults to DOCTOR otherwise.
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
        # No strong signal -> default to DOCTOR
        self.logger.debug("No strong signal; defaulting initial resource to DOCTOR for patient=%s", patient.id)
        return ResourceType.DOCTOR