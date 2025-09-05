import random
from enum import Enum
from typing import Tuple


class HospitalAction(Enum):
    """Enumeration of hospital actions with their descriptions and duration ranges."""
    ADMIT_PATIENT = ("Admit Patient", (1, 3))
    ASSIGN_PATIENT = ("Assign Patient", (2, 5))
    RELEASE_PATIENT = ("Release Patient", (1, 2))
    ALLOCATE_RESOURCES = ("Allocate Resources", (3, 6))

    def __init__(self, description: str, duration_range: Tuple[int, int]):
        self.description = description
        self.duration_range = duration_range

    def random_duration(self) -> int:
        """Generate a random duration within the action's range."""
        return random.randint(*self.duration_range)