"""Fuzzy Rule Source Protocol

This module defines the protocol for fuzzy rule sources, enabling dependency inversion
for different rule sources in the FMTS system.

Reference: FMTS paper by Cremeens & Khorasani (2014)
https://www.researchgate.net/publication/286737453_FMTS_A_fuzzy_implementation_of_the_Manchester_triage_system

Paper Quote: "FMTS is a dynamic fuzzy inference system which implements the flowcharts 
designed by the Manchester Triage Group."

This protocol supports the paper's emphasis on dynamic fuzzy systems by allowing
different rule sources to be plugged into the system.
"""

from skfuzzy import control as ctrl
from typing import List, Protocol


class FuzzyRuleSource(Protocol):
    """Protocol for fuzzy rule sources
    
    Enables dependency inversion for different rule sources in the FMTS system.
    
    Reference: FMTS paper Section II describes the need for a flexible fuzzy system
    that can handle the imprecise linguistic terms found in MTS flowcharts.
    
    Paper Context: "MTS flowcharts are full of imprecise linguistic terms such as 
    very low PEFR, exhaustion, significant respiratory history, urgent, etc."
    
    This protocol allows different implementations of rule generation to be used,
    supporting the paper's goal of creating an objective triage system.
    """
    
    def get_rules(self, input_vars: List[ctrl.Antecedent], output_var: ctrl.Consequent) -> List[ctrl.Rule]:
        """Get fuzzy rules for the system
        
        Args:
            input_vars: List of fuzzy input variables (symptoms)
            output_var: Fuzzy output variable (triage category)
            
        Returns:
            List of fuzzy rules for the triage system
            
        Reference: FMTS paper describes the need for fuzzy rules that can handle
        the imprecise nature of medical triage decisions, providing objective
        categorization where human judgment might be subjective.
        """
        ...