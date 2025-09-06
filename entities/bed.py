from __future__ import annotations
from dataclasses import dataclass
from entities.base import BaseResource

@dataclass(slots=True)
class Bed(BaseResource):
    def __post_init__(self) -> None:
        BaseResource.__post_init__(self)