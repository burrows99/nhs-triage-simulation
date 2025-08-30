from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import json
import logging
import time
from src.utils.telemetry import get_telemetry_collector, DecisionStepType

logger = logging.getLogger(__name__)

class BaseTriage(ABC):
    """
    Abstract base class for triage systems in the NHS Emergency Department simulation.
    
    This class defines the interface that all triage system implementations must follow.
    Different triage systems (Manchester, LLM-based, etc.) will inherit from this class
    and implement their specific triage logic.
    """
    
    REQUIRED_KEYS = {"priority", "rationale", "recommended_actions"}

    @abstractmethod
    def perform_triage(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform triage on a patient and return structured triage data.
        
        Args:
            patient_data: Dictionary containing patient information
            
        Returns:
            dict: Triage results including priority, rationale, and recommended actions
        """
        pass

    def _validate_response(self, response: str) -> bool:
        """Validate JSON structure meets triage requirements"""
        try:
            data = json.loads(response)
            return all(key in data for key in self.REQUIRED_KEYS)
        except json.JSONDecodeError:
            return False

    @abstractmethod
    def estimate_triage_time(self):
        """
        Estimate the time required to triage a patient.
        
        Returns:
            float: Estimated time in minutes for the triage process
        """
        pass
    
    @abstractmethod
    def estimate_consult_time(self, priority):
        """
        Estimate the time required for doctor consultation based on patient priority.
        
        Args:
            priority: The priority level assigned to the patient (1-5)
            
        Returns:
            float: Estimated time in minutes for the consultation process
        """
        pass

    @abstractmethod
    def get_triage_system_name(self):
        """
        Get the name of the triage system.
        
        Returns:
            str: Name of the triage system
        """
        pass
    
    def _start_telemetry_session(self, patient_data: Dict[str, Any]) -> str:
        """Start a telemetry session for tracking decision steps"""
        telemetry = get_telemetry_collector()
        session_id = telemetry.start_patient_session(
            patient_data.get('id', 0),
            self.get_triage_system_name(),
            patient_data
        )
        return session_id
    
    def _log_telemetry_step(self, session_id: str, step_type: DecisionStepType,
                           input_data: Dict[str, Any], output_data: Dict[str, Any],
                           duration_ms: float, success: bool = True,
                           error_message: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log a telemetry step"""
        telemetry = get_telemetry_collector()
        return telemetry.log_decision_step(
            session_id, step_type, input_data, output_data,
            duration_ms, success, error_message, metadata
        )
    
    def _end_telemetry_session(self, session_id: str, final_priority: int,
                              final_rationale: str, success: bool = True) -> None:
        """End a telemetry session"""
        telemetry = get_telemetry_collector()
        telemetry.end_patient_session(session_id, final_priority, final_rationale, success)

    # Triage-specific validation and extraction methods
    @staticmethod
    def validate_triage_response(data: Dict[str, Any], required_keys: List[str]) -> bool:
        """
        Validate that a triage response contains all required keys.
        
        Args:
            data (Dict[str, Any]): Parsed JSON data to validate
            required_keys (List[str]): List of required keys
            
        Returns:
            bool: True if all required keys are present, False otherwise
        """
        if not isinstance(data, dict):
            logger.error(f"Invalid data type for validation: {type(data)}")
            return False
        
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            logger.error(f"Missing required keys in triage response: {missing_keys}")
            return False
        
        return True

    @staticmethod
    def validate_priority_value(priority: Any) -> bool:
        """
        Validate that a priority value is within the valid range (1-5).
        
        Args:
            priority (Any): Priority value to validate
            
        Returns:
            bool: True if priority is valid, False otherwise
        """
        try:
            priority_int = int(priority)
            if 1 <= priority_int <= 5:
                return True
            else:
                logger.error(f"Priority {priority_int} out of valid range (1-5)")
                return False
        except (ValueError, TypeError):
            logger.error(f"Invalid priority type: {type(priority)} - {priority}")
            return False

    @staticmethod
    def extract_priority_from_response(data: Dict[str, Any]) -> Optional[int]:
        """
        Extract priority value from various possible keys in triage response.
        
        Tries multiple common priority key names used across different triage systems.
        
        Args:
            data (Dict[str, Any]): Parsed triage response data
            
        Returns:
            Optional[int]: Extracted priority value or None if not found
        """
        priority_keys = [
            'mts_priority',
            'priority',
            'clinical_priority',
            'priority_recommendation',
            'triage_priority',
            'final_priority'
        ]
        
        for key in priority_keys:
            if key in data:
                priority = data[key]
                if BaseTriage.validate_priority_value(priority):
                    return int(priority)
                else:
                    logger.warning(f"Invalid priority value for key '{key}': {priority}")
        
        logger.error(f"No valid priority found in response keys: {list(data.keys())}")
        return None

    @staticmethod
    def extract_confidence_from_response(data: Dict[str, Any]) -> str:
        """
        Extract confidence level from triage response with fallback to default.
        
        Args:
            data (Dict[str, Any]): Parsed triage response data
            
        Returns:
            str: Confidence level ('high', 'medium', 'low')
        """
        confidence_keys = ['confidence', 'confidence_level', 'certainty']
        
        for key in confidence_keys:
            if key in data:
                confidence = str(data[key]).lower()
                if confidence in ['high', 'medium', 'low']:
                    return confidence
                else:
                    logger.warning(f"Invalid confidence value: {confidence}")
        
        return 'medium'  # Default fallback

    @staticmethod
    def extract_rationale_from_response(data: Dict[str, Any]) -> str:
        """
        Extract rationale/reasoning from triage response with fallback.
        
        Args:
            data (Dict[str, Any]): Parsed triage response data
            
        Returns:
            str: Rationale text or default message
        """
        rationale_keys = ['rationale', 'reasoning', 'explanation', 'justification']
        
        for key in rationale_keys:
            if key in data and data[key]:
                return str(data[key])
        
        return 'Triage assessment completed'

    @staticmethod
    def create_fallback_response(error_message: str, fallback_priority: int = 3) -> Dict[str, Any]:
        """
        Create a standardized fallback response for failed triage processing.
        
        Args:
            error_message (str): Description of the error
            fallback_priority (int): Default priority to use
            
        Returns:
            Dict[str, Any]: Standardized fallback response
        """
        return {
            'priority': fallback_priority,
            'confidence': 'low',
            'rationale': f'Fallback assessment: {error_message}',
            'error': True,
            'error_message': error_message,
            'fallback_used': True
        }