import attr
from typing import Optional, TYPE_CHECKING

from ..doctor import Doctor
from ..MRI_machine import MRI_Machine
from ..blood_test_nurse import BloodTestNurse

@attr.s(auto_attribs=True)
class PreemptionDecision:
    """AI agent response for preemption decisions"""
    should_preempt: bool
    doctor_to_preempt: Optional['Doctor']
    mri_machine_to_preempt: Optional['MRI_Machine']
    blood_nurse_to_preempt: Optional['BloodTestNurse']
    reason: str
    confidence: float