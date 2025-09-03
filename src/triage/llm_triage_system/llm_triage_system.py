import json
import os
from typing import Dict, Any
from openai import OpenAI

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
import numpy as np

from src.logger import logger
from .config.system_prompts import get_system_prompt, get_triage_categories, get_wait_time_for_category, get_full_triage_prompt
from src.models.triage_result import TriageResult

HF_API_KEY = os.getenv('HF_API_KEY', 'your-huggingface-api-key-here')
HF_BASE_URL = os.getenv('HF_BASE_URL', 'https://router.huggingface.co/v1')
HF_MODEL = os.getenv('HF_MODEL', 'openai/gpt-oss-120b:together')



class LLMTriageSystem:
    """
    LLM-based triage system using Hugging Face API for medical text classification.
    
    This system uses the Hugging Face router API to access advanced language models
    for NHS-compliant triage recommendations.
    """
    
    def __init__(self, model_name: str = HF_MODEL, operation_metrics=None, nhs_metrics=None):
        """
        Initialize the LLM Triage System with Hugging Face API.
        
        Args:
            model_name (str): Model identifier for the Hugging Face API
            operation_metrics: OperationMetrics instance for operational context
            nhs_metrics: NHSMetrics instance for patient flow context
        """
        self.model_name = model_name
        self.operation_metrics = operation_metrics
        self.nhs_metrics = nhs_metrics
        logger.info(f"🤖 Initializing LLM Triage System: {model_name}")
        
        try:
            self.client = OpenAI(
                base_url=HF_BASE_URL,
                api_key=HF_API_KEY,
            )
            logger.info(f"✅ LLM Triage System ready")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM system: {e}")
            raise RuntimeError(f"Failed to initialize LLM system: {e}") from e
        
        # Initialize triage categories mapping
        self.triage_categories = get_triage_categories()




    def triage_patient(self, symptoms: str) -> TriageResult:
        """
        Triage a patient using the Hugging Face API.
        
        Args:
            symptoms (str): Patient symptoms
            
        Returns:
            TriageResult: Triage result object with category, priority, and reasoning
            
        Raises:
            ValueError: If API call fails
            RuntimeError: If client is not initialized
        """
        logger.info(f"🩺 Triaging patient: {symptoms[:80]}{'...' if len(symptoms) > 80 else ''}")
        
        if not symptoms or not symptoms.strip():
            logger.error("❌ Empty symptoms provided")
            raise ValueError("Empty symptoms provided to LLM triage system")
        
        try:
            operational_context = ""
            if self.operation_metrics and self.nhs_metrics:
                current_time = 0.0
                if self.operation_metrics.system_snapshots:
                    current_time = self.operation_metrics.system_snapshots[-1].timestamp
                operational_context = self._generate_operational_context(current_time)
                logger.debug(f"📊 Added operational context ({len(operational_context)} chars)")
            
            prompt = get_full_triage_prompt(symptoms, operational_context)
            logger.debug(f"🔍 API Request: {self.model_name} ({len(prompt)} chars)")
            
            try:
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0
                )
                
                response_content = completion.choices[0].message.content
                logger.debug(f"📨 API Response: {len(response_content)} chars")
                
            except Exception as api_call_error:
                logger.error(f"❌ API call failed: {api_call_error}")
                raise RuntimeError(f"HF API call failed: {api_call_error}") from api_call_error
            
            try:
                triage_data = json.loads(response_content)
                logger.debug(f"📋 Parsed: {json.dumps(triage_data, separators=(',', ':'))}")
            except json.JSONDecodeError as json_error:
                logger.error(f"❌ Invalid JSON response: {response_content[:200]}...")
                raise ValueError(f"Invalid JSON response: {json_error}") from json_error
            
            required_fields = ["triage_category", "priority_score", "confidence", "reasoning", "wait_time"]
            missing_fields = [field for field in required_fields if field not in triage_data]
            if missing_fields:
                logger.error(f"❌ Missing fields: {missing_fields}")
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            valid_categories = get_triage_categories()
            if triage_data["triage_category"] not in valid_categories:
                logger.error(f"❌ Invalid category: {triage_data['triage_category']}")
                raise ValueError(f"Invalid triage category: {triage_data['triage_category']}")
            
            try:
                triage_data["priority_score"] = int(triage_data["priority_score"])
                triage_data["confidence"] = float(triage_data["confidence"])
            except (ValueError, TypeError) as type_error:
                logger.error(f"❌ Invalid data types: {type_error}")
                raise ValueError(f"Invalid data types: {type_error}") from type_error
            
            logger.info(f"✅ {triage_data['triage_category']} (P{triage_data['priority_score']}) - {triage_data['confidence']:.0%} confidence")
                
        except Exception as api_error:
            logger.error(f"❌ Triage failed: {api_error}")
            raise RuntimeError(f"Triage failed: {api_error}") from api_error
        
        # Return TriageResult object using from_llm_result class method
        return TriageResult.from_llm_result(triage_data)
    
    def _generate_operational_context(self, current_time: float) -> str:
        """Generate operational context string from existing metrics classes
        
        Args:
            current_time: Current simulation time
            
        Returns:
            Formatted operational context string
        """
        if not self.operation_metrics or not self.nhs_metrics:
            return "\n📊 OPERATIONAL CONTEXT: Not available (metrics not provided)\n"
        
        try:
            # Get latest operational data
            operation_data = self.operation_metrics.calculate_metrics()
            nhs_data = self.nhs_metrics.calculate_metrics()
            
            # Get latest system snapshot
            latest_snapshot = None
            if self.operation_metrics.system_snapshots:
                latest_snapshot = self.operation_metrics.system_snapshots[-1]
            
            context = f"\n📊 CURRENT HOSPITAL OPERATIONAL STATUS (Time: {current_time:.1f}min):\n\n"
            
            # Resource utilization
            if latest_snapshot:
                context += "🏥 RESOURCE UTILIZATION:\n"
                for resource in latest_snapshot.resource_usage:
                    utilization = latest_snapshot.get_utilization(resource)
                    queue_len = latest_snapshot.queue_lengths.get(resource, 0)
                    status = self._get_utilization_status(utilization)
                    context += f"• {resource.title()}: {utilization:.1f}% {status} (Queue: {queue_len} patients)\n"
            
            # Wait times
            if 'wait_times' in operation_data:
                context += "\n⏰ CURRENT WAIT TIMES:\n"
                for resource, data in operation_data['wait_times'].items():
                    avg_wait = data.get('average_wait_time_minutes', 0.0)
                    max_wait = data.get('max_wait_time_minutes', 0.0)
                    context += f"• {resource.title()}: {avg_wait:.1f}min avg (peak: {max_wait:.1f}min)\n"
            
            # System pressure assessment
            system_pressure = self._assess_system_pressure(latest_snapshot, operation_data)
            context += f"\n🚦 SYSTEM PRESSURE: {system_pressure}\n"
            
            # Current patient load
            current_load = len(self.nhs_metrics.active_records)
            context += f"👥 CURRENT PATIENT LOAD: {current_load} patients in system\n"
            
            # Recent triage distribution
            triage_dist = nhs_data.get('triage_category_distribution', {})
            if triage_dist:
                context += "\n📊 RECENT TRIAGE DISTRIBUTION:\n"
                total_triaged = sum(triage_dist.values())
                for category, count in triage_dist.items():
                    if total_triaged > 0:
                        percentage = (count / total_triaged) * 100
                        context += f"• {category}: {count} patients ({percentage:.1f}%)\n"
            
            # Operational guidance
            guidance = self._generate_operational_guidance(latest_snapshot, operation_data)
            if guidance:
                context += f"\n💡 OPERATIONAL GUIDANCE:\n{guidance}\n"
            
            context += "\n⚠️ IMPORTANT: Use this operational context to inform wait time estimates and triage decisions based on CURRENT hospital conditions, not just clinical guidelines.\n"
            
            return context
            
        except Exception as e:
            logger.debug(f"⚠️ Operational context error: {e}")
            return "\n📊 OPERATIONAL CONTEXT: Not available\n"
    
    def _get_utilization_status(self, utilization: float) -> str:
        """Get utilization status indicator"""
        if utilization >= 95:
            return "🔴 CRITICAL"
        elif utilization >= 80:
            return "🟡 HIGH"
        elif utilization >= 60:
            return "🟢 MODERATE"
        else:
            return "🔵 LOW"
    
    def _assess_system_pressure(self, snapshot, operation_data) -> str:
        """Assess overall system pressure level"""
        if not snapshot:
            return "UNKNOWN"
        
        # Calculate average utilization
        utilizations = [snapshot.get_utilization(r) for r in snapshot.resource_usage]
        avg_utilization = sum(utilizations) / len(utilizations) if utilizations else 0
        
        # Get maximum queue length
        max_queue = max(snapshot.queue_lengths.values()) if snapshot.queue_lengths else 0
        
        # Determine pressure level
        if avg_utilization >= 95 or max_queue >= 20:
            return "CRITICAL - System at maximum capacity"
        elif avg_utilization >= 85 or max_queue >= 15:
            return "HIGH - Significant resource strain"
        elif avg_utilization >= 70 or max_queue >= 8:
            return "MODERATE - Manageable load"
        else:
            return "LOW - Normal operations"
    
    def _generate_operational_guidance(self, snapshot, operation_data) -> str:
        """Generate operational guidance based on current conditions"""
        if not snapshot:
            return ""
        
        guidance = []
        
        # Check for high utilization resources
        for resource in snapshot.resource_usage:
            utilization = snapshot.get_utilization(resource)
            queue_len = snapshot.queue_lengths.get(resource, 0)
            
            if utilization >= 90:
                guidance.append(f"• {resource.title()} at {utilization:.1f}% capacity - expedite appropriate cases")
            elif queue_len >= 15:
                guidance.append(f"• {resource.title()} has {queue_len} patients waiting - prioritize urgent cases")
        
        # System-wide guidance
        utilizations = [snapshot.get_utilization(r) for r in snapshot.resource_usage]
        avg_utilization = sum(utilizations) / len(utilizations) if utilizations else 0
        
        if avg_utilization >= 85:
            guidance.append("• High system load - use strict triage criteria and consider discharge planning")
        
        return "\n".join(guidance) if guidance else "• System operating within normal parameters"
    
    def _map_prediction_to_triage(self, prediction: str, confidence: float, symptoms: str) -> dict:
        """
        Map BioClinicalBERT model prediction to triage result format.
        
        Args:
            prediction (str): Model prediction (triage category)
            confidence (float): Prediction confidence score
            symptoms (str): Original symptoms text
            
        Returns:
            dict: Formatted triage result
        """
        logger.info(f"🔄 Mapping transformer prediction '{prediction}' to triage format...")
        
        # Map transformer prediction to standard triage categories
        # The BioClinicalBERT-Triage model may output different label formats
        # We need to map them to NHS triage categories (RED, ORANGE, YELLOW, GREEN, BLUE)
        
        # Create mapping from model labels to triage categories
        label_mapping = {
            # Common triage labels
            'URGENT': 'RED',
            'EMERGENCY': 'RED', 
            'IMMEDIATE': 'RED',
            'VERY_URGENT': 'ORANGE',
            'SEMI_URGENT': 'YELLOW',
            'STANDARD': 'GREEN',
            'NON_URGENT': 'BLUE',
            'LOW_PRIORITY': 'BLUE',
            # Direct NHS categories (if model already outputs them)
            'RED': 'RED',
            'ORANGE': 'ORANGE', 
            'YELLOW': 'YELLOW',
            'GREEN': 'GREEN',
            'BLUE': 'BLUE',
            # Numeric labels (some models use 0-4)
            '0': 'RED',    # Highest priority
            '1': 'ORANGE',
            '2': 'YELLOW', 
            '3': 'GREEN',
            '4': 'BLUE',   # Lowest priority
            # Alternative labels
            'HIGH': 'ORANGE',
            'MEDIUM': 'YELLOW',
            'LOW': 'GREEN'
        }
        
        # Normalize prediction and map to triage category
        normalized_prediction = str(prediction).upper().strip()
        triage_category = label_mapping.get(normalized_prediction, None)
        
        # Validate triage category
        valid_categories = get_triage_categories()
        if triage_category is None or triage_category not in valid_categories:
            logger.warning(f"⚠️ Unexpected prediction '{prediction}' -> '{normalized_prediction}'. Defaulting to YELLOW")
            triage_category = "YELLOW"  # Default to moderate priority
        
        # Map triage category to priority score
        priority_mapping = {
            "RED": 1,      # Immediate
            "ORANGE": 2,   # Very urgent
            "YELLOW": 3,   # Urgent
            "GREEN": 4,    # Standard
            "BLUE": 5      # Non-urgent
        }
        priority_score = priority_mapping.get(triage_category, 3)
        
        # Get expected wait time
        wait_time = get_wait_time_for_category(triage_category)
        
        # Generate reasoning based on transformer prediction
        reasoning = f"BioClinicalBERT-Triage transformer model classified symptoms as {triage_category} priority based on clinical text analysis. Original prediction: {prediction} (confidence: {confidence:.3f})"
        
        logger.info(f"✅ Mapped to: {triage_category} (Priority: {priority_score}, Wait: {wait_time})")
        
        return {
            'triage_category': triage_category,
            'priority_score': priority_score,
            'confidence': confidence,
            'reasoning': reasoning,
            'wait_time': wait_time
        }
    