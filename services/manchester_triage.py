from __future__ import annotations
from dataclasses import dataclass
from enums.priority import Priority


@dataclass(slots=True)
class ManchesterSymptoms:
    """Simplified symptom set for a fuzzy Manchester Triage classification.
    All fields are continuous severities in [0.0, 1.0], where 1.0 is worst.
    """
    respiration_distress: float = 0.0  # breathlessness/airway compromise
    bleeding: float = 0.0              # external bleeding/shock indicators
    consciousness_impairment: float = 0.0  # AVPU/GCS proxy
    pain: float = 0.0                  # reported or observed pain
    temperature_anomaly: float = 0.0   # hypothermia/fever
    trauma_severity: float = 0.0       # mechanism of injury/severity


class ManchesterTriageSystem:
    """Basic fuzzy rules approximating the Manchester Triage System (MTS).

    This is a coarse approximation intended for simulation:
    - Uses hard discriminators for life threats (airway/breathing, consciousness)
    - Uses weighted aggregation for remaining presentations
    - Maps to the 5 MTS priority levels
    """

    def classify(self, s: ManchesterSymptoms) -> Priority:
        # Hard discriminators (life-threatening): immediate
        if s.respiration_distress >= 0.9 or s.consciousness_impairment >= 0.9:
            return Priority.IMMEDIATE
        # Very urgent discriminators (massive bleed or high-energy trauma)
        if s.bleeding >= 0.85 or s.trauma_severity >= 0.85:
            return Priority.VERY_URGENT

        # Weighted fuzzy score for remaining cases
        score = (
            0.30 * float(s.respiration_distress)
            + 0.25 * float(s.consciousness_impairment)
            + 0.20 * float(s.bleeding)
            + 0.15 * float(s.pain)
            + 0.05 * float(s.temperature_anomaly)
            + 0.05 * float(s.trauma_severity)
        )

        if score >= 0.75:
            return Priority.VERY_URGENT
        if score >= 0.55:
            return Priority.URGENT
        if score >= 0.35:
            return Priority.STANDARD
        return Priority.NON_URGENT