"""Random Service for Hospital Simulation

This service centralizes all random data generation for the hospital simulation,
providing consistent and configurable random behavior across the system.

Single Responsibility: Only handles random data generation
"""

import random
from typing import Tuple
from src.triage.triage_constants import TriageCategories, DiagnosticTestTypes


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
            'immediate': (1, 3),        # Manchester Triage System: Immediate care 1-3 minutes
            '10_min': (8, 12),          # MTS standards: Very urgent 8-12 minutes variation
            '60_min': (50, 70),         # MTS guidelines: Urgent 50-70 minutes range
            '120_min': (100, 140),      # MTS protocol: Standard 100-140 minutes range
            '240_min': (200, 280)       # MTS framework: Non-urgent 200-280 minutes range
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
        return random.random() < 0.5  # Clinical practice: Conservative 50% diagnostic rate for simulation
    
    def get_diagnostics_time(self, test_type: str = DiagnosticTestTypes.MIXED) -> float:
        """Get diagnostics time with minimal variation (TRIAGE-INDEPENDENT).
        
        Diagnostic processing times are independent of triage decisions.
        Small random variations added for realism while maintaining fair comparison.
        
        Args:
            test_type: Type of diagnostic from DiagnosticTestTypes constants
            
        Returns:
            Diagnostics time with small random variation (±15%)
        """
        # Base diagnostic times for triage-independent processes
        base_diagnostic_times = {
            DiagnosticTestTypes.ECG: 30.0,     # ECG time
            DiagnosticTestTypes.BLOOD: 180.0,  # Blood test time (3 hours)
            DiagnosticTestTypes.XRAY: 60.0,    # X-ray time
            DiagnosticTestTypes.MIXED: 90.0    # Mixed diagnostics time
        }
        
        base_time = base_diagnostic_times.get(test_type, 90.0)
        # Add ±15% random variation for realism
        variation = base_time * 0.15
        return random.uniform(base_time - variation, base_time + variation)
    
    def should_admit_patient(self, triage_input) -> bool:
        """Determine admission based on NHS REALITY vs Official Standards.
        
        OFFICIAL NHS DATA:
        - NHS England A&E Statistics: ~11-15% overall admission rate
        - Higher acuity patients more likely to be admitted
        
        NHS REALITY (What Actually Happens):
        - Defensive medicine due to system pressures
        - Lack of community alternatives forces admissions
        - Social care crisis prevents safe discharge
        - "Bed blocking" creates admission pressure
        - Risk-averse decisions due to understaffing
        
        Reality: Higher admission rates due to system failures
        
        CLINICAL LOGIC:
        - RED and ORANGE cases ALWAYS require admission (life-threatening/urgent)
        - YELLOW cases have moderate admission probability
        - GREEN/BLUE cases have low admission probability
        
        Args:
            triage_input: TriageResult object or category string
            
        Returns:
            True if patient should be admitted (reflecting NHS reality)
        """
        # Import TriageResult for proper type checking
        from src.models.triage_result import TriageResult
        
        # Handle both TriageResult objects and raw category strings
        if isinstance(triage_input, TriageResult):
            category = triage_input.triage_category
            if triage_input.is_urgent():  # RED or ORANGE
                # ALWAYS admit RED and ORANGE cases - clinical necessity
                return True
        else:
            category = triage_input
            if category in [TriageCategories.RED, TriageCategories.ORANGE]:
                # ALWAYS admit RED and ORANGE cases - clinical necessity
                return True
            elif category == TriageCategories.YELLOW:
                return random.random() < 0.3  # Reality: Some yellow patients admitted
        
        # Reality: Even lower acuity patients sometimes admitted due to system pressures
        return random.random() < 0.1  # 10% admission rate for lower acuity
    
    def should_escalate_to_emergency(self) -> bool:
        """Determine if a patient should be escalated to RED priority (emergency).
        
        This simulates walk-in emergencies or patients who deteriorate during triage.
        Based on clinical practice where ~2-3% of ED patients are true emergencies.
        
        Returns:
            True if patient should be escalated to RED priority
        """
        return random.random() < 0.03  # 3% chance of emergency escalation
    
    def get_diagnostic_test_type(self, triage_input) -> str:
        """Get appropriate diagnostic test type based on triage category.
        
        Args:
            triage_input: TriageResult object or category string (for backward compatibility)
            
        Returns:
            Diagnostic test type from DiagnosticTestTypes
        """
        # Handle both TriageResult objects and raw category strings
        if hasattr(triage_input, 'triage_category'):
            # TriageResult object - can use additional data for more informed decisions
            category = triage_input.triage_category
            # Could potentially use fuzzy_score, confidence, or system_type for enhanced logic
        else:
            # Backward compatibility: raw category string
            category = triage_input
        
        if category == TriageCategories.RED:
            return random.choice([DiagnosticTestTypes.ECG, DiagnosticTestTypes.BLOOD, DiagnosticTestTypes.MIXED])
        elif category == TriageCategories.ORANGE:
            return random.choice([DiagnosticTestTypes.BLOOD, DiagnosticTestTypes.XRAY, DiagnosticTestTypes.MIXED])
        elif category == TriageCategories.YELLOW:
            return random.choice([DiagnosticTestTypes.XRAY, DiagnosticTestTypes.BLOOD])
        else:  # GREEN, BLUE
            return random.choice([DiagnosticTestTypes.XRAY, DiagnosticTestTypes.ECG])
    
    def get_admission_processing_time(self) -> float:
        """Get admission processing time with minimal variation (TRIAGE-INDEPENDENT).
        
        Admission processing time is independent of triage decisions.
        Small random variation added for realism while maintaining fair comparison.
        
        Returns:
            Admission processing time with small random variation (±20%)
        """
        # Base admission processing time for triage-independent processes
        base_time = 240.0  # 4-hour base admission processing time
        # Add ±20% random variation for realism
        variation = base_time * 0.20
        return random.uniform(base_time - variation, base_time + variation)
    
    def get_discharge_processing_time(self) -> float:
        """Get discharge processing time with minimal variation (TRIAGE-INDEPENDENT).
        
        Discharge processing time is independent of triage decisions.
        Small random variation added for realism while maintaining fair comparison.
        
        Returns:
            Discharge processing time with small random variation (±20%)
        """
        # Base discharge processing time for triage-independent processes
        base_time = 90.0  # 1.5-hour base discharge processing time
        # Add ±20% random variation for realism
        variation = base_time * 0.20
        return random.uniform(base_time - variation, base_time + variation)
    
    def determine_patient_disposition(self, triage_input) -> tuple[str, bool, float]:
        """Determine patient disposition (admission or discharge) with processing time.
        
        Based on conservative clinical practice estimates rather than
        specific research data for processing times.
        
        Args:
            triage_input: TriageResult object or category string (for backward compatibility)
            
        Returns:
            Tuple of (disposition, admitted, processing_time)
            - disposition: 'admitted' or 'discharged'
            - admitted: Boolean indicating admission status
            - processing_time: Time in minutes for disposition processing
        """
        # Use TriageResult-aware admission logic
        if self.should_admit_patient(triage_input):
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
        return random.expovariate(arrival_rate / 60)  # Poisson process: Standard healthcare modeling approach
        
    def get_triage_process_time(self, complexity: str = "standard") -> float:
        """Get triage process time based on NHS REALITY vs Official Standards.
        
        OFFICIAL NHS TARGETS:
        - NHS England (2022): Initial assessment within 15 minutes
        - Manchester Triage Group: 53 Emergency Triage charts, 3-15 minutes
        - StatPearls: Optimal triage in 10-15 minutes
        
        NHS REALITY (What Actually Happens):
        - Triage nurses overwhelmed with patient volumes
        - 15-minute target frequently missed
        - Interruptions and multiple patient management
        - Staff shortages causing delays
        - Complex cases take much longer in reality
        
        Reality: Triage takes longer due to system pressures and nurse workload
        
        Args:
            complexity: Case complexity (simple, standard, complex)
            
        Returns:
            Time in minutes reflecting NHS reality pressures
        """
        # NHS Reality: Triage nurses under pressure, targets frequently missed
        # Calibrated to achieve realistic NHS performance (59-76% 4-hour compliance)
        complexity_times = {
            'simple': (10.0, 30.0),    # Reality: Simple cases delayed but manageable
            'standard': (20.0, 60.0),  # Reality: Standard cases take longer than target
            'complex': (40.0, 120.0)   # Reality: Complex cases significantly delayed
        }
        
        min_time, max_time = complexity_times.get(complexity, complexity_times['standard'])
        base_time = random.uniform(min_time, max_time)
        
        # Add moderate system pressure factor reflecting queue delays and interruptions
        pressure_factor = random.uniform(1.2, 2.0)  # Moderate to high system strain
        
        # Add random queue delay (patients waiting for triage nurse availability)
        queue_delay = random.uniform(0, 30)  # 0-30 minutes additional queue wait
        
        return (base_time * pressure_factor) + queue_delay
    
    # Removed get_doctor_assessment_time - now using MTS priority_score and fuzzy_score directly
    
    def get_resource_allocation_delay(self, resource_type: str) -> float:
        """Get delay for resource allocation with minimal variation (TRIAGE-INDEPENDENT).
        
        These delays are independent of triage decisions. Small random variations
        added for realism while maintaining fair comparison between triage systems.
        
        Args:
            resource_type: Type of resource ('doctor', 'bed', 'nurse')
            
        Returns:
            Allocation delay with small random variation (±10%)
        """
        # Base delays for triage-independent processes with small variation
        base_delays = {
            'doctor': 5.0,    # Doctor handover time
            'bed': 10.0,      # Bed preparation time
            'nurse': 2.5,     # Nurse handover time
            'triage': 2.0     # Triage setup time
        }
        
        base_time = base_delays.get(resource_type, 2.0)
        # Add ±10% random variation for realism
        variation = base_time * 0.1
        return random.uniform(base_time - variation, base_time + variation)
    
    def get_handover_delay(self, resource_type: str, triage_input = None) -> float:
        """Get realistic handover delay based on patient priority and resource type.
        
        Higher priority patients get faster handovers but still have minimum realistic delays.
        
        Args:
            resource_type: Type of resource ('doctor', 'bed', 'nurse')
            triage_input: TriageResult object, priority integer, or None (for backward compatibility)
            
        Returns:
            Handover delay in minutes
        """
        base_delay = self.get_resource_allocation_delay(resource_type)
        priority, confidence_factor = self._extract_priority_and_confidence(triage_input)
        multiplier = self._calculate_priority_multiplier(priority, confidence_factor, triage_input)
        adjusted_delay = base_delay * multiplier
        return self._apply_minimum_delay(adjusted_delay, priority)
    
    def _extract_priority_and_confidence(self, triage_input):
        """Extract priority and confidence from different input types."""
        if hasattr(triage_input, 'priority_score'):
            # TriageResult object
            priority = triage_input.priority_score
            confidence_factor = getattr(triage_input, 'confidence', 1.0)
        elif isinstance(triage_input, int):
            # Raw priority integer (backward compatibility)
            priority = triage_input
            confidence_factor = 1.0
        else:
            # Default case
            priority = 5
            confidence_factor = 1.0
        return priority, confidence_factor
    
    def _calculate_priority_multiplier(self, priority, confidence_factor, triage_input):
        """Calculate delay multiplier based on priority and confidence."""
        priority_multipliers = {
            1: 0.5,  # RED: Fastest handover but still 50% of base delay
            2: 0.7,  # ORANGE: Quick handover
            3: 0.9,  # YELLOW: Standard handover
            4: 1.0,  # GREEN: Normal handover
            5: 1.2   # BLUE: Can wait slightly longer
        }
        
        multiplier = priority_multipliers.get(priority, 1.0)
        
        # Adjust for confidence if using TriageResult
        if hasattr(triage_input, 'confidence') and priority <= 2:  # RED/ORANGE
            multiplier *= (0.8 + 0.2 * confidence_factor)  # 0.8-1.0 range
        
        return multiplier
    
    def _apply_minimum_delay(self, adjusted_delay, priority):
        """Apply minimum realistic delay constraints."""
        min_realistic_delay = 0.5 if priority == 1 else 1.0
        return max(adjusted_delay, min_realistic_delay)