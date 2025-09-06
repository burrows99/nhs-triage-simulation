from __future__ import annotations
from dataclasses import dataclass, field
import logging
import numpy as np
from services.logger_service import LoggerService

@dataclass(slots=True)
class TimeService:
    seed: int | None = None
    logger: logging.Logger = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        self.logger = LoggerService.get_logger(__name__)
        if self.seed is not None:
            np.random.seed(self.seed)
            self.logger.info("TimeService RNG seeded with %d", self.seed)

    def interarrival_time(self) -> float:
        # NHS arrivals are often modeled with log-normal or non-homogeneous Poisson; using log-normal simplification.
        mu, sigma = 1.2, 0.5
        t = float(np.random.lognormal(mean=mu, sigma=sigma))
        self.logger.debug("Sampled interarrival time=%.3f (mu=%.2f, sigma=%.2f)", t, mu, sigma)
        return t

    def service_time_doctor(self) -> float:
        mu, sigma = 1.0, 0.4
        t = float(np.random.lognormal(mean=mu, sigma=sigma))
        self.logger.debug("Sampled doctor service time=%.3f (mu=%.2f, sigma=%.2f)", t, mu, sigma)
        return t

    def service_time_mri(self) -> float:
        mu, sigma = 1.3, 0.3
        t = float(np.random.lognormal(mean=mu, sigma=sigma))
        self.logger.debug("Sampled MRI service time=%.3f (mu=%.2f, sigma=%.2f)", t, mu, sigma)
        return t

    def service_time_bed(self) -> float:
        mu, sigma = 2.0, 0.6
        t = float(np.random.lognormal(mean=mu, sigma=sigma))
        self.logger.debug("Sampled bed service time=%.3f (mu=%.2f, sigma=%.2f)", t, mu, sigma)
        return t