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
    # Try to load .env.dev first, then fallback to .env
    if os.path.exists('.env.dev'):
        load_dotenv('.env.dev')
    else:
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
        Generate operational context string using existing metrics infrastructure.
        
        Args:
            current_time: Current simulation time
            
        Returns:
            Formatted operational context string
        """
        if not self._has_metrics():
            return "\n📊 OPERATIONAL CONTEXT: Not available (metrics not provided)\n"
        
        try:
            operation_data, nhs_data = self._get_metrics_data()
            latest_snapshot = self._get_latest_snapshot()
            
            context_parts = [
                f"\n📊 CURRENT HOSPITAL OPERATIONAL STATUS (Time: {current_time:.1f}min):\n",
                self._build_utilization_context(operation_data, latest_snapshot),
                # self._build_wait_times_context(operation_data),  # REMOVED: Agents should calculate wait times themselves
                self._build_queue_performance_context(operation_data),
                self._build_system_status_context(operation_data, nhs_data),
                self._build_triage_distribution_context(nhs_data),
                self._build_operational_guidance_context(operation_data),
                self._build_context_footer()
            ]
            
            return "".join(filter(None, context_parts))
            
        except Exception as e:
            logger.debug(f"⚠️ Operational context error: {e}")
            return "\n📊 OPERATIONAL CONTEXT: Not available\n"
    
    # Helper methods for operational context generation
    
    def _has_metrics(self) -> bool:
        """Check if metrics services are available."""
        return self.operation_metrics is not None and self.nhs_metrics is not None
    
    def _get_metrics_data(self) -> tuple:
        """Get calculated metrics data from both services."""
        operation_data = self.operation_metrics.calculate_metrics()
        nhs_data = self.nhs_metrics.calculate_metrics()
        return operation_data, nhs_data
    
    def _get_latest_snapshot(self):
        """Get the latest system snapshot from operation metrics."""
        if hasattr(self.operation_metrics, 'get_latest_snapshot'):
            return self.operation_metrics.get_latest_snapshot()
        elif self.operation_metrics.system_snapshots:
            return self.operation_metrics.system_snapshots[-1]
        return None
    
    def _build_utilization_context(self, operation_data: dict, latest_snapshot) -> str:
        """Build resource utilization context section."""
        if not ('utilization' in operation_data and operation_data['utilization']):
            return ""
        
        context = "\n🏥 RESOURCE UTILIZATION:\n"
        for resource, util_data in operation_data['utilization'].items():
            avg_util = util_data.get('average_utilization_pct', 0.0)
            peak_util = util_data.get('peak_utilization_pct', 0.0)
            status = self._get_utilization_status(avg_util)
            
            # Get current queue length from latest snapshot
            queue_len = 0
            if latest_snapshot and resource in latest_snapshot.queue_lengths:
                queue_len = latest_snapshot.queue_lengths[resource]
            
            context += f"• {resource.title()}: {avg_util:.1f}% {status} (Peak: {peak_util:.1f}%, Queue: {queue_len})\n"
        
        return context
    
    def _build_wait_times_context(self, operation_data: dict) -> str:
        """Build wait times context section - DISABLED for pure clinical decisions."""
        # 🔍 PURE CLINICAL DECISION: Wait times excluded to ensure agents calculate based on clinical analysis only
        return ""
    
    def _build_queue_performance_context(self, operation_data: dict) -> str:
        """Build queue performance context section."""
        if not ('queues' in operation_data and operation_data['queues']):
            return ""
        
        context = "\n📋 QUEUE PERFORMANCE:\n"
        for resource, queue_data in operation_data['queues'].items():
            avg_queue = queue_data.get('average_queue_length', 0.0)
            peak_queue = queue_data.get('peak_queue_length', 0)
            context += f"• {resource.title()}: {avg_queue:.1f} avg queue (peak: {peak_queue})\n"
        
        return context
    
    def _build_system_status_context(self, operation_data: dict, nhs_data: dict) -> str:
        """Build system status context section."""
        system_pressure = self._assess_system_pressure_from_metrics(operation_data)
        current_load = len(self.nhs_metrics.active_records) if hasattr(self.nhs_metrics, 'active_records') else 0
        
        return f"\n🚦 SYSTEM PRESSURE: {system_pressure}\n👥 CURRENT PATIENT LOAD: {current_load} patients in system\n"
    
    def _build_triage_distribution_context(self, nhs_data: dict) -> str:
        """Build triage distribution context section."""
        triage_dist = nhs_data.get('triage_category_distribution', {})
        if not triage_dist:
            return ""
        
        context = "\n📊 RECENT TRIAGE DISTRIBUTION:\n"
        total_triaged = sum(triage_dist.values())
        for category, count in triage_dist.items():
            if total_triaged > 0:
                percentage = (count / total_triaged) * 100
                context += f"• {category}: {count} patients ({percentage:.1f}%)\n"
        
        return context
    
    def _build_operational_guidance_context(self, operation_data: dict) -> str:
        """Build operational guidance context section."""
        guidance = self._generate_operational_guidance_from_metrics(operation_data)
        if not guidance:
            return ""
        
        return f"\n💡 OPERATIONAL GUIDANCE:\n{guidance}\n"
    
    def _build_context_footer(self) -> str:
        """Build context footer with important notice - Pure clinical focus."""
        return "\n⚠️ IMPORTANT: Use this operational context to inform triage decisions based on CURRENT hospital conditions and clinical severity. Calculate wait times based purely on your clinical assessment and operational analysis.\n"
    
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
    
    def _assess_system_pressure_from_metrics(self, operation_data) -> str:
        """Assess overall system pressure level using existing metrics data."""
        if not operation_data:
            return "UNKNOWN"
        
        # Calculate average utilization from metrics data
        avg_utilization = 0
        if 'utilization' in operation_data and operation_data['utilization']:
            utilizations = [util_data.get('average_utilization_pct', 0) 
                          for util_data in operation_data['utilization'].values()]
            avg_utilization = sum(utilizations) / len(utilizations) if utilizations else 0
        
        # Get maximum queue length from metrics data
        max_queue = 0
        if 'queues' in operation_data and operation_data['queues']:
            queue_lengths = [queue_data.get('peak_queue_length', 0) 
                           for queue_data in operation_data['queues'].values()]
            max_queue = max(queue_lengths) if queue_lengths else 0
        
        # Determine pressure level
        if avg_utilization >= 95 or max_queue >= 20:
            return "CRITICAL - System at maximum capacity"
        elif avg_utilization >= 85 or max_queue >= 15:
            return "HIGH - Significant resource strain"
        elif avg_utilization >= 70 or max_queue >= 8:
            return "MODERATE - Manageable load"
        else:
            return "LOW - Normal operations"
    
    def _generate_operational_guidance_from_metrics(self, operation_data) -> str:
        """Generate operational guidance based on existing metrics data."""
        if not operation_data:
            return ""
        
        guidance = []
        
        # Add utilization-based guidance
        guidance.extend(self._get_utilization_guidance(operation_data))
        
        # Add queue-based guidance
        guidance.extend(self._get_queue_guidance(operation_data))
        
        # Add system-wide guidance
        guidance.extend(self._get_system_wide_guidance(operation_data))
        
        return "\n".join(guidance) if guidance else "• System operating within normal parameters"
    
    def _get_utilization_guidance(self, operation_data: dict) -> list:
        """Get guidance based on resource utilization metrics."""
        guidance = []
        
        if 'utilization' in operation_data and operation_data['utilization']:
            for resource, util_data in operation_data['utilization'].items():
                avg_util = util_data.get('average_utilization_pct', 0.0)
                peak_util = util_data.get('peak_utilization_pct', 0.0)
                
                if peak_util >= 95:
                    guidance.append(f"• {resource.title()} at critical {peak_util:.1f}% peak capacity - immediate action required")
                elif avg_util >= 90:
                    guidance.append(f"• {resource.title()} at {avg_util:.1f}% avg capacity - expedite appropriate cases")
        
        return guidance
    
    def _get_queue_guidance(self, operation_data: dict) -> list:
        """Get guidance based on queue length metrics."""
        guidance = []
        
        if 'queues' in operation_data and operation_data['queues']:
            for resource, queue_data in operation_data['queues'].items():
                avg_queue = queue_data.get('average_queue_length', 0.0)
                peak_queue = queue_data.get('peak_queue_length', 0)
                
                if peak_queue >= 20:
                    guidance.append(f"• {resource.title()} has critical queue length of {peak_queue} - urgent intervention needed")
                elif avg_queue >= 15:
                    guidance.append(f"• {resource.title()} has high avg queue of {avg_queue:.1f} - prioritize urgent cases")
        
        return guidance
    
    def _get_system_wide_guidance(self, operation_data: dict) -> list:
        """Get system-wide guidance based on overall metrics."""
        guidance = []
        
        if 'utilization' in operation_data and operation_data['utilization']:
            utilizations = [util_data.get('average_utilization_pct', 0) 
                          for util_data in operation_data['utilization'].values()]
            avg_utilization = sum(utilizations) / len(utilizations) if utilizations else 0
            
            if avg_utilization >= 85:
                guidance.append("• High system load - use strict triage criteria and consider discharge planning")
            elif avg_utilization >= 75:
                guidance.append("• Moderate system load - monitor closely and prepare for capacity constraints")
        
        return guidance
    
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