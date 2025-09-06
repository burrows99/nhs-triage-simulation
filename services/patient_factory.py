from __future__ import annotations
from dataclasses import dataclass, field
import logging
from entities.patient import Patient
from services.logger_service import LoggerService


@dataclass(slots=True)
class PatientFactory:
    """Minimal factory that creates one Patient at a time.
    The simulation controls timing using TimeService; this factory only returns a new Patient object
    with an incrementing id. Resource allocation is handled by Hospital.
    """
    logger: logging.Logger = field(init=False, repr=False, compare=False)
    _next_id: int = field(default=0, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        self.logger = LoggerService.get_logger(__name__)

    def new_patient(self, arrival_time: float) -> Patient:
        """Create and return a single Patient for the given arrival_time. Hospital decides resource allocation."""
        pid = self._next_id
        self._next_id += 1
        p = Patient(id=pid, arrival_time=float(arrival_time))
        self.logger.debug("Factory created patient %s at t=%.3f", p.id, float(arrival_time))
        return p