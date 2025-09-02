"""Fuzzy Inference Engine

This module handles fuzzy inference operations following SOLID principles.

Reference: FMTS paper Section II - "The paper develops a Fuzzy Manchester Triage 
System (FMTS). FMTS is a dynamic fuzzy inference system which implements the 
flowcharts designed by the Manchester Triage Group."

Paper Context: "Hence, an objective triage system is needed that can correctly 
model the meaning of imprecise terms in the MTS and assign an appropriate waiting 
time to patients."

This engine implements the paper's core fuzzy inference system that provides 
objective triage decisions by processing imprecise linguistic inputs.

Single Responsibility: Only handles fuzzy inference
"""

from typing import List
from skfuzzy import control as ctrl


class FuzzyInferenceEngine:
    """Handles fuzzy inference operations
    
    Single Responsibility: Only handles fuzzy inference
    """
    
    def __init__(self, control_system: ctrl.ControlSystem):
        self._control_system = control_system
        self._simulation = ctrl.ControlSystemSimulation(control_system)
    

    
    def perform_inference(self, symptom_values: List[float]) -> float:
        """Perform complete fuzzy inference process"""
        # Set input values for fuzzy inference
        input_names = ['symptom1', 'symptom2', 'symptom3', 'symptom4', 'symptom5']
        
        for i, value in enumerate(symptom_values[:5]):
            if i < len(input_names):
                self._simulation.input[input_names[i]] = value
        
        # Compute fuzzy inference result
        self._simulation.compute()
        return self._simulation.output['triage_category']