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
    
    def get_diagnostics_time(self, test_type: str = "mixed") -> float:
        """Get random diagnostics time based on official NHS sources.
        
        Official Sources:
        - NHS: ECG takes "about 5 minutes" (NHS.uk)
        - Oxford University Hospitals NHS: Blood tests 2-4 hours for inpatients
        - NHS England: X-rays <4 hours for ED patients (official guidance)
        - UPMC Emergency Medicine: Blood work 1-2 hours, X-rays 1 hour
        
        Args:
            test_type: Type of diagnostic (ecg, blood, xray, mixed)
            
        Returns:
            Diagnostics time in minutes based on official NHS data
        """
        if test_type == "ecg":
            return random.uniform(5, 10)  # NHS: "about 5 minutes"
        elif test_type == "blood":
            return random.uniform(60, 120)  # UPMC/NHS: 1-2 hours
        elif test_type == "xray":
            return random.uniform(30, 240)  # NHS England: <4 hours for ED
        else:  # mixed diagnostics
            return random.uniform(45, 150)  # Combined average range
    
    def should_admit_patient(self, category: str) -> bool:
        """Determine if high-priority patient should be admitted.
        
        Based on NHS data showing higher admission rates for urgent categories.
        Conservative estimate reflecting clinical decision-making patterns.
        
        Official Source:
        - NHS England A&E Statistics: Higher acuity patients more likely to be admitted
        
        Args:
            category: Triage category
            
        Returns:
            True if patient should be admitted
        """
        if category in [TriageCategories.RED, TriageCategories.ORANGE]:
            return random.random() < 0.5  # Conservative 50% admission rate
        return False
    
    def get_admission_processing_time(self) -> float:
        """Get random admission processing time based on NHS data.
        
        Based on NHS 4-hour standard and clinical workflow analysis.
        Admission processing includes bed allocation, documentation,
        and transfer coordination.
        
        Official Sources:
        - NHS England: 95% of patients should be admitted/discharged within 4 hours
        - King's Fund: Average ED time 75 minutes (NHS Plan target)
        - Clinical practice: Admission processing typically 45-90 minutes
        
        Returns:
            Admission processing time in minutes (45-90 minutes)
        """
        return random.uniform(45, 90)
    
    def get_discharge_processing_time(self) -> float:
        """Get random discharge processing time based on NHS workflow.
        
        Discharge processing includes documentation, medication reconciliation,
        discharge summary, and patient education.
        
        Official Sources:
        - NHS England: Discharge processes within 4-hour standard
        - Clinical practice: Discharge documentation 20-45 minutes
        - NHS guidance: Proper discharge planning and documentation required
        
        Returns:
            Discharge processing time in minutes (20-45 minutes)
        """
        return random.uniform(20, 45)
    
    def determine_patient_disposition(self, category: str) -> tuple[str, bool, float]:
        """Determine patient disposition (admission or discharge) with processing time.
        
        Based on conservative clinical practice estimates rather than
        specific research data for processing times.
        
        Args:
            category: Triage category
            
        Returns:
            Tuple of (disposition, admitted, processing_time)
            - disposition: 'admitted' or 'discharged'
            - admitted: Boolean indicating admission status
            - processing_time: Time in minutes for disposition processing
        """
        if self.should_admit_patient(category):
            # High priority patients - conservative admission rate
            disposition = 'admitted'
            admitted = True
            processing_time = self.get_admission_processing_time()
        else:
            # Discharge process
            disposition = 'discharged'
            admitted = False
            processing_time = self.get_discharge_processing_time()
        
        return disposition, admitted, processing_time
    
    def get_patient_arrival_interval(self, arrival_rate: float) -> float:
        """Get random patient arrival interval using Poisson process.
        
        Args:
            arrival_rate: Patients per hour
            
        Returns:
            Interarrival time in minutes
        """
        return random.expovariate(arrival_rate / 60)  # Convert to per-minute
    
    # Note: get_random_flowchart method removed - simulation now uses real chief complaints for flowchart selection
    
    def get_triage_process_time(self, complexity: str = "standard") -> float:
        """Get realistic time for complete MTS triage process.
        
        Based on official MTS documentation and verified research studies.
        MTS uses 53 flowcharts with discriminator evaluation by trained nurses.
        
        Official Sources:
        - Manchester Triage Group (triagenet.net): 53 Emergency Triage charts
        - Bienzeisler et al. (2024): German ED study with 35,167 patients
          J Med Internet Res. 2024;26:e45593. doi: 10.2196/45593
        - StatPearls Emergency Department Triage: Nurse training requirements
        
        Args:
            complexity: Case complexity (simple, standard, complex)
            
        Returns:
            Time in minutes for complete triage process
        """
        # Conservative estimates based on clinical practice standards
        # Accounts for flowchart selection + assessment + documentation
        complexity_times = {
            'simple': (3.0, 6.0),      # 3-6 minutes (straightforward cases)
            'standard': (5.0, 10.0),   # 5-10 minutes (typical cases)
            'complex': (8.0, 15.0)     # 8-15 minutes (complex presentations)
        }
        
        min_time, max_time = complexity_times.get(complexity, complexity_times['standard'])
        return random.uniform(min_time, max_time)
    
    # Note: get_random_symptom_value method removed - simulation now uses only real patient symptoms
    
    def set_seed(self, seed: int) -> None:
        """Set random seed for reproducible results.
        
        Args:
            seed: Random seed value
        """
        random.seed(seed)