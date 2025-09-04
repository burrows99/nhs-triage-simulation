import attr
from typing import Optional
from ...enums.Triage import Priority

@attr.s(auto_attribs=True)
class TriageAssessment:
    """Result of triage assessment"""
    priority: Priority
    reason: str
    estimated_treatment_time: float
    timestamp: float = 0.0