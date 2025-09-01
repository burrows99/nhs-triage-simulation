"""Triage Processing Core

This module handles the core triage processing logic with smaller,
single-responsibility functions following SOLID principles.

Follows SOLID principles:
- Single Responsibility: Each function has one clear purpose
- Open/Closed: Extensible for new processing strategies
- Dependency Inversion: Uses abstractions for dependencies
"""

from typing import Dict, List, Any, Optional
from skfuzzy import control as ctrl
import numpy as np

from ..config import (
    FlowchartConfigManager,
    FuzzySystemConfigManager,
    LinguisticValueConverter,
    TriageCategoryMapper
)
from ..rules import FuzzyRulesManager


class FlowchartLookupService:
    """Service for flowchart lookup operations
    
    Single Responsibility: Only handles flowchart lookup logic
    """
    
    def __init__(self, flowchart_manager: FlowchartConfigManager):
        self._flowchart_manager = flowchart_manager
    
    def find_flowchart(self, flowchart_reason: str) -> Optional[Dict[str, Any]]:
        """Find flowchart configuration by reason"""
        return self._flowchart_manager.get_flowchart(flowchart_reason)
    
    def get_default_flowchart(self) -> Dict[str, Any]:
        """Get default flowchart when requested one is not found"""
        # Default to chest_pain as per original implementation
        return self._flowchart_manager.get_flowchart('chest_pain')
    
    def get_flowchart_symptoms(self, flowchart_reason: str) -> List[str]:
        """Get symptoms for a specific flowchart"""
        return self._flowchart_manager.get_symptoms_for_flowchart(flowchart_reason)


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


class FuzzyInferenceEngine:
    """Handles fuzzy inference operations
    
    Single Responsibility: Only handles fuzzy inference
    """
    
    def __init__(self, control_system: ctrl.ControlSystem):
        self._control_system = control_system
        self._simulation = ctrl.ControlSystemSimulation(control_system)
    
    def set_inputs(self, symptom_values: List[float]) -> None:
        """Set input values for fuzzy inference"""
        input_names = ['symptom1', 'symptom2', 'symptom3', 'symptom4', 'symptom5']
        
        for i, value in enumerate(symptom_values[:5]):
            if i < len(input_names):
                self._simulation.input[input_names[i]] = value
    
    def compute_result(self) -> float:
        """Compute fuzzy inference result"""
        self._simulation.compute()
        return self._simulation.output['triage_category']
    
    def perform_inference(self, symptom_values: List[float]) -> float:
        """Perform complete fuzzy inference process"""
        self.set_inputs(symptom_values)
        return self.compute_result()


class TriageResultBuilder:
    """Builds triage result objects
    
    Single Responsibility: Only builds result objects
    """
    
    def __init__(self, category_mapper: TriageCategoryMapper):
        self._category_mapper = category_mapper
    
    def build_result(self, 
                    flowchart_reason: str,
                    fuzzy_score: float,
                    symptom_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build complete triage result"""
        
        # Map fuzzy score to category and wait time
        category_info = self._category_mapper.map_score_to_category(fuzzy_score)
        
        return {
            'flowchart_used': flowchart_reason,
            'triage_category': category_info['category'],
            'wait_time': category_info['wait_time'],
            'fuzzy_score': float(fuzzy_score),
            'symptoms_processed': symptom_data['processed_symptoms'],
            'numeric_inputs': symptom_data['numeric_values'],
            'priority_score': category_info['priority_score']
        }


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