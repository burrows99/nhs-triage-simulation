import random
import attr
from typing import List, Optional, TYPE_CHECKING
from .sub_entities.preemption_decision import PreemptionDecision
from ..utils.logger import get_logger, EventType, LogLevel
from .doctor import Doctor
from .MRI_machine import MRI_Machine
from .blood_test_nurse import BloodTestNurse
from .patient import Patient
from .sub_entities.simulation_state import SimulationState
from .hospital import HospitalCore

class PreemptionAgent:
    """AI agent for making preemption decisions across all hospital resources"""
    
    def __init__(self, agent_id: str = "PREEMPTION_AGENT_001"):
        self.agent_id = agent_id
        self.decision_history = []
        self.logger = get_logger()
        self.total_decisions = 0
        self.preemptions_approved = 0
        self.preemptions_denied = 0
    
    def should_preempt(self, new_patient: 'Patient', simulation_state: 'SimulationState', 
                      hospital: 'HospitalCore', current_time: float = 0.0) -> 'PreemptionDecision':
        """Decide whether to preempt any hospital resource for a higher priority patient"""
        
        # Extract busy resources from hospital using dedicated methods
        busy_doctors = hospital.get_busy_doctors()
        busy_mri_machines = MRI_Machine.get_busy_machines(hospital.mri_machines)
        busy_blood_nurses = BloodTestNurse.get_busy_nurses(hospital.blood_nurses)
        
        # Log evaluation start
        self._log_evaluation_start(new_patient, busy_doctors, busy_mri_machines, busy_blood_nurses, current_time)
        
        # Determine preemption probability and confidence
        should_preempt, confidence = self._calculate_preemption_probability(new_patient.priority)
        
        if should_preempt:
            decision = self._create_preemption_decision(new_patient, busy_doctors, busy_mri_machines, 
                                                      busy_blood_nurses, confidence, current_time)
        else:
            decision = self._create_denial_decision(new_patient, busy_doctors, busy_mri_machines, 
                                                   busy_blood_nurses, confidence, current_time)
        
        # Update statistics and log decision
        self._update_statistics_and_log(decision, new_patient, current_time)
        
        return decision
    
    def _log_evaluation_start(self, new_patient: 'Patient', busy_doctors: List, busy_mri_machines: List, 
                             busy_blood_nurses: List, current_time: float):
        """Log the start of preemption evaluation"""
        self.logger.log_event(
            timestamp=current_time,
            event_type=EventType.PREEMPTION_DECISION,
            message=f"Evaluating preemption for Patient {new_patient.id} ({new_patient.priority.name if new_patient.priority else 'NO_PRIORITY'})",
            data={
                "new_patient_id": new_patient.id,
                "new_patient_priority": new_patient.priority.name if new_patient.priority else None,
                "new_patient_condition": new_patient.condition,
                "busy_doctors_count": len(busy_doctors),
                "busy_mri_machines_count": len(busy_mri_machines),
                "busy_blood_nurses_count": len(busy_blood_nurses),
                "evaluation_step": "start"
            },
            level=LogLevel.DEBUG,
            source="preemption_agent"
        )
    
    def _calculate_preemption_probability(self, priority) -> tuple[bool, float]:
        """Calculate preemption probability based on patient priority"""
        if priority and priority.name in ['RED', 'ORANGE']:
            should_preempt = random.choices([True, False], weights=[0.8, 0.2])[0]
            confidence = random.uniform(0.7, 0.95)
        elif priority and priority.name == 'YELLOW':
            should_preempt = random.choices([True, False], weights=[0.4, 0.6])[0]
            confidence = random.uniform(0.5, 0.8)
        else:
            should_preempt = random.choices([True, False], weights=[0.1, 0.9])[0]
            confidence = random.uniform(0.3, 0.7)
        
        return should_preempt, confidence
    
    def _create_preemption_decision(self, new_patient: 'Patient', busy_doctors: List, busy_mri_machines: List,
                                   busy_blood_nurses: List, confidence: float, current_time: float) -> PreemptionDecision:
        """Create a preemption decision when preemption is approved"""
        # Select single resource to preempt based on patient needs (patients are with one resource at a time)
        doctor_to_preempt = None
        mri_to_preempt = None
        nurse_to_preempt = None
        
        # Priority-based resource selection - check in order of patient needs
        if self._should_preempt_mri(new_patient, busy_mri_machines):
            mri_to_preempt = self._select_mri_to_preempt(busy_mri_machines, new_patient)
        elif self._should_preempt_blood_nurse(new_patient, busy_blood_nurses):
            nurse_to_preempt = self._select_nurse_to_preempt(busy_blood_nurses, new_patient)
        elif busy_doctors:
            doctor_to_preempt = self._select_doctor_to_preempt(busy_doctors)
        
        # Generate reason for the single selected resource
        reason = self._generate_preemption_reason(new_patient, doctor_to_preempt, mri_to_preempt, nurse_to_preempt)
        
        decision = PreemptionDecision(
            should_preempt=True,
            doctor_to_preempt=doctor_to_preempt,
            mri_machine_to_preempt=mri_to_preempt,
            blood_nurse_to_preempt=nurse_to_preempt,
            reason=reason,
            confidence=confidence
        )
        
        self.preemptions_approved += 1
        
        # Log preemption approval
        affected_patients = self._get_affected_patients(doctor_to_preempt, mri_to_preempt, nurse_to_preempt)
        self.logger.log_preemption_decision(
            timestamp=current_time,
            decision=True,
            reason=reason,
            new_patient_id=new_patient.id,
            affected_patients=affected_patients
        )
        
        return decision
    
    def _create_denial_decision(self, new_patient: 'Patient', busy_doctors: List, busy_mri_machines: List,
                               busy_blood_nurses: List, confidence: float, current_time: float) -> PreemptionDecision:
        """Create a denial decision when preemption is not approved"""
        reason = self._generate_denial_reason(busy_doctors, busy_mri_machines, busy_blood_nurses)
        
        decision = PreemptionDecision(
            should_preempt=False,
            doctor_to_preempt=None,
            mri_machine_to_preempt=None,
            blood_nurse_to_preempt=None,
            reason=reason,
            confidence=confidence
        )
        
        self.preemptions_denied += 1
        
        # Log preemption denial
        self.logger.log_preemption_decision(
            timestamp=current_time,
            decision=False,
            reason=reason,
            new_patient_id=new_patient.id,
            affected_patients=[]
        )
        
        return decision
    
    def _select_doctor_to_preempt(self, busy_doctors: List) -> Optional['Doctor']:
        """Select a doctor to preempt (random selection for now)"""
        return random.choice(busy_doctors) if busy_doctors else None
    
    def _should_preempt_mri(self, new_patient: 'Patient', busy_mri_machines: List) -> bool:
        """Determine if MRI machine should be preempted for this patient"""
        if not busy_mri_machines:
            return False
        
        # Preempt MRI for high priority patients or specific conditions requiring imaging
        return (new_patient.priority and new_patient.priority.name in ['RED', 'ORANGE'] and
                ('stroke' in new_patient.condition.lower() or 'head' in new_patient.condition.lower() or
                 'brain' in new_patient.condition.lower() or 'neurological' in new_patient.condition.lower()))
    
    def _should_preempt_blood_nurse(self, new_patient: 'Patient', busy_blood_nurses: List) -> bool:
        """Determine if blood test nurse should be preempted for this patient"""
        if not busy_blood_nurses:
            return False
        
        # Preempt blood nurse for high priority patients or cardiac conditions requiring blood work
        return (new_patient.priority and new_patient.priority.name in ['RED', 'ORANGE'] and
                ('cardiac' in new_patient.condition.lower() or 'chest_pain' in new_patient.condition.lower() or
                 'heart' in new_patient.condition.lower() or 'myocardial' in new_patient.condition.lower()))
    
    def _select_mri_to_preempt(self, busy_mri_machines: List, new_patient: 'Patient') -> Optional['MRI_Machine']:
        """Select an MRI machine to preempt"""
        return random.choice(busy_mri_machines) if busy_mri_machines else None
    
    def _select_nurse_to_preempt(self, busy_blood_nurses: List, new_patient: 'Patient') -> Optional['BloodTestNurse']:
        """Select a blood test nurse to preempt"""
        return random.choice(busy_blood_nurses) if busy_blood_nurses else None
    
    def _generate_preemption_reason(self, new_patient: 'Patient', doctor_to_preempt, mri_to_preempt, nurse_to_preempt) -> str:
        """Generate appropriate reason for preemption based on single resource and patient priority"""
        # Determine which single resource was preempted
        if doctor_to_preempt:
            resource_str = "doctor"
        elif mri_to_preempt:
            resource_str = "MRI"
        elif nurse_to_preempt:
            resource_str = "blood nurse"
        else:
            resource_str = "resource"
        
        if new_patient.priority and new_patient.priority.name == 'RED':
            return f"CRITICAL: {new_patient.condition} requires immediate {resource_str} - life-threatening condition"
        elif new_patient.priority and new_patient.priority.name == 'ORANGE':
            return f"HIGH PRIORITY: {new_patient.condition} requires urgent {resource_str} intervention"
        else:
            return f"PREEMPTION: {new_patient.condition} - clinical judgment favors immediate {resource_str} access"
    
    def _generate_denial_reason(self, busy_doctors: List, busy_mri_machines: List, busy_blood_nurses: List) -> str:
        """Generate appropriate reason for denial"""
        if not any([busy_doctors, busy_mri_machines, busy_blood_nurses]):
            return "No preemption needed - all resources available"
        else:
            return random.choice([
                "Preemption not warranted at this time",
                "Current treatments should not be interrupted",
                "Risk-benefit analysis favors maintaining current assignments",
                "Patient condition does not justify resource preemption"
            ])
    
    def _get_affected_patients(self, doctor_to_preempt, mri_to_preempt, nurse_to_preempt) -> List[str]:
        """Get list of affected patient IDs from preempted resources"""
        affected_patients = []
        
        if doctor_to_preempt and doctor_to_preempt.current_patient:
            affected_patients.append(doctor_to_preempt.current_patient.id)
        
        if mri_to_preempt and mri_to_preempt.current_patient:
            affected_patients.append(mri_to_preempt.current_patient.id)
        
        if nurse_to_preempt and nurse_to_preempt.current_patient:
            affected_patients.append(nurse_to_preempt.current_patient.id)
        
        return affected_patients
    
    def _update_statistics_and_log(self, decision: PreemptionDecision, new_patient: 'Patient', current_time: float):
        """Update statistics and log final decision"""
        self.total_decisions += 1
        
        # Store in decision history (using dictionaries for logging compatibility)
        # Determine which single resource was preempted (patients are with one resource at a time)
        preempted_resource = None
        if decision.doctor_to_preempt:
            preempted_resource = {
                'type': 'doctor',
                'id': decision.doctor_to_preempt.id,
                'name': decision.doctor_to_preempt.name,
                'specialization': decision.doctor_to_preempt.specialization,
                'current_patient_id': decision.doctor_to_preempt.current_patient.id if decision.doctor_to_preempt.current_patient else None
            }
        elif decision.mri_machine_to_preempt:
            preempted_resource = {
                'type': 'mri_machine',
                'id': decision.mri_machine_to_preempt.id,
                'name': decision.mri_machine_to_preempt.name,
                'model': decision.mri_machine_to_preempt.model,
                'current_patient_id': decision.mri_machine_to_preempt.current_patient.id if decision.mri_machine_to_preempt.current_patient else None
            }
        elif decision.blood_nurse_to_preempt:
            preempted_resource = {
                'type': 'blood_nurse',
                'id': decision.blood_nurse_to_preempt.id,
                'name': decision.blood_nurse_to_preempt.name,
                'specialization': decision.blood_nurse_to_preempt.specialization,
                'current_patient_id': decision.blood_nurse_to_preempt.current_patient.id if decision.blood_nurse_to_preempt.current_patient else None
            }
        
        decision_record = {
            'timestamp': current_time,
            'decision': {
                'should_preempt': decision.should_preempt,
                'reason': decision.reason,
                'confidence': decision.confidence
            },
            'new_patient': {
                'id': new_patient.id,
                'priority': new_patient.priority.name if new_patient.priority else None,
                'condition': new_patient.condition
            },
            'preempted_resource': preempted_resource  # Single resource that was preempted
        }
        self.decision_history.append(decision_record)
        
        # Log decision summary
        self.logger.log_event(
            timestamp=current_time,
            event_type=EventType.PREEMPTION_DECISION,
            message=f"Preemption decision completed: {'APPROVED' if decision.should_preempt else 'DENIED'} (confidence: {decision.confidence:.2f})",
            data={
                "decision": decision.should_preempt,
                "confidence": decision.confidence,
                "reason": decision.reason,
                "new_patient_id": new_patient.id,
                "new_patient_priority": new_patient.priority.name if new_patient.priority else None,
                "new_patient_condition": new_patient.condition,
                "preempted_resource": {
                    'type': preempted_resource['type'] if preempted_resource else None,
                    'id': preempted_resource['id'] if preempted_resource else None,
                    'name': preempted_resource['name'] if preempted_resource else None
                },
                "total_decisions": self.total_decisions,
                "approval_rate": self.preemptions_approved / self.total_decisions if self.total_decisions > 0 else 0
            },
            source="preemption_agent"
        )
    
    def get_performance_stats(self) -> dict:
        """Get agent performance statistics"""
        return {
            "agent_id": self.agent_id,
            "total_decisions": self.total_decisions,
            "preemptions_approved": self.preemptions_approved,
            "preemptions_denied": self.preemptions_denied,
            "approval_rate": self.preemptions_approved / self.total_decisions if self.total_decisions > 0 else 0
        }
