from __future__ import annotations
from dataclasses import dataclass, field
from typing import Sequence, Any, Mapping
from pathlib import Path
import logging
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from services.logger_service import LoggerService

# Use an Any-typed alias to satisfy strict type checkers for plotting calls
_mpl: Any = plt

# Simple palette
_RESOURCE_COLORS = {
    "DOCTOR": "#2563eb",
    "MRI": "#16a34a",
    "BED": "#f59e0b",
}
_PRIORITY_COLORS = {
    "IMMEDIATE": "#dc2626",
    "VERY_URGENT": "#ea580c",
    "URGENT": "#d97706",
    "STANDARD": "#2563eb",
    "NON_URGENT": "#16a34a",
}

@dataclass(slots=True)
class PlottingService:
    logger: logging.Logger = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        self.logger = LoggerService.get_logger(__name__)

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
            color = _PRIORITY_COLORS.get(label, None) or _RESOURCE_COLORS.get(label, None)
            _mpl.hist(vals, bins=20, alpha=0.5, label=label, color=color)
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
            color = _RESOURCE_COLORS.get(label, None) or _PRIORITY_COLORS.get(label, None)
            if len(xy):
                x, y = zip(*sorted(xy))
                _mpl.plot(x, y, label=label, color=color)
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

    def __post_init__(self) -> None:
        self.logger = LoggerService.get_logger(__name__)
        self.plotter = PlottingService()

    def average_and_median(self, values: Sequence[float]) -> tuple[float, float]:
        arr = np.asarray(values, dtype=float)
        if arr.size == 0:
            return 0.0, 0.0
        return float(np.mean(arr)), float(np.median(arr))

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
        colors = [ _PRIORITY_COLORS.get(p, "#6b7280") for p in priorities ]
        title = "Per-Patient Wait Times (colored by priority)"
        self.plotter.scatter(discharge_times, wait_times, title, "discharge time", "total time in system", out_path, colors)

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
            color = _RESOURCE_COLORS.get(rlabel, None)
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