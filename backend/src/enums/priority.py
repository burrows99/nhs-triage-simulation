from enum import Enum

class Priority(Enum):
    """Triage priority levels for Manchester Triage System"""
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"
    
    @property
    def name_display(self) -> str:
        """Get display name for priority"""
        names = {
            Priority.RED: "Immediate",
            Priority.ORANGE: "Very Urgent",
            Priority.YELLOW: "Urgent",
            Priority.GREEN: "Standard",
            Priority.BLUE: "Non-Urgent"
        }
        return names[self]
    
    @property
    def max_wait_time(self) -> str:
        """Get maximum wait time for priority"""
        wait_times = {
            Priority.RED: "0 minutes",
            Priority.ORANGE: "10 minutes",
            Priority.YELLOW: "60 minutes",
            Priority.GREEN: "2 hours",
            Priority.BLUE: "4 hours"
        }
        return wait_times[self]
    
    @property
    def description(self) -> str:
        """Get description for priority"""
        descriptions = {
            Priority.RED: "Life-threatening",
            Priority.ORANGE: "High-risk conditions",
            Priority.YELLOW: "Serious but not immediately life-threatening",
            Priority.GREEN: "Non life-threatening",
            Priority.BLUE: "Lowest urgency"
        }
        return descriptions[self]
    
    @classmethod
    def from_string(cls, priority_str: str) -> "Priority":
        """Convert string to Priority enum"""
        priority_map = {
            "red": cls.RED,
            "orange": cls.ORANGE,
            "yellow": cls.YELLOW,
            "green": cls.GREEN,
            "blue": cls.BLUE
        }
        return priority_map.get(priority_str.lower(), cls.GREEN)
    
    @classmethod
    def get_priority_order(cls) -> list["Priority"]:
        """Get priorities in order from highest to lowest urgency"""
        return [cls.RED, cls.ORANGE, cls.YELLOW, cls.GREEN, cls.BLUE]