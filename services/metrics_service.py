from __future__ import annotations
from dataclasses import dataclass, field
from typing import Sequence, Any
from pathlib import Path
import logging
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from services.logger_service import LoggerService

# Use an Any-typed alias to satisfy strict type checkers for plotting calls
_mpl: Any = plt

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