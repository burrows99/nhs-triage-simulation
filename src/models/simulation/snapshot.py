import attr
from typing import Dict, List, TYPE_CHECKING
from copy import deepcopy
from ..entities.entity import Entity
from ...utils.constants import SNAPSHOT_COUNTER

if TYPE_CHECKING:
    from ..entities.resources.resource import Resource
    from ..hospital.hospital import Hospital


@attr.s(auto_attribs=True)
class Snapshot(Entity):
    """Snapshot of hospital state at a specific simulation step."""
    step: int
    resources_state: Dict[str, List['Resource']]

    @classmethod
    def take(cls, hospital: 'Hospital', step: int) -> 'Snapshot':
        """Take a snapshot of the hospital's current state."""
        entity_id = next(SNAPSHOT_COUNTER)
        name = f"Snapshot Step {step}"
        copied = {rtype: [deepcopy(r) for r in reslist] for rtype, reslist in hospital.resources.items()}
        return cls(entity_id=entity_id, name=name, step=step, resources_state=copied)