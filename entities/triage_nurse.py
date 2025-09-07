from __future__ import annotations
from dataclasses import dataclass, field
from enums.priority import Priority
from entities.base import BaseEntity
from entities.patient import Patient
from services.manchester_triage import ManchesterTriageSystem, ManchesterSymptoms
from services.preemption_agent import PreemptionAgent, PreemptionDecision

@dataclass(slots=True)
class TriageNurse(BaseEntity):
    agent: PreemptionAgent = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        BaseEntity.__post_init__(self)
        self.agent = PreemptionAgent()

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

    def assess_and_assign_priority(self, patient: Patient) -> Priority:
        """Assess a patient and assign a triage priority using a simplified MTS classifier.
        Generates a basic symptoms profile (in lieu of full clinical data) and classifies it.
        Also sets patient's initial required resource guided by agent recommendation; must be explicitly provided.
        """
        # Deterministic pseudo-random profile from patient id for reproducibility
        def prng(a: int) -> float:
            v: int = (a * 1103515245 + 12345) % (2**31)
            return float(v) / float(2**31)

        rng_seed: int = (patient.id * 9301 + 49297) % 233280
        # Generate bounded severities in [0,1]
        respiration_distress: float = prng(rng_seed)
        bleeding: float = prng(rng_seed + 1)
        consciousness_impairment: float = prng(rng_seed + 2)
        pain: float = prng(rng_seed + 3)
        temperature_anomaly: float = prng(rng_seed + 4)
        trauma_severity: float = prng(rng_seed + 5)
        symptoms = ManchesterSymptoms(
            respiration_distress=respiration_distress,
            bleeding=bleeding,
            consciousness_impairment=consciousness_impairment,
            pain=pain,
            temperature_anomaly=temperature_anomaly,
            trauma_severity=trauma_severity,
        )
        mts = ManchesterTriageSystem()
        pr = mts.classify(symptoms)
        # Store triage outputs on patient
        patient.symptoms = symptoms
        patient.priority = pr
        # Attempt an initial resource recommendation via embedded agent (must not be None)
        initial = self.agent.recommend_initial_resource(patient)
        patient.required_resource = initial
        self.logger.info(
            f"Triage assessed patient {patient.id} -> priority={pr.name} "
            f"[resp={respiration_distress:.2f}, bleed={bleeding:.2f}, cons={consciousness_impairment:.2f}, "
            f"pain={pain:.2f}, temp={temperature_anomaly:.2f}, trauma={trauma_severity:.2f}] "
            f"initial_resource={getattr(patient.required_resource, 'name', patient.required_resource)}"
        )
        return pr

    def recommend_preemption(self, patient: Patient, ops_state: object) -> PreemptionDecision:
        """Return a preemption recommendation for the patient's currently required resource.
        Randomized for now via the embedded agent, but constrained by resource preemptibility.
        Only DOCTOR and MRI are considered preemptible; BED is not.
        """
        rtype = patient.required_resource
        # required_resource must be present
        if rtype is None:
            raise ValueError("Patient has no required_resource set; cannot make preemption recommendation")
        # Non-preemptible resource -> never preempt
        if not rtype.preemptible:
            self.logger.debug("Preemption not allowed for resource %s; returning no-preempt decision", rtype.name)
            return PreemptionDecision(False, rtype, None)
        # Delegate randomized decision to the embedded agent
        decision = self.agent.decide(patient, ops_state)
        # Ensure the decision targets the patient's current required resource when preempting
        if decision.should_preempt and decision.resource_type != rtype:
            # align to current resource context
            return PreemptionDecision(True, rtype, decision.target_index)
        return decision