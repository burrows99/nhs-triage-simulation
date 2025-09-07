from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import logging
from pathlib import Path
from enums.resource_type import ResourceType
from enums.patient_status import PatientStatus
from entities.doctor import Doctor
from entities.mri_machine import MRIMachine
from entities.bed import Bed
from entities.patient import Patient
from entities.triage_nurse import TriageNurse
from entities.operations_state import OperationsState, ResourceState, QueueEntry, PatientState
from services.time_service import TimeService
from services.metrics_service import MetricsService
from services.logger_service import LoggerService

@dataclass(slots=True)
class Hospital:
    num_doctors: int
    num_mri: int
    num_beds: int
    seed: int | None = None
    doctors: List[Doctor] = field(init=False)
    mri_machines: List[MRIMachine] = field(init=False)
    beds: List[Bed] = field(init=False)
    operations_state: OperationsState = field(init=False)
    triage: TriageNurse = field(init=False)
    time_service: TimeService = field(init=False)
    # PreemptionAgent now lives inside triage nurse; hospital queries triage for recommendations
    metrics: MetricsService = field(init=False)
    output_dir: Path = field(init=False)
    logger: logging.Logger = field(init=False)
    _alloc_idx: int = field(default=0, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        self._validate_config()
        self._setup_output_and_logging()
        self._init_resources()
        self._init_operations_state()
        self._init_services()

    # ---- Initialization helpers ----
    def _validate_config(self) -> None:
        if self.num_doctors <= 0 or self.num_mri <= 0 or self.num_beds <= 0:
            raise ValueError("All resource counts must be positive integers for a viable system configuration")

    def _setup_output_and_logging(self) -> None:
        # Prepare output directory and logging
        self.output_dir = Path(__file__).resolve().parents[1] / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        LoggerService.initialize(self.output_dir)
        self.logger = LoggerService.get_logger(__name__)

    def _init_resources(self) -> None:
        # Resources (domain-level references, not SimPy resources)
        self.doctors = [Doctor(i) for i in range(self.num_doctors)]
        self.mri_machines = [MRIMachine(i) for i in range(self.num_mri)]
        self.beds = [Bed(i) for i in range(self.num_beds)]

    def _init_operations_state(self) -> None:
        # initialize detailed operations state
        resources = {
            ResourceType.DOCTOR: ResourceState(ResourceType.DOCTOR, self.num_doctors, 0),
            ResourceType.MRI: ResourceState(ResourceType.MRI, self.num_mri, 0),
            ResourceType.BED: ResourceState(ResourceType.BED, self.num_beds, 0),
        }
        queues: dict[ResourceType, List[QueueEntry]] = {
            ResourceType.DOCTOR: [],
            ResourceType.MRI: [],
            ResourceType.BED: [],
        }
        self.operations_state = OperationsState(time=0.0, resources=resources, queues=queues, patients={})

    def _init_services(self) -> None:
        # services
        self.triage = TriageNurse(0)
        self.time_service = TimeService(self.seed)
        # decisions handled by triage nurse's embedded agent
        self.metrics = MetricsService()

    def _snapshot(self) -> None:
        # record snapshot in metrics (history-only source of truth)
        self.metrics.ingest(self.operations_state)

    def set_time(self, now: float) -> None:
        # engine should call this when simulation time advances before invoking hospital updates
        self.operations_state.time = float(now)

    def update_usage(self, rtype: ResourceType, delta: int, now: float) -> None:
        self.set_time(now)
        rs = self.operations_state.resources[rtype]
        rs.in_use = max(0, min(rs.capacity, rs.in_use + int(delta)))

    def on_patient_arrival(self, patient: Patient, now: float) -> ResourceType:
        # Advance time and register basic state first
        self.set_time(now)
        self.logger.info("Patient %s arrived at t=%.3f", patient.id, now)
        self.operations_state.patients[patient.id] = PatientState(
            id=patient.id,
            status=PatientStatus.ARRIVED,
            required_resource=None,
            arrival_time=float(now),
        )
        # Triage sets symptoms, priority and assigns the first resource to DOCTOR
        patient.priority = self.triage.assess_and_assign_priority(patient)
        pst = self.operations_state.patients[patient.id]
        pst.priority = patient.priority
        pst.status = PatientStatus.TRIAGED
        # Determine required resource based on triage output (must be provided by triage/agent)
        if patient.required_resource is None:
            raise ValueError("Patient required_resource not set by triage")
        rtype = patient.required_resource
        patient.required_resource = rtype
        pst.required_resource = rtype
        self.logger.debug("Patient %s triaged with priority=%s, first resource=%s", patient.id, str(patient.priority), rtype.name)
        # take a preemption recommendation from triage for auditability; execution occurs later
        decision = self.triage.recommend_preemption(patient, self.operations_state)
        # record decision in history snapshot
        self._snapshot()
        self.logger.info(
            "Preemption agent decision for patient %s: should_preempt=%s resource=%s target_index=%s",
            patient.id,
            str(decision.should_preempt),
            getattr(decision.resource_type, "name", None),
            str(decision.target_index),
        )
        return rtype

    def prepare_for_queue(self, patient: Patient, rtype: ResourceType, now: float) -> float:
        self.set_time(now)
        # enqueue representation
        qe = QueueEntry(patient_id=patient.id, priority=patient.priority, arrival_time=float(now), required_resource=rtype)
        self.operations_state.queues[rtype].append(qe)
        # sample planned service duration for simulation scheduling (history-derived metrics only)
        service_dur = self._sample_service_time(rtype)
        # tracked via history; no direct append of ad-hoc arrays
        pst = self.operations_state.patients[patient.id]
        pst.status = PatientStatus.WAITING
        self.logger.debug(
            "Patient %s enqueued for %s (queue_len=%d)",
            patient.id, rtype.name, len(self.operations_state.queues[rtype])
        )
        # snapshot the queue change
        self._snapshot()
        return float(service_dur)

    def _sample_service_time(self, rtype: ResourceType) -> float:
        if rtype == ResourceType.DOCTOR:
            return float(self.time_service.service_time_doctor())
        if rtype == ResourceType.MRI:
            return float(self.time_service.service_time_mri())
        return float(self.time_service.service_time_bed())

    def on_service_start(self, patient: Patient, rtype: ResourceType, now: float, planned_service_time: float) -> None:
        self.set_time(now)
        # dequeue if present
        q = self.operations_state.queues[rtype]
        self.operations_state.queues[rtype] = [e for e in q if e.patient_id != patient.id]
        pst = self.operations_state.patients[patient.id]
        pst.status = PatientStatus.IN_SERVICE
        pst.service_start_time = float(now)
        # tracked via history; no direct append of service start/duration arrays
        self.update_usage(rtype, +1, now)
        self.logger.info(
            "Patient %s started service at t=%.3f (resource=%s, svc_time=%.3f)",
            patient.id, now, rtype.name, float(planned_service_time)
        )
        # snapshot state after starting service
        self._snapshot()

    def should_preempt(self, patient: Patient, rtype: ResourceType, now: float) -> bool:
        """Consult triage for a preemption recommendation and record the decision in history.
        Returns True when a preemption should be executed for the given resource type.
        """
        decision = self.triage.recommend_preemption(patient, self.operations_state)
        # record decision in history snapshot for auditability
        self._snapshot()
        if not rtype.preemptible:
            self.logger.debug("Preemption is disallowed for resource %s; ignoring agent decision", rtype.name)
            return False
        self.logger.info(
            "Preemption agent decision at t=%.3f for patient %s on %s: should_preempt=%s target_index=%s",
            float(now), patient.id, rtype.name, str(decision.should_preempt), str(decision.target_index)
        )
        return bool(decision.should_preempt)

    def is_preemptive_resource(self, rtype: ResourceType) -> bool:
        """Whether the given resource type is modeled as preemptive in the system."""
        return rtype.preemptible

    def on_service_preempted(self, patient: Patient, rtype: ResourceType, now: float) -> None:
        self.set_time(now)
        pst = self.operations_state.patients[patient.id]
        pst.preemptions += 1
        pst.status = PatientStatus.PREEMPTED
        self.update_usage(rtype, -1, now)
        self.logger.warning(
            "Patient %s preempted at t=%.3f (total_preemptions=%d)", patient.id, now, pst.preemptions
        )
        self._snapshot()

    def on_service_complete(self, patient: Patient, rtype: ResourceType, now: float) -> Optional[ResourceType]:
        self.set_time(now)
        pst = self.operations_state.patients[patient.id]
        self.logger.info("Patient %s finished service at t=%.3f", patient.id, now)
        self.update_usage(rtype, -1, now)
        # record per-stage queue time (arrival -> first service start) for logging only; metrics derived from history
        arrival = pst.arrival_time
        queue_time = (pst.service_start_time or float(now)) - arrival
        # If doctor stage completed, determine the next required resource and continue the pathway
        if rtype == ResourceType.DOCTOR:
            # Use a doctor entity to make post-consultation decision (uses triage symptoms)
            doc = self.doctors[patient.id % len(self.doctors)]
            next_r = doc.decide_next_after_doctor(patient)
            patient.required_resource = next_r
            pst.required_resource = next_r
            pst.status = PatientStatus.ARRIVED  # will be set to WAITING when enqueued for next stage
            self.logger.info(
                "Patient %s routed to next resource: %s after doctor consultation",
                patient.id, next_r.name
            )
            self._snapshot()
            return next_r
        # Final stages (MRI or BED) discharge the patient; total time and waits computed from history in finalize
        total_time = float(now) - float(arrival)
        pst.status = PatientStatus.DISCHARGED
        self.logger.info(
            "Patient %s discharged at t=%.3f (queue_wait=%.3f, total_time=%.3f)",
            patient.id, now, float(queue_time), float(total_time)
        )
        self._snapshot()
        return None

    def finalize(self, sim_duration: float) -> None:
        # Delegate all metric computations and plotting to MetricsService using ingested history
        self.metrics.compute_and_export(self.output_dir, float(sim_duration))
        return