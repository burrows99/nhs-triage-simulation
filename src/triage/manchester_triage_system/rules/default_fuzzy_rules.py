"""Default Fuzzy Rules Implementation

This module provides the default fuzzy rules implementation based on the
Manchester Triage System logic as described in the FMTS paper.

Reference: FMTS paper by Cremeens & Khorasani (2014)
https://www.researchgate.net/publication/286737453_FMTS_A_fuzzy_implementation_of_the_Manchester_triage_system

Paper Quote: "Hence, an objective triage system is needed that can correctly model 
the meaning of imprecise terms in the MTS and assign an appropriate waiting time to patients."

This implementation provides the comprehensive fuzzy rule set that addresses the paper's
core objective of creating an objective triage system.
"""

from skfuzzy import control as ctrl
from typing import List
from .rule_builder import RuleBuilder


class DefaultFuzzyRules:
    """Default fuzzy rules implementation based on FMTS paper
    
    Reference: FMTS paper Section II describes comprehensive fuzzy rules needed
    to handle the imprecise linguistic terms found in MTS flowcharts.
    
    Paper Context: "MTS flowcharts are full of imprecise linguistic terms such as 
    very low PEFR, exhaustion, significant respiratory history, urgent, etc. this 
    might result in two nurses coming to different conclusions about the urgency of 
    a patient's condition even if the same flowcharts are being used."
    
    This class provides the objective rule set that eliminates subjective interpretation
    by implementing precise fuzzy logic rules for all triage categories.
    
    The rules implement the five-point triage scale mentioned in the paper:
    - RED (Immediate): Life-threatening conditions
    - ORANGE (Very Urgent): 10 minutes maximum wait
    - YELLOW (Urgent): 60 minutes maximum wait  
    - GREEN (Standard): 120 minutes maximum wait
    - BLUE (Non-urgent): 240 minutes maximum wait
    """
    
    def get_rules(self, input_vars: List[ctrl.Antecedent], output_var: ctrl.Consequent) -> List[ctrl.Rule]:
        """Get all fuzzy rules for the FMTS system
        
        Reference: FMTS paper emphasizes the need for a comprehensive rule set that can
        handle all the scenarios described in the ~50 MTS flowcharts.
        
        Paper Quote: "The system consists of around 50 flowcharts with standard definitions 
        designed to categorize patients arriving to an emergency room based on their level of urgency."
        
        This method combines all rule categories to create a complete fuzzy inference system
        that addresses the paper's goal of providing objective triage decisions.
        
        Args:
            input_vars: List of fuzzy input variables (5 symptoms as per paper)
            output_var: Fuzzy output variable (triage category 1-5 scale)
            
        Returns:
            Complete list of fuzzy rules implementing the FMTS logic
            
        Implementation Note: The rules are organized by triage category to match
        the paper's systematic approach to handling different urgency levels.
        """
        all_rules = []
        
        # Create rules for each triage category as described in the paper
        # Reference: Paper describes systematic categorization using five-point scale
        
        # RED rules - Immediate attention required
        # Paper context: "very urgent" situations requiring immediate attention
        all_rules.extend(RuleBuilder.create_red_rules(input_vars, output_var))
        
        # ORANGE rules - Very urgent (10 minutes)
        # Paper context: Conditions requiring rapid assessment
        all_rules.extend(RuleBuilder.create_orange_rules(input_vars, output_var))
        
        # YELLOW rules - Urgent (60 minutes)
        # Paper context: Standard urgent cases as per MTS flowcharts
        all_rules.extend(RuleBuilder.create_yellow_rules(input_vars, output_var))
        
        # GREEN rules - Standard (120 minutes)
        # Paper context: Non-urgent but requiring medical attention
        all_rules.extend(RuleBuilder.create_green_rules(input_vars, output_var))
        
        # BLUE rules - Non-urgent (240 minutes)
        # Paper context: Minor conditions that can wait
        all_rules.extend(RuleBuilder.create_blue_rules(input_vars, output_var))
        
        # Context-specific rules based on paper examples
        # Reference: Paper Figure 1 and specific flowchart examples
        all_rules.extend(RuleBuilder.create_context_specific_rules(input_vars, output_var))
        
        return all_rules
    
    def get_rule_description(self) -> str:
        """Get description of the rule set implementation
        
        Returns:
            Description of how the rules implement the FMTS paper logic
        """
        return (
            "Default FMTS fuzzy rules implementing the Manchester Triage System logic "
            "as described in Cremeens & Khorasani (2014). These rules address the "
            "paper's core problem of handling imprecise linguistic terms in medical "
            "triage by providing objective categorization across the five-point scale: "
            "RED (immediate), ORANGE (10 min), YELLOW (60 min), GREEN (120 min), "
            "and BLUE (240 min). The implementation follows the paper's systematic "
            "approach to eliminating subjective interpretation in emergency triage."
        )
    
    def get_paper_reference(self) -> dict:
        """Get the paper reference information
        
        Returns:
            Dictionary containing paper citation details
        """
        return {
            'title': 'FMTS: A fuzzy implementation of the Manchester triage system',
            'authors': ['Matthew Cremeens', 'Elham S. Khorasani'],
            'year': 2014,
            'institution': 'University of Illinois at Springfield',
            'url': 'https://www.researchgate.net/publication/286737453_FMTS_A_fuzzy_implementation_of_the_Manchester_triage_system',
            'key_contribution': 'Objective fuzzy triage system eliminating subjective interpretation',
            'implementation_focus': 'Five-point triage scale with precise waiting time assignments'
        }