import attr
from .resource import Resource


@attr.s(auto_attribs=True)
class MRI(Resource):
    """MRI machine resource class."""
    resource_type: str = "MRI"