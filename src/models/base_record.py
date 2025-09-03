"""Base Record Model

Base record class for all metric tracking in the hospital simulation system.
"""

from abc import ABC, abstractmethod


class BaseRecord(ABC):
    """Base record class for all metric tracking"""
    
    @property
    @abstractmethod
    def record_id(self) -> str:
        """Unique identifier for this record"""
        pass
    
    @property
    @abstractmethod
    def timestamp(self) -> float:
        """Timestamp for this record"""
        pass