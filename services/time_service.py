from typing import Final, Optional
import numpy as np
from dataclasses import dataclass
from enum import Enum


class TimeDistribution(Enum):
    """Statistical distributions used for time generation."""
    LOG_NORMAL = "log_normal"
    EXPONENTIAL = "exponential"
    GAMMA = "gamma"
    NORMAL = "normal"


@dataclass(frozen=True)
class TimeParameters:
    """
    Parameters for time distribution generation.
    
    Validation ensures parameters are within realistic bounds
    to prevent simulation anomalies.
    """
    mean: float
    std_dev: float
    min_time: float = 0.1  # Minimum 6 seconds
    max_time: float = 1440.0  # Maximum 24 hours
    
    def __post_init__(self) -> None:
        """Validate parameters to ensure realistic time generation."""
        if self.mean <= 0:
            raise ValueError("Mean time must be positive")
        if self.std_dev <= 0:
            raise ValueError("Standard deviation must be positive")
        if self.min_time >= self.max_time:
            raise ValueError("Minimum time must be less than maximum time")
        if self.mean < self.min_time or self.mean > self.max_time:
            raise ValueError("Mean must be within min/max bounds")


class TimeService:
    """
    Service for generating realistic healthcare service times.
    
    Based on NHS operational data and research:
    - Patient arrivals follow log-normal distribution (NHS Emergency Care Dataset)
    - Service times vary by resource type and patient acuity
    - Includes realistic bounds to prevent extreme outliers
    
    References:
    - NHS England A&E Statistics: https://www.england.nhs.uk/statistics/ae-waiting-times/
    - Healthcare Operations Research: Queuing Theory Applications
    """
    
    # NHS-based time parameters (in minutes)
    _NHS_TIME_PARAMS: Final[dict[str, TimeParameters]] = {
        "patient_arrival": TimeParameters(
            mean=8.5,      # Average 8.5 minutes between arrivals
            std_dev=12.3,   # High variability in emergency arrivals
            min_time=0.5,   # Minimum 30 seconds
            max_time=60.0   # Maximum 1 hour gap
        ),
        "triage_assessment": TimeParameters(
            mean=7.2,       # Average triage time: 7.2 minutes
            std_dev=3.1,    # Based on NHS triage standards
            min_time=2.0,   # Minimum 2 minutes
            max_time=20.0   # Maximum 20 minutes
        ),
        "doctor_consultation": TimeParameters(
            mean=18.5,      # Average consultation: 18.5 minutes
            std_dev=8.7,    # Varies by complexity
            min_time=5.0,   # Quick consultations: 5 minutes
            max_time=60.0   # Complex cases: 1 hour
        ),
        "mri_scan": TimeParameters(
            mean=35.0,      # Average MRI scan: 35 minutes
            std_dev=15.2,   # Varies by scan type
            min_time=15.0,  # Quick scans: 15 minutes
            max_time=90.0   # Complex scans: 1.5 hours
        ),
        "bed_occupancy": TimeParameters(
            mean=240.0,     # Average bed stay: 4 hours
            std_dev=180.0,  # High variability
            min_time=30.0,  # Minimum 30 minutes
            max_time=720.0  # Maximum 12 hours
        )
    }
    
    def __init__(self, random_seed: Optional[int] = None) -> None:
        """
        Initialize TimeService with optional random seed for reproducibility.
        
        Args:
            random_seed: Seed for numpy random number generator
        """
        if random_seed is not None:
            np.random.seed(random_seed)
        self._rng = np.random.default_rng(random_seed)
    
    def generate_arrival_time(self) -> float:
        """
        Generate inter-arrival time for patients using log-normal distribution.
        
        Log-normal distribution models the 'bursty' nature of emergency arrivals
        where most arrivals are close together with occasional longer gaps.
        
        Returns:
            Time in minutes until next patient arrival
        """
        params = self._NHS_TIME_PARAMS["patient_arrival"]
        return self._generate_log_normal_time(params)
    
    def generate_triage_time(self) -> float:
        """
        Generate triage assessment time.
        
        Returns:
            Triage time in minutes
        """
        params = self._NHS_TIME_PARAMS["triage_assessment"]
        return self._generate_gamma_time(params)
    
    def generate_doctor_time(self, priority_multiplier: float = 1.0) -> float:
        """
        Generate doctor consultation time.
        
        Args:
            priority_multiplier: Adjustment factor based on patient priority
                                (higher priority = longer consultation)
        
        Returns:
            Consultation time in minutes
        """
        params = self._NHS_TIME_PARAMS["doctor_consultation"]
        base_time = self._generate_gamma_time(params)
        return min(base_time * priority_multiplier, params.max_time)
    
    def generate_mri_time(self) -> float:
        """
        Generate MRI scan time.
        
        Returns:
            MRI scan time in minutes
        """
        params = self._NHS_TIME_PARAMS["mri_scan"]
        return self._generate_gamma_time(params)
    
    def generate_bed_time(self, priority_multiplier: float = 1.0) -> float:
        """
        Generate bed occupancy time.
        
        Args:
            priority_multiplier: Adjustment factor based on patient condition
        
        Returns:
            Bed occupancy time in minutes
        """
        params = self._NHS_TIME_PARAMS["bed_occupancy"]
        base_time = self._generate_log_normal_time(params)
        return min(base_time * priority_multiplier, params.max_time)
    
    def _generate_log_normal_time(self, params: TimeParameters) -> float:
        """
        Generate time using log-normal distribution.
        
        Log-normal is ideal for modeling service times that are:
        - Always positive
        - Right-skewed (most values small, few large values)
        - Multiplicatively distributed
        """
        # Convert mean and std to log-normal parameters
        variance = params.std_dev ** 2
        mu = np.log(params.mean ** 2 / np.sqrt(variance + params.mean ** 2))
        sigma = np.sqrt(np.log(1 + variance / params.mean ** 2))
        
        time_value = self._rng.lognormal(mu, sigma)
        return float(np.clip(time_value, params.min_time, params.max_time))
    
    def _generate_gamma_time(self, params: TimeParameters) -> float:
        """
        Generate time using gamma distribution.
        
        Gamma distribution is suitable for modeling:
        - Service times with natural lower bounds
        - Processes with multiple stages
        - More controlled variability than log-normal
        """
        # Convert mean and std to gamma parameters
        scale = params.std_dev ** 2 / params.mean
        shape = params.mean / scale
        
        time_value = self._rng.gamma(shape, scale)
        return float(np.clip(time_value, params.min_time, params.max_time))
    
    def calculate_priority_multiplier(self, priority_level: int) -> float:
        """
        Calculate time multiplier based on patient priority.
        
        Higher priority patients typically require more intensive care,
        resulting in longer service times.
        
        Args:
            priority_level: Priority level (1=highest, 5=lowest)
        
        Returns:
            Multiplier for base service time
        """
        if not 1 <= priority_level <= 5:
            raise ValueError("Priority level must be between 1 and 5")
        
        # Higher priority = longer service time multiplier
        multipliers: Final[dict[int, float]] = {
            1: 1.8,  # Immediate - complex cases
            2: 1.5,  # Very urgent - significant intervention
            3: 1.2,  # Urgent - moderate complexity
            4: 1.0,  # Standard - baseline time
            5: 0.8   # Non-urgent - quick resolution
        }
        return multipliers[priority_level]