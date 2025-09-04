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
            
            # Step 2: Build prompt with chat history context
            logger.info(f"🔍 Step 2: Building Clinical Prompt")
            chat_context = self._build_chat_context()
            prompt = get_full_triage_prompt(symptoms, operational_context + chat_context)
            logger.info(f"📝 Prompt generated: {len(prompt)} chars for model {self.model_name}")
            if chat_context:
                logger.info(f"🧠 Chat context included: {len(self.chat_history)} previous decisions")
            
            # Step 3: Query API with retry logic for malformed JSON
            logger.info(f"🔍 Step 3: Querying AI Model for Triage Decision")
            max_retries = 2
            json_result = None
            
            for attempt in range(max_retries + 1):
                if attempt > 0:
                    logger.warning(f"🔄 Retry attempt {attempt}/{max_retries} due to JSON parsing failure")
                    # Enhance prompt for retry with more explicit JSON requirements
                    prompt = self._enhance_prompt_for_retry(prompt, attempt)
                
                raw_response = self._query_single_model(prompt)
                
                # Step 4: Process JSON response with production handler
                logger.info(f"🔍 Step 4: Processing JSON Response (Attempt {attempt + 1})")
                json_result = self.json_handler.process_response(raw_response, retry_count=attempt)
                
                if json_result.quality != ResponseQuality.FAILED and json_result.data is not None:
                    break
                
                if attempt == max_retries:
                    error_msg = f"JSON processing failed after {max_retries + 1} attempts: {'; '.join(json_result.errors)}"
                    logger.error(f"❌ {error_msg}")
                    raise ValueError(error_msg)
            
            # Log quality metrics
            logger.info(f"✅ JSON processed (Quality: {json_result.quality.value}, Time: {json_result.processing_time_ms:.1f}ms)")
            if json_result.warnings:
                for warning in json_result.warnings:
                    logger.warning(f"⚠️  {warning}")
            
            triage_data = json_result.data
            self._log_triage_result(triage_data)
            
            # Step 5: Add to chat history for future context
            logger.info(f"🔍 Step 5: Adding to Chat History")
            self._add_to_chat_history(symptoms, operational_context, triage_data)
            
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
    
    def _enhance_prompt_for_retry(self, original_prompt: str, attempt: int) -> str:
        """Enhance prompt with stronger JSON formatting requirements for retry attempts.
        
        Args:
            original_prompt: The original prompt that failed
            attempt: Retry attempt number
            
        Returns:
            Enhanced prompt with stricter JSON requirements
        """
        retry_instructions = {
            1: "\n\n🚨 CRITICAL: Your previous response was not valid JSON. You MUST respond with ONLY a JSON object. No text before or after. Start with { and end with }.",
            2: "\n\n🚨 FINAL ATTEMPT: Respond with EXACTLY this format:\n{\"triage_category\": \"RED\", \"priority_score\": 1, \"confidence\": 0.9, \"reasoning\": \"Your reasoning here\", \"wait_time\": \"Immediate (0 min)\"}\n\nReplace values but keep exact structure. NO OTHER TEXT."
        }
        
        enhancement = retry_instructions.get(attempt, "")
        return original_prompt + enhancement
    
    # All JSON processing now handled by TriageJSONHandler