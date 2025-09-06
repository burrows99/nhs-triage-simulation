from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
import json
import logging
from pathlib import Path
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
    num_doctors: int
    num_mri: int
    num_beds: int
    seed: int | None = None
    doctors: List[Doctor] = field(init=False)
    mri_machines: List[MRIMachine] = field(init=False)
    beds: List[Bed] = field(init=False)
    operations_state: OperationsState = field(init=False)
    operations_state_history: List[OperationsState] = field(default_factory=list)
    triage: TriageNurse = field(init=False)
    time_service: TimeService = field(init=False)
    agent: PreemptionAgent = field(init=False)
    metrics: MetricsService = field(init=False)
    waits: List[float] = field(default_factory=list)
    queue_waits: List[float] = field(default_factory=list)
    arrivals_by_resource: dict[ResourceType, List[float]] = field(init=False)
    service_times_by_resource: dict[ResourceType, List[float]] = field(init=False)
    output_dir: Path = field(init=False)
    logger: logging.Logger = field(init=False)
    _alloc_idx: int = field(default=0, init=False, repr=False, compare=False)
    # utilization tracking (time-integrated in_use across horizon)
    util_area_by_resource: dict[ResourceType, float] = field(init=False)
    last_util_update_time: float = field(default=0.0, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.num_doctors <= 0 or self.num_mri <= 0 or self.num_beds <= 0:
            raise ValueError("All resource counts must be positive integers for a viable system configuration")
        # Prepare output directory and logging
        self.output_dir = Path(__file__).resolve().parents[1] / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        LoggerService.initialize(self.output_dir)
        self.logger = LoggerService.get_logger(__name__)
        # Resources (domain-level references, not SimPy resources)
        self.doctors = [Doctor(i) for i in range(self.num_doctors)]
        self.mri_machines = [MRIMachine(i) for i in range(self.num_mri)]
        self.beds = [Bed(i) for i in range(self.num_beds)]
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
        # services
        self.triage = TriageNurse(0)
        self.time_service = TimeService(self.seed)
        self.agent = PreemptionAgent()
        self.metrics = MetricsService()
        self.logger.info(
            "Hospital initialized: doctors=%d, mri=%d, beds=%d",
            self.num_doctors, self.num_mri, self.num_beds,
        )
        # tracking for modeled waits
        self.arrivals_by_resource = {
            ResourceType.DOCTOR: [],
            ResourceType.MRI: [],
            ResourceType.BED: [],
        }
        self.service_times_by_resource = {
            ResourceType.DOCTOR: [],
            ResourceType.MRI: [],
            ResourceType.BED: [],
        }
        # utilization areas start at 0
        self.util_area_by_resource = {
            ResourceType.DOCTOR: 0.0,
            ResourceType.MRI: 0.0,
            ResourceType.BED: 0.0,
        }

    def _snapshot(self) -> None:
        # push a copy before updating operation state elsewhere
        self.operations_state_history.append(self.operations_state.copy())

    def set_time(self, now: float) -> None:
        # engine should call this when simulation time advances before invoking hospital updates
        self._integrate_utilization_until(float(now))

    def update_usage(self, rtype: ResourceType, delta: int, now: float) -> None:
        self._snapshot()
        # integrate utilization up to this moment before changing in_use
        self._integrate_utilization_until(float(now))
        res_state = self.operations_state.resources[rtype]
        res_state.in_use = max(0, min(res_state.capacity, res_state.in_use + delta))

    def _integrate_utilization_until(self, now: float) -> None:
        now = float(now)
        # accumulate area = sum(in_use[r]) * delta_t for all resources across the elapsed interval
        if now <= self.last_util_update_time:
            self.operations_state.time = float(now)
            return
        delta_t = now - self.last_util_update_time
        for rtype, res_state in self.operations_state.resources.items():
            self.util_area_by_resource[rtype] = float(
                self.util_area_by_resource.get(rtype, 0.0) + float(res_state.in_use) * delta_t
            )
        self.last_util_update_time = now
        self.operations_state.time = float(now)

    def _next_resource_type(self) -> ResourceType:
        # Simple deterministic mix: DOCTOR -> MRI -> BED -> repeat
        seq = (ResourceType.DOCTOR, ResourceType.MRI, ResourceType.BED)
        r = seq[self._alloc_idx % len(seq)]
        self._alloc_idx += 1
        return r

    # --- Engine-driven methods (no SimPy inside) ---
    def on_patient_arrival(self, patient: Patient, now: float) -> ResourceType:
        # allocate required resource if not already set on patient
        # Decision should be taken by a doctor: delegate to first available doctor for now
        if patient.required_resource is None:
            doctor = self.doctors[patient.id % len(self.doctors)]
            rtype = doctor.decide_required_resource(patient)
        else:
            rtype = patient.required_resource
        patient.required_resource = rtype
        self.set_time(now)
        self.logger.info("Patient %s arrived at t=%.3f (needs=%s)", patient.id, now, rtype.name)
        # register patient arrival state
        self.operations_state.patients[patient.id] = PatientState(
            id=patient.id,
            status=PatientStatus.ARRIVED,
            required_resource=rtype,
            arrival_time=float(now),
        )
        # triage: decision should be taken by triage nurse
        patient.priority = self.triage.assess_and_assign_priority(patient)
        pst = self.operations_state.patients[patient.id]
        pst.priority = patient.priority
        pst.status = PatientStatus.TRIAGED
        self.logger.debug("Patient %s triaged with priority=%s", patient.id, str(patient.priority))
        # take a preemption decision and record it; execution will occur during service if applicable
        decision = self.agent.decide(patient, self.operations_state)
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
        # enqueue representation
        qe = QueueEntry(patient_id=patient.id, priority=patient.priority, arrival_time=float(now), required_resource=rtype)
        self.operations_state.queues[rtype].append(qe)
        # record arrival and planned service duration for modeled metrics
        service_dur = self._sample_service_time(rtype)
        self.arrivals_by_resource[rtype].append(float(now))
        self.service_times_by_resource[rtype].append(float(service_dur))
        pst = self.operations_state.patients[patient.id]
        pst.status = PatientStatus.WAITING
        self.logger.debug(
            "Patient %s enqueued for %s (queue_len=%d)",
            patient.id, rtype.name, len(self.operations_state.queues[rtype])
        )
        return float(service_dur)

    def _sample_service_time(self, rtype: ResourceType) -> float:
        if rtype == ResourceType.DOCTOR:
            return float(self.time_service.service_time_doctor())
        if rtype == ResourceType.MRI:
            return float(self.time_service.service_time_mri())
        return float(self.time_service.service_time_bed())

    def on_service_start(self, patient: Patient, rtype: ResourceType, now: float, planned_service_time: float) -> None:
        # dequeue if present
        q = self.operations_state.queues[rtype]
        self.operations_state.queues[rtype] = [e for e in q if e.patient_id != patient.id]
        pst = self.operations_state.patients[patient.id]
        pst.status = PatientStatus.IN_SERVICE
        pst.service_start_time = float(now)
        self.update_usage(rtype, +1, now)
        self.logger.info(
            "Patient %s started service at t=%.3f (resource=%s, svc_time=%.3f)",
            patient.id, now, rtype.name, float(planned_service_time)
        )

    def should_preempt(self, patient: Patient, rtype: ResourceType, now: float) -> bool:
        """Consult the preemption agent and record the decision in history.
        Returns True when a preemption should be executed for the given resource type.
        """
        decision = self.agent.decide(patient, self.operations_state)
        # record decision in history snapshot for auditability
        self._snapshot()
        self.logger.info(
            "Preemption agent decision at t=%.3f for patient %s on %s: should_preempt=%s target_index=%s",
            float(now), patient.id, rtype.name, str(decision.should_preempt), str(decision.target_index)
        )
        return bool(decision.should_preempt and rtype in (ResourceType.DOCTOR, ResourceType.MRI))

    def on_service_preempted(self, patient: Patient, rtype: ResourceType, now: float) -> None:
        pst = self.operations_state.patients[patient.id]
        pst.preemptions += 1
        pst.status = PatientStatus.PREEMPTED
        self.update_usage(rtype, -1, now)
        self.logger.warning(
            "Patient %s preempted at t=%.3f (total_preemptions=%d)", patient.id, now, pst.preemptions
        )

    def on_service_complete(self, patient: Patient, rtype: ResourceType, now: float) -> None:
        pst = self.operations_state.patients[patient.id]
        self.logger.info("Patient %s finished service at t=%.3f", patient.id, now)
        self.update_usage(rtype, -1, now)
        # record wait metrics
        arrival = pst.arrival_time
        queue_time = (pst.service_start_time or float(now)) - arrival
        total_time = float(now) - float(arrival)
        self.queue_waits.append(float(queue_time))
        self.waits.append(float(total_time))
        pst.status = PatientStatus.DISCHARGED
        self.logger.info(
            "Patient %s discharged at t=%.3f (queue_wait=%.3f, total_time=%.3f)",
            patient.id, now, float(queue_time), float(total_time)
        )

    def finalize(self, sim_duration: float) -> None:
        # ensure we integrate utilization up to simulation horizon
        sim_duration = float(sim_duration)
        self._integrate_utilization_until(sim_duration)
        # compute aggregate wait stats
        avg = float(np.mean(self.waits)) if len(self.waits) else 0.0
        med = float(np.median(self.waits)) if len(self.waits) else 0.0
        # mode-led: rough M/M/c Erlang C expected wait per resource, using aggregate arrival rate and mean service
        def erlang_c_expected_wq(lmbda: float, mu: float, c: int) -> float:
            """Return expected queue waiting time Wq for M/M/c using Erlang C formula.
            Assumes lmbda < c*mu for stability; returns 0.0 otherwise.
            """
            if c <= 0 or mu <= 0.0 or lmbda <= 0.0 or lmbda >= c * mu:
                return 0.0
            rho = lmbda / (c * mu)
            # compute P0
            inv_mu = 1.0 / mu
            sum_terms = 0.0
            a = lmbda * inv_mu
            fact = 1.0
            for n in range(0, c):
                if n > 0:
                    fact *= n
                sum_terms += (a ** n) / fact
            # last term
            fact *= c
            sum_terms += (a ** c) / (fact * (1 - rho))
            p0 = 1.0 / sum_terms
            pc = ((a ** c) / (fact * (1 - rho))) * p0
            # Erlang C waiting probability Pc
            Pw = pc
            # Expected Wq = Pw / (c*mu - lmbda)
            return float(Pw / (c * mu - lmbda))

        horizon = float(sim_duration) if float(sim_duration) > 0 else 1.0
        modeled_expected_queue_wait: dict[str, float] = {}
        # estimate per resource
        res_cfg = {
            ResourceType.DOCTOR: self.num_doctors,
            ResourceType.MRI: self.num_mri,
            ResourceType.BED: self.num_beds,
        }
        for rtype, c in res_cfg.items():
            arrivals = self.arrivals_by_resource.get(rtype, [])
            services = self.service_times_by_resource.get(rtype, [])
            lmbda = (len(arrivals) / horizon) if horizon > 0 else 0.0
            mu = (1.0 / float(np.mean(services))) if len(services) else 0.0
            wq = erlang_c_expected_wq(lmbda, mu, c)
            modeled_expected_queue_wait[rtype.name] = float(wq)
        # compute utilization per resource pool (average across servers)
        utilizations: list[float] = []
        for rtype, c in res_cfg.items():
            area = float(self.util_area_by_resource.get(rtype, 0.0))  # in_use * time
            util = float(area / (max(1.0, horizon) * max(1, c)))
            utilizations.append(util)
        stats = {
            "definition": "Total time in A&E from arrival to admission/transfer/discharge",
            "count": len(self.waits),
            "avg": avg,
            "median": med,
            "min": float(min(self.waits)) if len(self.waits) else 0.0,
            "max": float(max(self.waits)) if len(self.waits) else 0.0,
            "wait_times": self.waits,  # NHS clock (arrival -> departure)
            "queue_wait_times": self.queue_waits,  # queueing delay until treatment starts
            "modeled_expected_queue_wait": modeled_expected_queue_wait,
            "resource_utilization": {
                "DOCTOR": utilizations[0],
                "MRI": utilizations[1],
                "BED": utilizations[2],
            },
        }
        json_path = self.output_dir / "wait_times.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)
        # validate save
        with open(json_path, "r", encoding="utf-8") as f:
            _ = json.load(f)
        # plot metrics
        self.metrics.plot_wait_times(self.waits, self.output_dir / "wait_times.svg")
        # per user request, do not plot resource utilization