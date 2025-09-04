import attr
from typing import List, Dict, Optional, Tuple
from .doctor import Doctor
from .patient import Patient
from ..enums.Triage import Priority
from .sub_entities.triage_assessment import TriageAssessment
from ..triage_systems.base import BaseTriageSystem
from ..services.statistics import StatisticsService
from ..utils.logger import get_logger, EventType, LogLevel

@attr.s(auto_attribs=True)
class HospitalCore:
    """Core hospital business logic - simulation agnostic"""
    
    # Configuration
    num_doctors: int
    triage_system: BaseTriageSystem
    triage_nurses: int = 1
    
    # State
    doctors: List[Doctor] = attr.ib(factory=list)
    priority_queues: Dict[Priority, List[Patient]] = attr.ib(factory=dict)
    patient_registry: Dict[str, Patient] = attr.ib(factory=dict)
    completed_patients: List[Patient] = attr.ib(factory=list)
    
    # Statistics
    total_arrivals: int = 0
    total_completed: int = 0
    
    def __attrs_post_init__(self):
        """Initialize hospital state"""
        self.logger = get_logger()
        
        # Log hospital initialization
        self.logger.log_event(
            timestamp=0.0,
            event_type=EventType.SYSTEM_STATE,
            message=f"Hospital initialized with {self.num_doctors} doctors and {self.triage_nurses} triage nurses",
            data={
                "num_doctors": self.num_doctors,
                "triage_nurses": self.triage_nurses,
                "initialization": True
            },
            source="hospital_core"
        )
        
        # Initialize doctors
        for i in range(self.num_doctors):
            doctor = Doctor(
                id=f"DOC_{i:03d}",
                name=f"Dr. {chr(65 + i)}",
                specialization=f"Emergency_Medicine_{i % 3}"
            )
            self.doctors.append(doctor)
            
            # Log doctor initialization
            self.logger.log_event(
                timestamp=0.0,
                event_type=EventType.SYSTEM_STATE,
                message=f"Doctor {doctor.id} ({doctor.name}) initialized - {doctor.specialization}",
                data={
                    "doctor_id": doctor.id,
                    "doctor_name": doctor.name,
                    "specialization": doctor.specialization
                },
                level=LogLevel.DEBUG,
                source="hospital_core"
            )
        
        # Initialize priority queues
        for priority in Priority:
            self.priority_queues[priority] = []
            
        self.logger.log_event(
            timestamp=0.0,
            event_type=EventType.SYSTEM_STATE,
            message=f"Priority queues initialized for all {len(Priority)} priority levels",
            data={"priority_levels": [p.name for p in Priority]},
            level=LogLevel.DEBUG,
            source="hospital_core"
        )
    
    def register_patient(self, patient: Patient, current_time: float = 0.0) -> None:
        """Register new patient in hospital system"""
        self.patient_registry[patient.id] = patient
        self.total_arrivals += 1
        
        # Log patient registration
        self.logger.log_event(
            timestamp=current_time,
            event_type=EventType.PATIENT_REGISTRATION,
            message=f"Patient {patient.id} registered in hospital system",
            data={
                "patient_id": patient.id,
                "condition": patient.condition,
                "symptoms": patient.symptoms,
                "arrival_time": patient.arrival_time,
                "total_arrivals": self.total_arrivals
            },
            source="hospital_core"
        )
        
        # Log patient arrival details
        self.logger.log_patient_arrival(
            timestamp=current_time,
            patient_id=patient.id,
            condition=patient.condition,
            vital_signs={
                "bp_systolic": patient.vital_signs.bp_systolic,
                "bp_diastolic": patient.vital_signs.bp_diastolic,
                "heart_rate": patient.vital_signs.heart_rate,
                "temperature": patient.vital_signs.temperature,
                "oxygen_saturation": patient.vital_signs.oxygen_saturation
            }
        )
    
    def assign_patient_to_queue(self, patient: Patient, assessment: TriageAssessment, current_time: float = 0.0) -> None:
        """Assign triaged patient to appropriate priority queue"""
        patient.priority = assessment.priority
        patient.priority_reason = assessment.reason
        
        # Calculate effective queue length (patients ahead of same/higher priority)
        effective_queue_length = len(self.priority_queues[assessment.priority])
        
        # Get number of available doctors
        available_doctors = len([doc for doc in self.doctors if not doc.busy])
        
        # Use queueing theory-based wait time estimation
        estimated_wait = StatisticsService.estimated_wait_time(
            priority=assessment.priority,
            Nq_eff=effective_queue_length,
            num_doctors=max(1, available_doctors),  # Ensure at least 1 to avoid division by zero
            stochastic=False  # Use deterministic mean for consistency
        )
        
        # For treatment time, still use the actual service time generation
        patient.treatment_time = StatisticsService.nhs_service_time(assessment.priority)
        
        # Store the estimated wait time for potential use
        patient.estimated_wait_time = estimated_wait
        
        # Get queue position before adding
        queue_position = len(self.priority_queues[assessment.priority]) + 1
        
        self.priority_queues[assessment.priority].append(patient)
        
        # Log queue assignment
        self.logger.log_queue_assignment(
            timestamp=current_time,
            patient_id=patient.id,
            priority=assessment.priority.name,
            queue_position=queue_position
        )
        
        # Log detailed queue state
        queue_lengths = {p.name: len(q) for p, q in self.priority_queues.items()}
        self.logger.log_event(
            timestamp=current_time,
            event_type=EventType.QUEUE_UPDATE,
            message=f"Patient {patient.id} added to {assessment.priority.name} queue (position {queue_position})",
            data={
                "patient_id": patient.id,
                "priority": assessment.priority.name,
                "queue_position": queue_position,
                "queue_lengths": queue_lengths,
                "assessment_reason": assessment.reason,
                "calculated_treatment_time": patient.treatment_time
            },
            source="hospital_core"
        )
    
    def get_next_patient_for_treatment(self) -> Optional[Tuple[Patient, Priority]]:
        """Get highest priority patient for treatment"""
        for priority in Priority:
            if self.priority_queues[priority]:
                patient = self.priority_queues[priority].pop(0)
                return patient, priority
        return None
    
    def assign_doctor_to_patient(self, doctor: Doctor, patient: Patient, current_time: float) -> None:
        """Assign doctor to patient"""
        doctor.busy = True
        doctor.current_patient = patient
        patient.assigned_doctor = doctor.id
        patient.treatment_start_time = current_time
        patient.wait_time = current_time - patient.arrival_time
        
        # Log doctor assignment
        self.logger.log_doctor_assignment(
            timestamp=current_time,
            patient_id=patient.id,
            doctor_id=doctor.id,
            priority=patient.priority.name if patient.priority else "UNKNOWN"
        )
        
        # Log detailed assignment information
        self.logger.log_event(
            timestamp=current_time,
            event_type=EventType.DOCTOR_ASSIGNMENT,
            message=f"Doctor {doctor.id} ({doctor.name}) assigned to Patient {patient.id}",
            data={
                "doctor_id": doctor.id,
                "doctor_name": doctor.name,
                "doctor_specialization": doctor.specialization,
                "patient_id": patient.id,
                "patient_condition": patient.condition,
                "patient_priority": patient.priority.name if patient.priority else "UNKNOWN",
                "wait_time": patient.wait_time,
                "estimated_treatment_time": patient.treatment_time
            },
            source="hospital_core"
        )
    
    def complete_treatment(self, doctor: Doctor, patient: Patient, current_time: float) -> None:
        """Complete patient treatment"""
        # Calculate actual treatment duration
        actual_treatment_time = current_time - (patient.treatment_start_time or current_time)
        total_wait_time = current_time - patient.arrival_time
        
        doctor.busy = False
        doctor.current_patient = None
        doctor.total_patients_treated += 1
        
        patient.wait_time = total_wait_time - actual_treatment_time
        self.completed_patients.append(patient)
        self.total_completed += 1
        
        # Log treatment completion
        self.logger.log_treatment_complete(
            timestamp=current_time,
            patient_id=patient.id,
            doctor_id=doctor.id,
            wait_time=patient.wait_time
        )
        
        # Log detailed completion information
        self.logger.log_event(
            timestamp=current_time,
            event_type=EventType.TREATMENT_COMPLETE,
            message=f"Treatment completed: Patient {patient.id} discharged by Doctor {doctor.id}",
            data={
                "patient_id": patient.id,
                "doctor_id": doctor.id,
                "condition": patient.condition,
                "priority": patient.priority.name if patient.priority else "UNKNOWN",
                "total_wait_time": total_wait_time,
                "actual_treatment_time": actual_treatment_time,
                "estimated_treatment_time": patient.treatment_time,
                "interruption_count": patient.interruption_count,
                "doctor_total_patients": doctor.total_patients_treated,
                "hospital_total_completed": self.total_completed
            },
            source="hospital_core"
        )
    
    def handle_preemption(self, interrupted_patient: Patient, current_time: float) -> Priority:
        """Handle patient preemption (anti-starvation logic)"""
        old_priority = interrupted_patient.priority
        
        # Move to higher priority queue (anti-starvation)
        if old_priority.value > 1:
            new_priority = Priority(old_priority.value - 1)
            interrupted_patient.priority = new_priority
            interrupted_patient.interruption_count += 1
            
            # Remove from old queue if present
            if interrupted_patient in self.priority_queues[old_priority]:
                self.priority_queues[old_priority].remove(interrupted_patient)
            
            # Add to front of new priority queue
            self.priority_queues[new_priority].insert(0, interrupted_patient)
            return new_priority
        
        return old_priority
    
    def get_busy_doctors(self) -> List[Doctor]:
        """Get list of currently busy doctors"""
        return [doc for doc in self.doctors if doc.busy and doc.current_patient is not None]
    
    def get_hospital_status(self) -> Dict:
        """Get current hospital status"""
        queue_lengths = {priority.name: len(queue) for priority, queue in self.priority_queues.items()}
        doctor_status = {doc.id: {"busy": doc.busy, "patients_treated": doc.total_patients_treated} 
                        for doc in self.doctors}
        
        return {
            "total_arrivals": self.total_arrivals,
            "total_completed": self.total_completed,
            "patients_in_system": self.total_arrivals - self.total_completed,
            "queue_lengths": queue_lengths,
            "doctor_status": doctor_status
        }
