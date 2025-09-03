"""Single LLM Triage System

Implementation of single-agent LLM triage using the base class.
This is the standard implementation for single model triage decisions.
"""

from typing import Dict, Any

from src.logger import logger
from .base_llm_triage import BaseLLMTriageSystem
from .config.system_prompts import get_full_triage_prompt
from .json_handler import TriageJSONHandler, JSONProcessingResult, ResponseQuality
from src.models.triage_result import TriageResult


class SingleLLMTriage(BaseLLMTriageSystem):
    """
    Single-agent LLM triage system implementation.
    
    Uses a single language model to make triage decisions based on patient symptoms
    and operational context. This is the standard implementation for most use cases.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize Single LLM Triage System with JSON handler."""
        super().__init__(*args, **kwargs)
        self.json_handler = TriageJSONHandler(strict_mode=True)
    
    def triage_patient(self, symptoms: str) -> TriageResult:
        """
        Triage a patient using a single LLM.
        
        Args:
            symptoms (str): Patient symptoms description
            
        Returns:
            TriageResult: Triage result with category, priority, and reasoning
            
        Raises:
            ValueError: If symptoms are invalid or API response is malformed
            RuntimeError: If API call fails
        """
        logger.info(f"🩺 Starting LLM Triage Assessment")
        logger.info(f"📋 Patient Symptoms: {symptoms[:80]}{'...' if len(symptoms) > 80 else ''}")
        
        # Validate input
        self._validate_symptoms(symptoms)
        
        try:
            # Step 1: Generate operational context
            logger.info(f"🔍 Step 1: Gathering Operational Context")
            operational_context = ""
            if self.operation_metrics and self.nhs_metrics:
                current_time = 0.0
                if self.operation_metrics.system_snapshots:
                    current_time = self.operation_metrics.system_snapshots[-1].timestamp
                operational_context = self._generate_operational_context(current_time)
                logger.info(f"📊 Operational context included: {len(operational_context)} chars")
            else:
                logger.info(f"📊 No operational context available")
            
            # Step 2: Build prompt
            logger.info(f"🔍 Step 2: Building Clinical Prompt")
            prompt = get_full_triage_prompt(symptoms, operational_context)
            logger.info(f"📝 Prompt generated: {len(prompt)} chars for model {self.model_name}")
            
            # Step 3: Query API and process response
            logger.info(f"🔍 Step 3: Querying AI Model for Triage Decision")
            raw_response = self._query_single_model(prompt)
            
            # Step 4: Process JSON response with production handler
            logger.info(f"🔍 Step 4: Processing JSON Response")
            json_result = self.json_handler.process_response(raw_response)
            
            if json_result.quality == ResponseQuality.FAILED or json_result.data is None:
                error_msg = f"JSON processing failed: {'; '.join(json_result.errors)}"
                logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)
            
            # Log quality metrics
            logger.info(f"✅ JSON processed (Quality: {json_result.quality.value}, Time: {json_result.processing_time_ms:.1f}ms)")
            if json_result.warnings:
                for warning in json_result.warnings:
                    logger.warning(f"⚠️  {warning}")
            
            triage_data = json_result.data
            self._log_triage_result(triage_data)
            
        except Exception as api_error:
            logger.error(f"❌ Triage failed: {api_error}")
            raise RuntimeError(f"Triage failed: {api_error}") from api_error
        
        # Return TriageResult object
        return TriageResult.from_llm_result(triage_data)
    
    def _query_single_model(self, prompt: str) -> str:
        """
        Query the single LLM model for triage decision.
        
        Args:
            prompt (str): Complete triage prompt
            
        Returns:
            str: Raw response content from the model
            
        Raises:
            RuntimeError: If API call fails
        """
        try:
            # Use response_format for strict JSON when supported
            api_params = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "max_tokens": 500,  # Limit response length
            }
            
            # Add JSON mode for supported models
            if "gpt" in self.model_name.lower() or "claude" in self.model_name.lower():
                api_params["response_format"] = {"type": "json_object"}
            
            completion = self.client.chat.completions.create(**api_params)
            
            response_content = completion.choices[0].message.content
            logger.info(f"✅ AI Response received: {len(response_content)} chars")
            logger.debug(f"🔍 Raw response: {response_content[:200]}...")
            
            return response_content
            
        except Exception as api_call_error:
            logger.error(f"❌ API call failed: {api_call_error}")
            raise RuntimeError(f"HF API call failed: {api_call_error}") from api_call_error
    
    # All JSON processing now handled by TriageJSONHandler