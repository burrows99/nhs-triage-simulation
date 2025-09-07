from __future__ import annotations
from dataclasses import dataclass, field
from typing import cast
import simpy
from entities.hospital import Hospital
from services.patient_factory import PatientFactory
from enums.resource_type import ResourceType
from entities.patient import Patient


@dataclass(slots=True)
class SimulationConfig:
    num_doctors: int
    num_mri: int
    num_beds: int
    sim_duration: float
    seed: int | None = None


@dataclass(slots=True)
class SimulationRunner:
    config: SimulationConfig
    env: simpy.Environment = field(init=False)
    hospital: Hospital = field(init=False)
    patient_factory: PatientFactory = field(init=False)
    doctor_res: simpy.PreemptiveResource = field(init=False)
    mri_res: simpy.PreemptiveResource = field(init=False)
    bed_res: simpy.Resource = field(init=False)

    def __post_init__(self) -> None:
        self.env = simpy.Environment()
        self.hospital = Hospital(
            num_doctors=self.config.num_doctors,
            num_mri=self.config.num_mri,
            num_beds=self.config.num_beds,
            seed=self.config.seed,
        )
        self.patient_factory = PatientFactory()
        # Instantiate shared resources managed by the simulation engine
        self.doctor_res = simpy.PreemptiveResource(self.env, capacity=self.config.num_doctors)
        self.mri_res = simpy.PreemptiveResource(self.env, capacity=self.config.num_mri)
        self.bed_res = simpy.Resource(self.env, capacity=self.config.num_beds)

    # ------------- Helpers to reduce function size -------------
    def _choose_resource_for(self, rtype: ResourceType) -> simpy.Resource:
        if rtype == ResourceType.DOCTOR:
            return self.doctor_res
        if rtype == ResourceType.MRI:
            return self.mri_res
        if rtype == ResourceType.BED:
            return self.bed_res
        raise ValueError(f"Unknown ResourceType: {rtype}")

    def _compute_preempt_flag(self, patient: Patient, rtype: ResourceType, now: float) -> bool:
        return self.hospital.should_preempt(patient, rtype, now) if self.hospital.is_preemptive_resource(rtype) else False

    def _build_request(self, rtype: ResourceType, res: simpy.Resource, priority_value: int, preempt_flag: bool):
        if self.hospital.is_preemptive_resource(rtype):
            pre_res = cast(simpy.PreemptiveResource, res)
            return pre_res.request(priority=priority_value, preempt=preempt_flag)
        return res.request()

    def _on_service_start(self, patient: Patient, rtype: ResourceType, start: float, planned_service: float) -> None:
        self.hospital.on_service_start(patient, rtype, start, planned_service)

    def _handle_preemption(self, patient: Patient, rtype: ResourceType, now: float) -> float:
        self.hospital.on_service_preempted(patient, rtype, now)
        return self.hospital.prepare_for_queue(patient, rtype, now)

    def _route_after_completion(self, patient: Patient, rtype: ResourceType, now: float) -> tuple[ResourceType | None, float]:
        next_r = self.hospital.on_service_complete(patient, rtype, now)
        if next_r is None:
            return None, 0.0
        planned = self.hospital.prepare_for_queue(patient, next_r, now)
        return next_r, planned

    def _driver(self):
        # Generate one patient at a time using lognormal interarrival times until the time horizon
        horizon = float(self.config.sim_duration)
        ts = self.hospital.time_service
        while True:
            inter = float(ts.interarrival_time())
            if float(self.env.now) + inter > horizon:
                break
            yield self.env.timeout(inter)
            # start a patient flow process
            self.env.process(self._service_pipeline())

    def _service_pipeline(self):
        now = float(self.env.now)
        patient = self.patient_factory.new_patient(now)
        # arrival and queuing
        rtype = self.hospital.on_patient_arrival(patient, now)
        planned_service = self.hospital.prepare_for_queue(patient, rtype, now)
        # choose resource
        res = self._choose_resource_for(rtype)
        # request and serve with agent-driven preemption control and proper preemption handling
        while True:
            now = float(self.env.now)
            priority_value = int(patient.priority)
            preempt_flag = self._compute_preempt_flag(patient, rtype, now)
            req_evt = self._build_request(rtype, res, priority_value, preempt_flag)
            with req_evt:
                yield req_evt
                start = float(self.env.now)
                self._on_service_start(patient, rtype, start, planned_service)
                try:
                    yield self.env.timeout(planned_service)
                except simpy.Interrupt:
                    # interrupted by a higher-priority request; record and requeue
                    planned_service = self._handle_preemption(patient, rtype, float(self.env.now))
                    # try again
                    continue
                else:
                    # service completed without preemption
                    next_r, planned = self._route_after_completion(patient, rtype, float(self.env.now))
                    if next_r is None:
                        break
                    # route to next stage and continue the loop
                    rtype = next_r
                    planned_service = planned
                    # choose resource for next stage
                    res = self._choose_resource_for(rtype)
                    continue

    def run(self) -> None:
        # Start the driver that generates patients; let all processes finish
        self.env.process(self._driver())
        self.env.run()
        # After all processes complete, finalize data persistence and plotting
        self.hospital.finalize(sim_duration=self.config.sim_duration)


if __name__ == "__main__":
    cfg = SimulationConfig(num_doctors=2, num_mri=1, num_beds=3, sim_duration=1000.0, seed=42)
    sim = SimulationRunner(cfg)
    sim.run()