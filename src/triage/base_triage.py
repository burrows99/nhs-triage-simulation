from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from ..entities.patient import Patient, Priority


class TriageResult:
    """Result of triage assessment for a patient"""
    
    def __init__(self, 
                 patient: Patient,
                 priority: Priority,
                 reason: str,
                 service_time: float,
                 confidence_score: float = 1.0):
        self.patient = patient
        self.priority = priority
        self.reason = reason
        self.service_time = service_time  # Expected service/consultation time in minutes
        self.confidence_score = confidence_score  # 0.0 to 1.0
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'patient_id': self.patient.patient_id,
            'priority': self.priority.name,
            'priority_value': self.priority.value,
            'reason': self.reason,
            'service_time': self.service_time,
            'confidence_score': self.confidence_score
        }


class BaseTriage(ABC):
    """Abstract base class for all triage systems"""
    
    def __init__(self, name: str):
        self.name = name
        self.patients_processed = 0
        self.processing_history = []
        
        # Note: Wait times are now handled by the simulation engine
        # This class focuses on service time estimation
    
    @abstractmethod
    def assess_patients(self, patients: List[Patient]) -> List[TriageResult]:
        """
        Assess a list of patients and assign priorities with reasons and service times
        
        Args:
            patients: List of Patient objects to assess
            
        Returns:
            List of TriageResult objects with priority, reason, and service time
        """
        pass
    
    @abstractmethod
    def assess_single_patient(self, patient: Patient) -> TriageResult:
        """
        Assess a single patient
        
        Args:
            patient: Patient object to assess
            
        Returns:
            TriageResult with priority, reason, and service time
        """
        pass
    
    def get_target_service_time(self, priority: Priority) -> float:
        """Get expected service time for a priority level"""
        # Service times based on priority complexity
        service_times = {
            Priority.IMMEDIATE: 45.0,      # Complex emergency care
            Priority.VERY_URGENT: 35.0,   # Urgent care
            Priority.URGENT: 25.0,        # Standard urgent care
            Priority.STANDARD: 20.0,      # Routine care
            Priority.NON_URGENT: 15.0     # Simple care
        }
        return service_times.get(priority, 20.0)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get triage system statistics"""
        if not self.processing_history:
            return {'patients_processed': 0}
        
        priority_counts = {p.name: 0 for p in Priority}
        total_confidence = 0.0
        
        for result in self.processing_history:
            priority_counts[result.priority.name] += 1
            total_confidence += result.confidence_score
        
        return {
            'name': self.name,
            'patients_processed': self.patients_processed,
            'priority_distribution': priority_counts,
            'average_confidence': total_confidence / len(self.processing_history) if self.processing_history else 0.0,
            'processing_history_length': len(self.processing_history)
        }
    
    def check_wait_time_breaches(self, patients: List[Patient]) -> List[Patient]:
        """Check for patients exceeding maximum wait times - implemented by simulation"""
        # This is now handled by the simulation engine
        # Return empty list as triage system doesn't track wait times
        return []
    
    def get_triage_statistics(self) -> Dict[str, Any]:
        """Get triage system statistics - alias for get_statistics"""
        return self.get_statistics()
    
    def _record_assessment(self, result: TriageResult) -> None:
        """Record assessment result for statistics"""
        self.patients_processed += 1
        self.processing_history.append(result)
        
        # Keep only last 1000 assessments for memory efficiency
        if len(self.processing_history) > 1000:
            self.processing_history = self.processing_history[-1000:]