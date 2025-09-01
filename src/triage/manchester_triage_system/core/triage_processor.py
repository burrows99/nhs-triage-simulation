"""Triage Processing Core

This module coordinates the main triage processing workflow following SOLID principles.

Reference: FMTS paper Section II - "FMTS provides two user interfaces: one is a 
decision aid system for the ER nurses to properly categorize patients based on 
their symptoms, and the other one is a knowledge acquisition component used by 
the medical experts to configure the meaning of linguistic terms and maintain 
the fuzzy rules."

Paper Context: "For a triage nurse with 50 flowcharts in her hand, trying to 
correctly prioritize a patient is a clumsy process."

This processor implements the paper's decision aid system by coordinating all 
triage operations to provide nurses with systematic, objective patient categorization.

Single Responsibility: Coordinates triage processing workflow
Open/Closed: Can be extended with new processing strategies
Dependency Inversion: Depends on injected services
"""

from typing import Dict, List, Any
from skfuzzy import control as ctrl

from ..config import (
    FlowchartConfigManager,
    FuzzySystemConfigManager
)
from ..rules import FuzzyRulesManager

# Import individual service classes
from .flowchart_lookup_service import FlowchartLookupService
from .symptom_processor import SymptomProcessor
from .fuzzy_inference_engine import FuzzyInferenceEngine
from .triage_result_builder import TriageResultBuilder
from .triage_validator import TriageValidator


class TriageProcessor:
    """Main triage processor coordinating all operations
    
    Single Responsibility: Coordinates triage processing workflow
    Open/Closed: Can be extended with new processing strategies
    Dependency Inversion: Depends on injected services
    """
    
    def __init__(self,
                 flowchart_manager: FlowchartConfigManager,
                 fuzzy_manager: FuzzySystemConfigManager,
                 rules_manager: FuzzyRulesManager):
        
        # Initialize services
        self._flowchart_lookup = FlowchartLookupService(flowchart_manager)
        self._symptom_processor = SymptomProcessor(fuzzy_manager.get_linguistic_converter())
        self._result_builder = TriageResultBuilder(fuzzy_manager.get_category_mapper())
        
        # Initialize fuzzy system
        self._setup_fuzzy_system(fuzzy_manager, rules_manager)
    
    def _setup_fuzzy_system(self, fuzzy_manager: FuzzySystemConfigManager, rules_manager: FuzzyRulesManager):
        """Setup fuzzy inference system"""
        # Create fuzzy variables
        input_vars = fuzzy_manager.create_input_variables()
        output_var = fuzzy_manager.create_output_variable()
        
        # Create fuzzy rules
        rules = rules_manager.create_rules(input_vars, output_var)
        
        # Create control system
        control_system = ctrl.ControlSystem(rules)
        self._inference_engine = FuzzyInferenceEngine(control_system)
    
    def process_triage(self, flowchart_reason: str, symptoms_input: Dict[str, str]) -> Dict[str, Any]:
        """Process complete triage workflow
        
        Args:
            flowchart_reason: Flowchart identifier (e.g., 'chest_pain')
            symptoms_input: Dictionary of symptom assessments
            
        Returns:
            Complete triage result with category, wait time, etc.
        """
        
        # Validate inputs
        validation = TriageValidator.validate_inputs(flowchart_reason, symptoms_input)
        if not validation['valid']:
            raise ValueError(f"Invalid inputs: {validation['errors']}")
        
        # Lookup flowchart
        flowchart_config = self._flowchart_lookup.find_flowchart(flowchart_reason)
        if flowchart_config is None:
            flowchart_config = self._flowchart_lookup.get_default_flowchart()
        
        # Process symptoms
        symptom_data = self._symptom_processor.process_symptoms(flowchart_config, symptoms_input)
        
        # Perform fuzzy inference
        fuzzy_score = self._inference_engine.perform_inference(symptom_data['padded_values'])
        
        # Build result
        result = self._result_builder.build_result(flowchart_reason, fuzzy_score, symptom_data)
        
        # Validate result
        result_validation = TriageValidator.validate_result(result)
        if not result_validation['valid']:
            raise RuntimeError(f"Invalid result generated: {result_validation['errors']}")
        
        return result
    
    def get_available_flowcharts(self) -> List[str]:
        """Get list of available flowcharts"""
        return self._flowchart_lookup._flowchart_manager.get_available_flowcharts()
    
    def get_symptoms_for_flowchart(self, flowchart_reason: str) -> List[str]:
        """Get symptoms for a specific flowchart"""
        return self._flowchart_lookup.get_flowchart_symptoms(flowchart_reason)