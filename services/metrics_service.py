from __future__ import annotations
from dataclasses import dataclass, field
from typing import Sequence, Any, Mapping
from pathlib import Path
import logging
import json
import numpy as np
import matplotlib
# removed redundant alias import
# from enums.resource_type import ResourceType as _RT
# from enums.priority import Priority as _PR

from enums.priority import Priority
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from services.logger_service import LoggerService
from enums.resource_type import ResourceType
from enums.patient_status import PatientStatus
from entities.operations_state import OperationsState

# Use an Any-typed alias to satisfy strict type checkers for plotting calls
_mpl: Any = plt

# Simple palette
_RESOURCE_COLORS = {
    ResourceType.DOCTOR: "#2563eb",
    ResourceType.MRI: "#16a34a",
    ResourceType.BED: "#f59e0b"
}
_PRIORITY_COLORS = {
    Priority.IMMEDIATE: "#dc2626",
    Priority.VERY_URGENT: "#ea580c",
    Priority.URGENT: "#d97706",
    Priority.STANDARD: "#2563eb",
    Priority.NON_URGENT: "#16a34a",
}

@dataclass(slots=True)
class PlottingService:
    logger: logging.Logger = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        self.logger = LoggerService.get_logger(__name__)

    def _resolve_color(self, label: Any) -> str | None:
        # Accept either enum labels or their string names
        try:
            from enums.resource_type import ResourceType as rt_cls
            from enums.priority import Priority as pr_cls
        except Exception:
            rt_cls = ResourceType  # fallback to already imported enums
            pr_cls = Priority
        if isinstance(label, rt_cls):
            return _RESOURCE_COLORS.get(label)
        if isinstance(label, pr_cls):
            return _PRIORITY_COLORS.get(label)
        if isinstance(label, str):
            if label in rt_cls.__members__:
                return _RESOURCE_COLORS.get(rt_cls[label])
            if label in pr_cls.__members__:
                return _PRIORITY_COLORS.get(pr_cls[label])
        return None

    # Public wrapper to avoid accessing the protected resolver outside this class
    def resolve_color(self, label: Any) -> str | None:
        return self._resolve_color(label)

    def hist(self, values: Sequence[float], title: str, xlabel: str, ylabel: str, out_path: str | Path) -> None:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger.debug("Plotting histogram to %s", str(out_path))
        _mpl.figure(figsize=(6,4), dpi=120)
        _mpl.hist(values, bins=20, color="#3b82f6", edgecolor="#1e40af")
        _mpl.title(title)
        _mpl.xlabel(xlabel)
        _mpl.ylabel(ylabel)
        _mpl.tight_layout()
        _mpl.savefig(str(out_path), format="svg")
        _mpl.close()
        self.logger.info("Saved plot: %s", str(out_path))

    def hist_multi(self, series: Mapping[str, Sequence[float]], title: str, xlabel: str, ylabel: str, out_path: str | Path) -> None:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger.debug("Plotting multi-histogram to %s", str(out_path))
        _mpl.figure(figsize=(7,5), dpi=120)
        for label, vals in series.items():
            color = (self._resolve_color(label) or "#6b7280")
            label_str = getattr(label, "name", str(label))
            _mpl.hist(vals, bins=20, alpha=0.5, label=label_str, color=color)
        _mpl.title(title)
        _mpl.xlabel(xlabel)
        _mpl.ylabel(ylabel)
        _mpl.legend()
        _mpl.tight_layout()
        _mpl.savefig(str(out_path), format="svg")
        _mpl.close()
        self.logger.info("Saved plot: %s", str(out_path))

    def line(self, xy: Sequence[tuple[float, float]], title: str, xlabel: str, ylabel: str, out_path: str | Path) -> None:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger.debug("Plotting line chart to %s", str(out_path))
        _mpl.figure(figsize=(7,4), dpi=120)
        if len(xy):
            x, y = zip(*sorted(xy))
            _mpl.plot(x, y, color="#2563eb")
        _mpl.title(title)
        _mpl.xlabel(xlabel)
        _mpl.ylabel(ylabel)
        _mpl.tight_layout()
        _mpl.savefig(str(out_path), format="svg")
        _mpl.close()
        self.logger.info("Saved plot: %s", str(out_path))

    def multi_line(self, series: Mapping[str, Sequence[tuple[float, float]]], title: str, xlabel: str, ylabel: str, out_path: str | Path) -> None:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger.debug("Plotting multi-line chart to %s", str(out_path))
        _mpl.figure(figsize=(8,5), dpi=120)
        for label, xy in series.items():
            color = self._resolve_color(label) or "#6b7280"
            if len(xy):
                x, y = zip(*sorted(xy))
                _mpl.plot(x, y, label=getattr(label, "name", str(label)), color=color)
        _mpl.title(title)
        _mpl.xlabel(xlabel)
        _mpl.ylabel(ylabel)
        _mpl.legend()
        _mpl.tight_layout()
        _mpl.savefig(str(out_path), format="svg")
        _mpl.close()
        self.logger.info("Saved plot: %s", str(out_path))

    def scatter(self, xs: Sequence[float], ys: Sequence[float], title: str, xlabel: str, ylabel: str, out_path: str | Path, colors: Sequence[str] | None = None) -> None:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger.debug("Plotting scatter chart to %s", str(out_path))
        _mpl.figure(figsize=(7,4), dpi=120)
        if colors is None:
            _mpl.scatter(xs, ys, s=12, alpha=0.8)
        else:
            _mpl.scatter(xs, ys, s=12, alpha=0.8, c=colors)
        _mpl.title(title)
        _mpl.xlabel(xlabel)
        _mpl.ylabel(ylabel)
        _mpl.tight_layout()
        _mpl.savefig(str(out_path), format="svg")
        _mpl.close()
        self.logger.info("Saved plot: %s", str(out_path))

@dataclass(slots=True)
class MetricsService:
    logger: logging.Logger = field(init=False, repr=False, compare=False)
    plotter: PlottingService = field(init=False, repr=False, compare=False)
    # New: ingestible history of OperationsState snapshots
    history: list[OperationsState] = field(default_factory=list, repr=False, compare=False)

    def __post_init__(self) -> None:
        self.logger = LoggerService.get_logger(__name__)
        self.plotter = PlottingService()

    def average_and_median(self, values: Sequence[float]) -> tuple[float, float]:
        arr = np.asarray(values, dtype=float)
        if arr.size == 0:
            return 0.0, 0.0
        return float(np.mean(arr)), float(np.median(arr))

    # --- Ingestion API ---
    def ingest(self, state: OperationsState) -> None:
        """Ingest a snapshot of OperationsState for later metric computation.
        A copy is stored to ensure immutability of historical data.
        """
        self.history.append(state.copy())

    # --- Plotting helpers (unchanged) ---
    def plot_wait_times(self, wait_times: Sequence[float], out_path: str | Path) -> None:
        out_path = Path(out_path)
        avg, med = self.average_and_median(wait_times)
        self.logger.debug("Generating wait time plot: avg=%.3f, med=%.3f to %s", avg, med, str(out_path))
        title = f"Wait Times (avg={avg:.2f}, median={med:.2f})"
        self.plotter.hist(wait_times, title, "time units", "count", out_path)

    def plot_resource_utilization(self, utilizations: Sequence[float], out_path: str | Path) -> None:
        out_path = Path(out_path)
        avg, med = self.average_and_median(utilizations)
        self.logger.debug("Generating utilization plot: avg=%.3f, med=%.3f to %s", avg, med, str(out_path))
        title = f"Resource Utilization (avg={avg:.2f}, median={med:.2f})"
        self.plotter.hist(utilizations, title, "utilization (0..1)", "count", out_path)

    # New: by-priority wait time distributions
    def plot_wait_times_by_priority(self, wait_times_by_priority: Mapping[str, Sequence[float]], out_path: str | Path) -> None:
        total = [v for vals in wait_times_by_priority.values() for v in vals]
        avg, med = self.average_and_median(total)
        title = f"Wait Times by Priority (overall avg={avg:.2f}, median={med:.2f})"
        self.plotter.hist_multi(wait_times_by_priority, title, "time units", "count", out_path)

    # New: per-patient wait time scatter (colored by priority)
    def plot_per_patient_waits(self, discharge_times: Sequence[float], wait_times: Sequence[float], priorities: Sequence[str], out_path: str | Path) -> None:
        # Map priority names to colors robustly
        mapped_colors: list[str] = []
        for p in priorities:
            try:
                mapped_colors.append(_PRIORITY_COLORS[Priority[p]])
            except Exception:
                mapped_colors.append("#6b7280")
        title = "Per-Patient Wait Times (colored by priority)"
        self.plotter.scatter(discharge_times, wait_times, title, "discharge time", "total time in system", out_path, mapped_colors)

    # New: timelines for resource in-use and queue lengths
    def plot_resource_inuse_timeline(self, series_by_resource: Mapping[str, Sequence[tuple[float, float]]], out_path: str | Path) -> None:
        avgs_meds: dict[str, tuple[float, float]] = {}
        for label, xy in series_by_resource.items():
            ys = [y for _, y in xy]
            avgs_meds[label] = self.average_and_median(ys)
        parts = [f"{k}: avg={a:.2f}, med={m:.2f}" for k, (a, m) in avgs_meds.items()]
        title = "Resource In-Use Over Time (" + "; ".join(parts) + ")"
        self.plotter.multi_line(series_by_resource, title, "time", "in use", out_path)

    def plot_queue_length_timeline(self, series_by_resource: Mapping[str, Sequence[tuple[float, float]]], out_path: str | Path) -> None:
        avgs_meds: dict[str, tuple[float, float]] = {}
        for label, xy in series_by_resource.items():
            ys = [y for _, y in xy]
            avgs_meds[label] = self.average_and_median(ys)
        parts = [f"{k}: avg={a:.2f}, med={m:.2f}" for k, (a, m) in avgs_meds.items()]
        title = "Queue Length Over Time (" + "; ".join(parts) + ")"
        self.plotter.multi_line(series_by_resource, title, "time", "queue length", out_path)

    def plot_system_load_timeline(self, series: Sequence[tuple[float, float]], out_path: str | Path) -> None:
        ys = [y for _, y in series]
        avg, med = self.average_and_median(ys)
        title = f"System Load Over Time (patients in system; avg={avg:.2f}, median={med:.2f})"
        self.plotter.line(series, title, "time", "patients", out_path)

    # New: service time distributions and timeline
    def plot_service_times_hist_by_resource(self, service_times_by_resource: Mapping[str, Sequence[float]], out_path: str | Path) -> None:
        total = [v for vals in service_times_by_resource.values() for v in vals]
        avg, med = self.average_and_median(total)
        title = f"Service Times by Resource (overall avg={avg:.2f}, median={med:.2f})"
        self.plotter.hist_multi(service_times_by_resource, title, "time units", "count", out_path)

    def plot_service_times_timeline(self, start_times_by_resource: Mapping[str, Sequence[float]], durations_by_resource: Mapping[str, Sequence[float]], out_path: str | Path) -> None:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        _mpl.figure(figsize=(8,5), dpi=120)
        for rlabel, xs in start_times_by_resource.items():
            ys = durations_by_resource.get(rlabel, [])
            color = self.plotter.resolve_color(rlabel) or "#6b7280"
            if xs and ys:
                _mpl.scatter(xs, ys, s=12, alpha=0.8, label=rlabel, c=color)
        _mpl.title("Service Durations Over Time (by resource)")
        _mpl.xlabel("service start time")
        _mpl.ylabel("duration")
        _mpl.legend()
        _mpl.tight_layout()
        _mpl.savefig(str(out_path), format="svg")
        _mpl.close()
        self.logger.info("Saved plot: %s", str(out_path))

    # New: system load timeline by priority
    def plot_system_load_by_priority_timeline(self, series_by_priority: Mapping[str, Sequence[tuple[float, float]]], out_path: str | Path) -> None:
        avgs_meds: dict[str, tuple[float, float]] = {}
        for label, xy in series_by_priority.items():
            ys = [y for _, y in xy]
            avgs_meds[label] = self.average_and_median(ys)
        parts = [f"{k}: avg={a:.2f}, med={m:.2f}" for k, (a, m) in avgs_meds.items()]
        title = "System Load By Priority Over Time (" + "; ".join(parts) + ")"
        self.plotter.multi_line(series_by_priority, title, "time", "patients", out_path)

    # -------------------- Refactor helpers --------------------
    @staticmethod
    def _prepare_prio_labels() -> list[str]:
        # Derive labels directly from Priority enum to avoid hardcoding and ensure correct ordering
        return [p.name for p in sorted(Priority, key=lambda x: int(x.value))]

    @staticmethod
    def _erlang_c_expected_wq(lmbda: float, mu: float, c: int) -> float:
        if c <= 0 or mu <= 0.0 or lmbda <= 0.0 or lmbda >= c * mu:
            return 0.0
        rho = lmbda / (c * mu)
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

    @staticmethod
    def _infer_capacities(last: OperationsState) -> dict[ResourceType, int]:
        return {
            ResourceType.DOCTOR: int(last.resources[ResourceType.DOCTOR].capacity),
            ResourceType.MRI: int(last.resources[ResourceType.MRI].capacity),
            ResourceType.BED: int(last.resources[ResourceType.BED].capacity),
        }

    def _handle_empty_history(self, out_path: Path) -> None:
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
        with open(out_path / "wait_times.json", "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)
        # Save empty plots into structured subfolders only
        # timeline subfolders
        self.plot_per_patient_waits([], [], [], out_path / "timeline" / "wait_times" / "per_patient_waits.svg")
        self.plot_resource_inuse_timeline({"DOCTOR": [], "MRI": [], "BED": []}, out_path / "timeline" / "resource_utilizations" / "resource_inuse_timeline.svg")
        self.plot_queue_length_timeline({"DOCTOR": [], "MRI": [], "BED": []}, out_path / "timeline" / "resource_utilizations" / "queue_length_timeline.svg")
        self.plot_system_load_timeline([], out_path / "timeline" / "system" / "system_load_timeline.svg")
        self.plot_system_load_by_priority_timeline({}, out_path / "timeline" / "system" / "system_load_by_priority_timeline.svg")
        self.plot_service_times_timeline({}, {}, out_path / "timeline" / "service_times" / "service_times_timeline.svg")
        # average/median subfolders
        self.plot_wait_times([], out_path / "average" / "wait_times" / "wait_times.svg")
        self.plot_wait_times_by_priority({}, out_path / "average" / "wait_times" / "wait_times_by_priority.svg")
        self.plot_resource_utilization([0.0, 0.0, 0.0], out_path / "average" / "resource_utilizations" / "resource_utilization.svg")
        self.plot_service_times_hist_by_resource({}, out_path / "average" / "service_times" / "service_times_by_resource.svg")
        # duplicate into median folder as requested
        self.plot_wait_times([], out_path / "median" / "wait_times" / "wait_times.svg")
        self.plot_wait_times_by_priority({}, out_path / "median" / "wait_times" / "wait_times_by_priority.svg")
        self.plot_resource_utilization([0.0, 0.0, 0.0], out_path / "median" / "resource_utilizations" / "resource_utilization.svg")
        self.plot_service_times_hist_by_resource({}, out_path / "median" / "service_times" / "service_times_by_resource.svg")

    # New: restore computation helpers and exporter
    def _compute_timelines_and_episodes(
        self,
        hist: list[OperationsState],
        prio_labels: list[str],
        horizon: float,
    ) -> tuple[
        dict[str, list[tuple[float, float]]],
        dict[str, list[tuple[float, float]]],
        list[tuple[float, float]],
        dict[str, list[tuple[float, float]]],
        dict[ResourceType, float],
        dict[str, list[float]],
        dict[str, list[float]],
        dict[int, float],
        dict[int, str],
        dict[int, float],
        dict[int, float],
    ]:
        inuse_series: dict[str, list[tuple[float, float]]] = {"DOCTOR": [], "MRI": [], "BED": []}
        qlen_series: dict[str, list[tuple[float, float]]] = {"DOCTOR": [], "MRI": [], "BED": []}
        system_load_series: list[tuple[float, float]] = []
        system_load_by_priority: dict[str, list[tuple[float, float]]] = {lbl: [] for lbl in prio_labels}
        inuse_area: dict[ResourceType, float] = {ResourceType.DOCTOR: 0.0, ResourceType.MRI: 0.0, ResourceType.BED: 0.0}
        arrival_by_pid: dict[int, float] = {}
        prio_by_pid: dict[int, str] = {}
        first_service_start_by_pid: dict[int, float] = {}
        discharge_time_by_pid: dict[int, float] = {}
        active_episode: dict[int, tuple[ResourceType, float]] = {}
        episode_durations_by_res: dict[str, list[float]] = {"DOCTOR": [], "MRI": [], "BED": []}
        episode_starts_by_res: dict[str, list[float]] = {"DOCTOR": [], "MRI": [], "BED": []}
        prev: OperationsState | None = None
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
            prev = st
        # close any still-active episodes at horizon or final time
        final_time = float(hist[-1].time)
        if final_time < horizon:
            final_time = horizon
        for pid, (rtype, t_start) in list(active_episode.items()):
            dur = max(0.0, final_time - t_start)
            episode_durations_by_res[rtype.name].append(dur)
        return (
            inuse_series,
            qlen_series,
            system_load_series,
            system_load_by_priority,
            inuse_area,
            episode_durations_by_res,
            episode_starts_by_res,
            arrival_by_pid,
            prio_by_pid,
            first_service_start_by_pid,
            discharge_time_by_pid,
        )

    def _derive_patient_waits(
        self,
        arrival_by_pid: dict[int, float],
        prio_by_pid: dict[int, str],
        first_service_start_by_pid: dict[int, float],
        discharge_time_by_pid: dict[int, float],
    ) -> tuple[list[float], list[float], dict[str, list[float]], list[float], list[str]]:
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
        return waits, queue_waits, wait_times_by_priority, per_patient_discharge_times, per_patient_priorities

    def _compute_modeled_queue_wait_and_utilizations(
        self,
        episode_durations_by_res: dict[str, list[float]],
        inuse_area: dict[ResourceType, float],
        capacities: dict[ResourceType, int],
        last_time: float,
        horizon: float,
    ) -> tuple[dict[str, float], list[float]]:
        modeled_expected_queue_wait: dict[str, float] = {}
        utilizations: list[float] = []
        for rtype, c in capacities.items():
            durations = episode_durations_by_res[rtype.name]
            lmbda = (len(durations) / max(1.0, horizon))
            mu = (1.0 / float(np.mean(durations))) if len(durations) else 0.0
            wq = self._erlang_c_expected_wq(lmbda, mu, c)
            modeled_expected_queue_wait[rtype.name] = float(wq)
            area = inuse_area[rtype]
            util = float(area / (max(1.0, last_time) * max(1, c)))
            utilizations.append(util)
        return modeled_expected_queue_wait, utilizations

    def _export_stats_and_plots(
        self,
        out_path: Path,
        waits: list[float],
        queue_waits: list[float],
        modeled_expected_queue_wait: dict[str, float],
        utilizations: list[float],
        inuse_series: Mapping[str, Sequence[tuple[float, float]]],
        qlen_series: Mapping[str, Sequence[tuple[float, float]]],
        system_load_series: Sequence[tuple[float, float]],
        system_load_by_priority: Mapping[str, Sequence[tuple[float, float]]],
        episode_durations_by_res: Mapping[str, Sequence[float]],
        episode_starts_by_res: Mapping[str, Sequence[float]],
        wait_times_by_priority: Mapping[str, Sequence[float]],
        per_patient_discharge_times: Sequence[float],
        per_patient_priorities: Sequence[str],
    ) -> None:
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
        with open(out_path / "wait_times.json", "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)
        # Save plots into structured subfolders only
        # timeline subfolders
        self.plot_per_patient_waits(per_patient_discharge_times, waits, per_patient_priorities, out_path / "timeline" / "wait_times" / "per_patient_waits.svg")
        self.plot_resource_inuse_timeline(inuse_series, out_path / "timeline" / "resource_utilizations" / "resource_inuse_timeline.svg")
        self.plot_queue_length_timeline(qlen_series, out_path / "timeline" / "resource_utilizations" / "queue_length_timeline.svg")
        self.plot_system_load_timeline(system_load_series, out_path / "timeline" / "system" / "system_load_timeline.svg")
        self.plot_system_load_by_priority_timeline(system_load_by_priority, out_path / "timeline" / "system" / "system_load_by_priority_timeline.svg")
        self.plot_service_times_timeline(episode_starts_by_res, episode_durations_by_res, out_path / "timeline" / "service_times" / "service_times_timeline.svg")
        # average/median subfolders
        self.plot_wait_times(waits, out_path / "average" / "wait_times" / "wait_times.svg")
        self.plot_wait_times_by_priority(wait_times_by_priority, out_path / "average" / "wait_times" / "wait_times_by_priority.svg")
        self.plot_resource_utilization(utilizations, out_path / "average" / "resource_utilizations" / "resource_utilization.svg")
        self.plot_service_times_hist_by_resource(episode_durations_by_res, out_path / "average" / "service_times" / "service_times_by_resource.svg")
        # duplicate into median folder as requested
        self.plot_wait_times(waits, out_path / "median" / "wait_times" / "wait_times.svg")
        self.plot_wait_times_by_priority(wait_times_by_priority, out_path / "median" / "wait_times" / "wait_times_by_priority.svg")
        self.plot_resource_utilization(utilizations, out_path / "median" / "resource_utilizations" / "resource_utilization.svg")
        self.plot_service_times_hist_by_resource(episode_durations_by_res, out_path / "median" / "service_times" / "service_times_by_resource.svg")

    # --- Computation from ingested history ---
    def compute_and_export(self, output_dir: str | Path, sim_duration: float) -> None:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        horizon = float(sim_duration) if float(sim_duration) > 0 else 1.0
        hist = list(self.history)
        if not hist:
            self._handle_empty_history(out_path)
            return
        # Sort by time
        hist.sort(key=lambda s: float(s.time))
        prio_labels = self._prepare_prio_labels()
        (
            inuse_series,
            qlen_series,
            system_load_series,
            system_load_by_priority,
            inuse_area,
            episode_durations_by_res,
            episode_starts_by_res,
            arrival_by_pid,
            prio_by_pid,
            first_service_start_by_pid,
            discharge_time_by_pid,
        ) = self._compute_timelines_and_episodes(hist, prio_labels, horizon)
        waits, queue_waits, wait_times_by_priority, per_patient_discharge_times, per_patient_priorities = self._derive_patient_waits(
            arrival_by_pid,
            prio_by_pid,
            first_service_start_by_pid,
            discharge_time_by_pid,
        )
        capacities = self._infer_capacities(hist[-1])
        modeled_expected_queue_wait, utilizations = self._compute_modeled_queue_wait_and_utilizations(
            episode_durations_by_res,
            inuse_area,
            capacities,
            float(hist[-1].time),
            horizon,
        )
        self._export_stats_and_plots(
            out_path,
            waits,
            queue_waits,
            modeled_expected_queue_wait,
            utilizations,
            inuse_series,
            qlen_series,
            system_load_series,
            system_load_by_priority,
            episode_durations_by_res,
            episode_starts_by_res,
            wait_times_by_priority,
            per_patient_discharge_times,
            per_patient_priorities,
        )