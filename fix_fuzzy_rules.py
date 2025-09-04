#!/usr/bin/env python3
"""
Fix for Manchester Triage System fuzzy rules to ensure robust output generation
"""

import sys
sys.path.append('/Users/raunakburrows/dissertation')

from skfuzzy import control as ctrl
from typing import List

def create_robust_fuzzy_rules(symptoms: List[ctrl.Antecedent], triage_category: ctrl.Consequent) -> List[ctrl.Rule]:
    """Create robust fuzzy rules that ensure output for all input combinations"""
    rules = []
    
    # RED rules - Any very_severe symptom or multiple severe symptoms
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
    
    # ORANGE rules - Two severe symptoms
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
    
    # YELLOW rules - One severe symptom or multiple moderate symptoms
    one_severe = (
        symptoms[0]['severe'] |
        symptoms[1]['severe'] |
        symptoms[2]['severe'] |
        symptoms[3]['severe'] |
        symptoms[4]['severe']
    )
    rules.append(ctrl.Rule(one_severe, triage_category['yellow']))
    
    # Rule for multiple moderate symptoms -> YELLOW
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
    
    # GREEN rules - Moderate symptoms (1-2)
    moderate_symptoms = (
        symptoms[0]['moderate'] |
        symptoms[1]['moderate'] |
        symptoms[2]['moderate'] |
        symptoms[3]['moderate'] |
        symptoms[4]['moderate']
    )
    rules.append(ctrl.Rule(moderate_symptoms, triage_category['green']))
    
    # BLUE rules - Mild symptoms or no significant symptoms
    mild_symptoms = (
        symptoms[0]['mild'] |
        symptoms[1]['mild'] |
        symptoms[2]['mild'] |
        symptoms[3]['mild'] |
        symptoms[4]['mild']
    )
    rules.append(ctrl.Rule(mild_symptoms, triage_category['blue']))
    
    # Default rule - If no other rules trigger, assign BLUE
    no_symptoms = (
        symptoms[0]['none'] &
        symptoms[1]['none'] &
        symptoms[2]['none'] &
        symptoms[3]['none'] &
        symptoms[4]['none']
    )
    rules.append(ctrl.Rule(no_symptoms, triage_category['blue']))
    
    return rules

def test_robust_rules():
    """Test the robust rule set"""
    print("=== Testing Robust Fuzzy Rules ===")
    
    from src.triage.manchester_triage_system.config.fuzzy_config import FuzzySystemConfigManager
    
    # Create fuzzy system components
    fuzzy_manager = FuzzySystemConfigManager()
    input_vars = fuzzy_manager.create_input_variables()
    output_var = fuzzy_manager.create_output_variable()
    
    # Create robust rules
    rules = create_robust_fuzzy_rules(input_vars, output_var)
    print(f"Created {len(rules)} robust rules")
    
    # Create control system
    control_system = ctrl.ControlSystem(rules)
    simulation = ctrl.ControlSystemSimulation(control_system)
    
    # Test various input combinations
    test_cases = [
        ([2.0, 5.0, 5.0, 2.0, 5.0], "Original failing case"),
        ([0.0, 0.0, 0.0, 0.0, 0.0], "No symptoms"),
        ([2.0, 2.0, 2.0, 0.0, 0.0], "Mild symptoms"),
        ([5.0, 5.0, 0.0, 0.0, 0.0], "Moderate symptoms"),
        ([8.0, 0.0, 0.0, 0.0, 0.0], "One severe symptom"),
        ([8.0, 8.0, 0.0, 0.0, 0.0], "Two severe symptoms"),
        ([10.0, 0.0, 0.0, 0.0, 0.0], "Very severe symptom")
    ]
    
    input_names = ['symptom1', 'symptom2', 'symptom3', 'symptom4', 'symptom5']
    
    for test_values, description in test_cases:
        print(f"\nTesting: {description}")
        print(f"Input: {test_values}")
        
        # Set inputs
        for i, value in enumerate(test_values):
            simulation.input[input_names[i]] = value
        
        try:
            simulation.compute()
            if 'triage_category' in simulation.output:
                result = simulation.output['triage_category']
                print(f"Output: {result:.3f}")
                
                # Map to category
                if result <= 1.5:
                    category = "RED"
                elif result <= 2.5:
                    category = "ORANGE"
                elif result <= 3.5:
                    category = "YELLOW"
                elif result <= 4.5:
                    category = "GREEN"
                else:
                    category = "BLUE"
                print(f"Category: {category}")
            else:
                print("ERROR: No output generated")
        except Exception as e:
            print(f"ERROR: {e}")
    
    print("\n✅ Robust rules testing completed!")

if __name__ == "__main__":
    test_robust_rules()