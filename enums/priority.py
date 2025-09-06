from enum import IntEnum
from typing import Final


class TriagePriority(IntEnum):
    """
    Manchester Triage System (MTS) priority levels.
    
    Based on NHS Emergency Triage guidelines:
    - Priority 1 (Red): Immediate - life-threatening conditions
    - Priority 2 (Orange): Very urgent - potentially life-threatening
    - Priority 3 (Yellow): Urgent - serious conditions requiring prompt attention
    - Priority 4 (Green): Standard - less urgent conditions
    - Priority 5 (Blue): Non-urgent - minor conditions
    
    Reference: NHS England Emergency Care Data Set
    https://www.england.nhs.uk/statistics/statistical-work-areas/ae-waiting-times-and-activity/
    """
    IMMEDIATE = 1      # Red - Maximum waiting time: 0 minutes
    VERY_URGENT = 2    # Orange - Maximum waiting time: 10 minutes
    URGENT = 3         # Yellow - Maximum waiting time: 60 minutes
    STANDARD = 4       # Green - Maximum waiting time: 120 minutes
    NON_URGENT = 5     # Blue - Maximum waiting time: 240 minutes
    
    @property
    def max_wait_time_minutes(self) -> int:
        """Maximum acceptable waiting time in minutes for this priority level."""
        wait_times: Final[dict[int, int]] = {
            1: 0,    # Immediate
            2: 10,   # Very urgent
            3: 60,   # Urgent
            4: 120,  # Standard
            5: 240   # Non-urgent
        }
        return wait_times[self.value]
    
    @property
    def color_code(self) -> str:
        """Color code associated with priority level."""
        colors: Final[dict[int, str]] = {
            1: "RED",
            2: "ORANGE", 
            3: "YELLOW",
            4: "GREEN",
            5: "BLUE"
        }
        return colors[self.value]
    
    def __str__(self) -> str:
        return f"{self.name} ({self.color_code})"