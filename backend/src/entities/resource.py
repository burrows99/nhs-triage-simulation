from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING
from .entity import Entity

if TYPE_CHECKING:
    from .patient.patient import Patient

@dataclass
class Resource(Entity):
    available: bool = True
    service_time: int = 0
    patient_queue: Dict[str, List["Patient"]] = field(default_factory=lambda: {
        "red": [],
        "orange": [],
        "yellow": [],
        "green": [],
        "blue": []
    })
    
    def set_available(self, available: bool) -> None:
        """Set resource availability status"""
        self.available = available
    
    def is_available(self) -> bool:
        """Check if resource is available"""
        return self.available
    
    def get_service_time(self) -> int:
        """Get resource service time"""
        return self.service_time
    
    def add_patient_to_queue(self, patient: "Patient", priority: str = "green") -> None:
        """Add a patient to the priority queue"""
        if priority not in self.patient_queue:
            raise ValueError(f"Invalid priority: {priority}. Must be one of: red, orange, yellow, green, blue")
        
        self.patient_queue[priority].append(patient)
        patient.resource_assigned = self
        print(f"Patient {patient.name} added to {priority} priority queue for {self.name}")
    
    def remove_patient_from_queue(self, patient: "Patient") -> None:
        """Remove a patient from any priority queue"""
        for priority, queue in self.patient_queue.items():
            if patient in queue:
                queue.remove(patient)
                patient.resource_assigned = None
                print(f"Patient {patient.name} removed from {priority} priority queue for {self.name}")
                return
        print(f"Patient {patient.name} not found in any queue for {self.name}")
    
    def get_current_serving_patient(self) -> Optional["Patient"]:
        """Get the first patient from the highest priority queue without removing them"""
        for priority in ["red", "orange", "yellow", "green", "blue"]:
            if self.patient_queue[priority]:
                return self.patient_queue[priority][0]
        return None
    
    def get_next_patient(self) -> Optional["Patient"]:
        """Get the next patient from the highest priority queue"""
        for priority in ["red", "orange", "yellow", "green", "blue"]:
            if self.patient_queue[priority]:
                return self.patient_queue[priority].pop(0)
        return None
    
    def get_queue_status(self) -> Dict[str, int]:
        """Get the number of patients in each priority queue"""
        return {priority: len(queue) for priority, queue in self.patient_queue.items()}
    
    def get_total_patients_in_queue(self) -> int:
        """Get total number of patients in all queues"""
        return sum(len(queue) for queue in self.patient_queue.values())