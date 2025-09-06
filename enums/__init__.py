"""Hospital enums package."""

from .priority import TriagePriority
from .resource_type import ResourceType
from .patient_status import PatientStatus

__all__ = [
    "TriagePriority",
    "ResourceType", 
    "PatientStatus"
]