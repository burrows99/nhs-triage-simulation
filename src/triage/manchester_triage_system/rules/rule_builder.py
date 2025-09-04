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
        
        # Any very severe symptom = RED (Paper: critical conditions)
        # Reference: Paper emphasizes need for objective system to handle critical cases
        # Validate input variables match expected configuration
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
        
        very_severe_condition = (
            symptoms[0]['very_severe'] |
            symptoms[1]['very_severe'] |
            symptoms[2]['very_severe'] |
            symptoms[3]['very_severe'] |
            symptoms[4]['very_severe']
        )
        rules.append(ctrl.Rule(very_severe_condition, triage_category['red']))
        
        # Multiple severe symptoms = RED (Paper: compound urgency)
        # Reference: Addresses paper's concern about distinguishing between urgent cases
        multiple_severe_conditions = [
            (symptoms[0]['severe'] & symptoms[1]['severe'] & symptoms[2]['severe']),
            (symptoms[0]['severe'] & symptoms[1]['severe'] & symptoms[3]['severe']),
            (symptoms[0]['severe'] & symptoms[1]['severe'] & symptoms[4]['severe'])
        ]
        
        for condition in multiple_severe_conditions:
            rules.append(ctrl.Rule(condition, triage_category['red']))
        
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
        # Reference: Paper's objective system for distinguishing urgency levels
        two_severe_combinations = [
            (symptoms[i]['severe'] & symptoms[j]['severe'])
            for i in range(5) for j in range(i+1, 5)
        ]
        
        orange_condition = two_severe_combinations[0]
        for condition in two_severe_combinations[1:]:
            orange_condition = orange_condition | condition
        
        rules.append(ctrl.Rule(orange_condition, triage_category['orange']))
        
        # One severe + multiple moderate = ORANGE
        # Reference: Implements paper's goal of objective triage categorization
        severe_moderate_conditions = [
            (symptoms[0]['severe'] & symptoms[1]['moderate'] & symptoms[2]['moderate']),
            (symptoms[1]['severe'] & symptoms[0]['moderate'] & symptoms[2]['moderate']),
            (symptoms[2]['severe'] & symptoms[0]['moderate'] & symptoms[1]['moderate'])
        ]
        
        for condition in severe_moderate_conditions:
            rules.append(ctrl.Rule(condition, triage_category['orange']))
        
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
        
        # Single severe symptom = YELLOW
        # Reference: Paper's systematic approach to handling single severe symptoms
        single_severe_conditions = []
        for i in range(5):
            # Create condition for symptom i being severe and others not severe
            other_symptoms_not_severe = [
                ~symptoms[j]['severe'] for j in range(5) if j != i
            ]
            
            condition = symptoms[i]['severe']
            for not_severe in other_symptoms_not_severe:
                condition = condition & not_severe
            
            single_severe_conditions.append(condition)
        
        # Combine all single severe conditions
        yellow_condition = single_severe_conditions[0]
        for condition in single_severe_conditions[1:]:
            yellow_condition = yellow_condition | condition
        
        rules.append(ctrl.Rule(yellow_condition, triage_category['yellow']))
        
        # Multiple moderate symptoms = YELLOW
        # Reference: Implements paper's objective categorization for moderate symptoms
        moderate_combinations = [
            (symptoms[0]['moderate'] & symptoms[1]['moderate'] & symptoms[2]['moderate']),
            (symptoms[0]['moderate'] & symptoms[1]['moderate'] & symptoms[3]['moderate']),
            (symptoms[0]['moderate'] & symptoms[1]['moderate'] & symptoms[4]['moderate'])
        ]
        
        for condition in moderate_combinations:
            rules.append(ctrl.Rule(condition, triage_category['yellow']))
        
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
        
        # Single or double moderate symptoms = GREEN
        # Reference: Paper's systematic approach to non-urgent cases
        green_conditions = []
        
        # Single moderate conditions
        for i in range(5):
            # Symptom i is moderate, but not multiple moderate symptoms together
            other_moderate_pairs = [
                ~(symptoms[j]['moderate'] & symptoms[k]['moderate'])
                for j in range(5) for k in range(j+1, 5)
                if j != i and k != i
            ]
            
            condition = symptoms[i]['moderate']
            for not_multiple in other_moderate_pairs:
                condition = condition & not_multiple
            
            green_conditions.append(condition)
        
        # Double moderate (but not triple)
        double_moderate_condition = (
            symptoms[0]['moderate'] & symptoms[1]['moderate'] &
            ~(symptoms[2]['moderate'] | symptoms[3]['moderate'] | symptoms[4]['moderate'])
        )
        green_conditions.append(double_moderate_condition)
        
        # Combine all green conditions
        final_green_condition = green_conditions[0]
        for condition in green_conditions[1:]:
            final_green_condition = final_green_condition | condition
        
        rules.append(ctrl.Rule(final_green_condition, triage_category['green']))
        
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
        
        # Only mild symptoms = BLUE
        # Reference: Paper's systematic approach to minor conditions
        mild_or_none_conditions = []
        for symptom in symptoms:
            mild_or_none_conditions.append(symptom['mild'] | symptom['none'])
        
        # No moderate or higher symptoms
        no_moderate_or_higher = []
        for symptom in symptoms:
            no_moderate_or_higher.append(
                ~(symptom['moderate'] | symptom['severe'] | symptom['very_severe'])
            )
        
        # Combine conditions
        blue_condition = mild_or_none_conditions[0]
        for condition in mild_or_none_conditions[1:]:
            blue_condition = blue_condition & condition
        
        for condition in no_moderate_or_higher:
            blue_condition = blue_condition & condition
        
        rules.append(ctrl.Rule(blue_condition, triage_category['blue']))
        
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