from dataclasses import dataclass
from ..resource import Resource

@dataclass
class Doctor(Resource):
    specialty: str = ""