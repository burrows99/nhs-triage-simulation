from __future__ import annotations
from dataclasses import dataclass, field
import logging
from enums.resource_type import ResourceType
from entities.patient import Patient
from services.logger_service import LoggerService


@dataclass(slots=True)
class PatientFactory:
    """Minimal factory that creates one Patient at a time.
    The simulation controls timing using TimeService; this factory only returns a new Patient object
    with an incrementing id and a simple round-robin required_resource.
    """
    logger: logging.Logger = field(init=False, repr=False, compare=False)
    _next_id: int = field(default=0, init=False, repr=False, compare=False)
    _cycle_idx: int = field(default=0, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        self.logger = LoggerService.get_logger(__name__)

    def _next_resource(self) -> ResourceType:
        # Simple deterministic mix: DOCTOR -> MRI -> BED -> repeat
        seq = (ResourceType.DOCTOR, ResourceType.MRI, ResourceType.BED)
        r = seq[self._cycle_idx % len(seq)]
        self._cycle_idx += 1
        return r

    def new_patient(self, arrival_time: float) -> Patient:
        """Create and return a single Patient for the given arrival_time."""
        rtype = self._next_resource()
        pid = self._next_id
        self._next_id += 1
        p = Patient(id=pid, arrival_time=float(arrival_time), required_resource=rtype)
        self.logger.debug("Factory created patient %s at t=%.3f (needs=%s)", p.id, float(arrival_time), rtype.name)
        return p