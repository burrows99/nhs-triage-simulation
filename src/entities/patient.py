import attr
from typing import List, Optional
from ..enums.Triage import Priority
from .sub_entities.vital_signs import VitalSigns

@attr.s(auto_attribs=True)
class Patient:
    """Patient class with medical condition and priority information"""
    id: int
    arrival_time: float
    condition: str
    symptoms: List[str]
    vital_signs: VitalSigns
    priority: Optional[Priority] = None
    priority_reason: str = ""
    treatment_time: float = 0.0
    wait_time: float = 0.0
    interruption_count: int = 0
    assigned_doctor: Optional[int] = None
    treatment_start_time: Optional[float] = None