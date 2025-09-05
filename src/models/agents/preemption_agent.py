import attr
import random
from typing import Dict, List, Any
from ..entities.entity import Entity
from ..entities.patient import Patient
from ..entities.resources.resource import Resource
from ...utils.constants import TRIAGE_PRIORITIES


@attr.s(auto_attribs=True)
class PreemptionAgent(Entity):
    """Agent that makes preemption decisions for hospital resources."""
    
    def should_preempt(self, hospital_resources: Dict[str, List[Resource]], patient: Patient) -> Dict[str, Any]:
        """Determine if preemption should occur and return preemption decision."""
        if not hospital_resources:
            return {"preempt": False, "target_resource_id": None, "target_queue": None}
        
        resource_type = random.choice(list(hospital_resources.keys()))
        resource_list = hospital_resources[resource_type]
        
        if not resource_list:
            return {"preempt": False, "target_resource_id": None, "target_queue": None}
        
        target_res = random.choice(resource_list)
        return {
            "preempt": random.choice([True, False]),
            "target_resource_id": target_res.entity_id,
            "target_queue": random.choice(TRIAGE_PRIORITIES),
        }