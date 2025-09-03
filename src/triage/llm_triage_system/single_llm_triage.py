"""Single LLM Triage System

Implementation of single-agent LLM triage using the base class.
This is the standard implementation for single model triage decisions.
"""

import json
from typing import Dict, Any

from src.logger import logger
from .base_llm_triage import BaseLLMTriageSystem
from .config.system_prompts import get_full_triage_prompt
from src.models.triage_result import TriageResult


class SingleLLMTriage(BaseLLMTriageSystem):
    """
    Single-agent LLM triage system implementation.
    
    Uses a single language model to make triage decisions based on patient symptoms
    and operational context. This is the standard implementation for most use cases.
    """
    
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
            
            # Step 3: Query API
            logger.info(f"🔍 Step 3: Querying AI Model for Triage Decision")
            triage_data = self._query_single_model(prompt)
            
            # Step 4: Validate and log result
            logger.info(f"🔍 Step 4: Parsing AI Decision")
            self._validate_api_response(triage_data)
            self._log_triage_result(triage_data)
            
        except Exception as api_error:
            logger.error(f"❌ Triage failed: {api_error}")
            raise RuntimeError(f"Triage failed: {api_error}") from api_error
        
        # Return TriageResult object
        return TriageResult.from_llm_result(triage_data)
    
    def _query_single_model(self, prompt: str) -> Dict[str, Any]:
        """
        Query the single LLM model for triage decision.
        
        Args:
            prompt (str): Complete triage prompt
            
        Returns:
            Dict[str, Any]: Parsed JSON response from the model
            
        Raises:
            RuntimeError: If API call fails
            ValueError: If response is not valid JSON
        """
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            
            response_content = completion.choices[0].message.content
            logger.info(f"✅ AI Response received: {len(response_content)} chars")
            
        except Exception as api_call_error:
            logger.error(f"❌ Step 3 Failed: API call error - {api_call_error}")
            raise RuntimeError(f"HF API call failed: {api_call_error}") from api_call_error
        
        # Parse JSON response
        try:
            triage_data = json.loads(response_content)
            logger.info(f"📋 AI Decision parsed successfully")
            logger.info(f"🎯 Raw Decision: {json.dumps(triage_data, separators=(',', ':'))}")
            return triage_data
            
        except json.JSONDecodeError as json_error:
            logger.error(f"❌ Step 4 Failed: Invalid JSON response - {response_content[:200]}...")
            raise ValueError(f"Invalid JSON response: {json_error}") from json_error