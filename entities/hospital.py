from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
import json
import logging
from pathlib import Path
import simpy
import numpy as np
from enums.resource_type import ResourceType
from enums.patient_status import PatientStatus
from entities.doctor import Doctor
from entities.mri_machine import MRIMachine
from entities.bed import Bed
from entities.patient import Patient
from entities.triage_nurse import TriageNurse
from entities.operations_state import OperationsState, ResourceState, QueueEntry, PatientState
from services.time_service import TimeService
from services.preemption_agent import PreemptionAgent
from services.metrics_service import MetricsService
from services.logger_service import LoggerService


@dataclass(slots=True)
class Hospital:
    env: simpy.Environment
    num_doctors: int
    num_mri: int
    num_beds: int
    seed: int | None = None
    doctors: List[Doctor] = field(init=False)
    mri_machines: List[MRIMachine] = field(init=False)
    beds: List[Bed] = field(init=False)
    doctor_res: simpy.PreemptiveResource = field(init=False)
    mri_res: simpy.PreemptiveResource = field(init=False)
    bed_res: simpy.Resource = field(init=False)
    operations_state: OperationsState = field(init=False)
    operations_state_history: List[OperationsState] = field(default_factory=list)
    triage: TriageNurse = field(init=False)
    time_service: TimeService = field(init=False)
    agent: PreemptionAgent = field(init=False)
    metrics: MetricsService = field(init=False)
    waits: List[float] = field(default_factory=list)
    output_dir: Path = field(init=False)
    logger: logging.Logger = field(init=False)

    def __post_init__(self) -> None:
        if self.num_doctors <= 0 or self.num_mri <= 0 or self.num_beds <= 0:
            raise ValueError("All resource counts must be positive integers for a viable system configuration")
        # Prepare output directory and logging
        self.output_dir = Path(__file__).resolve().parents[1] / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        LoggerService.initialize(self.output_dir)
        self.logger = LoggerService.get_logger(__name__)
        # Resources
        self.doctors = [Doctor(i) for i in range(self.num_doctors)]
        self.mri_machines = [MRIMachine(i) for i in range(self.num_mri)]
        self.beds = [Bed(i) for i in range(self.num_beds)]
        self.doctor_res = simpy.PreemptiveResource(self.env, capacity=self.num_doctors)
        self.mri_res = simpy.PreemptiveResource(self.env, capacity=self.num_mri)
        self.bed_res = simpy.Resource(self.env, capacity=self.num_beds)
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
        self.operations_state = OperationsState(time=float(self.env.now), resources=resources, queues=queues, patients={})
        # services
        self.triage = TriageNurse(0)
        self.time_service = TimeService(self.seed)
        self.agent = PreemptionAgent()
        self.metrics = MetricsService()
        self.logger.info(
            "Hospital initialized: doctors=%d, mri=%d, beds=%d",
            self.num_doctors, self.num_mri, self.num_beds,
        )

    def _snapshot(self) -> None:
        # push a copy before updating operation state elsewhere
        self.operations_state_history.append(self.operations_state.copy())

    def update_usage(self, rtype: ResourceType, delta: int) -> None:
        self._snapshot()
        # update time snapshot
        self.operations_state.time = float(self.env.now)
        # update in_use for the specific resource
        res_state = self.operations_state.resources[rtype]
        res_state.in_use += delta
        # ensure bounds
        if res_state.in_use < 0:
            res_state.in_use = 0
        if res_state.in_use > res_state.capacity:
            res_state.in_use = res_state.capacity

    # --- Simulation flows encapsulated in Hospital ---
    def admit_patient(self, patient: Patient):
        arrival = self.env.now
        self.logger.info("Patient %s arrived at t=%.3f (needs=%s)", patient.id, arrival, patient.required_resource.name)
        # register patient arrival state
        self.operations_state.time = float(self.env.now)
        self.operations_state.patients[patient.id] = PatientState(
            id=patient.id,
            status=PatientStatus.ARRIVED,
            required_resource=patient.required_resource,
            arrival_time=float(arrival),
        )
        # triage
        patient.priority = self.triage.assign_priority(symptoms_score=float(np.random.rand()))
        pst = self.operations_state.patients[patient.id]
        pst.priority = patient.priority
        pst.status = PatientStatus.TRIAGED
        self.logger.debug("Patient %s triaged with priority=%s", patient.id, str(patient.priority))
        # preemption decision (mocked)
        decision = self.agent.decide(patient, self.operations_state)
        _ = decision
        # choose resource
        if patient.required_resource == ResourceType.DOCTOR:
            res = self.doctor_res
            svc = self.time_service.service_time_doctor()
            rtype = ResourceType.DOCTOR
        elif patient.required_resource == ResourceType.MRI:
            res = self.mri_res
            svc = self.time_service.service_time_mri()
            rtype = ResourceType.MRI
        else:
            res = self.bed_res
            svc = self.time_service.service_time_bed()
            rtype = ResourceType.BED
        # enqueue representation
        qe = QueueEntry(patient_id=patient.id, priority=patient.priority, arrival_time=float(arrival), required_resource=rtype)
        self.operations_state.queues[rtype].append(qe)
        pst.status = PatientStatus.WAITING
        self.logger.debug(
            "Patient %s enqueued for %s (queue_len=%d)",
            patient.id, rtype.name, len(self.operations_state.queues[rtype])
        )
        # request resource (preemptive where applicable)
        priority_value = int(patient.priority)
        is_preemptive = isinstance(res, simpy.PreemptiveResource)
        req_evt = res.request(priority=priority_value, preempt=True) if is_preemptive else res.request()
        with req_evt:
            yield req_evt
            # dequeue
            try:
                self.operations_state.queues[rtype].remove(qe)
            except ValueError:
                pass
            # start service
            pst.status = PatientStatus.IN_SERVICE
            pst.service_start_time = float(self.env.now)
            self.update_usage(rtype, +1)
            self.logger.info(
                "Patient %s started service at t=%.3f (resource=%s, svc_time=%.3f)",
                patient.id, self.env.now, rtype.name, float(svc)
            )
            try:
                yield self.env.timeout(svc)
                self.logger.info("Patient %s finished service at t=%.3f", patient.id, self.env.now)
            except simpy.Interrupt:
                pst.preemptions += 1
                pst.status = PatientStatus.PREEMPTED
                self.logger.warning("Patient %s preempted at t=%.3f (total_preemptions=%d)", patient.id, self.env.now, pst.preemptions)
                raise
            finally:
                self.update_usage(rtype, -1)
        # record wait (queueing delay)
        waited = (pst.service_start_time or float(self.env.now)) - arrival
        self.waits.append(float(waited))
        pst.status = PatientStatus.DISCHARGED
        self.logger.info(
            "Patient %s discharged at t=%.3f (waited=%.3f)", patient.id, self.env.now, float(waited)
        )

    def finalize(self) -> None:
        self.logger.info("Hospital finalizing: persisting data and generating plots")
        # Persist wait times to JSON for debugging before plotting
        avg = float(np.mean(self.waits)) if len(self.waits) else 0.0
        med = float(np.median(self.waits)) if len(self.waits) else 0.0
        stats = {
            "count": len(self.waits),
            "avg": avg,
            "median": med,
            "min": float(min(self.waits)) if len(self.waits) else 0.0,
            "max": float(max(self.waits)) if len(self.waits) else 0.0,
            "wait_times": self.waits,
        }
        json_path = self.output_dir / "wait_times.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)
        self.logger.info("Saved wait times JSON: %s (count=%d, avg=%.3f, med=%.3f)", str(json_path), stats["count"], stats["avg"], stats["median"])
        # Read back and validate
        with open(json_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        if loaded.get("count") != len(self.waits):
            self.logger.warning("Mismatch in wait count after reload: saved=%s now=%d", loaded.get("count"), len(self.waits))
        self.logger.debug("Reloaded JSON summary: avg=%.3f, med=%.3f, min=%.3f, max=%.3f", loaded.get("avg", 0.0), loaded.get("median", 0.0), loaded.get("min", 0.0), loaded.get("max", 0.0))
        # Now plot using the saved data (or in-memory) to ensure consistency
        self.metrics.plot_wait_times(loaded.get("wait_times", self.waits), self.output_dir / "wait_times.svg")
        self.logger.info("Saved plot: %s", str(self.output_dir / "wait_times.svg"))