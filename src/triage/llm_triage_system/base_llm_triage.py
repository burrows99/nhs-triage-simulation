"""Base LLM Triage System

Abstract base class for LLM-based triage systems providing common functionality
for single and multi-agent implementations.
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from openai import OpenAI

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.logger import logger
from .config.system_prompts import get_system_prompt, get_triage_categories, get_wait_time_for_category, get_full_triage_prompt
from src.models.triage_result import TriageResult

# Environment configuration
HF_API_KEY = os.getenv('HF_API_KEY', 'your-huggingface-api-key-here')
HF_BASE_URL = os.getenv('HF_BASE_URL', 'https://router.huggingface.co/v1')
HF_MODEL = os.getenv('HF_MODEL', 'openai/gpt-oss-120b:together')


class BaseLLMTriageSystem(ABC):
    """
    Abstract base class for LLM-based triage systems.
    
    Provides common functionality for:
    - API client management
    - Operational context generation
    - Response validation
    - Error handling
    
    Subclasses must implement the triage_patient method.
    """
    
    def __init__(self, model_name: str = HF_MODEL, operation_metrics=None, nhs_metrics=None):
        """
        Initialize the base LLM Triage System.
        
        Args:
            model_name (str): Model identifier for the Hugging Face API
            operation_metrics: OperationMetrics instance for operational context
            nhs_metrics: NHSMetrics instance for patient flow context
        """
        self.model_name = model_name
        self.operation_metrics = operation_metrics
        self.nhs_metrics = nhs_metrics
        self.client = None
        
        self._initialize_client()
        
        # Initialize triage categories mapping
        self.triage_categories = get_triage_categories()
    
    def _initialize_client(self):
        """Initialize the OpenAI client for Hugging Face API."""
        logger.info(f"🤖 Initializing LLM Triage System: {self.model_name}")
        
        try:
            self.client = OpenAI(
                base_url=HF_BASE_URL,
                api_key=HF_API_KEY,
            )
            logger.info(f"✅ LLM Triage System ready")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM system: {e}")
            raise RuntimeError(f"Failed to initialize LLM system: {e}") from e
    
    @abstractmethod
    def triage_patient(self, symptoms: str) -> TriageResult:
        """
        Abstract method for patient triage.
        
        Args:
            symptoms (str): Patient symptoms description
            
        Returns:
            TriageResult: Triage result with category, priority, and reasoning
        """
        pass
    
    def _validate_symptoms(self, symptoms: str) -> None:
        """
        Validate input symptoms.
        
        Args:
            symptoms (str): Patient symptoms
            
        Raises:
            ValueError: If symptoms are empty or invalid
        """
        if not symptoms or not symptoms.strip():
            logger.error("❌ Empty symptoms provided")
            raise ValueError("Empty symptoms provided to LLM triage system")
    
    def _generate_operational_context(self, current_time: float) -> str:
        """
        Generate operational context string from existing metrics classes.
        
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
        """Get utilization status indicator."""
        if utilization >= 95:
            return "🔴 CRITICAL"
        elif utilization >= 80:
            return "🟡 HIGH"
        elif utilization >= 60:
            return "🟢 MODERATE"
        else:
            return "🔵 LOW"
    
    def _assess_system_pressure(self, snapshot, operation_data) -> str:
        """Assess overall system pressure level."""
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
        """Generate operational guidance based on current conditions."""
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
    
    def _validate_api_response(self, triage_data: Dict[str, Any]) -> None:
        """
        Validate API response data.
        
        Args:
            triage_data: Parsed JSON response from API
            
        Raises:
            ValueError: If response is invalid
        """
        # Validate required fields
        required_fields = ["triage_category", "priority_score", "confidence", "reasoning", "wait_time"]
        missing_fields = [field for field in required_fields if field not in triage_data]
        if missing_fields:
            logger.error(f"❌ Step 5 Failed: Missing required fields - {missing_fields}")
            raise ValueError(f"Missing required fields: {missing_fields}")
        logger.info(f"✅ All required fields present")
        
        # Validate triage category
        valid_categories = get_triage_categories()
        if triage_data["triage_category"] not in valid_categories:
            logger.error(f"❌ Step 5 Failed: Invalid triage category - {triage_data['triage_category']}")
            raise ValueError(f"Invalid triage category: {triage_data['triage_category']}")
        logger.info(f"✅ Triage category '{triage_data['triage_category']}' is valid")
        
        # Convert and validate data types
        try:
            triage_data["priority_score"] = int(triage_data["priority_score"])
            triage_data["confidence"] = float(triage_data["confidence"])
            logger.info(f"✅ Data types validated and converted")
        except (ValueError, TypeError) as type_error:
            logger.error(f"❌ Step 5 Failed: Invalid data types - {type_error}")
            raise ValueError(f"Invalid data types: {type_error}") from type_error
    
    def _log_triage_result(self, triage_data: Dict[str, Any]) -> None:
        """
        Log the final triage result.
        
        Args:
            triage_data: Validated triage data
        """
        logger.info(f"🔍 Step 6: Final Triage Decision")
        logger.info(f"🏥 TRIAGE RESULT: {triage_data['triage_category']} (Priority {triage_data['priority_score']})")
        logger.info(f"📊 Confidence: {triage_data['confidence']:.1%}")
        logger.info(f"⏰ Wait Time: {triage_data['wait_time']}")
        logger.info(f"💭 Clinical Reasoning: {triage_data['reasoning'][:100]}{'...' if len(triage_data['reasoning']) > 100 else ''}")
        logger.info(f"✅ LLM Triage Assessment Complete")