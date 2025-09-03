"""System Snapshot Model

Model for capturing system state snapshots in hospital simulation.
"""

import attr
from typing import Dict
from src.models.base_record import BaseRecord


@attr.s(auto_attribs=True)
class SystemSnapshot(BaseRecord):
    """Represents a snapshot of system state at a specific time."""
    snapshot_id: str
    _timestamp: float = attr.ib()
    resource_usage: Dict[str, int] = attr.Factory(dict)  # resource_name -> current usage
    resource_capacity: Dict[str, int] = attr.Factory(dict)  # resource_name -> total capacity
    queue_lengths: Dict[str, int] = attr.Factory(dict)  # resource_name -> queue length
    entities_processed: int = 0
    
    @property
    def record_id(self) -> str:
        """Implementation of abstract method from BaseRecord."""
        return self.snapshot_id
    
    @property
    def timestamp(self) -> float:
        """Implementation of abstract method from BaseRecord."""
        return self._timestamp
    
    def get_utilization(self, resource_name: str) -> float:
        """Get utilization percentage for a resource"""
        from src.logger import logger
        
        if resource_name not in self.resource_capacity or self.resource_capacity[resource_name] == 0:
            logger.debug(f"🔍 UTIL CALC | {resource_name} | No capacity data or zero capacity")
            return 0.0
        
        usage = self.resource_usage.get(resource_name, 0)
        capacity = self.resource_capacity[resource_name]
        utilization = (usage / capacity) * 100
        
        logger.debug(f"🔍 UTIL CALC | {resource_name} | Usage: {usage}/{capacity} = {utilization:.1f}%")
        return utilization