import random
from typing import List
from .sub_entities.preemption_decision import PreemptionDecision
from ..utils.logger import get_logger, EventType, LogLevel

class PreemptionAgent:
    """AI agent for making preemption decisions (randomized)"""
    
    def __init__(self, agent_id: str = "PREEMPTION_AGENT_001"):
        self.agent_id = agent_id
        self.decision_history = []
        self.logger = get_logger()
        self.total_decisions = 0
        self.preemptions_approved = 0
        self.preemptions_denied = 0
    
    def should_preempt(self, new_patient: 'Patient', busy_doctors: List['Doctor'], current_time: float = 0.0) -> 'PreemptionDecision':
        """Decide whether to preempt a doctor for a higher priority patient with comprehensive logging"""
        
        new_patient_id = getattr(new_patient, 'id', 'UNKNOWN')
        new_patient_priority = getattr(new_patient, 'priority', None)
        new_patient_condition = getattr(new_patient, 'condition', 'unknown')
        
        # Log preemption evaluation start
        self.logger.log_event(
            timestamp=current_time,
            event_type=EventType.PREEMPTION_DECISION,
            message=f"Evaluating preemption for Patient {new_patient_id} ({new_patient_priority.name if new_patient_priority else 'NO_PRIORITY'})",
            data={
                "new_patient_id": new_patient_id,
                "new_patient_priority": new_patient_priority.name if new_patient_priority else None,
                "new_patient_condition": new_patient_condition,
                "busy_doctors_count": len(busy_doctors),
                "busy_doctor_ids": [doc.id for doc in busy_doctors],
                "evaluation_step": "start"
            },
            level=LogLevel.DEBUG,
            source="preemption_agent"
        )
        
        # Analyze current patient priorities being treated
        current_patients_info = []
        for doctor in busy_doctors:
            if doctor.current_patient:
                current_patients_info.append({
                    "doctor_id": doctor.id,
                    "patient_id": doctor.current_patient.id,
                    "patient_priority": doctor.current_patient.priority.name if doctor.current_patient.priority else None,
                    "patient_condition": doctor.current_patient.condition
                })
        
        # Log current treatment analysis
        self.logger.log_event(
            timestamp=current_time,
            event_type=EventType.PREEMPTION_DECISION,
            message=f"Analyzing current treatments for preemption consideration",
            data={
                "new_patient_id": new_patient_id,
                "current_treatments": current_patients_info,
                "evaluation_step": "analysis"
            },
            level=LogLevel.DEBUG,
            source="preemption_agent"
        )
        
        # Make decision (simplified random logic for now)
        should_preempt = random.choice([True, False])
        confidence = random.uniform(0.5, 0.95)
        
        if should_preempt and busy_doctors:
            # Select doctor to preempt
            doctor_to_preempt = random.choice(busy_doctors)
            preempted_patient = doctor_to_preempt.current_patient
            reason = f"Random preemption decision: {new_patient_priority.name if new_patient_priority else 'UNKNOWN'} priority patient needs immediate attention"
            
            decision = PreemptionDecision(
                should_preempt=True,
                doctor_to_preempt=doctor_to_preempt.id,
                reason=reason,
                confidence=confidence
            )
            
            self.preemptions_approved += 1
            
            # Log preemption approval
            self.logger.log_preemption_decision(
                timestamp=current_time,
                decision=True,
                reason=reason,
                new_patient_id=new_patient_id,
                affected_patients=[preempted_patient.id] if preempted_patient else []
            )
            
        else:
            reason = "No preemption needed" if not busy_doctors else "Preemption not warranted at this time"
            decision = PreemptionDecision(
                should_preempt=False,
                doctor_to_preempt=None,
                reason=reason,
                confidence=confidence
            )
            
            self.preemptions_denied += 1
            
            # Log preemption denial
            self.logger.log_preemption_decision(
                timestamp=current_time,
                decision=False,
                reason=reason,
                new_patient_id=new_patient_id,
                affected_patients=[]
            )
        
        # Update statistics
        self.total_decisions += 1
        
        # Store in decision history
        decision_record = {
            'timestamp': current_time,
            'decision': decision,
            'new_patient_id': new_patient_id,
            'preempted_patient_id': decision.doctor_to_preempt,
            'confidence': confidence,
            'busy_doctors_count': len(busy_doctors)
        }
        self.decision_history.append(decision_record)
        
        # Log decision summary
        self.logger.log_event(
            timestamp=current_time,
            event_type=EventType.PREEMPTION_DECISION,
            message=f"Preemption decision completed: {'APPROVED' if decision.should_preempt else 'DENIED'} (confidence: {confidence:.2f})",
            data={
                "decision": decision.should_preempt,
                "confidence": confidence,
                "reason": decision.reason,
                "new_patient_id": new_patient_id,
                "doctor_to_preempt": decision.doctor_to_preempt,
                "total_decisions": self.total_decisions,
                "approval_rate": self.preemptions_approved / self.total_decisions if self.total_decisions > 0 else 0
            },
            source="preemption_agent"
        )
        
        return decision
    
    def get_performance_stats(self) -> dict:
        """Get agent performance statistics"""
        return {
            "agent_id": self.agent_id,
            "total_decisions": self.total_decisions,
            "preemptions_approved": self.preemptions_approved,
            "preemptions_denied": self.preemptions_denied,
            "approval_rate": self.preemptions_approved / self.total_decisions if self.total_decisions > 0 else 0
        }
