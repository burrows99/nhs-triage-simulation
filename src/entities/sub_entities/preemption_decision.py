import attr
from typing import Optional

@attr.s(auto_attribs=True)
class PreemptionDecision:
    """AI agent response for preemption decisions"""
    should_preempt: bool
    doctor_to_preempt: Optional[int]
    reason: str
    confidence: float