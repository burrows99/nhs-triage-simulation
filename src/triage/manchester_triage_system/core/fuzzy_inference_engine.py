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
        try:
            self._simulation.compute()
            # Get the defuzzified output value from the triage_category variable
            output_var_name = 'triage_category'
            if output_var_name in self._simulation.output:
                return self._simulation.output[output_var_name]
            else:
                # If the variable name doesn't exist, get the first (and should be only) output
                output_keys = list(self._simulation.output.keys())
                if output_keys:
                    return self._simulation.output[output_keys[0]]
                else:
                    raise KeyError("No output variables found in fuzzy system")
        except Exception as e:
            # No fallbacks - propagate error for proper handling
            raise RuntimeError(
                f"Fuzzy inference computation failed: {str(e)}. "
                f"Symptom values: {symptom_values}. "
                f"Available outputs: {list(self._simulation.output.keys()) if hasattr(self._simulation, 'output') else 'None'}. "
                "System cannot proceed without valid fuzzy score."
            ) from e