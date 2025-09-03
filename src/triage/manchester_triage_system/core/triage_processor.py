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
        self._flowchart_manager = flowchart_manager
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
        from src.logger import logger
        
        logger.info(f"🔄 DATA_TRANSFER_START: MTS.process_triage() initiated")
        logger.info(f"📊 TRANSFER_SOURCE: Flowchart={flowchart_reason}, Symptoms={str(symptoms_input)}")
        logger.info(f"📍 TRANSFER_DESTINATION: Manchester Triage System fuzzy logic engine")
        logger.info(f"🏥 Starting Manchester Triage System Assessment")
        logger.info(f"📋 Flowchart: {flowchart_reason}")
        logger.info(f"📝 Symptoms Input: {symptoms_input}")
        
        # Step 1: Validate inputs
        logger.info(f"🔍 Step 1: Validating Input Parameters")
        logger.info(f"🔄 DATA_TRANSFER: Validating input parameters...")
        validation = TriageValidator.validate_inputs(flowchart_reason, symptoms_input)
        logger.info(f"📊 TRANSFER_RESULT: Validation result - {str(validation)}")
        if not validation['valid']:
            logger.error(f"❌ Step 1 Failed: Input validation errors - {validation['errors']}")
            raise ValueError(f"Invalid inputs: {validation['errors']}")
        logger.info(f"✅ Input validation passed")
        
        # Step 2: Lookup flowchart
        logger.info(f"🔍 Step 2: Loading Flowchart Configuration")
        logger.info(f"🔄 DATA_TRANSFER: Loading flowchart config for {flowchart_reason}...")
        flowchart_config = self._flowchart_manager.get_flowchart(flowchart_reason)
        if flowchart_config is None:
            logger.info(f"⚠️ Flowchart '{flowchart_reason}' not found, defaulting to 'chest_pain'")
            flowchart_config = self._flowchart_manager.get_flowchart('chest_pain')
            flowchart_reason = 'chest_pain'
        logger.info(f"📊 TRANSFER_RESULT: Flowchart config loaded - {str(flowchart_config)[:200]}...")
        logger.info(f"✅ Flowchart '{flowchart_reason}' loaded successfully")
        
        # Step 3: Process symptoms
        logger.info(f"🔍 Step 3: Processing Symptoms with Fuzzy Logic")
        logger.info(f"🔄 DATA_TRANSFER: Processing symptoms through fuzzy logic...")
        symptom_data = self._symptom_processor.process_symptoms(flowchart_config, symptoms_input)
        logger.info(f"📊 TRANSFER_RESULT: Symptom processing complete - {str(symptom_data)}")
        logger.info(f"📊 Processed {len(symptom_data.get('symptoms_processed', {}))} symptoms")
        logger.info(f"📈 Fuzzy values: {symptom_data.get('padded_values', [])}")
        
        # Step 4: Perform fuzzy inference
        logger.info(f"🔍 Step 4: Executing Fuzzy Inference Engine")
        logger.info(f"🔄 DATA_TRANSFER: Running fuzzy inference on processed values...")
        fuzzy_score = self._inference_engine.perform_inference(symptom_data['padded_values'])
        logger.info(f"📊 TRANSFER_RESULT: Fuzzy inference score calculated - {fuzzy_score:.3f}")
        logger.info(f"🎯 Fuzzy inference score: {fuzzy_score:.3f}")
        
        # Step 5: Build result
        logger.info(f"🔍 Step 5: Building Triage Result")
        logger.info(f"🔄 DATA_TRANSFER: Building final triage result...")
        result = self._result_builder.build_result(flowchart_reason, fuzzy_score, symptom_data)
        logger.info(f"📊 TRANSFER_RESULT: Triage result built - {str(result)}")
        logger.info(f"🏥 TRIAGE RESULT: {result.get('triage_category', 'Unknown')} (Priority {result.get('priority_score', 'Unknown')})")
        logger.info(f"⏰ Wait Time: {result.get('wait_time', 'Unknown')}")
        logger.info(f"📊 Fuzzy Score: {result.get('fuzzy_score', 'Unknown')}")
        
        # Step 6: Validate result
        logger.info(f"🔍 Step 6: Validating Final Result")
        logger.info(f"🔄 DATA_TRANSFER: Validating final result...")
        result_validation = TriageValidator.validate_result(result)
        logger.info(f"📊 TRANSFER_RESULT: Result validation - {str(result_validation)}")
        if not result_validation['valid']:
            logger.error(f"❌ Step 6 Failed: Result validation errors - {result_validation['errors']}")
            raise RuntimeError(f"Invalid result generated: {result_validation['errors']}")
        logger.info(f"✅ Result validation passed")
        logger.info(f"✅ DATA_TRANSFER_SUCCESS: Manchester Triage System Assessment Complete")
        logger.info(f"📊 FINAL_MTS_RESULT: {str(result)}")
        
        return result