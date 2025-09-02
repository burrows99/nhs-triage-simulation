"""Random Service for Hospital Simulation

This service centralizes all random data generation for the hospital simulation,
providing consistent and configurable random behavior across the system.

Single Responsibility: Only handles random data generation
"""

import random
from typing import Tuple
from src.triage.triage_constants import TriageCategories


class RandomService:
    """Centralized random data generation service for hospital simulation."""
    
    def __init__(self, seed: int = None):
        """Initialize random service with optional seed for reproducibility.
        
        Args:
            seed: Optional seed for random number generator
        """
        if seed is not None:
            random.seed(seed)
    
    def get_wait_time_variation(self, wait_time_type: str) -> float:
        """Get random variation for MTS wait time conversion.
        
        Args:
            wait_time_type: Type of wait time ('immediate', '10_min', '60_min', '120_min', '240_min')
            
        Returns:
            Random time in minutes with appropriate variation
        """
        wait_time_ranges = {
            'immediate': (1, 3),
            '10_min': (8, 12),
            '60_min': (50, 70),
            '120_min': (100, 140),
            '240_min': (200, 280)
        }
        
        if wait_time_type not in wait_time_ranges:
            raise ValueError(f"Unknown wait time type: {wait_time_type}")
        
        min_time, max_time = wait_time_ranges[wait_time_type]
        return random.uniform(min_time, max_time)
    
    def should_perform_diagnostics(self) -> bool:
        """Determine if patient should receive diagnostics (50% chance).
        
        Returns:
            True if diagnostics should be performed
        """
        return random.random() < 0.5
    
    def get_diagnostics_time(self) -> float:
        """Get random diagnostics time.
        
        Returns:
            Diagnostics time in minutes (30-60 minutes)
        """
        return random.uniform(30, 60)
    
    def should_admit_patient(self, category: str) -> bool:
        """Determine if high-priority patient should be admitted (60% chance).
        
        Args:
            category: Triage category
            
        Returns:
            True if patient should be admitted
        """
        if category in [TriageCategories.RED, TriageCategories.ORANGE]:
            return random.random() < 0.6
        return False
    
    def get_admission_time(self) -> float:
        """Get random admission processing time.
        
        Returns:
            Admission time in minutes (40-80 minutes)
        """
        return random.uniform(40, 80)
    
    def get_discharge_time(self) -> float:
        """Get random discharge processing time.
        
        Returns:
            Discharge time in minutes (10-20 minutes)
        """
        return random.uniform(10, 20)
    
    def determine_patient_disposition(self, category: str) -> tuple[str, bool, float]:
        """Determine patient disposition (admission or discharge) with processing time.
        
        Args:
            category: Triage category
            
        Returns:
            Tuple of (disposition, admitted, processing_time)
            - disposition: 'admitted' or 'discharged'
            - admitted: Boolean indicating admission status
            - processing_time: Time in minutes for disposition processing
        """
        if self.should_admit_patient(category):
            # High priority patients have 60% chance of admission
            disposition = 'admitted'
            admitted = True
            processing_time = self.get_admission_time()
        else:
            # Discharge process
            disposition = 'discharged'
            admitted = False
            processing_time = self.get_discharge_time()
        
        return disposition, admitted, processing_time
    
    def get_patient_arrival_interval(self, arrival_rate: float) -> float:
        """Get random patient arrival interval using Poisson process.
        
        Args:
            arrival_rate: Patients per hour
            
        Returns:
            Interarrival time in minutes
        """
        return random.expovariate(arrival_rate / 60)  # Convert to per-minute
    
    def set_seed(self, seed: int) -> None:
        """Set random seed for reproducible results.
        
        Args:
            seed: Random seed value
        """
        random.seed(seed)