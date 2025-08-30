from abc import ABC, abstractmethod

class BaseTriage(ABC):
    """
    Abstract base class for triage systems in the NHS Emergency Department simulation.
    
    This class defines the interface that all triage system implementations must follow.
    Different triage systems (Manchester, LLM-based, etc.) will inherit from this class
    and implement their specific triage logic.
    """
    
    @abstractmethod
    def assign_priority(self, patient):
        """
        Assign a priority level to a patient based on their condition.
        
        Args:
            patient: The patient object containing relevant medical information
            
        Returns:
            int: Priority level where:
                1: Immediate (Red) - Immediately life-threatening condition
                2: Very Urgent (Orange) - Potentially life-threatening condition
                3: Urgent (Yellow) - Serious condition but not immediately life-threatening
                4: Standard (Green) - Standard condition that requires treatment
                5: Non-Urgent (Blue) - Minor condition that can safely wait
        """
        pass
    
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