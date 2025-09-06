from __future__ import annotations
from enum import Enum

class PatientStatus(Enum):
    ARRIVED = "ARRIVED"
    TRIAGED = "TRIAGED"
    WAITING = "WAITING"
    IN_SERVICE = "IN_SERVICE"
    PREEMPTED = "PREEMPTED"
    DISCHARGED = "DISCHARGED"