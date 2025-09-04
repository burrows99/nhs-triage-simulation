
from typing import Protocol, Optional
from ..entities.patient import Patient

class PatientDataProvider(Protocol):
    """Interface for patient data sources"""
    def get_next_patient(self) -> Optional[Patient]: ...