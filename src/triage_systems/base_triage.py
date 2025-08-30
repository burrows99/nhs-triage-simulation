from abc import ABC, abstractmethod
from typing import Dict, Any
import json

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
            string: Name of the triage system
        """
        pass