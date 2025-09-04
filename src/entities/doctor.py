import attr
from typing import Optional
from .patient import Patient

@attr.s(auto_attribs=True)
class Doctor:
    """Doctor resource with specialization and current assignment"""
    id: int
    name: str
    specialization: str
    current_patient: Optional[Patient] = None
    busy: bool = False
    total_patients_treated: int = 0