from __future__ import annotations
from enum import Enum

class ResourceType(Enum):
    DOCTOR = "DOCTOR"
    MRI = "MRI"
    BED = "BED"
    @property
    def preemptible(self) -> bool:
        """Whether this resource type is preemptible in the simulation."""
        return self in (ResourceType.DOCTOR, ResourceType.MRI)