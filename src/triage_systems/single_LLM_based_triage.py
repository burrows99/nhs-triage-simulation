from src.triage_systems.base_triage import BaseTriage
from src.config.config_manager import get_ollama_config, get_single_agent_prompt
from src.utils.json_utils import (
    parse_json_response,
    safe_json_dumps,
    log_json_operation
)
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SingleLLMBasedTriage(BaseTriage):
    def __init__(self, model_provider=None):
        self.config = get_ollama_config()
        
        # Initialize provider with config if not provided
        if model_provider is None:
            from src.model_providers.ollama import OllamaProvider
            self.provider = OllamaProvider(
                base_url=self.config['base_url'],
                model=self.config['model']
            )
        else:
            self.provider = model_provider
        
        # Configure the model provider with Ollama settings
        if hasattr(self.provider, 'configure'):
            self.provider.configure(self.config['request'])
    
    def perform_triage(self, patient_data):
        """Perform single-agent LLM triage assessment"""
        logger.debug(f"Single LLM Triage received patient data: {patient_data}")
        
        try:
            # Prepare context for the prompt
            context = self._prepare_patient_context(patient_data)
            
            # Format the prompt using the dedicated prompt function
            template = get_single_agent_prompt()
            prompt = template.format(**context)
            
            logger.debug(f"Generated prompt for single LLM triage: {prompt[:200]}...")
            
            # Get decision from LLM with configured options
            decision = self.provider.generate_triage_decision(
                prompt, 
                options=self.config['single_agent'].get('options', {})
            )
            
            logger.debug(f"Raw LLM response: {decision}")
            
            # Parse and validate the response
            parsed_decision = self._parse_llm_response(decision)
            
            if not parsed_decision:
                logger.error(f"Failed to parse LLM response: {decision}")
                return self._get_fallback_response(patient_data)
            
            # Convert to standard triage format
            result = self._convert_to_standard_format(parsed_decision, patient_data)
            
            logger.debug(f"Single LLM Triage result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in single LLM triage: {str(e)}")
            logger.exception("Full traceback:")
            return self._get_fallback_response(patient_data)
    
    def _prepare_patient_context(self, patient_data):
        """Prepare patient context for prompt formatting"""
        return {
            'patient_age': patient_data.get('age', 'Unknown'),
            'patient_gender': patient_data.get('gender', 'Unknown'),
            'reason_description': patient_data.get('chief_complaint', 'Not specified'),
            'patient_history': patient_data.get('medical_history', 'No history available'),
            'vital_signs': self._format_vital_signs(patient_data),
            'clinical_context': safe_json_dumps(patient_data, indent=2)
        }
    
    def _format_vital_signs(self, patient_data):
        """Format vital signs for display"""
        vitals = []
        if 'heart_rate' in patient_data:
            vitals.append(f"HR: {patient_data['heart_rate']}")
        if 'blood_pressure' in patient_data:
            vitals.append(f"BP: {patient_data['blood_pressure']}")
        if 'temperature' in patient_data:
            vitals.append(f"Temp: {patient_data['temperature']}°C")
        if 'oxygen_saturation' in patient_data:
            vitals.append(f"O2 Sat: {patient_data['oxygen_saturation']}%")
        if 'respiratory_rate' in patient_data:
            vitals.append(f"RR: {patient_data['respiratory_rate']}")
        
        return ', '.join(vitals) if vitals else 'No vital signs recorded'
    
    def _parse_llm_response(self, response):
        """Parse LLM JSON response using centralized utilities"""
        result = parse_json_response(response)
        log_json_operation("parsing", result is not None, f"Response length: {len(response)}")
        return result
    
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
    
    def _get_actions_for_priority(self, priority):
        """Get recommended actions for priority level"""
        from src.config.config_manager import get_triage_actions_config
        actions_config = get_triage_actions_config()
        return actions_config.get(priority, ["Standard monitoring"])
    
    def _get_fallback_response(self, patient_data):
        """Get fallback response when LLM fails - use severity-based priority"""
        from src.config.config_manager import get_patient_generation_config
        patient_config = get_patient_generation_config()
        
        # Use patient severity to assign a reasonable priority
        severity = patient_data.get('severity', 0.5)
        if severity >= 0.8:
            priority = 1  # High severity -> High priority
        elif severity >= 0.6:
            priority = 2
        elif severity >= 0.4:
            priority = 3
        elif severity >= 0.2:
            priority = 4
        else:
            priority = 5  # Low severity -> Low priority
        
        return {
            'priority': priority,
            'rationale': f'Fallback assessment based on severity {severity:.2f} (LLM unavailable)',
            'recommended_actions': self._get_actions_for_priority(priority),
            'confidence': 'low',
            'service_time_estimate': 25,
            'error': 'LLM processing failed - used severity-based fallback'
        }
    
    def assign_priority(self, patient):
        """Assign priority to patient using LLM triage"""
        logger.debug(f"assign_priority called for Patient {patient.id}")
        
        try:
            triage_result = self.perform_triage(patient.__dict__)
            priority = triage_result['priority']
            logger.info(f"Patient {patient.id} assigned priority {priority} by Single LLM Triage")
            return priority
        except Exception as e:
            logger.error(f"Error in assign_priority for Patient {patient.id}: {str(e)}")
            logger.exception("Full traceback:")
            # Use configured default priority
            from src.config.config_manager import get_patient_generation_config
            patient_config = get_patient_generation_config()
            return patient_config['default_priority']
    
    def estimate_triage_time(self):
        """Estimate triage time for LLM-based system"""
        from src.config.config_manager import get_service_time_config
        service_config = get_service_time_config()
        base_time = service_config['triage']['mean']
        
        # LLM triage may take longer due to processing time
        llm_factor = 1.5
        
        import random
        import numpy as np
        stdev = service_config['triage']['stdev']
        return random.lognormvariate(
            np.log(base_time * llm_factor),
            stdev / (base_time * llm_factor)
        )
    
    def estimate_consult_time(self, priority):
        """Estimate consultation time based on priority"""
        from src.config.config_manager import get_service_time_config
        service_config = get_service_time_config()
        base_time = service_config['consultation']['mean']
        
        # Adjust based on priority
        priority_factors = {1: 1.5, 2: 1.3, 3: 1.0, 4: 0.8, 5: 0.7}
        factor = priority_factors.get(priority, 1.0)
        
        import random
        import numpy as np
        adjusted_mean = base_time * factor
        stdev = service_config['consultation']['stdev']
        return random.lognormvariate(
            np.log(adjusted_mean),
            stdev / adjusted_mean
        )
    
    def get_triage_system_name(self):
        """Get the name of the triage system"""
        return "Single LLM-Based Triage System"