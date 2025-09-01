"""Symptom Processor

This module processes symptom inputs and converts them to numeric values
following SOLID principles.

Reference: FMTS paper Section II - "MTS flowcharts are full of imprecise linguistic 
terms such as very low PEFR, exhaustion, significant respiratory history, urgent, etc. 
this might result in two nurses coming to different conclusions about the urgency of 
a patient's condition even if the same flowcharts are being used."

Paper Context: "What does it mean for PEFR to be very low? What about the output? 
What is the difference between very urgent and urgent?"

This processor addresses the paper's concern by providing systematic conversion 
of imprecise linguistic terms to precise numeric values for fuzzy processing.

Single Responsibility: Only handles symptom processing
"""

from typing import Dict, List, Any
from ..config import LinguisticValueConverter


class SymptomProcessor:
    """Processes symptom inputs and converts them to numeric values
    
    Single Responsibility: Only handles symptom processing
    """
    
    def __init__(self, linguistic_converter: LinguisticValueConverter):
        self._linguistic_converter = linguistic_converter
    
    def extract_symptoms(self, flowchart_config: Dict[str, Any], max_symptoms: int = 5) -> List[str]:
        """Extract symptoms from flowchart configuration"""
        symptoms = flowchart_config.get('symptoms', [])
        return symptoms[:max_symptoms]  # Take first N symptoms
    
    def convert_symptom_inputs(self, symptoms: List[str], symptoms_input: Dict[str, str]) -> List[float]:
        """Convert symptom inputs from linguistic to numeric values"""
        numeric_values = []
        
        for symptom in symptoms:
            linguistic_val = symptoms_input.get(symptom, 'none')
            numeric_val = self._linguistic_converter.convert_to_numeric(linguistic_val)
            numeric_values.append(numeric_val)
        
        return numeric_values
    
    def pad_symptom_values(self, numeric_values: List[float], target_length: int = 5) -> List[float]:
        """Pad symptom values with zeros to reach target length"""
        padded_values = numeric_values.copy()
        while len(padded_values) < target_length:
            padded_values.append(0.0)
        return padded_values
    
    def process_symptoms(self, flowchart_config: Dict[str, Any], symptoms_input: Dict[str, str]) -> Dict[str, Any]:
        """Process all symptom-related operations"""
        symptoms = self.extract_symptoms(flowchart_config)
        numeric_values = self.convert_symptom_inputs(symptoms, symptoms_input)
        padded_values = self.pad_symptom_values(numeric_values)
        
        return {
            'symptoms': symptoms,
            'numeric_values': numeric_values,
            'padded_values': padded_values,
            'processed_symptoms': dict(zip(symptoms, [symptoms_input.get(s, 'none') for s in symptoms]))
        }