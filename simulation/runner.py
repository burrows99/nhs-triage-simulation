from __future__ import annotations
from dataclasses import dataclass, field
import simpy
from entities.hospital import Hospital
from services.patient_factory import PatientFactory


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

    def __post_init__(self) -> None:
        self.env = simpy.Environment()
        self.hospital = Hospital(
            env=self.env,
            num_doctors=self.config.num_doctors,
            num_mri=self.config.num_mri,
            num_beds=self.config.num_beds,
            seed=self.config.seed,
        )
        self.patient_factory = PatientFactory()

    def _driver(self):
        # Generate one patient at a time using lognormal interarrival times until the time horizon
        horizon = float(self.config.sim_duration)
        ts = self.hospital.time_service
        while True:
            inter = float(ts.interarrival_time())
            if float(self.env.now) + inter > horizon:
                break
            yield self.env.timeout(inter)
            p = self.patient_factory.new_patient(float(self.env.now))
            self.env.process(self.hospital.admit_patient(p))

    def run(self) -> None:
        # Start the driver that generates patients; let all processes finish
        self.env.process(self._driver())
        self.env.run()
        # After all processes complete, finalize data persistence and plotting
        self.hospital.finalize()


if __name__ == "__main__":
    cfg = SimulationConfig(num_doctors=2, num_mri=1, num_beds=3, sim_duration=200.0, seed=42)
    sim = SimulationRunner(cfg)
    sim.run()