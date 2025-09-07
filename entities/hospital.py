from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
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
    # PreemptionAgent now lives inside triage nurse; hospital queries triage for recommendations
    metrics: MetricsService = field(init=False)
    waits: List[float] = field(default_factory=list)
    queue_waits: List[float] = field(default_factory=list)
    arrivals_by_resource: dict[ResourceType, List[float]] = field(init=False)
    service_times_by_resource: dict[ResourceType, List[float]] = field(init=False)
    # Added: per-priority waits and per-patient scatter data
    wait_times_by_priority: dict[str, List[float]] = field(init=False)
    per_patient_discharge_times: List[float] = field(default_factory=list)
    per_patient_priorities: List[str] = field(default_factory=list)
    # Added: service start times and durations captured at service start for timeline plotting
    service_start_times_by_resource: dict[ResourceType, List[float]] = field(init=False)
    service_durations_by_resource_at_start: dict[ResourceType, List[float]] = field(init=False)
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
        # decisions handled by triage nurse's embedded agent
        self.metrics = MetricsService()
        # per-resource metrics data
        self.arrivals_by_resource = {ResourceType.DOCTOR: [], ResourceType.MRI: [], ResourceType.BED: []}
        self.service_times_by_resource = {ResourceType.DOCTOR: [], ResourceType.MRI: [], ResourceType.BED: []}
        # Added: initialize per-priority and per-patient structures
        self.wait_times_by_priority = {
            "IMMEDIATE": [],
            "VERY_URGENT": [],
            "URGENT": [],
            "STANDARD": [],
            "NON_URGENT": [],
        }
        self.service_start_times_by_resource = {ResourceType.DOCTOR: [], ResourceType.MRI: [], ResourceType.BED: []}
        self.service_durations_by_resource_at_start = {ResourceType.DOCTOR: [], ResourceType.MRI: [], ResourceType.BED: []}
        # utilization integration
        self.util_area_by_resource = {ResourceType.DOCTOR: 0.0, ResourceType.MRI: 0.0, ResourceType.BED: 0.0}

    def _snapshot(self) -> None:
        # push a copy before updating operation state elsewhere
        self.operations_state_history.append(self.operations_state.copy())

    def set_time(self, now: float) -> None:
        # engine should call this when simulation time advances before invoking hospital updates
        self.operations_state.time = float(now)

    def update_usage(self, rtype: ResourceType, delta: int, now: float) -> None:
        self.set_time(now)
        rs = self.operations_state.resources[rtype]
        rs.in_use = max(0, min(rs.capacity, rs.in_use + int(delta)))

    def _integrate_utilization_until(self, now: float) -> None:
        now = float(now)
        last = float(self.last_util_update_time)
        if now <= last:
            return
        dt = now - last
        for rtype, rs in self.operations_state.resources.items():
            self.util_area_by_resource[rtype] += float(rs.in_use) * dt
        self.last_util_update_time = now

    def _next_resource_type(self) -> ResourceType:
        # Simple deterministic mix: DOCTOR -> MRI -> BED -> repeat
        seq = (ResourceType.DOCTOR, ResourceType.MRI, ResourceType.BED)
        r = seq[self._alloc_idx % len(seq)]
        self._alloc_idx += 1
        return r

    # --- Engine-driven methods (no SimPy inside) ---
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
        # Determine required resource based on triage output (should be DOCTOR per user requirement)
        if patient.required_resource is None:
            rtype = ResourceType.DOCTOR
        else:
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
        # ensure we integrate utilization up to simulation horizon (kept for compatibility, but not used for metrics)
        sim_duration = float(sim_duration)
        horizon = float(sim_duration) if float(sim_duration) > 0 else 1.0
        hist = list(self.operations_state_history)
        if not hist:
            # still produce empty artifacts for consistency
            stats: dict[str, object] = {
                "definition": "Total time in A&E from arrival to admission/transfer/discharge",
                "count": 0,
                "avg": 0.0,
                "median": 0.0,
                "min": 0.0,
                "max": 0.0,
                "wait_times": [],
                "queue_wait_times": [],
                "modeled_expected_queue_wait": {"DOCTOR": 0.0, "MRI": 0.0, "BED": 0.0},
                "resource_utilization": {"DOCTOR": 0.0, "MRI": 0.0, "BED": 0.0},
            }
            json_path = self.output_dir / "wait_times.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2)
            # empty plots
            self.metrics.plot_wait_times([], self.output_dir / "wait_times.svg")
            self.metrics.plot_wait_times_by_priority({}, self.output_dir / "wait_times_by_priority.svg")
            self.metrics.plot_per_patient_waits([], [], [], self.output_dir / "per_patient_waits.svg")
            self.metrics.plot_resource_utilization([0.0, 0.0, 0.0], self.output_dir / "resource_utilization.svg")
            self.metrics.plot_resource_inuse_timeline({"DOCTOR": [], "MRI": [], "BED": []}, self.output_dir / "resource_inuse_timeline.svg")
            self.metrics.plot_queue_length_timeline({"DOCTOR": [], "MRI": [], "BED": []}, self.output_dir / "queue_length_timeline.svg")
            self.metrics.plot_system_load_timeline([], self.output_dir / "system_load_timeline.svg")
            self.metrics.plot_system_load_by_priority_timeline({}, self.output_dir / "system_load_by_priority_timeline.svg")
            self.metrics.plot_service_times_hist_by_resource({}, self.output_dir / "service_times_by_resource.svg")
            self.metrics.plot_service_times_timeline({}, {}, self.output_dir / "service_times_timeline.svg")
            return
        # Sort by time to be safe
        hist.sort(key=lambda s: float(s.time))
        # Timelines derived from history
        inuse_series: dict[str, list[tuple[float, float]]] = {"DOCTOR": [], "MRI": [], "BED": []}
        qlen_series: dict[str, list[tuple[float, float]]] = {"DOCTOR": [], "MRI": [], "BED": []}
        system_load_series: list[tuple[float, float]] = []
        prio_labels = ["IMMEDIATE", "VERY_URGENT", "URGENT", "STANDARD", "NON_URGENT"]
        system_load_by_priority: dict[str, list[tuple[float, float]]] = {lbl: [] for lbl in prio_labels}
        # Utilization area from stepwise integration of in_use over time
        inuse_area: dict[ResourceType, float] = {ResourceType.DOCTOR: 0.0, ResourceType.MRI: 0.0, ResourceType.BED: 0.0}
        # Per-patient and per-resource episode tracking
        arrival_by_pid: dict[int, float] = {}
        prio_by_pid: dict[int, str] = {}
        first_service_start_by_pid: dict[int, float] = {}
        discharge_time_by_pid: dict[int, float] = {}
        # Active service episodes keyed by patient id -> (rtype, start_time)
        active_episode: dict[int, tuple[ResourceType, float]] = {}
        # Episodes by resource
        episode_durations_by_res: dict[str, list[float]] = {"DOCTOR": [], "MRI": [], "BED": []}
        episode_starts_by_res: dict[str, list[float]] = {"DOCTOR": [], "MRI": [], "BED": []}
        # Track previous snapshot for integration and state transitions
        prev = None
        prev_status: dict[int, PatientStatus] = {}
        for st in hist:
            t = float(st.time)
            # timelines
            inuse_series["DOCTOR"].append((t, float(st.resources[ResourceType.DOCTOR].in_use)))
            inuse_series["MRI"].append((t, float(st.resources[ResourceType.MRI].in_use)))
            inuse_series["BED"].append((t, float(st.resources[ResourceType.BED].in_use)))
            qlen_series["DOCTOR"].append((t, float(len(st.queues[ResourceType.DOCTOR]))))
            qlen_series["MRI"].append((t, float(len(st.queues[ResourceType.MRI]))))
            qlen_series["BED"].append((t, float(len(st.queues[ResourceType.BED]))))
            load = float(sum(1 for p in st.patients.values() if p.status != PatientStatus.DISCHARGED))
            system_load_series.append((t, load))
            # by-priority counts
            prio_counts = {lbl: 0 for lbl in prio_labels}
            for p in st.patients.values():
                if p.status != PatientStatus.DISCHARGED and getattr(p, "priority", None) is not None:
                    lbl = getattr(p.priority, "name", None)
                    if lbl in prio_counts:
                        prio_counts[lbl] += 1
            for lbl in prio_labels:
                system_load_by_priority[lbl].append((t, float(prio_counts[lbl])))
            # utilization area integration (step function across prev->current)
            if prev is not None:
                dt = t - float(prev.time)
                if dt > 0:
                    inuse_area[ResourceType.DOCTOR] += float(prev.resources[ResourceType.DOCTOR].in_use) * dt
                    inuse_area[ResourceType.MRI] += float(prev.resources[ResourceType.MRI].in_use) * dt
                    inuse_area[ResourceType.BED] += float(prev.resources[ResourceType.BED].in_use) * dt
            # patient-level transitions
            # record arrival/prio first time seen; detect service start/stop and discharge
            for pid, pst in st.patients.items():
                if pid not in arrival_by_pid:
                    arrival_by_pid[pid] = float(pst.arrival_time)
                if pid not in prio_by_pid and getattr(pst, "priority", None) is not None:
                    prio_by_pid[pid] = getattr(pst.priority, "name", "UNKNOWN")
                prev_st = prev_status.get(pid)
                # detect service start
                if pst.status == PatientStatus.IN_SERVICE and prev_st != PatientStatus.IN_SERVICE:
                    rtype = pst.required_resource
                    if rtype is not None:
                        active_episode[pid] = (rtype, t)
                        episode_starts_by_res[rtype.name].append(t)
                        if pid not in first_service_start_by_pid:
                            first_service_start_by_pid[pid] = t
                # detect service end (left IN_SERVICE)
                if prev_st == PatientStatus.IN_SERVICE and pst.status != PatientStatus.IN_SERVICE:
                    start_info = active_episode.pop(pid, None)
                    if start_info is not None:
                        rtype_started, t_start = start_info
                        dur = max(0.0, t - t_start)
                        episode_durations_by_res[rtype_started.name].append(dur)
                # detect discharge
                if pst.status == PatientStatus.DISCHARGED and pid not in discharge_time_by_pid:
                    discharge_time_by_pid[pid] = t
                # update trackers
                prev_status[pid] = pst.status
            # Handle patients that disappeared (unlikely in our snapshots since we persist patients until discharge)
            prev = st
        # close any still-active episodes at horizon
        final_time = float(hist[-1].time)
        if final_time < horizon:
            final_time = horizon
        for pid, (rtype, t_start) in list(active_episode.items()):
            dur = max(0.0, final_time - t_start)
            episode_durations_by_res[rtype.name].append(dur)
        # compute waits and queue waits from derived per-patient times
        waits: list[float] = []
        queue_waits: list[float] = []
        wait_times_by_priority: dict[str, list[float]] = {}
        per_patient_discharge_times: list[float] = []
        per_patient_priorities: list[str] = []
        for pid, arr in arrival_by_pid.items():
            if pid in discharge_time_by_pid:
                total = float(discharge_time_by_pid[pid] - arr)
                waits.append(total)
                pstr = prio_by_pid.get(pid, "UNKNOWN")
                wait_times_by_priority.setdefault(pstr, []).append(total)
                per_patient_discharge_times.append(float(discharge_time_by_pid[pid]))
                per_patient_priorities.append(pstr)
            if pid in first_service_start_by_pid:
                qwt = float(first_service_start_by_pid[pid] - arr)
                if qwt >= 0.0:
                    queue_waits.append(qwt)
        # Erlang C modeled expected queue wait per resource from derived arrival/service rates
        res_cfg = {
            ResourceType.DOCTOR: self.num_doctors,
            ResourceType.MRI: self.num_mri,
            ResourceType.BED: self.num_beds,
        }
        def erlang_c_expected_wq(lmbda: float, mu: float, c: int) -> float:
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
            fact *= c
            sum_terms += (a ** c) / (fact * (1 - rho))
            p0 = 1.0 / sum_terms
            pc = ((a ** c) / (fact * (1 - rho))) * p0
            Pw = pc
            return float(Pw / (c * mu - lmbda))
        modeled_expected_queue_wait: dict[str, float] = {}
        utilizations: list[float] = []
        for rtype, c in res_cfg.items():
            durations = episode_durations_by_res[rtype.name]
            lmbda = (len(durations) / max(1.0, horizon))
            mu = (1.0 / float(np.mean(durations))) if len(durations) else 0.0
            wq = erlang_c_expected_wq(lmbda, mu, c)
            modeled_expected_queue_wait[rtype.name] = float(wq)
            # utilization from in_use area integration
            area = inuse_area[rtype]
            util = float(area / (max(1.0, hist[-1].time) * max(1, c)))
            utilizations.append(util)
        # aggregate stats
        avg = float(np.mean(waits)) if len(waits) else 0.0
        med = float(np.median(waits)) if len(waits) else 0.0
        stats = {
            "definition": "Total time in A&E from arrival to admission/transfer/discharge",
            "count": len(waits),
            "avg": avg,
            "median": med,
            "min": float(min(waits)) if len(waits) else 0.0,
            "max": float(max(waits)) if len(waits) else 0.0,
            "wait_times": waits,
            "queue_wait_times": queue_waits,
            "modeled_expected_queue_wait": modeled_expected_queue_wait,
            "resource_utilization": {
                "DOCTOR": utilizations[0] if len(utilizations) > 0 else 0.0,
                "MRI": utilizations[1] if len(utilizations) > 1 else 0.0,
                "BED": utilizations[2] if len(utilizations) > 2 else 0.0,
            },
        }
        json_path = self.output_dir / "wait_times.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)
        # Plot using history-derived series
        self.metrics.plot_wait_times(waits, self.output_dir / "wait_times.svg")
        self.metrics.plot_wait_times_by_priority(wait_times_by_priority, self.output_dir / "wait_times_by_priority.svg")
        self.metrics.plot_per_patient_waits(per_patient_discharge_times, waits, per_patient_priorities, self.output_dir / "per_patient_waits.svg")
        self.metrics.plot_resource_utilization(utilizations, self.output_dir / "resource_utilization.svg")
        self.metrics.plot_resource_inuse_timeline(inuse_series, self.output_dir / "resource_inuse_timeline.svg")
        self.metrics.plot_queue_length_timeline(qlen_series, self.output_dir / "queue_length_timeline.svg")
        self.metrics.plot_system_load_timeline(system_load_series, self.output_dir / "system_load_timeline.svg")
        self.metrics.plot_system_load_by_priority_timeline(system_load_by_priority, self.output_dir / "system_load_by_priority_timeline.svg")
        # Service time distributions and timeline
        self.metrics.plot_service_times_hist_by_resource(episode_durations_by_res, self.output_dir / "service_times_by_resource.svg")
        self.metrics.plot_service_times_timeline(episode_starts_by_res, episode_durations_by_res, self.output_dir / "service_times_timeline.svg")