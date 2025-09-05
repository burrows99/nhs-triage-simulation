import numpy as np
from typing import List, Generator, Optional
from ..models.entities.patient import Patient
from ..factories.patient import PatientFactory


class StatisticsService:
    """Service for generating patients with log-normal arrival times using PatientFactory."""
    
    def __init__(self, mu: float = 0.0, sigma: float = 1.0, seed: Optional[int] = None):
        """
        Initialize the statistics service.
        
        Args:
            mu: Mean of underlying normal distribution (default: 0.0)
            sigma: Standard deviation of underlying normal distribution (default: 1.0)
            seed: Random seed for reproducibility (optional)
        """
        self.mu = mu
        self.sigma = sigma
        self.patient_factory = PatientFactory(seed=seed)
        if seed is not None:
            np.random.seed(seed)
    
    def generate_arrival_time(self) -> float:
        """Generate a single log-normal distributed arrival time."""
        return np.random.lognormal(self.mu, self.sigma)
    
    def generate_patients(self, count: int, name_prefix: str = "Patient") -> List[Patient]:
        """Generate a list of patients with log-normal arrival times using PatientFactory."""
        patients: List[Patient] = []
        cumulative_time = 0.0
        
        for i in range(count):
            # Generate inter-arrival time using log-normal distribution
            inter_arrival_time = self.generate_arrival_time()
            cumulative_time += inter_arrival_time
            
            # Create realistic patient using factory
            patient = self.patient_factory.create_patient(
                entity_id=i,
                name=f"{name_prefix}_{i}"
            )
            # Override arrival time with log-normal distribution
            patient.arrival_time = int(cumulative_time)
            patients.append(patient)
        
        return patients
    
    def generate_patient_stream(self, name_prefix: str = "Patient") -> Generator[Patient, None, None]:
        """Generate an infinite stream of patients with log-normal arrival times using PatientFactory."""
        patient_id = 0
        cumulative_time = 0.0
        
        while True:
            inter_arrival_time = self.generate_arrival_time()
            cumulative_time += inter_arrival_time
            
            # Create realistic patient using factory
            patient = self.patient_factory.create_patient(
                entity_id=patient_id,
                name=f"{name_prefix}_{patient_id}"
            )
            # Override arrival time with log-normal distribution
            patient.arrival_time = int(cumulative_time)
            
            yield patient
            patient_id += 1