import random
import numpy as np
from src.triage_systems.base_triage import BaseTriage
from src.config.constants import SymptomSeverity, LogMessages
from src.config.config_manager import get_manchester_triage_config, get_service_time_config, get_triage_actions_config
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
        # Get configuration from centralized config manager
        self.config = get_manchester_triage_config()
        self.actions_config = get_triage_actions_config()
        
        # Define the fuzzy membership functions for different symptoms
        self.symptom_severity = SymptomSeverity.LEVELS
        
        # Use configured priority weights
        self.priority_weights = self.config['priority_weights']
        
        # Build membership functions from configuration
        self.membership = self._build_membership_functions()
        
        # Use configured fuzzy rules
        self.rules = self.config['fuzzy_rules']
    
    def _build_membership_functions(self):
        """Build membership functions from configuration"""
        membership_funcs = {}
        for name, func_config in self.config['membership_functions'].items():
            if func_config['type'] == 'triangle':
                a, b, c = func_config['params']
                membership_funcs[name] = lambda x, a=a, b=b, c=c: self.triangle(x, a, b, c)
            elif func_config['type'] == 'trapezoid':
                a, b, c, d = func_config['params']
                membership_funcs[name] = lambda x, a=a, b=b, c=c, d=d: self.trapezoid(x, a, b, c, d)
        return membership_funcs
        
    def _fuzzy_categorize(self, severity):
        """
        Categorize the severity using fuzzy logic.
        """
        logger.debug(f"Fuzzy categorization for severity: {severity}")
        
        clinical_params = {'severity': severity}
        
        # Fuzzify inputs
        membership_values = {
            'severity': [func(severity) for func in self.membership.values()]
        }
        
        logger.debug(f"Membership values: {dict(zip(self.membership.keys(), membership_values['severity']))}")
        
        # Rule activation
        activated_rules = []
        for rule in self.rules:
            min_strength = membership_values['severity'][list(self.membership.keys()).index(rule['conditions'][0])]
            if min_strength > 0:
                activated_rules.append({'strength': min_strength, 'output': rule['output']})
                logger.debug(f"Activated rule: {rule['conditions'][0]} -> priority {rule['output']} (strength: {min_strength:.3f})")
        
        # Defuzzification (centroid method)
        if not activated_rules:
            logger.debug("No rules activated, defaulting to priority 5")
            return 5
        numerator = sum(r['strength'] * r['output'] for r in activated_rules)
        denominator = sum(r['strength'] for r in activated_rules)
        final_priority = round(numerator / denominator)
        
        logger.debug(f"Defuzzification: numerator={numerator:.3f}, denominator={denominator:.3f}, final_priority={final_priority}")
        return final_priority

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
            

    def perform_triage(self, patient_data):
        """
        Perform MTS assessment and return structured triage results
        {"priority": int, "rationale": str, "recommended_actions": list}
        """
        logger.debug(f"Manchester Triage System received patient data: {patient_data}")
        
        if 'severity' not in patient_data:
            logger.error(f"Missing 'severity' key in patient data: {patient_data}")
            raise KeyError(f"Patient data missing required 'severity' key. Available keys: {list(patient_data.keys())}")
        
        severity = patient_data['severity']
        logger.debug(f"Processing severity value: {severity}")
        
        priority = self._fuzzy_categorize(severity)
        
        # Get configured actions for this priority
        recommended_actions = self.actions_config.get(priority, ["Standard monitoring"])
        
        result = {
            "priority": priority,
            "rationale": f"Manchester Triage System priority {priority} based on severity {severity:.3f}",
            "recommended_actions": recommended_actions
        }
        
        logger.debug(f"Manchester Triage System result: {result}")
        return result

    def assign_priority(self, patient):
        logger.debug(f"assign_priority called for Patient {patient.id}")
        logger.debug(f"Patient attributes: {patient.__dict__}")
        
        try:
            triage_result = self.perform_triage(patient.__dict__)
            priority = triage_result['priority']
            logger.info(f"Patient {patient.id} assigned priority {priority} (severity: {patient.severity:.3f})")
            return priority
        except Exception as e:
            logger.error(f"Error in assign_priority for Patient {patient.id}: {str(e)}")
            logger.exception("Full traceback:")
            raise

    def estimate_triage_time(self):
        """
        Estimate the time required to triage a patient using the Manchester system.
        
        The Manchester Triage System typically takes longer than simple triage
        systems because it involves following detailed flowcharts.
        
        Returns:
            float: Estimated time in minutes for the triage process
        """
        # Get service time configuration
        service_config = get_service_time_config()
        base_time = service_config['triage']['mean']
        
        # Use configured MTS time factor
        mts_factor = self.config['time_factor']
        
        # Add some random variation with a lognormal distribution
        stdev = service_config['triage']['stdev']
        return random.lognormvariate(
            np.log(base_time * mts_factor), 
            stdev / (base_time * mts_factor)
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
        # Get service time configuration
        service_config = get_service_time_config()
        base_time = service_config['consultation']['mean']
        
        # Use configured priority consultation factors
        priority_factor = self.config['priority_consultation_factors'].get(priority, 1.0)
        
        # Calculate adjusted mean time
        adjusted_mean = base_time * priority_factor
        
        # Add some random variation with a lognormal distribution
        stdev = service_config['consultation']['stdev']
        return random.lognormvariate(
            np.log(adjusted_mean), 
            stdev / adjusted_mean
        )

    def get_triage_system_name(self):
        """
        Get the name of the triage system.
        
        Returns:
            string: Name of the triage system
        """
        return "Manchester Triage System"