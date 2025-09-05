import attr
from .resource import Resource


@attr.s(auto_attribs=True)
class Bed(Resource):
    """Bed resource class."""
    resource_type: str = "Bed"