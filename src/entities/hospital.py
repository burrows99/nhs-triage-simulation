import attr
from typing import List, Dict, Optional, Tuple
from .doctor import Doctor
from .patient import Patient
from ..enums.Triage import Priority
from .sub_entities.triage_assessment import TriageAssessment

@attr.s(auto_attribs=True)
class HospitalCore:
    """Core hospital business logic - simulation agnostic"""
    
    # Configuration
    num_doctors: int
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
        # Initialize doctors
        for i in range(self.num_doctors):
            doctor = Doctor(
                id=f"DOC_{i:03d}",
                name=f"Dr. {chr(65 + i)}",
                specialization=f"Emergency_Medicine_{i % 3}"
            )
            self.doctors.append(doctor)
        
        # Initialize priority queues
        for priority in Priority:
            self.priority_queues[priority] = []
    
    def register_patient(self, patient: Patient) -> None:
        """Register new patient in hospital system"""
        self.patient_registry[patient.id] = patient
        self.total_arrivals += 1
    
    def assign_patient_to_queue(self, patient: Patient, assessment: TriageAssessment) -> None:
        """Assign triaged patient to appropriate priority queue"""
        patient.priority = assessment.priority
        patient.priority_reason = assessment.reason
        patient.treatment_time = assessment.estimated_treatment_time
        
        self.priority_queues[assessment.priority].append(patient)
    
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
    
    def complete_treatment(self, doctor: Doctor, patient: Patient, current_time: float) -> None:
        """Complete patient treatment"""
        doctor.busy = False
        doctor.current_patient = None
        doctor.total_patients_treated += 1
        
        patient.wait_time = current_time - patient.arrival_time - patient.treatment_time
        self.completed_patients.append(patient)
        self.total_completed += 1
    
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
