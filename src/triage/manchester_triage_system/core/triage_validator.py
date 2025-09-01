"""Triage Validator

This module validates triage inputs and results following SOLID principles.

Reference: FMTS paper Section II - "The evaluation is typically performed by a 
triage nurse who collects patient information and relies on her memory of guidelines 
and subjective assessment to assign an urgency level to patients."

Paper Context: "this might result in two nurses coming to different conclusions 
about the urgency of a patient's condition even if the same flowcharts are being used."

This validator addresses the paper's concern by providing systematic validation 
that ensures consistent, objective assessment regardless of individual nurse 
interpretation.

Single Responsibility: Only handles validation
"""

from typing import Dict, Any


class TriageValidator:
    """Validates triage inputs and results
    
    Single Responsibility: Only handles validation
    """
    
    @staticmethod
    def validate_inputs(flowchart_reason: str, symptoms_input: Dict[str, str]) -> Dict[str, Any]:
        """Validate triage inputs"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate flowchart reason
        if not flowchart_reason or not isinstance(flowchart_reason, str):
            validation_result['valid'] = False
            validation_result['errors'].append("Invalid flowchart reason")
        
        # Validate symptoms input
        if not isinstance(symptoms_input, dict):
            validation_result['valid'] = False
            validation_result['errors'].append("Symptoms input must be a dictionary")
        elif len(symptoms_input) == 0:
            validation_result['warnings'].append("No symptoms provided")
        
        # Validate symptom values
        valid_linguistic_values = ['none', 'mild', 'moderate', 'severe', 'very_severe']
        for symptom, value in symptoms_input.items():
            if value.lower() not in valid_linguistic_values:
                validation_result['warnings'].append(f"Non-standard value '{value}' for symptom '{symptom}'")
        
        return validation_result
    
    @staticmethod
    def validate_result(result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate triage result"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required fields
        required_fields = ['flowchart_used', 'triage_category', 'wait_time', 'fuzzy_score']
        for field in required_fields:
            if field not in result:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Missing required field: {field}")
        
        # Validate triage category
        if 'triage_category' in result:
            valid_categories = ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE']
            if result['triage_category'] not in valid_categories:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Invalid triage category: {result['triage_category']}")
        
        # Validate fuzzy score
        if 'fuzzy_score' in result:
            score = result['fuzzy_score']
            if not isinstance(score, (int, float)) or score < 1 or score > 5:
                validation_result['warnings'].append(f"Fuzzy score {score} outside expected range [1-5]")
        
        return validation_result