"""System Snapshot Model

Model for capturing system state snapshots in hospital simulation.
"""

from typing import Dict
from src.services.base_metrics import BaseRecord


class SystemSnapshot(BaseRecord):
    """Snapshot of system state at a point in time"""
    
    def __init__(self, snapshot_id: str, timestamp: float, resource_usage: Dict[str, int],
                 resource_capacity: Dict[str, int], queue_lengths: Dict[str, int],
                 entities_processed: int = 0):
        """Initialize SystemSnapshot with proper inheritance"""
        # Call parent constructor with base record fields
        super().__init__(record_id=snapshot_id, timestamp=timestamp)
        
        # Set system snapshot specific fields
        self.snapshot_id = snapshot_id
        self.resource_usage = resource_usage  # resource_name -> current usage
        self.resource_capacity = resource_capacity  # resource_name -> total capacity
        self.queue_lengths = queue_lengths  # resource_name -> queue length
        self.entities_processed = entities_processed
    
    def get_utilization(self, resource_name: str) -> float:
        """Get utilization percentage for a resource"""
        if resource_name not in self.resource_capacity or self.resource_capacity[resource_name] == 0:
            return 0.0
        usage = self.resource_usage.get(resource_name, 0)
        capacity = self.resource_capacity[resource_name]
        return (usage / capacity) * 100