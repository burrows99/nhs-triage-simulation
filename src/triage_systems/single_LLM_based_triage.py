from src.triage_systems.ai_triage import AITriage
from src.config.config_manager import get_single_agent_prompt
from src.utils.telemetry import DecisionStepType
import json
import logging
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SingleLLMBasedTriage(AITriage):
    def __init__(self, model_provider=None):
        super().__init__(model_provider)
        
        # Set up specialized single agent system prompt
        from src.config.config_manager import get_single_agent_prompt
        if hasattr(self.provider, 'setup'):
            self.provider.setup(get_single_agent_prompt())
    
    def perform_triage(self, patient_data):
        """Perform single-agent LLM triage assessment"""
        logger.debug(f"Single LLM Triage received patient data: {patient_data}")
        
        # Start telemetry session
        session_id = self._start_telemetry_session(patient_data)
        
        try:
            # Step 1: Data preprocessing
            start_time = time.time()
            context = self._prepare_patient_context(patient_data)
            
            self._log_telemetry_step(
                session_id, DecisionStepType.DATA_PREPROCESSING,
                {'raw_patient_data': patient_data},
                {'prepared_context': context},
                (time.time() - start_time) * 1000
            )
            
            # Step 2: Generate prompt and get LLM decision
            template = get_single_agent_prompt()
            prompt = template.format(**context)
            
            logger.debug(f"Generated prompt for single LLM triage: {prompt[:200]}...")
            
            # Step 3: LLM inference with telemetry
            llm_result = self._generate_llm_decision(prompt, session_id, "Single_LLM_Agent")
            
            # Step 4: Parse and validate response
            parsed_decision = self._parse_and_validate_response(llm_result, session_id, "Single_LLM_Agent")
            
            if not parsed_decision:
                logger.error(f"Failed to get valid LLM response")
                fallback_result = self._get_fallback_response(patient_data)
                
                self._end_telemetry_session(
                    session_id,
                    fallback_result['priority'],
                    fallback_result['rationale'],
                    success=False
                )
                
                return fallback_result
            
            # Step 5: Convert to standard format
            start_time = time.time()
            result = self._convert_to_standard_format(parsed_decision, patient_data)
            
            self._log_telemetry_step(
                session_id, DecisionStepType.FINAL_VALIDATION,
                {'parsed_decision': parsed_decision},
                result,
                (time.time() - start_time) * 1000
            )
            
            # End telemetry session
            self._end_telemetry_session(
                session_id,
                result['priority'],
                result['rationale'],
                success=True
            )
            
            logger.debug(f"Single LLM Triage result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in single LLM triage: {str(e)}")
            logger.exception("Full traceback:")
            
            fallback_result = self._get_fallback_response(patient_data)
            
            self._end_telemetry_session(
                session_id,
                fallback_result['priority'],
                f"Error in Single LLM Triage: {str(e)}",
                success=False
            )
            
            return fallback_result
    

    
    def _convert_to_standard_format(self, llm_response, patient_data):
        """Convert LLM response to standard triage format using centralized utilities"""
        priority = self.extract_priority_from_response(llm_response) or 3
        confidence = self.extract_confidence_from_response(llm_response)
        rationale = self.extract_rationale_from_response(llm_response)
        
        return {
            'priority': priority,
            'rationale': f"Single LLM Assessment: {rationale}",
            'recommended_actions': self._get_actions_for_priority(priority),
            'confidence': confidence,
            'service_time_estimate': llm_response.get('service_min', 30),
            'mandatory_rule_applied': llm_response.get('mandatory_rule_applied', False)
        }
    

    

    
    def get_triage_system_name(self):
        """Get the name of the triage system"""
        return "Single LLM-Based Triage System"