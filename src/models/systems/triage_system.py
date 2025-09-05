import attr
import random
from ..entities.entity import Entity
from ..entities.patient import Patient
from ...utils.constants import TRIAGE_PRIORITIES


@attr.s(auto_attribs=True)
class TriageSystem(Entity):
    """Triage system for assigning priorities to patients."""
    
    def assign_priority(self, patient: Patient):
        """Assign a random triage priority to a patient."""
        patient.priority = random.choice(TRIAGE_PRIORITIES)