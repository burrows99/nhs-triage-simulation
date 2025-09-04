import random
from ..enums.Triage import Priority
from .sub_entities.triage_assessment import TriageAssessment
from ..utils.logger import get_logger, EventType, LogLevel

class TriageNurse:
    """MTS (Manchester Triage System) implementation with random responses"""
    
    def __init__(self, nurse_id: str = "NURSE_001"):
        self.nurse_id = nurse_id
        self.logger = get_logger()
        self.assessments_completed = 0
    
    def assess_patient(self, patient, current_time: float = 0.0) -> TriageAssessment:
        """Assess patient using MTS priorities with comprehensive logging"""
        patient_id = getattr(patient, 'id', 'UNKNOWN')
        condition = getattr(patient, 'condition', 'unknown')
        symptoms = getattr(patient, 'symptoms', [])
        
        # Log triage start
        self.logger.log_triage_start(
            timestamp=current_time,
            patient_id=patient_id,
            nurse_id=self.nurse_id
        )
        
        # Log patient condition analysis
        self.logger.log_event(
            timestamp=current_time,
            event_type=EventType.TRIAGE_ASSESSMENT,
            message=f"Analyzing patient {patient_id}: condition={condition}, symptoms={symptoms}",
            data={
                "patient_id": patient_id,
                "condition": condition,
                "symptoms": symptoms,
                "nurse_id": self.nurse_id,
                "assessment_step": "condition_analysis"
            },
            level=LogLevel.DEBUG,
            source="triage_nurse"
        )
        
        # Perform priority assessment
        priority = self._determine_priority(condition, symptoms, current_time, patient_id)
        
        # Generate reason based on condition and priority
        reason_text = self._generate_assessment_reason(condition, priority, symptoms)
        
        # Create assessment
        assessment = TriageAssessment(
            priority=priority,
            reason=reason_text,
            timestamp=current_time
        )
        
        # Log final assessment
        self.logger.log_triage_assessment(
            timestamp=current_time,
            patient_id=patient_id,
            priority=priority.name,
            reason=reason_text
        )
        
        # Log assessment completion
        self.assessments_completed += 1
        self.logger.log_event(
            timestamp=current_time,
            event_type=EventType.TRIAGE_COMPLETE,
            message=f"Triage assessment completed for Patient {patient_id} by {self.nurse_id}",
            data={
                "patient_id": patient_id,
                "nurse_id": self.nurse_id,
                "total_assessments": self.assessments_completed,
                "assessment_duration": 2.5  # Simulated assessment time
            },
            source="triage_nurse"
        )
        
        return assessment
    
    def _determine_priority(self, condition: str, symptoms: list, current_time: float, patient_id: str) -> Priority:
        """Determine priority based on condition and symptoms with logging"""
        # Priority determination logic with logging
        high_priority_conditions = ['cardiac_arrest', 'stroke_symptoms', 'severe_trauma']
        medium_priority_conditions = ['chest_pain', 'abdominal_pain', 'allergic_reaction']
        
        if condition in high_priority_conditions:
            priority = random.choice([Priority.RED, Priority.ORANGE])
            reason = f"High-priority condition: {condition}"
        elif condition in medium_priority_conditions:
            priority = random.choice([Priority.ORANGE, Priority.YELLOW])
            reason = f"Medium-priority condition: {condition}"
        else:
            priority = random.choice([Priority.YELLOW, Priority.GREEN, Priority.BLUE])
            reason = f"Standard triage assessment for: {condition}"
        
        # Log priority determination reasoning
        self.logger.log_event(
            timestamp=current_time,
            event_type=EventType.TRIAGE_ASSESSMENT,
            message=f"Priority determination for Patient {patient_id}: {reason} -> {priority.name}",
            data={
                "patient_id": patient_id,
                "condition": condition,
                "symptoms": symptoms,
                "priority_assigned": priority.name,
                "reasoning": reason,
                "assessment_step": "priority_determination"
            },
            level=LogLevel.DEBUG,
            source="triage_nurse"
        )
        
        return priority
    
    def _generate_assessment_reason(self, condition: str, priority: Priority, symptoms: list) -> str:
        """Generate human-readable assessment reason"""
        symptom_text = f" with symptoms: {', '.join(symptoms)}" if symptoms else ""
        return f"MTS Assessment: {condition}{symptom_text} classified as {priority.name} priority"
    

    
    def get_performance_stats(self) -> dict:
        """Get nurse performance statistics"""
        return {
            "nurse_id": self.nurse_id,
            "total_assessments": self.assessments_completed,
            "average_assessment_time": 2.5  # Simulated
        }