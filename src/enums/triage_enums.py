from enum import Enum


class TriagePriority(Enum):
    """Manchester Triage System priority levels."""
    RED = "Red"        # Immediate (0 minutes)
    ORANGE = "Orange"  # Very urgent (10 minutes)
    YELLOW = "Yellow"  # Urgent (60 minutes)
    GREEN = "Green"    # Standard (120 minutes)
    BLUE = "Blue"      # Non-urgent (240 minutes)

    @classmethod
    def get_values(cls):
        """Get all priority values as a list."""
        return [priority.value for priority in cls]