"""AI-based Triage System Base Class

This module provides a base class for AI-powered triage systems that use
Large Language Models (LLMs) for decision making. It inherits from BaseTriage
and adds common functionality for LLM-based triage systems.
"""

from abc import abstractmethod
from typing import Dict, Any, Optional
import json
import logging
import time
from src.triage_systems.base_triage import BaseTriage
from src.config.config_manager import get_ollama_config
from src.utils.json_utils import (
    parse_json_response,
    safe_json_dumps,
    log_json_operation
)
from src.utils.telemetry import DecisionStepType

logger = logging.getLogger(__name__)

class AITriage(BaseTriage):
    """Base class for AI-powered triage systems using LLMs
    
    This class provides common functionality for triage systems that use
    Large Language Models for decision making, including:
    - LLM provider management
    - Common prompt handling
    - Response parsing and validation
    - Error handling and fallback mechanisms
    - Telemetry integration for AI-specific metrics
    """
    
    def __init__(self, model_provider=None):
        """Initialize AI Triage system
        
        Args:
            model_provider: Optional LLM provider instance. If None, will create OllamaProvider
        """
        super().__init__()
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
        
        # Set up system prompt for triage context
        # This will be overridden by specific triage systems with their specialized prompts
        from src.config.config_manager import get_base_agent_prompt
        if hasattr(self.provider, 'setup'):
            self.provider.setup(get_base_agent_prompt())
    
    def _prepare_patient_context(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare patient data for LLM prompt generation
        
        Args:
            patient_data: Raw patient data dictionary
            
        Returns:
            Dict containing formatted patient context for prompts
        """
        return {
            'patient_id': patient_data.get('id', 'Unknown'),
            'age': patient_data.get('age', 'Unknown'),
            'gender': patient_data.get('gender', 'Unknown'),
            'chief_complaint': patient_data.get('chief_complaint', 'Not specified'),
            'vital_signs': self._format_vital_signs(patient_data),
            'medical_history': patient_data.get('medical_history', 'No significant history'),
            'severity': patient_data.get('severity', 0.5)
        }
    
    def _format_vital_signs(self, patient_data: Dict[str, Any]) -> str:
        """Format vital signs for LLM consumption
        
        Args:
            patient_data: Patient data containing vital signs
            
        Returns:
            Formatted string of vital signs
        """
        vital_signs = patient_data.get('vital_signs', {})
        if not vital_signs:
            return "Vital signs not available"
        
        formatted = []
        if 'heart_rate' in vital_signs:
            formatted.append(f"HR: {vital_signs['heart_rate']} bpm")
        if 'blood_pressure' in vital_signs:
            formatted.append(f"BP: {vital_signs['blood_pressure']} mmHg")
        if 'temperature' in vital_signs:
            formatted.append(f"Temp: {vital_signs['temperature']}°C")
        if 'respiratory_rate' in vital_signs:
            formatted.append(f"RR: {vital_signs['respiratory_rate']} /min")
        if 'oxygen_saturation' in vital_signs:
            formatted.append(f"SpO2: {vital_signs['oxygen_saturation']}%")
        if 'pain_score' in vital_signs:
            formatted.append(f"Pain: {vital_signs['pain_score']}/10")
        
        return ", ".join(formatted) if formatted else "Vital signs not available"
    
    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse LLM response into structured data
        
        Args:
            response: Raw LLM response string
            
        Returns:
            Parsed response dictionary or None if parsing fails
        """
        return parse_json_response(response)
    
    def _generate_llm_decision(self, prompt: str, session_id: str, 
                              agent_name: str = "LLM") -> Dict[str, Any]:
        """Generate LLM decision with telemetry tracking
        
        Args:
            prompt: Formatted prompt for the LLM
            session_id: Telemetry session ID
            agent_name: Name of the agent for telemetry
            
        Returns:
            Dictionary containing LLM response and metadata
        """
        # Log prompt generation
        start_time = time.time()
        self._log_telemetry_step(
            session_id, DecisionStepType.LLM_PROMPT_GENERATION,
            {'agent': agent_name, 'prompt_length': len(prompt)},
            {'prompt_preview': prompt[:200]},
            (time.time() - start_time) * 1000,
            metadata={'agent_type': agent_name.lower()}
        )
        
        # LLM inference
        start_time = time.time()
        try:
            response = self.provider.generate_triage_decision(
                prompt, 
                options=self.config.get('request', {}).get('options', {})
            )
            inference_time = (time.time() - start_time) * 1000
            
            self._log_telemetry_step(
                session_id, DecisionStepType.LLM_INFERENCE,
                {
                    'agent': agent_name,
                    'prompt_length': len(prompt),
                    'llm_options': self.config.get('request', {}).get('options', {})
                },
                {
                    'response_length': len(response),
                    'response_preview': response[:200],
                    'inference_time_ms': inference_time
                },
                inference_time,
                metadata={'agent_type': agent_name.lower()}
            )
            
            return {
                'response': response,
                'inference_time_ms': inference_time,
                'success': True
            }
            
        except Exception as e:
            inference_time = (time.time() - start_time) * 1000
            
            self._log_telemetry_step(
                session_id, DecisionStepType.LLM_INFERENCE,
                {'agent': agent_name, 'prompt_length': len(prompt)},
                {'error': str(e), 'inference_time_ms': inference_time},
                inference_time,
                success=False,
                error_message=f"LLM inference failed: {str(e)}",
                metadata={'agent_type': agent_name.lower()}
            )
            
            return {
                'response': None,
                'inference_time_ms': inference_time,
                'success': False,
                'error': str(e)
            }
    
    def _parse_and_validate_response(self, llm_result: Dict[str, Any], 
                                   session_id: str, agent_name: str = "LLM") -> Optional[Dict[str, Any]]:
        """Parse and validate LLM response with telemetry
        
        Args:
            llm_result: Result from _generate_llm_decision
            session_id: Telemetry session ID
            agent_name: Name of the agent for telemetry
            
        Returns:
            Parsed and validated response or None if invalid
        """
        start_time = time.time()
        
        if not llm_result['success']:
            self._log_telemetry_step(
                session_id, DecisionStepType.RESPONSE_PARSING,
                {'agent': agent_name, 'llm_success': False},
                {'parsing_success': False, 'error': llm_result.get('error', 'Unknown error')},
                (time.time() - start_time) * 1000,
                success=False,
                error_message=f"LLM generation failed: {llm_result.get('error', 'Unknown error')}",
                metadata={'agent_type': agent_name.lower()}
            )
            return None
        
        response = llm_result['response']
        parsed_response = self._parse_llm_response(response)
        
        if not parsed_response:
            self._log_telemetry_step(
                session_id, DecisionStepType.RESPONSE_PARSING,
                {'agent': agent_name, 'raw_response': response[:500]},
                {'parsing_success': False, 'error': 'Failed to parse JSON'},
                (time.time() - start_time) * 1000,
                success=False,
                error_message="Failed to parse LLM response as JSON",
                metadata={'agent_type': agent_name.lower()}
            )
            return None
        
        self._log_telemetry_step(
            session_id, DecisionStepType.RESPONSE_PARSING,
            {'agent': agent_name, 'raw_response': response[:500]},
            {'parsing_success': True, 'parsed_data': parsed_response},
            (time.time() - start_time) * 1000,
            metadata={'agent_type': agent_name.lower()}
        )
        
        return parsed_response
    
    def _get_actions_for_priority(self, priority: int) -> list:
        """Get recommended actions for a given priority level
        
        Args:
            priority: Triage priority (1-5)
            
        Returns:
            List of recommended actions
        """
        actions_map = {
            1: ["Immediate resuscitation", "Call trauma team", "Prepare for emergency intervention"],
            2: ["Urgent assessment", "Continuous monitoring", "Prepare for immediate treatment"],
            3: ["Assessment within 30 minutes", "Regular monitoring", "Pain management if needed"],
            4: ["Assessment within 1 hour", "Comfort measures", "Patient education"],
            5: ["Assessment within 2 hours", "Discharge planning", "Follow-up instructions"]
        }
        return actions_map.get(priority, ["Standard monitoring"])
    
    def _get_fallback_response(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback response when AI systems fail
        
        Args:
            patient_data: Patient data for fallback assessment
            
        Returns:
            Fallback triage decision
        """
        # Use severity-based fallback logic
        severity = patient_data.get('severity', 0.5)
        
        if severity >= 0.8:
            priority = 1
            rationale = "High severity score - immediate attention required"
        elif severity >= 0.6:
            priority = 2
            rationale = "Moderate-high severity - urgent assessment needed"
        elif severity >= 0.4:
            priority = 3
            rationale = "Moderate severity - standard assessment"
        elif severity >= 0.2:
            priority = 4
            rationale = "Low-moderate severity - routine assessment"
        else:
            priority = 5
            rationale = "Low severity - non-urgent assessment"
        
        return {
            'priority': priority,
            'rationale': f"AI Triage Fallback: {rationale}",
            'recommended_actions': self._get_actions_for_priority(priority),
            'confidence': 'low',
            'fallback_used': True
        }
    
    def assign_priority(self, patient):
        """Assign priority to patient using AI triage
        
        This method should be implemented by subclasses to define
        their specific AI triage logic.
        """
        logger.debug(f"assign_priority called for Patient {patient.id}")
        
        try:
            triage_result = self.perform_triage(patient.__dict__)
            priority = triage_result['priority']
            
            # Set triage results using the Patient method
            patient.set_triage_result(
                priority=priority,
                triage_system=self.get_triage_system_name()
            )
            
            logger.info(f"Patient {patient.id} assigned priority {priority} by {self.get_triage_system_name()}")
            return priority
            
        except Exception as e:
            logger.error(f"Error in assign_priority for Patient {patient.id}: {str(e)}")
            logger.exception("Full traceback:")
            
            # Use fallback priority
            fallback_result = self._get_fallback_response(patient.__dict__)
            fallback_priority = fallback_result['priority']
            
            patient.set_triage_result(
                priority=fallback_priority,
                triage_system=self.get_triage_system_name()
            )
            
            return fallback_priority
    
    def estimate_triage_time(self):
        """Estimate triage time for AI-based systems
        
        AI systems typically take longer than traditional triage
        due to LLM inference time.
        """
        from src.config.config_manager import get_service_time_config
        service_config = get_service_time_config()
        base_time = service_config['triage']['mean']
        
        # AI systems take 2-3x longer due to LLM processing
        ai_factor = 2.5
        
        import random
        import numpy as np
        
        # Add random variation with lognormal distribution
        variation = np.random.lognormal(0, 0.3)
        estimated_time = base_time * ai_factor * variation
        
        return max(1.0, estimated_time)  # Minimum 1 minute
    
    def estimate_consult_time(self, priority: int):
        """Estimate consultation time based on priority
        
        Args:
            priority: Triage priority (1-5)
            
        Returns:
            Estimated consultation time in minutes
        """
        from src.config.config_manager import get_service_time_config
        service_config = get_service_time_config()
        base_time = service_config['consultation']['mean']
        
        # Priority-based time factors
        priority_factors = {
            1: 2.0,   # Immediate - longest consultations
            2: 1.5,   # Very urgent
            3: 1.0,   # Urgent - baseline
            4: 0.8,   # Standard
            5: 0.6    # Non-urgent - shortest
        }
        
        factor = priority_factors.get(priority, 1.0)
        
        import random
        import numpy as np
        
        # Add random variation
        variation = np.random.lognormal(0, 0.2)
        estimated_time = base_time * factor * variation
        
        return max(5.0, estimated_time)  # Minimum 5 minutes
    
    @abstractmethod
    def perform_triage(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform AI-based triage assessment
        
        This method must be implemented by subclasses to define
        their specific AI triage logic.
        
        Args:
            patient_data: Patient data dictionary
            
        Returns:
            Triage decision dictionary with priority, rationale, etc.
        """
        pass
    
    @abstractmethod
    def get_triage_system_name(self) -> str:
        """Get the name of the AI triage system
        
        Returns:
            String name of the triage system
        """
        pass