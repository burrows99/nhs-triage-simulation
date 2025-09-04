"""Random Service for Hospital Simulation

This service centralizes all random data generation for the hospital simulation,
providing consistent and configurable random behavior across the system.

Single Responsibility: Only handles random data generation
"""

import attr
import random
from typing import Tuple, Dict, List, Any, Optional
import logging

from src.triage.triage_constants import TriageCategories, DiagnosticTestTypes


@attr.s(auto_attribs=True)
class RandomService:
    """Centralized random data generation service for hospital simulation."""
    
    seed: Optional[int] = None
    
    def __attrs_post_init__(self):
        """Initialize random service with optional seed for reproducibility."""
        if self.seed is not None:
            random.seed(self.seed)
        
        self.logger = logging.getLogger(__name__)
    
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
        
        # Handle both TriageResult objects and raw category strings using duck typing
        try:
            category = triage_input.triage_category
            # Check if it's a TriageResult with is_urgent method
            try:
                if triage_input.is_urgent():  # RED or ORANGE
                    # ALWAYS admit RED and ORANGE cases - clinical necessity
                    return True
            except AttributeError:
                pass  # Not a TriageResult with is_urgent method
        except AttributeError:
            # Raw category string (backward compatibility)
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
        # Handle both TriageResult objects and raw category strings using duck typing
        try:
            # TriageResult object - can use additional data for more informed decisions
            category = triage_input.triage_category
            # Could potentially use fuzzy_score, confidence, or system_type for enhanced logic
        except AttributeError:
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
        """Get admission processing time reflecting NHS REALITY 2024/25.
        
        NHS REALITY:
        - Bed occupancy consistently >90% since September 2021
        - Patients regularly remain despite being fit for discharge
        - No capacity in social care creating bed blocking
        - 1.61 million people waited >4 hours in A&E in past 12 months
        - Severe delays in bed allocation due to overcrowding
        
        Returns:
            Admission processing time reflecting NHS bed crisis
        """
        # Realistic MTS baseline - allows LLM optimization through better bed management
        base_time = 45.0  # 45-minute base admission processing time
        
        # Bed allocation delays that LLMs can optimize through predictive allocation
        bed_allocation_delay = random.uniform(15, 60)  # 15-60 minutes (optimizable)
        
        # Flow management delays that smart scheduling can reduce
        flow_delay = random.uniform(10, 30)  # 10-30 minutes (optimizable)
        
        # Shift-based variations (LLMs can optimize staffing patterns)
        import datetime
        now = datetime.datetime.now()
        if now.weekday() >= 5 or now.hour < 8 or now.hour > 18:  # Weekend or out-of-hours
            shift_multiplier = random.uniform(1.2, 1.5)  # Moderate increase
        else:
            shift_multiplier = random.uniform(1.0, 1.2)
        
        return (base_time + bed_allocation_delay + flow_delay) * shift_multiplier
    
    def get_discharge_processing_time(self) -> float:
        """Get discharge processing time reflecting NHS SOCIAL CARE CRISIS 2024/25.
        
        NHS REALITY:
        - Patients regularly remain in hospital despite being fit for discharge
        - No capacity in social care creating massive delays
        - Delayed discharge is a major cause of bed blocking
        - Social care crisis prevents safe discharge home
        - Complex discharge planning takes hours/days not minutes
        
        Returns:
            Discharge processing time reflecting social care crisis reality
        """
        # Realistic MTS baseline - allows LLM optimization through better discharge coordination
        base_time = 30.0  # 30-minute base discharge processing time
        
        # Discharge coordination delays that LLMs can optimize through better planning
        coordination_delay = random.uniform(15, 45)  # 15-45 minutes (optimizable)
        
        # Administrative processing that smart systems can streamline
        admin_processing = random.uniform(10, 30)  # 10-30 minutes (optimizable)
        
        # Weekend discharge variations (LLMs can optimize weekend workflows)
        import datetime
        now = datetime.datetime.now()
        if now.weekday() >= 5:  # Weekend
            weekend_multiplier = random.uniform(1.3, 1.7)  # Moderate weekend increase
        else:
            weekend_multiplier = random.uniform(1.0, 1.2)
        
        # Patient complexity factor (LLMs can optimize based on patient profiles)
        complexity_factor = random.uniform(1.0, 1.8)  # Variable complexity
        
        return (base_time + coordination_delay + admin_processing) * weekend_multiplier * complexity_factor
    
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
        
        NHS REALITY 2024/25 (What Actually Happens):
        - Only 59% of Type 1 A&E patients seen within 4 hours total
        - Triage nurses overwhelmed with patient volumes
        - 15-minute target routinely missed due to system pressures
        - Staff shortages causing significant delays
        - Interruptions from multiple critical patients
        - Bed occupancy >90% creating flow problems
        
        Reality: Triage takes much longer due to crisis-level system pressures
        
        Args:
            complexity: Case complexity (simple, standard, complex)
            
        Returns:
            Time in minutes reflecting harsh NHS reality
        """
        # Realistic MTS baseline times - allows LLM optimization through better prioritization
        complexity_times = {
            'simple': (8.0, 20.0),      # MTS Reality: Simple cases 8-20 minutes
            'standard': (15.0, 35.0),   # MTS Reality: Standard cases 15-35 minutes  
            'complex': (25.0, 60.0)     # MTS Reality: Complex cases 25-60 minutes
        }
        
        min_time, max_time = complexity_times.get(complexity, complexity_times['standard'])
        base_time = random.uniform(min_time, max_time)
        
        # Moderate system pressure - realistic but optimizable
        pressure_factor = random.uniform(1.2, 1.6)  # Moderate system strain
        
        # Queue delays that LLMs can optimize through better scheduling
        queue_delay = random.uniform(5, 25)  # 5-25 minutes queue wait (optimizable)
        
        # Seasonal variation (winter pressures)
        import datetime
        current_month = datetime.datetime.now().month
        if current_month in [11, 12, 1, 2, 3]:  # Winter months
            winter_multiplier = random.uniform(1.2, 1.4)
        else:
            winter_multiplier = random.uniform(1.0, 1.1)
        
        return (base_time * pressure_factor * winter_multiplier) + queue_delay
    
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
        """Extract priority and confidence from different input types using duck typing."""
        try:
            # TriageResult object
            priority = triage_input.priority_score
            confidence_factor = getattr(triage_input, 'confidence', 1.0)
        except AttributeError:
            if isinstance(triage_input, int):
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
        from src.triage.triage_constants import PRIORITY_MULTIPLIERS
        priority_multipliers = PRIORITY_MULTIPLIERS
        
        multiplier = priority_multipliers.get(priority, 1.0)
        
        # Adjust for confidence if using TriageResult (duck typing)
        try:
            if triage_input.confidence and priority <= 2:  # RED/ORANGE
                multiplier *= (0.8 + 0.2 * confidence_factor)  # 0.8-1.0 range
        except AttributeError:
            pass  # No confidence attribute, use base multiplier
        
        return multiplier
    
    def _apply_minimum_delay(self, adjusted_delay, priority):
        """Apply minimum realistic delay constraints."""
        min_realistic_delay = 0.5 if priority == 1 else 1.0
        return max(adjusted_delay, min_realistic_delay)