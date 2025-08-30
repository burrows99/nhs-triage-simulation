from src.triage_systems.base_triage import BaseTriage
from src.model_providers.simulation_aware_provider import SimulationAwareProvider
from src.model_providers.ollama import OllamaProvider
from src.config.config_manager import (
    get_ollama_config, 
    get_single_agent_prompt, 
    get_pediatric_assessor_prompt,
    get_clinical_assessor_prompt,
    get_consensus_coordinator_prompt
)
from src.utils.telemetry import DecisionStepType
import time
import json
import logging
from typing import Dict, Any, Optional, List
import threading
import re

logger = logging.getLogger(__name__)

class SimulationAwareAITriage(BaseTriage):
    """
    Unified simulation-aware AI triage system that supports both single and multi-agent LLM approaches.
    
    This system:
    1. Pre-computes all LLM responses before simulation starts
    2. Uses cached responses during simulation (instant retrieval)
    3. Estimates realistic triage times without blocking simulation
    4. Supports multiple triage strategies (single LLM, multi-agent)
    """
    
    def __init__(self, model_provider=None, strategy="single", system_name=None):
        """
        Initialize simulation-aware AI Triage system
        
        Args:
            model_provider: Optional LLM provider instance
            strategy: "single" for single LLM, "multi" for multi-agent approach
            system_name: Custom name for the triage system
        """
        super().__init__()
        self.strategy = strategy
        self.system_name = system_name or f"{strategy.title()} LLM-Based Triage System"
        self.config = get_ollama_config()
        
        # Initialize simulation-aware provider
        if model_provider is None:
            base_provider = OllamaProvider(
                base_url=self.config['base_url'],
                model=self.config['model']
            )
            base_provider.configure(self.config['request'])
            self.provider = SimulationAwareProvider(base_provider)
        else:
            if isinstance(model_provider, SimulationAwareProvider):
                self.provider = model_provider
            else:
                self.provider = SimulationAwareProvider(model_provider)
        
        # Configure the provider
        self.provider.configure(self.config['request'])
        
        # Cache for precomputed responses
        self.response_cache_keys = {}
        self._precompute_lock = threading.Lock()
        
        logger.info(f"SimulationAwareAITriage initialized: {self.system_name} with strategy '{strategy}'")
    
    def precompute_patient_responses(self, patient_data_list):
        """
        Pre-compute LLM responses for a list of patients before simulation starts.
        This should be called before running the simulation.
        """
        logger.info(f"Pre-computing {self.strategy} LLM responses for {len(patient_data_list)} patients...")
        
        for i, patient_data in enumerate(patient_data_list):
            try:
                if self.strategy == "single":
                    self._precompute_single_agent_response(patient_data, i)
                elif self.strategy == "multi":
                    self._precompute_multi_agent_responses(patient_data, i)
                else:
                    raise ValueError(f"Unknown strategy: {self.strategy}")
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Submitted {i + 1}/{len(patient_data_list)} patients for pre-computation")
                    
            except Exception as e:
                logger.error(f"Error pre-computing response for patient {i}: {e}")
        
        logger.info(f"Pre-computation submitted for {len(patient_data_list)} patients")
        
        # Log cache statistics
        stats = self.provider.get_cache_stats()
        logger.info(f"Cache stats: {stats}")
    
    def _precompute_single_agent_response(self, patient_data, patient_index):
        """Pre-compute single agent LLM response"""
        # Use the new prompt function that accepts patient data directly
        prompt = get_single_agent_prompt(patient_data)
        
        cache_key = self.provider.precompute_response(
            prompt, 
            self.config.get('request', {}).get('options', {})
        )
        
        patient_id = patient_data.get('id', f'patient_{patient_index}')
        with self._precompute_lock:
            self.response_cache_keys[patient_id] = {'single': cache_key}
    
    def _precompute_multi_agent_responses(self, patient_data, patient_index):
        """Pre-compute multi-agent LLM responses"""
        patient_id = patient_data.get('id', f'patient_{patient_index}')
        
        # Pre-compute all three agent responses using new prompt functions
        cache_keys = {}
        
        try:
            # Pediatric assessment
            pediatric_prompt = get_pediatric_assessor_prompt(patient_data)
            cache_keys['pediatric'] = self.provider.precompute_response(
                pediatric_prompt,
                self.config.get('request', {}).get('options', {})
            )
            
            # Clinical assessment (will need pediatric results, but for precomputation we'll use empty)
            clinical_prompt = get_clinical_assessor_prompt(patient_data, "")
            cache_keys['clinical'] = self.provider.precompute_response(
                clinical_prompt,
                self.config.get('request', {}).get('options', {})
            )
            
            # Consensus coordinator (will need both assessments, but for precomputation we'll use basic prompt)
            consensus_prompt = get_consensus_coordinator_prompt()
            cache_keys['consensus'] = self.provider.precompute_response(
                consensus_prompt,
                self.config.get('request', {}).get('options', {})
            )
            
        except Exception as e:
            logger.error(f"Error pre-computing multi-agent responses for patient {patient_id}: {e}")
        
        with self._precompute_lock:
            self.response_cache_keys[patient_id] = cache_keys
    
    def _prepare_patient_context(self, patient_data):
        """Prepare patient context for LLM prompts"""
        # Handle different field names that might exist in patient data
        age = patient_data.get('age') or patient_data.get('patient_age', 'Unknown')
        gender = patient_data.get('gender', 'Unknown')
        chief_complaint = patient_data.get('chief_complaint', 'Not specified')
        
        # Handle vital signs - could be JSON string or dict
        vital_signs = patient_data.get('vital_signs', {})
        if isinstance(vital_signs, str):
            try:
                vital_signs = json.loads(vital_signs)
            except json.JSONDecodeError:
                vital_signs = {}
        
        # Extract individual vital signs with defaults
        heart_rate = vital_signs.get('heart_rate', 'Unknown')
        blood_pressure = vital_signs.get('blood_pressure', 'Unknown')
        temperature = vital_signs.get('temperature', 'Unknown')
        respiratory_rate = vital_signs.get('respiratory_rate', 'Unknown')
        oxygen_saturation = vital_signs.get('oxygen_saturation', 'Unknown')
        
        # Handle medical history
        medical_history = patient_data.get('medical_history', 'None reported')
        if isinstance(medical_history, list):
            medical_history = ', '.join(medical_history)
        
        # Calculate severity if not provided
        severity = patient_data.get('severity', 0.5)
        
        return {
            'patient_age': age,
            'age': age,  # Include both for compatibility
            'patient_gender': gender,  # For prompt template compatibility
            'gender': gender,
            'reason_description': chief_complaint,  # For prompt template compatibility
            'chief_complaint': chief_complaint,
            'patient_history': medical_history,  # For prompt template compatibility
            'medical_history': medical_history,
            'heart_rate': heart_rate,
            'blood_pressure': blood_pressure,
            'temperature': temperature,
            'respiratory_rate': respiratory_rate,
            'oxygen_saturation': oxygen_saturation,
            'severity': severity,
            'vital_signs': f"HR: {heart_rate}, BP: {blood_pressure}, Temp: {temperature}, RR: {respiratory_rate}, O2Sat: {oxygen_saturation}",
            'vital_signs_summary': f"HR: {heart_rate}, BP: {blood_pressure}, Temp: {temperature}, RR: {respiratory_rate}, O2Sat: {oxygen_saturation}",
            'clinical_context': json.dumps(patient_data, indent=2)  # For detailed context
        }
    
    def assign_priority(self, patient) -> int:
        """
        Assign priority using cached LLM response (simulation-time safe).
        This method is called during simulation and should return instantly.
        """
        try:
            # Get patient data
            patient_data = self._extract_patient_data(patient)
            patient_id = patient_data.get('id', getattr(patient, 'id', 'unknown'))
            
            # Get cached responses
            with self._precompute_lock:
                cache_keys = self.response_cache_keys.get(patient_id, {})
            
            if not cache_keys:
                logger.warning(f"No pre-computed responses for patient {patient_id}, using fallback")
                return self._get_fallback_priority(patient_data)
            
            if self.strategy == "single":
                return self._process_single_agent_response(patient_id, cache_keys, patient_data)
            elif self.strategy == "multi":
                return self._process_multi_agent_responses(patient_id, cache_keys, patient_data)
            else:
                logger.error(f"Unknown strategy: {self.strategy}")
                return self._get_fallback_priority(patient_data)
            
        except Exception as e:
            logger.error(f"Error in assign_priority for patient {getattr(patient, 'id', 'unknown')}: {e}")
            return self._get_fallback_priority(self._extract_patient_data(patient))
    
    def _process_single_agent_response(self, patient_id, cache_keys, patient_data):
        """Process single agent cached response"""
        cache_key = cache_keys.get('single')
        if not cache_key:
            logger.warning(f"No single agent cache key for patient {patient_id}")
            return self._get_fallback_priority(patient_data)
        
        cached_response = self.provider.get_cached_response(cache_key, timeout=5.0)
        if cached_response is None:
            logger.warning(f"Failed to retrieve single agent response for patient {patient_id}")
            return self._get_fallback_priority(patient_data)
        
        parsed_response = self._parse_llm_response(cached_response)
        if parsed_response is None:
            logger.warning(f"Failed to parse single agent response for patient {patient_id}")
            return self._get_fallback_priority(patient_data)
        
        priority = self._extract_priority_from_parsed_response(parsed_response)
        logger.debug(f"Patient {patient_id} assigned priority {priority} from single agent")
        return priority
    
    def _process_multi_agent_responses(self, patient_id, cache_keys, patient_data):
        """Process multi-agent cached responses"""
        agent_responses = {}
        
        # Collect all agent responses
        for agent_name in ['pediatric', 'clinical', 'consensus']:
            cache_key = cache_keys.get(agent_name)
            if cache_key:
                response = self.provider.get_cached_response(cache_key, timeout=5.0)
                if response:
                    parsed = self._parse_llm_response(response)
                    if parsed:
                        agent_responses[agent_name] = parsed
        
        if not agent_responses:
            logger.warning(f"No valid multi-agent responses for patient {patient_id}")
            return self._get_fallback_priority(patient_data)
        
        # Use consensus coordinator response if available, otherwise aggregate
        if 'consensus' in agent_responses:
            priority = self._extract_priority_from_parsed_response(agent_responses['consensus'])
        else:
            # Aggregate priorities from available agents
            priorities = []
            for agent_name, response in agent_responses.items():
                agent_priority = self._extract_priority_from_parsed_response(response)
                priorities.append(agent_priority)
            
            if priorities:
                # Use the most urgent (lowest number) priority
                priority = min(priorities)
            else:
                priority = self._get_fallback_priority(patient_data)
        
        logger.debug(f"Patient {patient_id} assigned priority {priority} from multi-agent ({len(agent_responses)} agents)")
        return priority
    
    def _extract_patient_data(self, patient) -> Dict[str, Any]:
        """Extract patient data dictionary from patient object"""
        if hasattr(patient, '__dict__'):
            return patient.__dict__.copy()
        else:
            return {'id': getattr(patient, 'id', 'unknown')}
    
    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse LLM response into structured data"""
        try:
            # Clean the response
            response = response.strip()
            
            # Try to parse as JSON first
            if response.startswith('{') and response.endswith('}'):
                return json.loads(response)
            
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Try to extract priority from text response
            priority_match = re.search(r'priority["\s]*:?["\s]*(\d+)', response, re.IGNORECASE)
            if priority_match:
                return {'priority': int(priority_match.group(1))}
            
            # Look for urgency levels
            urgency_patterns = [
                (r'immediate|resuscitation|priority\s*1', 1),
                (r'very\s*urgent|emergent|priority\s*2', 2),
                (r'urgent|priority\s*3', 3),
                (r'standard|less\s*urgent|priority\s*4', 4),
                (r'non[\s-]*urgent|priority\s*5', 5)
            ]
            
            for pattern, priority in urgency_patterns:
                if re.search(pattern, response, re.IGNORECASE):
                    return {'priority': priority}
            
            # Fallback: return raw response
            return {'raw_response': response, 'priority': 3}
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse LLM response: {e}. Response: {response[:100]}...")
            return {'raw_response': response, 'priority': 3}
    
    def _extract_priority_from_parsed_response(self, parsed_response: Dict[str, Any]) -> int:
        """Extract priority from parsed LLM response"""
        # Look for priority in various fields
        for field in ['priority', 'triage_priority', 'urgency_level', 'recommended_priority']:
            if field in parsed_response:
                try:
                    priority = int(parsed_response[field])
                    # Validate priority range
                    if 1 <= priority <= 5:
                        return priority
                except (ValueError, TypeError):
                    continue
        
        # Look in rationale or explanation text
        for field in ['rationale', 'explanation', 'reasoning', 'raw_response']:
            if field in parsed_response:
                text = str(parsed_response[field]).lower()
                if 'priority 1' in text or 'immediate' in text:
                    return 1
                elif 'priority 2' in text or 'very urgent' in text:
                    return 2
                elif 'priority 3' in text or 'urgent' in text:
                    return 3
                elif 'priority 4' in text or 'standard' in text:
                    return 4
                elif 'priority 5' in text or 'non-urgent' in text:
                    return 5
        
        # Default fallback
        logger.warning(f"Could not extract valid priority from response: {parsed_response}")
        return 3
    
    def _get_fallback_priority(self, patient_data: Dict[str, Any]) -> int:
        """Get fallback priority when LLM response is not available"""
        # Enhanced fallback logic based on available patient data
        age = patient_data.get('age', 50)
        severity = patient_data.get('severity', 0.5)
        chief_complaint = str(patient_data.get('chief_complaint', '')).lower()
        
        # Age-based risk factors
        high_risk_age = age < 2 or age > 80
        
        # Complaint-based urgency
        urgent_complaints = ['chest pain', 'difficulty breathing', 'unconscious', 'severe bleeding', 'stroke']
        is_urgent_complaint = any(complaint in chief_complaint for complaint in urgent_complaints)
        
        # Determine priority
        if high_risk_age and (severity > 0.7 or is_urgent_complaint):
            return 1  # Immediate
        elif high_risk_age or severity > 0.8 or is_urgent_complaint:
            return 2  # Very urgent
        elif severity > 0.6:
            return 3  # Urgent
        elif severity > 0.3:
            return 4  # Standard
        else:
            return 5  # Non-urgent
    
    def estimate_triage_time(self) -> float:
        """
        Estimate triage time based on strategy and LLM inference time statistics.
        This provides realistic timing without blocking simulation.
        """
        from src.config.config_manager import get_service_time_config
        service_config = get_service_time_config()
        base_time = service_config['triage']['mean']
        
        # Get estimated LLM inference time
        llm_time_seconds = self.provider.estimate_inference_time()
        llm_time_minutes = llm_time_seconds / 60.0
        
        # Strategy-specific time factors
        if self.strategy == "single":
            # Single LLM call + processing overhead
            strategy_factor = 1.5
            overhead_minutes = 0.5
        elif self.strategy == "multi":
            # Multiple LLM calls + coordination overhead
            strategy_factor = 2.0
            overhead_minutes = 1.0
        else:
            strategy_factor = 1.0
            overhead_minutes = 0.5
        
        # Calculate total time
        total_time = base_time + (llm_time_minutes * strategy_factor) + overhead_minutes
        
        # Add random variation
        import random
        import numpy as np
        variation = np.random.lognormal(0, 0.2)
        estimated_time = total_time * variation
        
        return max(1.0, estimated_time)  # Minimum 1 minute
    
    def perform_triage(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform triage assessment and return structured results"""
        # This method is called by assign_priority internally
        # For simulation-aware system, we use cached responses
        priority = self.assign_priority(type('Patient', (), patient_data)())
        
        return {
            'priority': priority,
            'rationale': f'Priority {priority} assigned by {self.system_name}',
            'recommended_actions': f'Follow priority {priority} protocols',
            'triage_system': self.system_name
        }
    
    def estimate_consult_time(self, priority: int) -> float:
        """Estimate consultation time based on priority"""
        from src.config.config_manager import get_service_time_config
        service_config = get_service_time_config()
        base_time = service_config['consultation']['mean']
        
        # Adjust based on priority (higher priority = longer consultation)
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
    
    def get_triage_system_name(self) -> str:
        """Get the name of the triage system"""
        return self.system_name
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get statistics about the response cache"""
        stats = self.provider.get_cache_stats()
        with self._precompute_lock:
            stats['precomputed_patients'] = len(self.response_cache_keys)
            stats['strategy'] = self.strategy
        return stats
    
    def shutdown(self):
        """Shutdown the provider and clean up resources"""
        logger.info(f"Shutting down {self.system_name}...")
        self.provider.shutdown()
        with self._precompute_lock:
            self.response_cache_keys.clear()
        logger.info(f"{self.system_name} shutdown complete")


# Convenience factory functions for creating specific triage systems
def create_single_llm_triage(model_provider=None) -> SimulationAwareAITriage:
    """Create a single LLM-based triage system"""
    return SimulationAwareAITriage(
        model_provider=model_provider,
        strategy="single",
        system_name="Single LLM-Based Triage System"
    )

def create_multi_agent_triage(model_provider=None) -> SimulationAwareAITriage:
    """Create a multi-agent LLM-based triage system"""
    return SimulationAwareAITriage(
        model_provider=model_provider,
        strategy="multi",
        system_name="Multi-Agent LLM-Based Triage System"
    )