"""Fuzzy Rule Builder

This module provides a builder for creating individual fuzzy rules based on the
Manchester Triage System logic as described in the FMTS paper.

Reference: FMTS paper by Cremeens & Khorasani (2014)
https://www.researchgate.net/publication/286737453_FMTS_A_fuzzy_implementation_of_the_Manchester_triage_system

Paper Quote: "The system consists of around 50 flowcharts with standard definitions 
designed to categorize patients arriving to an emergency room based on their level of urgency."

This builder implements the five-point triage scale (RED, ORANGE, YELLOW, GREEN, BLUE)
as specified in the paper.
"""

from skfuzzy import control as ctrl
from typing import List


class RuleBuilder:
    """Builder for creating individual fuzzy rules
    
    Single Responsibility: Only builds fuzzy rules based on MTS logic
    
    Reference: FMTS paper Section II describes the Manchester Triage System as
    "an algorithmic standard designed to aid the triage nurse in choosing an 
    appropriate triage category using a five-point scale."
    
    This class implements the fuzzy rule logic that addresses the paper's core problem:
    "What does it mean for PEFR to be very low? What about the output? What is the 
    difference between very urgent and urgent?"
    """
    
    @staticmethod
    def create_red_rules(symptoms: List[ctrl.Antecedent], triage_category: ctrl.Consequent) -> List[ctrl.Rule]:
        """Create RED (Immediate) triage rules
        
        Reference: FMTS paper describes RED category as "very urgent" situations 
        requiring immediate attention.
        
        Paper Context: The paper addresses scenarios where "two children are in triage 
        for shortness of breath and one has what would be considered very low oxygenation 
        (SaO2) and the other has acute onset after injury, which should be seen first?"
        
        These rules implement the logic for life-threatening conditions that require
        immediate medical attention.
        
        Args:
            symptoms: List of fuzzy input variables representing patient symptoms
            triage_category: Fuzzy output variable for triage categorization
            
        Returns:
            List of fuzzy rules for RED (immediate) triage category
        """
        rules = []
        
        # Validate inputs
        if len(symptoms) != 5:
            raise ValueError(
                f"Expected exactly 5 input variables for FMTS fuzzy system, got {len(symptoms)}. "
                f"This indicates a configuration mismatch between fuzzy system setup and rule creation."
            )
        
        # Validate that all symptoms have required membership functions
        required_memberships = ['very_severe', 'severe', 'moderate', 'mild', 'none']
        for i, symptom in enumerate(symptoms):
            for membership in required_memberships:
                if membership not in symptom:
                    raise ValueError(
                        f"Symptom {i} ({symptom.label}) missing required membership function '{membership}'. "
                        f"Available: {list(symptom.terms.keys())}"
                    )
        
        # Rule 1: Any very severe symptom -> RED
        very_severe_condition = (
            symptoms[0]['very_severe'] |
            symptoms[1]['very_severe'] |
            symptoms[2]['very_severe'] |
            symptoms[3]['very_severe'] |
            symptoms[4]['very_severe']
        )
        rules.append(ctrl.Rule(very_severe_condition, triage_category['red']))
        
        # Rule 2: Three or more severe symptoms -> RED
        three_severe = (
            (symptoms[0]['severe'] & symptoms[1]['severe'] & symptoms[2]['severe']) |
            (symptoms[0]['severe'] & symptoms[1]['severe'] & symptoms[3]['severe']) |
            (symptoms[0]['severe'] & symptoms[1]['severe'] & symptoms[4]['severe']) |
            (symptoms[0]['severe'] & symptoms[2]['severe'] & symptoms[3]['severe']) |
            (symptoms[0]['severe'] & symptoms[2]['severe'] & symptoms[4]['severe']) |
            (symptoms[0]['severe'] & symptoms[3]['severe'] & symptoms[4]['severe']) |
            (symptoms[1]['severe'] & symptoms[2]['severe'] & symptoms[3]['severe']) |
            (symptoms[1]['severe'] & symptoms[2]['severe'] & symptoms[4]['severe']) |
            (symptoms[1]['severe'] & symptoms[3]['severe'] & symptoms[4]['severe']) |
            (symptoms[2]['severe'] & symptoms[3]['severe'] & symptoms[4]['severe'])
        )
        rules.append(ctrl.Rule(three_severe, triage_category['red']))
        
        return rules
    
    @staticmethod
    def create_orange_rules(symptoms: List[ctrl.Antecedent], triage_category: ctrl.Consequent) -> List[ctrl.Rule]:
        """Create ORANGE (Very Urgent) triage rules
        
        Reference: FMTS paper describes the need for rapid assessment of urgent cases.
        
        Paper Context: The paper states "What does the categorization of a patient mean 
        for her waiting time to be treated?" This rule set addresses patients who need
        treatment within 10 minutes.
        
        Args:
            symptoms: List of fuzzy input variables representing patient symptoms
            triage_category: Fuzzy output variable for triage categorization
            
        Returns:
            List of fuzzy rules for ORANGE (very urgent) triage category
        """
        rules = []
        
        # Two severe symptoms = ORANGE
        two_severe = (
            (symptoms[0]['severe'] & symptoms[1]['severe']) |
            (symptoms[0]['severe'] & symptoms[2]['severe']) |
            (symptoms[0]['severe'] & symptoms[3]['severe']) |
            (symptoms[0]['severe'] & symptoms[4]['severe']) |
            (symptoms[1]['severe'] & symptoms[2]['severe']) |
            (symptoms[1]['severe'] & symptoms[3]['severe']) |
            (symptoms[1]['severe'] & symptoms[4]['severe']) |
            (symptoms[2]['severe'] & symptoms[3]['severe']) |
            (symptoms[2]['severe'] & symptoms[4]['severe']) |
            (symptoms[3]['severe'] & symptoms[4]['severe'])
        )
        rules.append(ctrl.Rule(two_severe, triage_category['orange']))
        
        return rules
    
    @staticmethod
    def create_yellow_rules(symptoms: List[ctrl.Antecedent], triage_category: ctrl.Consequent) -> List[ctrl.Rule]:
        """Create YELLOW (Urgent) triage rules
        
        Reference: FMTS paper describes YELLOW as standard urgent cases as per MTS flowcharts.
        
        Paper Context: Addresses the paper's concern about subjective assessment by providing
        objective rules for urgent cases that can wait up to 60 minutes for treatment.
        
        Args:
            symptoms: List of fuzzy input variables representing patient symptoms
            triage_category: Fuzzy output variable for triage categorization
            
        Returns:
            List of fuzzy rules for YELLOW (urgent) triage category
        """
        rules = []
        
        # One severe symptom = YELLOW
        one_severe = (
            symptoms[0]['severe'] |
            symptoms[1]['severe'] |
            symptoms[2]['severe'] |
            symptoms[3]['severe'] |
            symptoms[4]['severe']
        )
        rules.append(ctrl.Rule(one_severe, triage_category['yellow']))
        
        # Multiple moderate symptoms = YELLOW
        three_moderate = (
            (symptoms[0]['moderate'] & symptoms[1]['moderate'] & symptoms[2]['moderate']) |
            (symptoms[0]['moderate'] & symptoms[1]['moderate'] & symptoms[3]['moderate']) |
            (symptoms[0]['moderate'] & symptoms[1]['moderate'] & symptoms[4]['moderate']) |
            (symptoms[0]['moderate'] & symptoms[2]['moderate'] & symptoms[3]['moderate']) |
            (symptoms[0]['moderate'] & symptoms[2]['moderate'] & symptoms[4]['moderate']) |
            (symptoms[0]['moderate'] & symptoms[3]['moderate'] & symptoms[4]['moderate']) |
            (symptoms[1]['moderate'] & symptoms[2]['moderate'] & symptoms[3]['moderate']) |
            (symptoms[1]['moderate'] & symptoms[2]['moderate'] & symptoms[4]['moderate']) |
            (symptoms[1]['moderate'] & symptoms[3]['moderate'] & symptoms[4]['moderate']) |
            (symptoms[2]['moderate'] & symptoms[3]['moderate'] & symptoms[4]['moderate'])
        )
        rules.append(ctrl.Rule(three_moderate, triage_category['yellow']))
        
        return rules
    
    @staticmethod
    def create_green_rules(symptoms: List[ctrl.Antecedent], triage_category: ctrl.Consequent) -> List[ctrl.Rule]:
        """Create GREEN (Standard) triage rules
        
        Reference: FMTS paper describes GREEN as non-urgent but requiring medical attention.
        
        Paper Context: Addresses cases that are "non-urgent but requiring medical attention"
        with waiting times up to 120 minutes, as mentioned in the paper's discussion of
        waiting time categorization.
        
        Args:
            symptoms: List of fuzzy input variables representing patient symptoms
            triage_category: Fuzzy output variable for triage categorization
            
        Returns:
            List of fuzzy rules for GREEN (standard) triage category
        """
        rules = []
        
        # Moderate symptoms = GREEN
        moderate_symptoms = (
            symptoms[0]['moderate'] |
            symptoms[1]['moderate'] |
            symptoms[2]['moderate'] |
            symptoms[3]['moderate'] |
            symptoms[4]['moderate']
        )
        rules.append(ctrl.Rule(moderate_symptoms, triage_category['green']))
        
        return rules
    
    @staticmethod
    def create_blue_rules(symptoms: List[ctrl.Antecedent], triage_category: ctrl.Consequent) -> List[ctrl.Rule]:
        """Create BLUE (Non-urgent) triage rules
        
        Reference: FMTS paper describes BLUE as minor conditions that can wait.
        
        Paper Context: Implements the lowest priority category for patients who can
        wait up to 240 minutes, addressing the paper's goal of providing objective
        waiting time assignments.
        
        Args:
            symptoms: List of fuzzy input variables representing patient symptoms
            triage_category: Fuzzy output variable for triage categorization
            
        Returns:
            List of fuzzy rules for BLUE (non-urgent) triage category
        """
        rules = []
        
        # Mild symptoms = BLUE
        mild_symptoms = (
            symptoms[0]['mild'] |
            symptoms[1]['mild'] |
            symptoms[2]['mild'] |
            symptoms[3]['mild'] |
            symptoms[4]['mild']
        )
        rules.append(ctrl.Rule(mild_symptoms, triage_category['blue']))
        
        # No symptoms = BLUE (default case)
        no_symptoms = (
            symptoms[0]['none'] &
            symptoms[1]['none'] &
            symptoms[2]['none'] &
            symptoms[3]['none'] &
            symptoms[4]['none']
        )
        rules.append(ctrl.Rule(no_symptoms, triage_category['blue']))
        
        return rules
    
    @staticmethod
    def create_context_specific_rules(symptoms: List[ctrl.Antecedent], triage_category: ctrl.Consequent) -> List[ctrl.Rule]:
        """Create context-specific rules based on FMTS paper examples
        
        Reference: FMTS paper Figure 1 shows an example MTS flowchart for evaluation 
        of shortness of breath in children.
        
        Paper Context: "Figure 1 shows an example of one such flowchart designed to 
        evaluate the treatment urgency for the shortness of breath in children."
        
        These rules implement specific scenarios mentioned in the paper, such as
        "very low PEFR" and "exhaustion" combinations.
        
        Args:
            symptoms: List of fuzzy input variables representing patient symptoms
            triage_category: Fuzzy output variable for triage categorization
            
        Returns:
            List of context-specific fuzzy rules based on paper examples
        """
        rules = []
        
        # Emergency respiratory conditions (very low PEFR + exhaustion)
        # Reference: Paper Figure 1 example of shortness of breath flowchart
        respiratory_emergency = symptoms[0]['very_severe'] & symptoms[1]['severe']
        rules.append(ctrl.Rule(respiratory_emergency, triage_category['red']))
        
        # Significant respiratory history with acute symptoms
        # Reference: Paper mentions "significant respiratory history" as example of imprecise term
        respiratory_urgent = symptoms[2]['severe'] & symptoms[3]['moderate']
        rules.append(ctrl.Rule(respiratory_urgent, triage_category['orange']))
        
        return rules