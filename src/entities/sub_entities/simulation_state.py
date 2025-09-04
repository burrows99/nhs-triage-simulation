import attr
from typing import Dict, List, Optional
from ..patient import Patient
from ..doctor import Doctor
from ...enums.Triage import Priority

@attr.s(auto_attribs=True)
class SimulationState:
    """Centralized simulation state management using attrs"""
    
    # Time tracking
    current_time: float = 0.0
    simulation_duration: float = 480.0
    
    # Patient tracking
    total_arrivals: int = 0
    total_completed: int = 0
    patients_in_system: int = 0
    active_patients: List[Patient] = attr.ib(factory=list)
    completed_patients: List[Patient] = attr.ib(factory=list)
    
    # Queue state
    queue_lengths: Dict[Priority, int] = attr.ib(factory=lambda: {
        Priority.RED: 0,
        Priority.ORANGE: 0, 
        Priority.YELLOW: 0,
        Priority.GREEN: 0,
        Priority.BLUE: 0
    })
    
    # Doctor state
    busy_doctors: List[int] = attr.ib(factory=list)
    available_doctors: List[int] = attr.ib(factory=list)
    doctor_patient_assignments: Dict[int, Optional[int]] = attr.ib(factory=dict)
    
    # Resource utilization
    triage_utilization: float = 0.0
    doctor_utilization: float = 0.0
    
    # Statistics
    total_wait_time: float = 0.0
    total_treatment_time: float = 0.0
    preemptions_count: int = 0
    
    def update_time(self, new_time: float) -> None:
        """Update simulation time"""
        self.current_time = new_time
    
    def register_patient_arrival(self, patient: Patient) -> None:
        """Register a new patient arrival"""
        self.total_arrivals += 1
        self.patients_in_system += 1
        self.active_patients.append(patient)
    
    def register_patient_completion(self, patient: Patient) -> None:
        """Register patient completion"""
        self.total_completed += 1
        self.patients_in_system -= 1
        if patient in self.active_patients:
            self.active_patients.remove(patient)
        self.completed_patients.append(patient)
        
        # Update statistics (Patient is attr-based, these attributes are always present)
        self.total_wait_time += patient.wait_time
        self.total_treatment_time += patient.treatment_time
    
    def update_queue_length(self, priority: Priority, length: int) -> None:
        """Update queue length for a specific priority"""
        self.queue_lengths[priority] = length
    
    def update_all_queue_lengths(self, queue_lengths: Dict[Priority, int]) -> None:
        """Update all queue lengths at once"""
        for priority, length in queue_lengths.items():
            self.queue_lengths[priority] = length
    
    def assign_doctor_to_patient(self, doctor_id: int, patient_id: int) -> None:
        """Assign doctor to patient"""
        if doctor_id in self.available_doctors:
            self.available_doctors.remove(doctor_id)
        if doctor_id not in self.busy_doctors:
            self.busy_doctors.append(doctor_id)
        self.doctor_patient_assignments[doctor_id] = patient_id
    
    def release_doctor(self, doctor_id: int) -> None:
        """Release doctor from current assignment"""
        if doctor_id in self.busy_doctors:
            self.busy_doctors.remove(doctor_id)
        if doctor_id not in self.available_doctors:
            self.available_doctors.append(doctor_id)
        self.doctor_patient_assignments[doctor_id] = None
    
    def record_preemption(self) -> None:
        """Record a preemption event"""
        self.preemptions_count += 1
    
    def update_resource_utilization(self, triage_util: float, doctor_util: float) -> None:
        """Update resource utilization metrics"""
        self.triage_utilization = triage_util
        self.doctor_utilization = doctor_util
    
    def get_average_wait_time(self) -> float:
        """Calculate average wait time"""
        if self.total_completed > 0:
            return self.total_wait_time / self.total_completed
        return 0.0
    
    def get_average_treatment_time(self) -> float:
        """Calculate average treatment time"""
        if self.total_completed > 0:
            return self.total_treatment_time / self.total_completed
        return 0.0
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        return {
            'current_time': self.current_time,
            'total_arrivals': self.total_arrivals,
            'total_completed': self.total_completed,
            'patients_in_system': self.patients_in_system,
            'queue_lengths': dict(self.queue_lengths),
            'busy_doctors': len(self.busy_doctors),
            'available_doctors': len(self.available_doctors),
            'triage_utilization': self.triage_utilization,
            'doctor_utilization': self.doctor_utilization,
            'average_wait_time': self.get_average_wait_time(),
            'average_treatment_time': self.get_average_treatment_time(),
            'preemptions_count': self.preemptions_count
        }
    
    def get_log_summary(self) -> Dict:
        """Get compact simulation state summary for logging"""
        return {
            "simulation_time": self.current_time,
            "total_arrivals": self.total_arrivals,
            "total_completed": self.total_completed,
            "patients_in_system": self.patients_in_system,
            "busy_doctors": len(self.busy_doctors),
            "available_doctors": len(self.available_doctors),
            "preemptions_count": self.preemptions_count,
            "queue_lengths": {priority.name: length for priority, length in self.queue_lengths.items()}
        }
    
    def reset(self) -> None:
        """Reset simulation state"""
        self.current_time = 0.0
        self.total_arrivals = 0
        self.total_completed = 0
        self.patients_in_system = 0
        self.active_patients.clear()
        self.completed_patients.clear()
        
        for priority in self.queue_lengths:
            self.queue_lengths[priority] = 0
            
        self.busy_doctors.clear()
        self.available_doctors.clear()
        self.doctor_patient_assignments.clear()
        
        self.triage_utilization = 0.0
        self.doctor_utilization = 0.0
        self.total_wait_time = 0.0
        self.total_treatment_time = 0.0
        self.preemptions_count = 0