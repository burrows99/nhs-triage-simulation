"""Base Record Model

Base record class for all metric tracking in the hospital simulation system.
"""

from dataclasses import dataclass


@dataclass
class BaseRecord:
    """Base record class for all metric tracking"""
    record_id: str
    timestamp: float
    
    def __post_init__(self):
        """Validate record after initialization"""
        if not self.record_id:
            raise ValueError("Record ID cannot be empty")
        if self.timestamp < 0:
            raise ValueError("Timestamp cannot be negative")