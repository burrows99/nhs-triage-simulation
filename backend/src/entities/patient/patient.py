from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING
from .symptoms import Symptoms
from ..entity import Entity

if TYPE_CHECKING:
    from ..resource import Resource

@dataclass
class Patient(Entity):
    symptoms: Symptoms = field(default_factory=Symptoms)
    history: str = ""
    resource_assigned: Optional["Resource"] = None
    
    def update_history(self, history_to_add: str):
        """Update the patient's medical history"""
        self.history += history_to_add