from src.triage_systems.base_triage import BaseTriage
from src.config.config_manager import (
    get_ollama_config, 
    get_pediatric_assessor_prompt,
    get_clinical_assessor_prompt,
    get_consensus_coordinator_prompt
)
from src.utils.json_utils import (
    parse_json_response,
    safe_json_dumps,
    log_json_operation
)
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class MultiLLMBasedTriage(BaseTriage):
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
        """Perform multi-agent LLM triage assessment"""
        logger.debug(f"Multi LLM Triage received patient data: {patient_data}")
        
        try:
            # Step 1: Pediatric Risk Assessment
            pediatric_assessment = self._run_pediatric_assessment(patient_data)
            logger.debug(f"Pediatric assessment: {pediatric_assessment}")
            
            # Step 2: Clinical Assessment
            clinical_assessment = self._run_clinical_assessment(patient_data, pediatric_assessment)
            logger.debug(f"Clinical assessment: {clinical_assessment}")
            
            # Step 3: Consensus Coordination
            final_decision = self._run_consensus_coordination(patient_data, pediatric_assessment, clinical_assessment)
            logger.debug(f"Final consensus: {final_decision}")
            
            # Convert to standard format
            result = self._convert_to_standard_format(final_decision, patient_data)
            
            logger.debug(f"Multi LLM Triage result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in multi LLM triage: {str(e)}")
            logger.exception("Full traceback:")
            return self._get_fallback_response(patient_data)
    
    def _run_pediatric_assessment(self, patient_data):
        """Run pediatric risk assessment agent"""
        context = self._prepare_patient_context(patient_data)
        template = get_pediatric_assessor_prompt()
        prompt = template.format(**context)
        
        logger.debug(f"Pediatric assessment prompt: {prompt[:200]}...")
        
        response = self.provider.generate_triage_decision(prompt)
        parsed_response = self._parse_llm_response(response)
        
        if not parsed_response:
            logger.warning("Failed to parse pediatric assessment, using fallback")
            return {
                'pediatric_risk': 'medium',
                'mandatory_rules_triggered': [],
                'age_calculated': patient_data.get('age', 'Unknown'),
                'priority_recommendation': 3,
                'rationale': 'Fallback pediatric assessment'
            }
        
        return parsed_response
    
    def _run_clinical_assessment(self, patient_data, pediatric_assessment):
        """Run clinical assessment agent"""
        context = self._prepare_patient_context(patient_data)
        context['pediatric_assessment'] = json.dumps(pediatric_assessment, indent=2)
        
        template = get_clinical_assessor_prompt()
        prompt = template.format(**context)
        
        logger.debug(f"Clinical assessment prompt: {prompt[:200]}...")
        
        response = self.provider.generate_triage_decision(prompt)
        parsed_response = self._parse_llm_response(response)
        
        if not parsed_response:
            logger.warning("Failed to parse clinical assessment, using fallback")
            return {
                'clinical_priority': 3,
                'confidence': 'low',
                'key_findings': ['Assessment failed'],
                'rationale': 'Fallback clinical assessment',
                'service_min': 30
            }
        
        return parsed_response
    
    def _run_consensus_coordination(self, patient_data, pediatric_assessment, clinical_assessment):
        """Run consensus coordination agent"""
        context = self._prepare_patient_context(patient_data)
        context['pediatric_assessment'] = json.dumps(pediatric_assessment, indent=2)
        context['clinical_assessment'] = json.dumps(clinical_assessment, indent=2)
        
        template = get_consensus_coordinator_prompt()
        prompt = template.format(**context)
        
        logger.debug(f"Consensus coordination prompt: {prompt[:200]}...")
        
        response = self.provider.generate_triage_decision(prompt)
        parsed_response = self._parse_llm_response(response)
        
        if not parsed_response:
            logger.warning("Failed to parse consensus coordination, using fallback")
            # Use the higher priority from the two assessments as fallback
            pediatric_priority = pediatric_assessment.get('priority_recommendation', 3)
            clinical_priority = clinical_assessment.get('clinical_priority', 3)
            final_priority = min(pediatric_priority, clinical_priority)  # Lower number = higher priority
            
            return {
                'mts_priority': final_priority,
                'confidence': 'low',
                'rationale': 'Fallback consensus - used higher priority from assessments',
                'service_min': 30,
                'consensus_method': 'fallback_higher_priority',
                'critical_history_factors': [],
                'history_risk_modifier': 'neutral'
            }
        
        return parsed_response
    
    def _prepare_patient_context(self, patient_data):
        """Prepare patient context for prompt formatting"""
        return {
            'patient_age': patient_data.get('age', 'Unknown'),
            'patient_gender': patient_data.get('gender', 'Unknown'),
            'reason_description': patient_data.get('chief_complaint', 'Not specified'),
            'patient_history': patient_data.get('medical_history', 'No history available'),
            'vital_signs': self._format_vital_signs(patient_data),
            'clinical_context': json.dumps(patient_data, indent=2)
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
    
    def _convert_to_standard_format(self, consensus_decision, patient_data):
        """Convert consensus decision to standard triage format"""
        priority = self.extract_priority_from_response(consensus_decision) or 3
        confidence = self.extract_confidence_from_response(consensus_decision)
        rationale = self.extract_rationale_from_response(consensus_decision)
        
        return {
            'priority': priority,
            'rationale': f"Multi-Agent LLM Assessment: {rationale}",
            'recommended_actions': self._get_actions_for_priority(priority),
            'confidence': confidence,
            'service_time_estimate': consensus_decision.get('service_min', 30),
            'consensus_method': consensus_decision.get('consensus_method', 'multi_agent_coordination'),
            'critical_history_factors': consensus_decision.get('critical_history_factors', []),
            'history_risk_modifier': consensus_decision.get('history_risk_modifier', 'neutral')
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
            'rationale': f'Multi-agent fallback assessment based on severity {severity:.2f} (LLM unavailable)',
            'recommended_actions': self._get_actions_for_priority(priority),
            'confidence': 'low',
            'service_time_estimate': 25,
            'consensus_method': 'severity_based_fallback',
            'critical_history_factors': ['LLM_timeout'],
            'history_risk_modifier': 'neutral',
            'error': 'Multi-agent LLM processing failed - used severity-based fallback'
        }
    
    def assign_priority(self, patient):
        """Assign priority to patient using multi-agent LLM triage"""
        logger.debug(f"assign_priority called for Patient {patient.id}")
        
        try:
            triage_result = self.perform_triage(patient.__dict__)
            priority = triage_result['priority']
            logger.info(f"Patient {patient.id} assigned priority {priority} by Multi-Agent LLM Triage")
            return priority
        except Exception as e:
            logger.error(f"Error in assign_priority for Patient {patient.id}: {str(e)}")
            logger.exception("Full traceback:")
            # Use configured default priority
            from src.config.config_manager import get_patient_generation_config
            patient_config = get_patient_generation_config()
            return patient_config['default_priority']
    
    def estimate_triage_time(self):
        """Estimate triage time for multi-agent LLM system"""
        from src.config.config_manager import get_service_time_config
        service_config = get_service_time_config()
        base_time = service_config['triage']['mean']
        
        # Multi-agent LLM triage takes longer due to multiple LLM calls
        multi_agent_factor = 2.0
        
        import random
        import numpy as np
        stdev = service_config['triage']['stdev']
        return random.lognormvariate(
            np.log(base_time * multi_agent_factor),
            stdev / (base_time * multi_agent_factor)
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
        return "Multi-Agent LLM-Based Triage System"