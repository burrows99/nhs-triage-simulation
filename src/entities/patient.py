import random
import logging

logger = logging.getLogger(__name__)

class Patient:
    """Patient class for NHS Triage Simulation
    
    Represents a patient in the emergency department with tracking
    of various timestamps and wait times throughout their journey.
    """
    def __init__(self, id, arrival_time=0):
        self.id = id
        self.arrival_time = arrival_time
        self.priority = 0  # 1: immediate, 2: very urgent, 3: urgent, 4: standard, 5: non-urgent
        self.triage_time = 0
        self.wait_for_triage = 0
        self.consult_time = 0
        self.wait_for_consult = 0
        self.discharge_time = 0
        self.admitted = False
        
        # Generate severity for triage system (0.0 to 1.0)
        self.severity = self._generate_severity()
        
        logger.debug(f"Created Patient {self.id} with severity {self.severity:.3f} at time {arrival_time}")
    
    def _generate_severity(self):
        """Generate a severity score for the patient based on realistic distributions
        
        Returns a value between 0.0 and 1.0 where:
        - 0.0-0.3: Low severity (non-urgent to standard)
        - 0.3-0.6: Medium severity (urgent)
        - 0.6-0.8: High severity (very urgent)
        - 0.8-1.0: Very high severity (immediate)
        """
        # Use a beta distribution to create realistic severity distribution
        # Most patients have lower severity, fewer have high severity
        return random.betavariate(2, 5)  # Skewed towards lower values
        
    def calculate_wait_times(self):
        """Calculate various wait times based on recorded timestamps"""
        if self.triage_time > 0:
            self.wait_for_triage = self.triage_time - self.arrival_time
        if self.consult_time > 0:
            self.wait_for_consult = self.consult_time - self.triage_time
        if self.discharge_time > 0:
            self.total_time = self.discharge_time - self.arrival_time