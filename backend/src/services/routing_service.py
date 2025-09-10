from typing import List, Optional, Tuple, Dict, Any
from ..entities.patient.patient import Patient
from ..entities.doctor.doctor import Doctor
from ..entities.equipment.bed.bed import Bed
from ..entities.hospital.hospital import Hospital
from ..enums.priority import Priority


class RoutingService:
    """Centralized routing service for managing all patient routing decisions and resource assignments"""
    
    def __init__(self, hospital: Hospital):
        self.hospital = hospital
    
    def make_routing_decision(self, patient: Patient, priority: Priority) -> Dict[str, Any]:
        """Make comprehensive routing decision for a patient
        
        Returns:
            Dict containing routing decisions and assignments
        """
        # Basic routing decisions
        should_assign_doctor = self._should_assign_to_doctor(patient, priority)
        should_assign_bed = self._should_assign_urgent_bed(patient, priority)
        
        # Resource assignments
        assigned_doctor = None
        assigned_bed = None
        
        if should_assign_doctor:
            assigned_doctor = self._select_optimal_doctor(patient, priority)
        
        if should_assign_bed:
            assigned_bed = self._select_optimal_bed(patient, priority)
        
        return {
            "assign_doctor": should_assign_doctor,
            "assign_bed": should_assign_bed,
            "assigned_doctor": assigned_doctor,
            "assigned_bed": assigned_bed,
            "routing_logic": self._get_routing_explanation(patient, priority, should_assign_doctor, should_assign_bed)
        }
    
    def _should_assign_to_doctor(self, patient: Patient, priority: Priority) -> bool:
        """Determine if patient should be assigned to doctor"""
        # All patients need doctor consultation
        return True
    
    def _should_assign_urgent_bed(self, patient: Patient, priority: Priority) -> bool:
        """Determine if patient needs urgent bed assignment"""
        # High priority patients (RED, ORANGE) need beds
        return priority in [Priority.RED, Priority.ORANGE]
    
    def _select_optimal_doctor(self, patient: Patient, priority: Priority) -> Optional[Doctor]:
        """Select the best available doctor for the patient
        
        Selection criteria:
        1. Doctor availability
        2. Queue length (load balancing)
        3. Priority-based specialization (future enhancement)
        """
        available_doctors = self.hospital.get_available_doctors()
        
        if not available_doctors:
            return None
        
        # For now, use simple load balancing - choose doctor with least patients
        optimal_doctor = min(available_doctors, key=lambda d: d.get_total_patients_in_queue())
        
        return optimal_doctor
    
    def _select_optimal_bed(self, patient: Patient, priority: Priority) -> Optional[Bed]:
        """Select the best available bed for the patient
        
        Selection criteria:
        1. Bed availability
        2. Priority-based bed type (ICU for critical patients)
        3. Bed capacity
        """
        available_beds = self.hospital.get_available_beds()
        
        if not available_beds:
            return None
        
        # For critical patients (RED), prefer ICU beds
        if priority == Priority.RED:
            icu_beds = [bed for bed in available_beds if "ICU" in bed.name]
            if icu_beds:
                return icu_beds[0]
        
        # Otherwise, return first available bed
        return available_beds[0]
    
    def assign_patient_to_doctor(self, patient: Patient, doctor: Doctor, priority: Priority) -> Dict[str, Any]:
        """Assign patient to doctor and manage queue
        
        Returns:
            Dict with queue information
        """
        # Add to doctor's queue
        doctor.add_patient_to_queue(patient, priority.value)
        
        queue_info = {
            "queue_position": len([p for p in doctor.patient_queue[priority.value]]),
            "total_in_queue": doctor.get_total_patients_in_queue(),
            "doctor_name": doctor.name,
            "priority": priority.value
        }
        
        return queue_info
    
    def assign_patient_to_bed(self, patient: Patient, bed: Bed, priority: Priority) -> Dict[str, Any]:
        """Assign patient to bed
        
        Returns:
            Dict with bed assignment information
        """
        bed.add_patient_to_queue(patient, priority.value)
        
        bed_info = {
            "bed_name": bed.name,
            "bed_type": "ICU" if "ICU" in bed.name else "Ward",
            "priority": priority.value
        }
        
        return bed_info
    
    def calculate_wait_time(self, priority: Priority, doctor: Doctor) -> float:
        """Calculate expected wait time for patient based on priority and doctor queue"""
        base_wait_times = {
            Priority.RED: 0,      # Immediate
            Priority.ORANGE: 2,   # 2 minutes
            Priority.YELLOW: 5,   # 5 minutes
            Priority.GREEN: 10,   # 10 minutes
            Priority.BLUE: 15     # 15 minutes
        }
        
        base_wait = base_wait_times.get(priority, 10)
        queue_factor = doctor.get_total_patients_in_queue() * 2  # 2 minutes per patient in queue
        
        return base_wait + queue_factor
    
    def calculate_consultation_time(self, priority: Priority) -> float:
        """Calculate consultation duration based on priority"""
        consultation_times = {
            Priority.RED: 45,     # 45 minutes for critical
            Priority.ORANGE: 30,  # 30 minutes for very urgent
            Priority.YELLOW: 20,  # 20 minutes for urgent
            Priority.GREEN: 15,   # 15 minutes for standard
            Priority.BLUE: 10     # 10 minutes for non-urgent
        }
        
        return consultation_times.get(priority, 15)
    
    def calculate_bed_time(self, priority: Priority) -> float:
        """Calculate bed occupancy duration based on priority"""
        bed_times = {
            Priority.RED: 120,    # 2 hours for critical
            Priority.ORANGE: 90,  # 1.5 hours for very urgent
            Priority.YELLOW: 60,  # 1 hour for urgent
            Priority.GREEN: 30,   # 30 minutes for standard
            Priority.BLUE: 15     # 15 minutes for non-urgent
        }
        
        return bed_times.get(priority, 60)
    
    def _get_routing_explanation(self, patient: Patient, priority: Priority, 
                               assign_doctor: bool, assign_bed: bool) -> str:
        """Generate human-readable explanation of routing decision"""
        explanations = []
        
        if assign_doctor:
            explanations.append(f"Doctor consultation required for {priority.name_display} priority")
        
        if assign_bed:
            explanations.append(f"Urgent bed assignment for {priority.name_display} priority")
        
        if not assign_bed and priority in [Priority.YELLOW, Priority.GREEN, Priority.BLUE]:
            explanations.append("No bed required - outpatient treatment")
        
        return "; ".join(explanations) if explanations else "Standard routing protocol"
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get current routing and resource utilization statistics"""
        doctors = self.hospital.get_all_doctors()
        beds = self.hospital.get_all_beds()
        
        doctor_stats = {
            "total_doctors": len(doctors),
            "available_doctors": len(self.hospital.get_available_doctors()),
            "doctor_utilization": {}
        }
        
        for doctor in doctors:
            doctor_stats["doctor_utilization"][doctor.name] = {
                "total_patients": doctor.get_total_patients_in_queue(),
                "by_priority": dict(doctor.patient_queue)
            }
        
        bed_stats = {
            "total_beds": len(beds),
            "available_beds": len(self.hospital.get_available_beds()),
            "bed_utilization": {}
        }
        
        for bed in beds:
            bed_stats["bed_utilization"][bed.name] = {
                "occupied": bed.get_total_patients_in_queue() > 0,
                "patients": bed.get_total_patients_in_queue()
            }
        
        return {
            "doctors": doctor_stats,
            "beds": bed_stats,
            "timestamp": self.hospital.env.now if hasattr(self.hospital, 'env') else 0
        }