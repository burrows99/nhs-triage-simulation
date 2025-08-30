from src.triage_systems.ai_triage import AITriage
from src.config.config_manager import (
    get_pediatric_assessor_prompt,
    get_clinical_assessor_prompt,
    get_consensus_coordinator_prompt
)
from src.utils.telemetry import DecisionStepType
import json
import logging
import time
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class MultiLLMBasedTriage(AITriage):
    def __init__(self, model_provider=None):
        super().__init__(model_provider)
        
        # Create specialized providers for each agent with their specific system prompts
        from src.config.config_manager import (
            get_pediatric_assessor_prompt,
            get_clinical_assessor_prompt, 
            get_consensus_coordinator_prompt
        )
        
        # Create separate provider instances for each specialized agent
        if model_provider is None:
            from src.model_providers.ollama import OllamaProvider
            
            # Pediatric assessor provider
            self.pediatric_provider = OllamaProvider(
                base_url=self.config['base_url'],
                model=self.config['model']
            )
            self.pediatric_provider.configure(self.config['request'])
            self.pediatric_provider.setup(get_pediatric_assessor_prompt())
            
            # Clinical assessor provider  
            self.clinical_provider = OllamaProvider(
                base_url=self.config['base_url'],
                model=self.config['model']
            )
            self.clinical_provider.configure(self.config['request'])
            self.clinical_provider.setup(get_clinical_assessor_prompt())
            
            # Consensus coordinator provider
            self.consensus_provider = OllamaProvider(
                base_url=self.config['base_url'],
                model=self.config['model']
            )
            self.consensus_provider.configure(self.config['request'])
            self.consensus_provider.setup(get_consensus_coordinator_prompt())
        else:
            # Use the same provider for all agents if one is provided
            self.pediatric_provider = model_provider
            self.clinical_provider = model_provider
            self.consensus_provider = model_provider
    
    def perform_triage(self, patient_data):
        """Perform multi-agent LLM triage assessment"""
        logger.debug(f"Multi LLM Triage received patient data: {patient_data}")
        
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
            
            # Step 2: Pediatric Risk Assessment
            pediatric_assessment = self._run_pediatric_assessment_with_telemetry(patient_data, session_id)
            logger.debug(f"Pediatric assessment: {pediatric_assessment}")
            
            # Step 3: Clinical Assessment
            clinical_assessment = self._run_clinical_assessment_with_telemetry(
                patient_data, pediatric_assessment, session_id
            )
            logger.debug(f"Clinical assessment: {clinical_assessment}")
            
            # Step 4: Consensus Coordination
            final_decision = self._run_consensus_coordination_with_telemetry(
                patient_data, pediatric_assessment, clinical_assessment, session_id
            )
            
            logger.debug(f"Final consensus: {final_decision}")
            
            # Step 6: Convert to standard format
            start_time = time.time()
            result = self._convert_to_standard_format(final_decision, patient_data)
            
            self._log_telemetry_step(
                session_id, DecisionStepType.FINAL_VALIDATION,
                {'consensus_decision': final_decision},
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
            
            logger.debug(f"Multi LLM Triage result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in multi LLM triage: {str(e)}")
            logger.exception("Full traceback:")
            
            fallback_result = self._get_fallback_response(patient_data)
            
            self._end_telemetry_session(
                session_id,
                fallback_result['priority'],
                f"Error in Multi-Agent LLM Triage: {str(e)}",
                success=False
            )
            
            return fallback_result
    
    def _run_pediatric_assessment(self, patient_data):
        """Run pediatric risk assessment agent"""
        assessment, _ = self._run_pediatric_assessment_with_telemetry(patient_data, None)
        return assessment
    
    def _run_pediatric_assessment_with_telemetry(self, patient_data, session_id):
        """Run pediatric risk assessment agent with telemetry"""
        context = self._prepare_patient_context(patient_data)
        template = get_pediatric_assessor_prompt()
        prompt = template.format(**context)
        
        logger.debug(f"Pediatric assessment prompt: {prompt[:200]}...")
        
        # Use AI triage infrastructure for LLM decision
        llm_result = self._generate_llm_decision(prompt, session_id, "Pediatric_Assessor")
        parsed_response = self._parse_and_validate_response(llm_result, session_id, "Pediatric_Assessor")
        
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
        assessment, _ = self._run_clinical_assessment_with_telemetry(patient_data, pediatric_assessment, None)
        return assessment
    
    def _run_clinical_assessment_with_telemetry(self, patient_data, pediatric_assessment, session_id):
        """Run clinical assessment agent with telemetry"""
        context = self._prepare_patient_context(patient_data)
        context['pediatric_assessment'] = json.dumps(pediatric_assessment, indent=2)
        
        template = get_clinical_assessor_prompt()
        prompt = template.format(**context)
        
        logger.debug(f"Clinical assessment prompt: {prompt[:200]}...")
        
        # Log prompt generation if telemetry session exists
        telemetry = get_telemetry_collector()
        if session_id:
            start_time = time.time()
            telemetry.log_decision_step(
                session_id, DecisionStepType.LLM_PROMPT_GENERATION,
                {'agent': 'clinical_assessor', 'context': context, 'pediatric_input': pediatric_assessment},
                {'prompt_length': len(prompt), 'prompt_preview': prompt[:200]},
                (time.time() - start_time) * 1000,
                metadata={'agent_type': 'clinical_assessor'}
            )
        
        # LLM inference with specialized clinical provider
        start_time = time.time()
        response = self.clinical_provider.generate_triage_decision(prompt)
        inference_time = (time.time() - start_time) * 1000
        
        if session_id:
            telemetry.log_decision_step(
                session_id, DecisionStepType.LLM_INFERENCE,
                {'agent': 'clinical_assessor', 'prompt_length': len(prompt)},
                {'response_length': len(response), 'response_preview': response[:200]},
                inference_time,
                metadata={'agent_type': 'clinical_assessor', 'inference_time_ms': inference_time}
            )
        
        # Response parsing
        start_time = time.time()
        parsed_response = self._parse_llm_response(response)
        
        if not parsed_response:
            logger.warning("Failed to parse clinical assessment, using fallback")
            fallback = {
                'clinical_priority': 3,
                'confidence': 'low',
                'key_findings': ['Assessment failed'],
                'rationale': 'Fallback clinical assessment',
                'service_min': 30
            }
            
            if session_id:
                telemetry.log_decision_step(
                    session_id, DecisionStepType.RESPONSE_PARSING,
                    {'raw_response': response[:500]},
                    {'parsing_success': False, 'fallback_used': True, 'fallback_result': fallback},
                    (time.time() - start_time) * 1000,
                    success=False,
                    error_message="Failed to parse clinical assessment response",
                    metadata={'agent_type': 'clinical_assessor'}
                )
            
            return fallback, {'parsing_success': False, 'fallback_used': True}
        
        if session_id:
            telemetry.log_decision_step(
                session_id, DecisionStepType.RESPONSE_PARSING,
                {'raw_response': response[:500]},
                {'parsing_success': True, 'parsed_result': parsed_response},
                (time.time() - start_time) * 1000,
                metadata={'agent_type': 'clinical_assessor'}
            )
        
        return parsed_response, {'parsing_success': True, 'fallback_used': False}
    
    def _run_consensus_coordination(self, patient_data, pediatric_assessment, clinical_assessment):
        """Run consensus coordination agent"""
        decision, _ = self._run_consensus_coordination_with_telemetry(
            patient_data, pediatric_assessment, clinical_assessment, None
        )
        return decision
    
    def _run_consensus_coordination_with_telemetry(self, patient_data, pediatric_assessment, clinical_assessment, session_id):
        """Run consensus coordination agent with telemetry"""
        context = self._prepare_patient_context(patient_data)
        context['pediatric_assessment'] = json.dumps(pediatric_assessment, indent=2)
        context['clinical_assessment'] = json.dumps(clinical_assessment, indent=2)
        
        template = get_consensus_coordinator_prompt()
        prompt = template.format(**context)
        
        logger.debug(f"Consensus coordination prompt: {prompt[:200]}...")
        
        # Log prompt generation if telemetry session exists
        telemetry = get_telemetry_collector()
        if session_id:
            start_time = time.time()
            telemetry.log_decision_step(
                session_id, DecisionStepType.LLM_PROMPT_GENERATION,
                {
                    'agent': 'consensus_coordinator', 
                    'context': context,
                    'pediatric_input': pediatric_assessment,
                    'clinical_input': clinical_assessment
                },
                {'prompt_length': len(prompt), 'prompt_preview': prompt[:200]},
                (time.time() - start_time) * 1000,
                metadata={'agent_type': 'consensus_coordinator'}
            )
        
        # LLM inference with specialized consensus provider
        start_time = time.time()
        response = self.consensus_provider.generate_triage_decision(prompt)
        inference_time = (time.time() - start_time) * 1000
        
        if session_id:
            telemetry.log_decision_step(
                session_id, DecisionStepType.LLM_INFERENCE,
                {'agent': 'consensus_coordinator', 'prompt_length': len(prompt)},
                {'response_length': len(response), 'response_preview': response[:200]},
                inference_time,
                metadata={'agent_type': 'consensus_coordinator', 'inference_time_ms': inference_time}
            )
        
        # Response parsing
        start_time = time.time()
        parsed_response = self._parse_llm_response(response)
        
        if not parsed_response:
            logger.warning("Failed to parse consensus coordination, using fallback")
            # Use the higher priority from the two assessments as fallback
            pediatric_priority = pediatric_assessment.get('priority_recommendation', 3)
            clinical_priority = clinical_assessment.get('clinical_priority', 3)
            final_priority = min(pediatric_priority, clinical_priority)  # Lower number = higher priority
            
            fallback = {
                'mts_priority': final_priority,
                'confidence': 'low',
                'rationale': 'Fallback consensus - used higher priority from assessments',
                'service_min': 30,
                'consensus_method': 'fallback_higher_priority',
                'critical_history_factors': [],
                'history_risk_modifier': 'neutral'
            }
            
            if session_id:
                telemetry.log_decision_step(
                    session_id, DecisionStepType.RESPONSE_PARSING,
                    {'raw_response': response[:500]},
                    {'parsing_success': False, 'fallback_used': True, 'fallback_result': fallback},
                    (time.time() - start_time) * 1000,
                    success=False,
                    error_message="Failed to parse consensus coordination response",
                    metadata={'agent_type': 'consensus_coordinator'}
                )
            
            return fallback, {'parsing_success': False, 'fallback_used': True}
        
        if session_id:
            telemetry.log_decision_step(
                session_id, DecisionStepType.RESPONSE_PARSING,
                {'raw_response': response[:500]},
                {'parsing_success': True, 'parsed_result': parsed_response},
                (time.time() - start_time) * 1000,
                metadata={'agent_type': 'consensus_coordinator'}
            )
        
        return parsed_response, {'parsing_success': True, 'fallback_used': False}
    
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
            
            # Set triage results using the Patient method
            patient.set_triage_result(
                priority=priority,
                triage_system=self.get_triage_system_name()
            )
            
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