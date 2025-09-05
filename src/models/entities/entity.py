import attr


@attr.s(auto_attribs=True)
class Entity:
    """Base class for all entities in the hospital simulation."""
    entity_id: int
    name: str