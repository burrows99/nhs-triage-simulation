import attr
from typing import List, Dict, Optional, Tuple
from .doctor import Doctor
from .patient import Patient
from .MRI_machine import MRI_Machine
from .blood_test_nurse import BloodTestNurse
from .bed import Bed
from .testing.mri_test import MRITest
from .testing.blood_test import BloodTest

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
    num_mri_machines: int = 2
    num_blood_nurses: int = 3
    num_beds: int = 20
    
    # State
    doctors: List[Doctor] = attr.ib(factory=list)
    mri_machines: List[MRI_Machine] = attr.ib(factory=list)
    blood_nurses: List[BloodTestNurse] = attr.ib(factory=list)
    beds: List[Bed] = attr.ib(factory=list)
    priority_queues: Dict[Priority, List[Patient]] = attr.ib(factory=dict)
    # Removed separate queues - all resources use priority_queues directly
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
            message=f"Hospital initialized with {self.num_doctors} doctors, {self.num_mri_machines} MRI machines, {self.num_blood_nurses} blood nurses, {self.num_beds} beds, and {self.triage_nurses} triage nurses",
            data={
                "num_doctors": self.num_doctors,
                "num_mri_machines": self.num_mri_machines,
                "num_blood_nurses": self.num_blood_nurses,
                "num_beds": self.num_beds,
                "triage_nurses": self.triage_nurses,
                "initialization": True
            }
        )
        
        # Initialize doctors
        for i in range(self.num_doctors):
            doctor = Doctor(
                id=i + 1,
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
        
        # Initialize MRI machines
        for i in range(self.num_mri_machines):
            mri_machine = MRI_Machine(
                id=i + 1,
                name=f"MRI Unit {chr(65 + i)}",
                model="Siemens Magnetom",
                field_strength="3.0T"
            )
            self.mri_machines.append(mri_machine)
            
            # Log MRI machine initialization
            self.logger.log_event(
                timestamp=0.0,
                event_type=EventType.SYSTEM_STATE,
                message=f"MRI Machine {mri_machine.id} ({mri_machine.name}) initialized - {mri_machine.model}",
                data={
                    "mri_id": mri_machine.id,
                    "mri_name": mri_machine.name,
                    "model": mri_machine.model,
                    "field_strength": mri_machine.field_strength
                },
                level=LogLevel.DEBUG,
                source="hospital_core"
            )
        
        # Initialize blood test nurses
        for i in range(self.num_blood_nurses):
            blood_nurse = BloodTestNurse(
                id=i + 1,
                name=f"Nurse {chr(65 + i)}",
                specialization="Blood Testing"
            )
            self.blood_nurses.append(blood_nurse)
            
            # Log blood nurse initialization
            self.logger.log_event(
                timestamp=0.0,
                event_type=EventType.SYSTEM_STATE,
                message=f"Blood Nurse {blood_nurse.id} ({blood_nurse.name}) initialized - {blood_nurse.specialization}",
                data={
                    "nurse_id": blood_nurse.id,
                    "nurse_name": blood_nurse.name,
                    "specialization": blood_nurse.specialization
                },
                level=LogLevel.DEBUG,
                source="hospital_core"
            )
        
        # Initialize beds
        for i in range(self.num_beds):
            bed = Bed(
                id=i + 1,
                name=f"Bed {i + 1:02d}",
                bed_type="General" if i < 15 else "ICU" if i < 18 else "Emergency",
                ward="General Ward" if i < 15 else "ICU" if i < 18 else "Emergency Ward"
            )
            self.beds.append(bed)
            
            # Log bed initialization
            self.logger.log_event(
                timestamp=0.0,
                event_type=EventType.SYSTEM_STATE,
                message=f"Bed {bed.id} ({bed.name}) initialized - {bed.bed_type} in {bed.ward}",
                data={
                    "bed_id": bed.id,
                    "bed_name": bed.name,
                    "bed_type": bed.bed_type,
                    "ward": bed.ward,
                    "preemptive": bed.preemptive
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
            message=f"All queues initialized: {len(Priority)} priority levels for all resources including beds",
            data={
                "priority_levels": [p.name for p in Priority],
                "beds_initialized": len(self.beds),
                "beds_non_preemptive": True
            },
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
        try:
            queue_lengths = {p.name: len(q) for p, q in self.priority_queues.items()}
        except TypeError as e:
            print(f"DEBUG: Error in get_hospital_status: {e}")
            print(f"DEBUG: priority_queues type: {type(self.priority_queues)}")
            for priority, queue in self.priority_queues.items():
                print(f"DEBUG: Priority {priority}: type={type(queue)}, value={queue}")
            raise
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
        """Complete patient treatment and assign tests if needed"""
        # Calculate actual treatment duration
        actual_treatment_time = current_time - (patient.treatment_start_time or current_time)
        total_wait_time = current_time - patient.arrival_time
        
        # Get test recommendation from doctor
        diagnosis_result = doctor.diagnose(patient)
        
        # Extract recommended tests from diagnosis result
        recommended_tests = diagnosis_result.get('recommended_tests', [])
        
        # Add tests to patient if any were recommended
        if recommended_tests:
            patient.test_results = recommended_tests
        
        doctor.busy = False
        doctor.current_patient = None
        doctor.total_patients_treated += 1
        
        # Check if patient needs tests - if so, put back in priority queue for appropriate resource
        if patient.test_results:
            # Get the first test from the list
            test = patient.test_results[0] if patient.test_results else None
            
            # Put patient back in priority queue for appropriate resource to pick up
            if test and (isinstance(test, MRITest) or isinstance(test, BloodTest)):
                # Patient goes back to priority queue and will be picked up by appropriate resource
                self.priority_queues[patient.priority].insert(0, patient)  # Insert at front for priority
                
                # Log test assignment
                test_type = "MRI" if isinstance(test, MRITest) else "Blood Test"
                self.logger.log_event(
                    timestamp=current_time,
                    event_type=EventType.QUEUE_UPDATE,
                    message=f"Patient {patient.id} returned to priority queue for {test_type}",
                    data={
                        "patient_id": patient.id,
                        "test_type": test_type,
                        "priority": patient.priority.name,
                        "condition": patient.condition
                    },
                    source="hospital_core"
                )
            else:
                # Complete patient if no recognized test
                self._complete_patient_discharge(patient, doctor, current_time, actual_treatment_time, total_wait_time)
        else:
            # Complete patient if no tests needed
            self._complete_patient_discharge(patient, doctor, current_time, actual_treatment_time, total_wait_time)
    
    def _complete_patient_discharge(self, patient: Patient, doctor: Doctor, current_time: float, actual_treatment_time: float, total_wait_time: float) -> None:
        """Complete patient discharge process"""
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
    
    def assign_mri_to_patient(self, mri_machine: MRI_Machine, patient: Patient, current_time: float) -> None:
        """Assign MRI machine to patient"""
        mri_machine.busy = True
        mri_machine.current_patient = patient
        patient.mri_start_time = current_time
        
        # Log MRI assignment
        self.logger.log_event(
            timestamp=current_time,
            event_type=EventType.DOCTOR_ASSIGNMENT,  # Reuse existing event type
            message=f"MRI Machine {mri_machine.id} ({mri_machine.name}) assigned to Patient {patient.id}",
            data={
                "mri_id": mri_machine.id,
                "mri_name": mri_machine.name,
                "patient_id": patient.id,
                "patient_condition": patient.condition,
                "patient_priority": patient.priority.name if patient.priority else "UNKNOWN"
            },
            source="hospital_core"
        )
    
    def assign_blood_nurse_to_patient(self, blood_nurse: BloodTestNurse, patient: Patient, current_time: float) -> None:
        """Assign blood test nurse to patient"""
        blood_nurse.busy = True
        blood_nurse.current_patient = patient
        patient.blood_test_start_time = current_time
        
        # Log blood nurse assignment
        self.logger.log_event(
            timestamp=current_time,
            event_type=EventType.DOCTOR_ASSIGNMENT,  # Reuse existing event type
            message=f"Blood Nurse {blood_nurse.id} ({blood_nurse.name}) assigned to Patient {patient.id}",
            data={
                "nurse_id": blood_nurse.id,
                "nurse_name": blood_nurse.name,
                "patient_id": patient.id,
                "patient_condition": patient.condition,
                "patient_priority": patient.priority.name if patient.priority else "UNKNOWN"
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
    
    def assign_bed_to_patient(self, bed: Bed, patient: Patient, current_time: float) -> None:
        """Assign bed to patient (non-preemptive)"""
        bed.admit_patient(patient, current_time)
        patient.assigned_bed = bed.id
        
        # Log bed assignment
        self.logger.log_event(
            timestamp=current_time,
            event_type=EventType.DOCTOR_ASSIGNMENT,  # Reuse existing event type
            message=f"Bed {bed.id} ({bed.name}) assigned to Patient {patient.id}",
            data={
                "bed_id": bed.id,
                "bed_name": bed.name,
                "bed_type": bed.bed_type,
                "ward": bed.ward,
                "patient_id": patient.id,
                "patient_condition": patient.condition,
                "patient_priority": patient.priority.name if patient.priority else "UNKNOWN",
                "non_preemptive": True
            },
            source="hospital_core"
        )
    
    def get_available_bed(self, bed_type: str = None) -> Optional[Bed]:
        """Get next available bed, optionally filtered by bed type"""
        available_beds = Bed.get_available_beds(self.beds)
        
        if bed_type:
            available_beds = [bed for bed in available_beds if bed.bed_type == bed_type]
        
        return available_beds[0] if available_beds else None

    def get_hospital_status(self) -> Dict:
        """Get current hospital status"""
        queue_lengths = {priority.name: len(queue) for priority, queue in self.priority_queues.items()}
        doctor_status = {doc.id: {"busy": doc.busy, "patients_treated": doc.total_patients_treated} 
                        for doc in self.doctors}
        
        # MRI machine status
        mri_status = {mri.id: {"busy": mri.busy, "patients_treated": mri.total_patients_treated} 
                     for mri in self.mri_machines}
        
        # Blood nurse status
        blood_nurse_status = {nurse.id: {"busy": nurse.busy, "patients_treated": nurse.total_patients_treated} 
                             for nurse in self.blood_nurses}
        
        # Bed status
        bed_status = {bed.id: {"busy": bed.busy, "patients_treated": bed.total_patients_treated, "bed_type": bed.bed_type, "ward": bed.ward} 
                     for bed in self.beds}
        
        return {
            "total_arrivals": self.total_arrivals,
            "total_completed": self.total_completed,
            "patients_in_system": self.total_arrivals - self.total_completed,
            "queue_lengths": queue_lengths,
            # All resources now managed through priority_queues
            "doctor_status": doctor_status,
            "mri_status": mri_status,
            "blood_nurse_status": blood_nurse_status,
            "bed_status": bed_status,
            "available_beds": len(Bed.get_available_beds(self.beds)),
            "occupied_beds": len(Bed.get_busy_beds(self.beds))
        }
