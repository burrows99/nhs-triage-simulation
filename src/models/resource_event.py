"""Resource Event Model

Model for tracking resource usage events in hospital simulation.
"""

import attr
from src.models.base_record import BaseRecord


@attr.s(auto_attribs=True)
class ResourceEvent(BaseRecord):
    """Record for tracking resource usage events using attrs for consistency."""
    
    event_id: str = attr.ib(validator=attr.validators.instance_of(str))
    event_timestamp: float = attr.ib(validator=attr.validators.instance_of((int, float)))
    event_type: str = attr.ib(validator=attr.validators.in_(['request', 'acquire', 'release']))
    resource_name: str = attr.ib(validator=attr.validators.in_(['triage', 'doctor', 'bed', 'nurse']))
    entity_id: str = attr.ib(validator=attr.validators.instance_of(str))
    queue_length: int = attr.ib(default=0, validator=attr.validators.and_(
        attr.validators.instance_of(int),
        lambda instance, attribute, value: value >= 0 or attr.validators._fail("queue_length must be non-negative", attribute, value)
    ))
    wait_time: float = attr.ib(default=0.0, validator=attr.validators.and_(
        attr.validators.instance_of((int, float)),
        lambda instance, attribute, value: value >= 0.0 or attr.validators._fail("wait_time must be non-negative", attribute, value)
    ))
    service_time: float = attr.ib(default=0.0, validator=attr.validators.and_(
        attr.validators.instance_of((int, float)),
        lambda instance, attribute, value: value >= 0.0 or attr.validators._fail("service_time must be non-negative", attribute, value)
    ))
    priority: int = attr.ib(default=5, validator=attr.validators.and_(
        attr.validators.instance_of(int),
        attr.validators.in_(range(1, 6))
    ))
    
    @property
    def record_id(self) -> str:
        return self.event_id
    
    @property
    def timestamp(self) -> float:
        return self.event_timestamp