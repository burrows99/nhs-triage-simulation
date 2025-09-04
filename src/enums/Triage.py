from enum import Enum
class Priority(Enum):
    RED = 1      # Resuscitation - Immediate
    ORANGE = 2   # Emergency - 10 minutes
    YELLOW = 3   # Urgent - 60 minutes
    GREEN = 4    # Semi-urgent - 120 minutes
    BLUE = 5     # Non-urgent - 240 minutes