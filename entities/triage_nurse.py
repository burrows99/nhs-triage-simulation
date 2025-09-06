from __future__ import annotations
from dataclasses import dataclass
from enums.priority import Priority
from entities.base import BaseEntity

@dataclass(slots=True)
class TriageNurse(BaseEntity):
    def __post_init__(self) -> None:
        BaseEntity.__post_init__(self)

    def assign_priority(self, symptoms_score: float) -> Priority:
        # Minimal stand-in for MTS categorisation: use a simple threshold mapping.
        if symptoms_score >= 0.9:
            pr = Priority.IMMEDIATE
        elif symptoms_score >= 0.7:
            pr = Priority.VERY_URGENT
        elif symptoms_score >= 0.5:
            pr = Priority.URGENT
        elif symptoms_score >= 0.3:
            pr = Priority.STANDARD
        else:
            pr = Priority.NON_URGENT
        self.logger.debug("Assigned priority %s for symptoms_score=%.2f", pr.name, symptoms_score)
        return pr