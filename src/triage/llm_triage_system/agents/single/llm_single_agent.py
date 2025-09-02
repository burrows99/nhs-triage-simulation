"""Single Agent LLM Triage System

Implements a single AI agent that performs comprehensive triage assessment
following NHS guidelines while potentially outperforming traditional MTS.
"""

import json
import numpy as np
from typing import Dict, List, Any, Optional
from ..base_agent import BaseTriageAgent
from src.services.ollama_service import OllamaService
from src.logger import logger


class LLMSingleTriageAgent(BaseTriageAgent):
    """Single LLM agent for comprehensive triage assessment"""
    
    def __init__(self, model_name: str = "llama3.2:1b", temperature: float = 0.1, 
                 ollama_url: str = "http://localhost:11434"):
        """Initialize the single LLM triage agent
        
        Args:
            model_name: Name of the LLM model to use
            temperature: Temperature for LLM generation (lower = more consistent)
            ollama_url: URL for Ollama service
        """
        super().__init__(f"llm_single_{model_name}")
        self.model_name = model_name
        self.temperature = temperature
        self.ollama_url = ollama_url
        
        # Initialize Ollama service
        logger.debug(f"Initializing Ollama service at {ollama_url}")
        self.llm_service = OllamaService(base_url=ollama_url)
        
        # Check LLM service availability
        self.llm_available = self._check_llm_availability()
        
        # NHS-compliant system prompt
        self.system_prompt = self._create_system_prompt()
        
        logger.info(f"LLM Single Agent initialized - Model: {model_name}, Available: {self.llm_available}")
    
    def _check_llm_availability(self) -> bool:
        """Check if LLM service is available and model exists
        
        Returns:
            True if LLM service and model are available
        """
        try:
            logger.debug("Checking LLM service availability")
            
            # Check service health
            if not self.llm_service.check_health():
                logger.warning("Ollama service health check failed")
                return False
            
            # Check if model is available
            models = self.llm_service.list_models()
            available_models = [m.get('name', '') for m in models.get('models', [])]
            
            if self.model_name in available_models:
                logger.info(f"Model {self.model_name} is available")
                return True
            else:
                logger.warning(f"Model {self.model_name} not found. Available models: {available_models}")
                logger.info(f"Attempting to pull model {self.model_name}")
                
                # Try to pull the model
                if self.llm_service.pull_model(self.model_name):
                    logger.info(f"Model {self.model_name} pulled successfully")
                    return True
                else:
                    logger.error(f"Failed to pull model {self.model_name}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error checking LLM availability: {e}")
            return False
    
    def _create_system_prompt(self) -> str:
        """Create NHS-compliant system prompt for dynamic triage assessment"""
        return """You are an expert emergency department triage nurse with extensive clinical experience and advanced AI-assisted decision-making capabilities. Your role is to perform comprehensive triage assessment considering patient data, clinical context, and resource availability.

NHS TRIAGE CATEGORIES:
- RED (Priority 1): Immediate life-threatening conditions requiring instant attention
- ORANGE (Priority 2): Very urgent conditions, maximum 10-minute wait
- YELLOW (Priority 3): Urgent conditions, maximum 60-minute wait  
- GREEN (Priority 4): Less urgent conditions, maximum 120-minute wait
- BLUE (Priority 5): Non-urgent conditions, maximum 240-minute wait

DYNAMIC ASSESSMENT FRAMEWORK:
1. PATIENT DATA ANALYSIS: Consider demographics, comorbidities, medication history, and social factors
2. CLINICAL PRESENTATION: Assess symptom patterns, severity, progression, and vital signs
3. CONTEXTUAL FACTORS: Account for time of presentation, patient anxiety, and communication barriers
4. RESOURCE AWARENESS: Consider current ED capacity, specialist availability, and diagnostic resources
5. RISK STRATIFICATION: Evaluate deterioration risk, safety netting requirements, and follow-up needs
6. HOLISTIC JUDGMENT: Apply clinical reasoning that transcends rigid protocol limitations

CORE PRINCIPLES:
- Prioritize patient safety above all other considerations
- Use evidence-based clinical reasoning with flexibility for complex presentations
- Consider the full spectrum of patient needs, not just immediate symptoms
- Optimize resource utilization while maintaining quality of care
- Adapt assessment based on real-time ED conditions and capacity
- Apply advanced pattern recognition to identify subtle but significant clinical indicators

You have the capability to outperform traditional triage systems by integrating multiple data sources and applying sophisticated clinical reasoning. Make decisions that reflect expert clinical judgment enhanced by AI capabilities.

Respond ONLY with a valid JSON object containing your comprehensive triage assessment."""
    
    def triage_patient(self, symptoms: Dict[str, Any], patient_data: Dict[str, Any], 
                          resource_status: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform comprehensive triage assessment using AI-driven analysis
        
        Args:
            symptoms: Dictionary of patient symptoms and their severity
            patient_data: Additional patient information (age, gender, etc.)
            resource_status: Current ED resource availability and capacity
            
        Returns:
            Dictionary containing triage results in the specified format
        """
        logger.info(f"Starting triage assessment for patient with symptoms: {list(symptoms.keys())}")
        logger.debug(f"Patient data: age={patient_data.get('age')}, gender={patient_data.get('gender')}, complaint='{patient_data.get('presenting_complaint')}'")
        
        if resource_status:
            logger.debug(f"Resource status provided: {resource_status}")
        else:
            logger.warning("No resource status provided - assessment will proceed without ED context")
        
        # Prepare comprehensive patient information for AI assessment
        logger.debug("Formatting patient information for AI assessment")
        patient_info = self._format_patient_info(symptoms, patient_data, resource_status)
        logger.debug(f"Patient info formatted: {len(patient_info)} characters")
        
        # Create the dynamic assessment prompt
        logger.debug("Creating dynamic assessment prompt")
        assessment_prompt = self._create_assessment_prompt(patient_info)
        logger.debug(f"Assessment prompt created: {len(assessment_prompt)} characters")
        
        # Get LLM assessment (no fallback - fail if LLM unavailable)
        logger.info("Requesting LLM assessment")
        llm_response = self._get_llm_assessment(assessment_prompt)
        logger.debug(f"LLM response received: {len(llm_response)} characters")
        
        # Parse and validate response
        logger.debug("Parsing LLM response")
        triage_result = self._parse_llm_response(llm_response, symptoms, patient_data)
        
        logger.info(f"Triage assessment completed: {triage_result.get('triage_category')} category, {triage_result.get('flowchart_used')} domain")
        logger.debug(f"Full triage result: {triage_result}")
        
        return triage_result
    
    def _format_patient_info(self, symptoms: Dict[str, Any], patient_data: Dict[str, Any], 
                            resource_status: Optional[Dict[str, Any]] = None) -> str:
        """Format comprehensive patient information for AI assessment"""
        info_parts = []
        
        # Patient demographics
        age = patient_data.get('age', 'Unknown')
        gender = patient_data.get('gender', 'Unknown')
        info_parts.append(f"Patient: {age} years old, {gender}")
        
        # Chief complaint
        complaint = patient_data.get('presenting_complaint', 'General complaint')
        info_parts.append(f"Chief Complaint: {complaint}")
        
        # Symptoms with severity
        if symptoms:
            info_parts.append("Symptoms:")
            for symptom, severity in symptoms.items():
                if severity and severity != 'none':
                    info_parts.append(f"- {symptom.replace('_', ' ').title()}: {severity}")
        
        # Vital signs if available
        vital_signs = patient_data.get('vital_signs', {})
        if vital_signs and isinstance(vital_signs, dict):
            numeric_values = vital_signs.get('numeric_values', [])
            if numeric_values and len(numeric_values) >= 5:
                info_parts.append("Vital Signs:")
                info_parts.append(f"- Pain Score: {numeric_values[0]}/10")
                info_parts.append(f"- Blood Pressure: {numeric_values[1]} mmHg (systolic)")
                info_parts.append(f"- Heart Rate: {numeric_values[2]} bpm")
                info_parts.append(f"- Temperature: {numeric_values[3]}°C")
                info_parts.append(f"- Respiratory Rate: {numeric_values[4]} breaths/min")
        
        # Medical history
        conditions = patient_data.get('conditions', [])
        if conditions:
            info_parts.append(f"Medical History: {', '.join(conditions[:3])}")
        
        # Patient context from get_context() if available
        if hasattr(patient_data, 'get') and 'context' in patient_data:
            context = patient_data['context']
            if context:
                info_parts.append("\nPatient Context:")
                # Include relevant context data (medications, procedures, etc.)
                for key, value in context.items():
                    if isinstance(value, list) and len(value) > 0:
                        info_parts.append(f"- {key.replace('_', ' ').title()}: {len(value)} records")
        
        # Resource status and ED context
        if resource_status:
            info_parts.append("\nCurrent ED Status:")
            
            # Resource availability
            if 'resources' in resource_status:
                resources = resource_status['resources']
                info_parts.append("Resource Availability:")
                for resource, data in resources.items():
                    if isinstance(data, dict):
                        available = data.get('available', 0)
                        total = data.get('total', 0)
                        utilization = (total - available) / total * 100 if total > 0 else 0
                        info_parts.append(f"- {resource.title()}: {available}/{total} available ({utilization:.0f}% utilized)")
            
            # Queue lengths
            if 'queue_lengths' in resource_status:
                queues = resource_status['queue_lengths']
                info_parts.append("Current Queue Lengths:")
                for queue, length in queues.items():
                    info_parts.append(f"- {queue.replace('_', ' ').title()}: {length} patients waiting")
            
            # ED capacity and flow
            if 'capacity_status' in resource_status:
                capacity = resource_status['capacity_status']
                info_parts.append(f"ED Capacity: {capacity.get('current_load', 'Unknown')}")
                if 'average_wait_time' in capacity:
                    info_parts.append(f"Average Wait Time: {capacity['average_wait_time']} minutes")
        
        return "\n".join(info_parts)
    
    def _create_assessment_prompt(self, patient_info: str) -> str:
        """Create the dynamic assessment prompt for AI evaluation"""
        return f"""Please perform a comprehensive triage assessment for this patient using advanced clinical reasoning:

{patient_info}

Conduct a thorough evaluation considering:
1. Clinical presentation and symptom severity
2. Patient demographics and medical history
3. Current ED resource availability and capacity
4. Risk stratification and deterioration potential
5. Optimal resource allocation and patient flow

Provide your assessment as a JSON object with the following structure:
{{
    "clinical_domain": "<primary_clinical_domain>",
    "triage_category": "<RED|ORANGE|YELLOW|GREEN|BLUE>",
    "wait_time": "<immediate|10 min|60 min|120 min|240 min>",
    "clinical_reasoning": "<comprehensive_explanation_of_decision>",
    "severity_assessment": "<overall_severity_score_1_to_10>",
    "risk_factors": ["<list_of_key_risk_factors>"],
    "resource_considerations": "<how_resource_status_influenced_decision>",
    "safety_netting": "<follow_up_and_monitoring_requirements>"
}}

Apply sophisticated clinical judgment that integrates all available data sources. Your decision should reflect expert-level triage assessment enhanced by AI capabilities, potentially exceeding traditional protocol-based systems while maintaining NHS safety standards."""
    
    def _get_llm_assessment(self, prompt: str) -> str:
        """Get assessment from LLM service - no fallbacks, detailed logging"""
        logger.debug(f"LLM assessment request - model: {self.model_name}, temperature: {self.temperature}")
        logger.debug(f"LLM available flag: {self.llm_available}")
        
        if not self.llm_available:
            logger.error("LLM service is not available - cannot perform assessment")
            logger.error("No fallback mechanism - triage assessment will fail")
            raise RuntimeError("LLM service unavailable and no fallback configured")
        
        logger.info(f"Calling LLM service with model: {self.model_name}")
        logger.debug(f"System prompt length: {len(self.system_prompt)} characters")
        logger.debug(f"User prompt length: {len(prompt)} characters")
        
        try:
            logger.debug("Sending request to Ollama service")
            response = self.llm_service.generate_response(
                prompt=prompt,
                system_prompt=self.system_prompt,
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=500
            )
            
            logger.info("LLM response received successfully")
            logger.debug(f"Response length: {len(response)} characters")
            
            return response
            
        except Exception as e:
            logger.error(f"LLM service call failed: {type(e).__name__}: {e}")
            logger.error("Triage assessment cannot continue without LLM service")
            raise RuntimeError(f"LLM assessment failed: {e}") from e
    
    def _parse_llm_response(self, llm_response: str, symptoms: Dict[str, Any], patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse LLM response and format according to required structure - no fallbacks"""
        logger.debug("Starting LLM response parsing")
        logger.debug(f"Raw LLM response: {llm_response[:200]}..." if len(llm_response) > 200 else f"Raw LLM response: {llm_response}")
        
        # Extract JSON from response
        logger.debug("Searching for JSON structure in LLM response")
        json_start = llm_response.find('{')
        json_end = llm_response.rfind('}') + 1
        
        logger.debug(f"JSON boundaries: start={json_start}, end={json_end}")
        
        if json_start == -1 or json_end == 0:
            logger.error("No JSON structure found in LLM response")
            logger.error(f"Response content: {llm_response}")
            raise ValueError("LLM response does not contain valid JSON structure")
        
        json_str = llm_response[json_start:json_end]
        logger.debug(f"Extracted JSON string: {json_str}")
        
        try:
            llm_result = json.loads(json_str)
            logger.debug(f"Successfully parsed JSON: {llm_result}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Invalid JSON string: {json_str}")
            raise ValueError(f"Invalid JSON in LLM response: {e}") from e
        
        # Validate required fields
        required_fields = ['clinical_domain', 'triage_category', 'severity_assessment']
        missing_fields = [field for field in required_fields if field not in llm_result]
        
        if missing_fields:
            logger.error(f"Missing required fields in LLM response: {missing_fields}")
            logger.error(f"Available fields: {list(llm_result.keys())}")
            raise KeyError(f"LLM response missing required fields: {missing_fields}")
        
        # Extract and validate key information
        logger.debug("Extracting key information from parsed response")
        
        triage_category = llm_result.get('triage_category')
        logger.debug(f"Extracted triage category: {triage_category}")
        
        if triage_category not in ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE']:
            logger.error(f"Invalid triage category: {triage_category}")
            raise ValueError(f"Invalid triage category '{triage_category}' - must be RED, ORANGE, YELLOW, GREEN, or BLUE")
        
        clinical_domain = llm_result.get('clinical_domain')
        logger.debug(f"Extracted clinical domain: {clinical_domain}")
        
        try:
            severity_score = float(llm_result.get('severity_assessment'))
            logger.debug(f"Extracted severity score: {severity_score}")
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid severity assessment: {llm_result.get('severity_assessment')}")
            raise ValueError(f"Invalid severity assessment - must be numeric: {e}") from e
        
        if not (1.0 <= severity_score <= 10.0):
            logger.warning(f"Severity score {severity_score} outside expected range 1-10")
        
        # Process symptoms for output format
        logger.debug("Processing symptoms for output format")
        symptoms_processed = self._process_symptoms_for_output(symptoms)
        logger.debug(f"Processed {len(symptoms_processed)} symptoms")
        
        # Generate numeric inputs
        logger.debug("Generating numeric inputs")
        numeric_inputs = self._generate_numeric_inputs(patient_data, severity_score)
        logger.debug(f"Generated {len(numeric_inputs)} numeric inputs: {numeric_inputs}")
        
        # Calculate fuzzy score based on severity and symptoms
        logger.debug("Calculating fuzzy score")
        fuzzy_score = self._calculate_fuzzy_score(severity_score, symptoms_processed)
        logger.debug(f"Calculated fuzzy score: {fuzzy_score}")
        
        # Format final result (maintaining compatibility with expected format)
        logger.debug("Formatting final result")
        result = {
            'flowchart_used': clinical_domain,  # Using clinical_domain for compatibility
            'triage_category': np.str_(triage_category),
            'wait_time': np.str_(self._get_wait_time(triage_category)),
            'fuzzy_score': fuzzy_score,
            'symptoms_processed': symptoms_processed,
            'numeric_inputs': numeric_inputs,
            'priority_score': np.int64(self._calculate_priority_score(triage_category))
        }
        
        logger.debug(f"Final result formatted: {result}")
        logger.info("LLM response parsing completed successfully")
        
        return result
    
    def _process_symptoms_for_output(self, symptoms: Dict[str, Any]) -> Dict[str, str]:
        """Process symptoms into the required output format"""
        processed = {}
        
        # Map common symptoms to severity levels
        severity_mapping = {
            'none': 'none',
            'mild': 'mild',
            'moderate': 'moderate', 
            'severe': 'severe',
            'very_severe': 'very_severe'
        }
        
        for symptom, value in symptoms.items():
            if value and value != 'none':
                # Map to standard severity levels
                if isinstance(value, str) and value.lower() in severity_mapping:
                    processed[symptom] = severity_mapping[value.lower()]
                elif isinstance(value, (int, float)):
                    # Convert numeric to severity
                    if value >= 8:
                        processed[symptom] = 'very_severe'
                    elif value >= 6:
                        processed[symptom] = 'severe'
                    elif value >= 4:
                        processed[symptom] = 'moderate'
                    elif value >= 2:
                        processed[symptom] = 'mild'
                    else:
                        processed[symptom] = 'none'
                else:
                    processed[symptom] = 'moderate'  # Default
        
        return processed
    
    def _generate_numeric_inputs(self, patient_data: Dict[str, Any], severity_score: float) -> List[float]:
        """Generate numeric inputs array"""
        # Try to get vital signs from patient data
        vital_signs = patient_data.get('vital_signs', {})
        numeric_values = vital_signs.get('numeric_values', []) if isinstance(vital_signs, dict) else []
        
        if len(numeric_values) >= 5:
            return [float(x) for x in numeric_values[:5]]
        
        # Generate based on severity score and patient data
        age = patient_data.get('age', 30)
        
        # Estimate values based on severity and age
        pain_score = min(10.0, severity_score)
        systolic_bp = 120 + (severity_score - 5) * 5  # Varies with severity
        heart_rate = 70 + (severity_score - 5) * 8    # Increases with severity
        temperature = 36.5 + (severity_score - 5) * 0.3  # Slight increase with severity
        resp_rate = 16 + (severity_score - 5) * 2      # Increases with severity
        
        return [pain_score, systolic_bp, heart_rate, temperature, resp_rate]
    
    def _calculate_fuzzy_score(self, severity_score: float, symptoms_processed: Dict[str, str]) -> float:
        """Calculate fuzzy score based on severity and symptoms"""
        # Base score from severity
        base_score = severity_score / 2.0  # Scale to roughly 0-5 range
        
        # Adjust based on number and severity of symptoms
        symptom_weight = 0
        severity_weights = {
            'very_severe': 1.0,
            'severe': 0.8,
            'moderate': 0.5,
            'mild': 0.2,
            'none': 0
        }
        
        for symptom, severity in symptoms_processed.items():
            symptom_weight += severity_weights.get(severity, 0.3)
        
        # Combine base score with symptom weight
        fuzzy_score = (base_score + symptom_weight * 0.3) / 1.3
        
        return round(fuzzy_score, 6)
    
    # Fallback assessment method removed - no fallbacks allowed
    # System will fail gracefully if LLM service is unavailable