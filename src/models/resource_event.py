"""Resource Event Model

Model for tracking resource usage events in hospital simulation.
"""

from src.models.base_record import BaseRecord


class ResourceEvent(BaseRecord):
    """Record for tracking resource usage events"""
    
    def __init__(self, event_id: str, timestamp: float, event_type: str, 
                 resource_name: str, entity_id: str, queue_length: int = 0,
                 wait_time: float = 0.0, service_time: float = 0.0, priority: int = 5):
        """Initialize ResourceEvent with proper inheritance"""
        # Set resource event specific fields
        self.event_id = event_id
        self._timestamp = timestamp
        self.event_type = event_type  # 'request', 'acquire', 'release'
        self.resource_name = resource_name  # 'triage', 'doctor', 'bed'
        self.entity_id = entity_id  # patient_id or other entity
        self.queue_length = queue_length
        self.wait_time = wait_time
        self.service_time = service_time
        self.priority = priority
    
    @property
    def record_id(self) -> str:
        return self.event_id
    
    @property
    def timestamp(self) -> float:
        return self._timestamp