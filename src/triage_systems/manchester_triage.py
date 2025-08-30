import random
import numpy as np
from src.config.parameters import p
from src.triage_systems.base_triage import BaseTriage
from src.config.constants import SymptomSeverity, LogMessages
import logging

logger = logging.getLogger(__name__)

class ManchesterTriage(BaseTriage):
    """
    Implementation of the Manchester Triage System (MTS) for the NHS Emergency Department simulation.
    
    The Manchester Triage System is a widely used standard in the UK and Europe for prioritizing
    patients in emergency rooms. It consists of flowcharts with standard definitions to categorize
    patients based on their level of urgency.
    
    This implementation includes a fuzzy approach as described in the paper:
    "FMTS: A fuzzy implementation of the Manchester triage system"
    by Matthew Cremeens and Elham S. Khorasani.
    
    The system uses fuzzy logic to handle the imprecise linguistic terms in the MTS such as
    "very low", "significant", "urgent", etc., which can lead to more consistent triage decisions.
    
    Priority levels in Manchester Triage System:
    1: Immediate (Red) - Immediately life-threatening condition (0 minute wait)
    2: Very Urgent (Orange) - Potentially life-threatening condition (10 minute wait)
    3: Urgent (Yellow) - Serious condition but not immediately life-threatening (60 minute wait)
    4: Standard (Green) - Standard condition that requires treatment (120 minute wait)
    5: Non-Urgent (Blue) - Minor condition that can safely wait (240 minute wait)
    """
    
    def __init__(self):
        # Define the fuzzy membership functions for different symptoms
        # In a full implementation, these would be more complex and based on medical expertise
        self.symptom_severity = SymptomSeverity.LEVELS
        
        # Probability weights for different priority levels (based on typical ED distributions)
        self.priority_weights = [0.05, 0.15, 0.3, 0.3, 0.2]  # Priorities 1-5
        
        # Define membership functions for severity levels
        self.membership = {
            'very_low': lambda x: self.trapezoid(x, 0, 0, 0.1, 0.3),
            'low': lambda x: self.triangle(x, 0.2, 0.4, 0.6),
            'medium': lambda x: self.triangle(x, 0.4, 0.6, 0.8),
            'high': lambda x: self.triangle(x, 0.6, 0.8, 1.0),
            'very_high': lambda x: self.trapezoid(x, 0.7, 0.9, 1, 1)
        }
        
        # Define simple rules mapping severity to priority
        self.rules = [
            {'conditions': ['very_high'], 'output': 1},
            {'conditions': ['high'], 'output': 2},
            {'conditions': ['medium'], 'output': 3},
            {'conditions': ['low'], 'output': 4},
            {'conditions': ['very_low'], 'output': 5}
        ]
        
    def _fuzzy_categorize(self, severity):
        """
        Categorize the severity using fuzzy logic.
        """
        clinical_params = {'severity': severity}
        
        # Fuzzify inputs
        membership_values = {
            'severity': [func(severity) for func in self.membership.values()]
        }
        
        # Rule activation
        activated_rules = []
        for rule in self.rules:
            min_strength = membership_values['severity'][list(self.membership.keys()).index(rule['conditions'][0])]
            if min_strength > 0:
                activated_rules.append({'strength': min_strength, 'output': rule['output']})
        
        # Defuzzification (centroid method)
        if not activated_rules:
            return 5
        numerator = sum(r['strength'] * r['output'] for r in activated_rules)
        denominator = sum(r['strength'] for r in activated_rules)
        return round(numerator / denominator)

    @staticmethod
    def trapezoid(x, a, b, c, d):
        if x < a or x > d:
            return 0.0
        if b <= x <= c:
            return 1.0
        if x < b:
            if b > a:
                return (x - a) / (b - a)
            else:
                return 1.0 if x == a else 0.0
        else:
            if d > c:
                return (d - x) / (d - c)
            else:
                return 1.0 if x == d else 0.0

    @staticmethod
    def triangle(x, a, b, c):
        return max(min((x - a)/(b - a), (c - x)/(c - b)), 0)
            
    def assign_priority(self, patient):
        """
        Assign a priority level to a patient based on their condition using
        a fuzzy implementation of the Manchester Triage System.
        
        In a real implementation, this would use the ~50 flowcharts from the MTS
        to evaluate specific symptoms. This is a simplified version that simulates
        the process using random severity values with weighted distributions.
        
        Args:
            patient: The patient object containing relevant medical information
            
        Returns:
            int: Priority level (1-5)
        """
        # In a real implementation, we would select the appropriate flowchart based on
        # the patient's presenting symptoms and follow the decision tree
        
        # Simulate symptom severity with a distribution that reflects real-world triage outcomes
        # This creates a beta distribution that's weighted toward lower severity (more common)
        severity = np.random.beta(2, 5)  
        
        # Add some random variation to simulate the fuzzy nature of symptom assessment
        severity += np.random.normal(0, 0.1)
        severity = max(0, min(1, severity))  # Clamp to [0,1]
        
        try:
            # Apply fuzzy categorization
            priority = self._fuzzy_categorize(severity)
            logger.info(
                LogMessages.TRIAGE_DECISION.format(
                    patient.id,
                    priority
                )
            )
        except Exception as e:
            logger.error(LogMessages.TRIAGE_ERROR.format(patient.id, str(e)))
            priority = 3  # Default to Urgent (Yellow) if categorization fails
        
        # In some cases, override with direct priority assignment to match expected distribution
        if random.random() < 0.2:  # 20% of the time, use direct assignment
            priority = random.choices([1, 2, 3, 4, 5], weights=self.priority_weights)[0]
            
        return priority
    
    def estimate_triage_time(self):
        """
        Estimate the time required to triage a patient using the Manchester system.
        
        The Manchester Triage System typically takes longer than simple triage
        systems because it involves following detailed flowcharts.
        
        Returns:
            float: Estimated time in minutes for the triage process
        """
        # Base triage time from parameters
        base_time = p.mean_nurse_triage
        
        # MTS is more structured and may take slightly longer than simple triage
        # Add a small increase to represent the structured nature of MTS
        mts_factor = 1.2
        
        # Add some random variation with a lognormal distribution
        return random.lognormvariate(
            np.log(base_time * mts_factor), 
            p.stdev_nurse_triage / (base_time * mts_factor)
        )
    
    def estimate_consult_time(self, priority):
        """
        Estimate the time required for doctor consultation based on patient priority.
        
        In the Manchester system, higher priority (lower numbers) typically requires
        more immediate and intensive care.
        
        Args:
            priority: The priority level assigned to the patient (1-5)
            
        Returns:
            float: Estimated time in minutes for the consultation process
        """
        # Base consultation time from parameters
        base_time = p.mean_doc_consult
        
        # Adjust time based on priority - higher priority (lower number) typically
        # requires more intensive care
        # Priority 1 (immediate) might need 1.5x the time of a standard case
        # Priority 5 (non-urgent) might need only 0.7x the time
        priority_factor = 1.5 - (priority - 1) * 0.2  # Maps priority 1->1.5, 5->0.7
        
        # Calculate adjusted mean time
        adjusted_mean = base_time * priority_factor
        
        # Add some random variation with a lognormal distribution
        return random.lognormvariate(
            np.log(adjusted_mean), 
            p.stdev_doc_consult / adjusted_mean
        )

    def get_triage_system_name(self):
        """
        Get the name of the triage system.
        
        Returns:
            string: Name of the triage system
        """
        return "Manchester Triage System"