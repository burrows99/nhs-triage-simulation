import attr
from .resource import Resource


@attr.s(auto_attribs=True)
class Doctor(Resource):
    """Doctor resource class."""
    resource_type: str = "Doctor"