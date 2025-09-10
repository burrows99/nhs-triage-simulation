from dataclasses import dataclass, field
from typing import List, Dict, Any
from ..entity import Entity
from ..doctor.doctor import Doctor
from ..patient.patient import Patient
from ..equipment.bed.bed import Bed
from ..equipment.MRI.MRI import MRI
from ..equipment.ultrasonic.ultrasonic import Ultrasonic
from ..triage.triage import FuzzyManchesterTriage
from ..routing.routing_agent import RoutingAgent
from ...enums.priority import Priority

@dataclass
class Hospital(Entity):
    doctors: List[Doctor] = field(default_factory=list)
    patients: List[Patient] = field(default_factory=list)
    beds: List[Bed] = field(default_factory=list)
    mri_machines: List[MRI] = field(default_factory=list)
    ultrasonic_machines: List[Ultrasonic] = field(default_factory=list)
    triage_system: FuzzyManchesterTriage = field(default_factory=FuzzyManchesterTriage)
    routing_agent: RoutingAgent = field(default_factory=RoutingAgent)
    
    # Doctor management
    def add_doctor(self, doctor: Doctor) -> None:
        """Add a doctor to the hospital"""
        self.doctors.append(doctor)
        print(f"Dr. {doctor.name} ({doctor.specialty}) added to {self.name}")
    
    def remove_doctor(self, doctor: Doctor) -> None:
        """Remove a doctor from the hospital"""
        if doctor in self.doctors:
            self.doctors.remove(doctor)
            print(f"Dr. {doctor.name} removed from {self.name}")
        else:
            print(f"Dr. {doctor.name} not found in {self.name}")
    
    def get_available_doctors(self) -> List[Doctor]:
        """Get list of available doctors"""
        return [doctor for doctor in self.doctors if doctor.is_available()]
    
    def get_doctors_by_specialty(self, specialty: str) -> List[Doctor]:
        """Get doctors by specialty"""
        return [doctor for doctor in self.doctors if doctor.specialty.lower() == specialty.lower()]
    
    # Private helper methods
    def _perform_triage(self, patient: Patient) -> Priority:
        """Perform triage and display results"""
        priority = self.triage_system.determine_priority(patient)
        print(f"Triage Priority: {priority.name_display} ({priority.value.upper()})")
        print(f"Max wait time: {priority.max_wait_time}")
        return priority
    
    def _assign_to_doctor(self, patient: Patient, priority: Priority) -> None:
        """Assign patient to available doctor using routing agent"""
        if self.routing_agent.should_assign_to_doctor(patient, priority):
            available_doctors = self.get_available_doctors()
            if available_doctors:
                doctor = available_doctors[0]
                doctor.add_patient_to_queue(patient, priority.value)
                print(f"Patient {patient.name} assigned to Dr. {doctor.name} with {priority.value} priority")
            else:
                print(f"No available doctors. Patient {patient.name} added to waiting list with {priority.value} priority")
    
    def _assign_urgent_bed(self, patient: Patient, priority: Priority) -> None:
        """Assign bed for urgent patients using routing agent"""
        if self.routing_agent.should_assign_urgent_bed(patient, priority):
            available_beds = self.get_available_beds()
            if available_beds:
                bed = available_beds[0]
                bed.add_patient_to_queue(patient, priority.value)
                print(f"Urgent patient {patient.name} also assigned to bed {bed.name}")
            else:
                print(f"No available beds for urgent patient {patient.name}")
    
    # Patient management
    def admit_patient(self, patient: Patient) -> None:
        """Admit a patient to the hospital with automatic triage"""
        self.patients.append(patient)
        print(f"Patient {patient.name} admitted to {self.name}")
        
        priority = self._perform_triage(patient)
        self._assign_to_doctor(patient, priority)
    
    def discharge_patient(self, patient: Patient) -> None:
        """Discharge a patient from the hospital"""
        if patient in self.patients:
            self.patients.remove(patient)
            # Remove from any resource queues
            if patient.resource_assigned:
                patient.resource_assigned.remove_patient_from_queue(patient)
            print(f"Patient {patient.name} discharged from {self.name}")
        else:
            print(f"Patient {patient.name} not found in {self.name}")
    
    def _add_equipment(self, equipment_list: List[Any], equipment: Any, equipment_type: str) -> None:
        """Generic helper to add equipment to hospital"""
        equipment_list.append(equipment)
        print(f"{equipment_type} {equipment.name} added to {self.name}")
    
    # Equipment management
    def add_bed(self, bed: Bed) -> None:
        """Add a bed to the hospital"""
        self._add_equipment(self.beds, bed, "Bed")
    
    def add_mri_machine(self, mri: MRI) -> None:
        """Add an MRI machine to the hospital"""
        self._add_equipment(self.mri_machines, mri, "MRI")
    
    def add_ultrasonic_machine(self, ultrasonic: Ultrasonic) -> None:
        """Add an ultrasonic machine to the hospital"""
        self._add_equipment(self.ultrasonic_machines, ultrasonic, "Ultrasonic")
    
    def get_available_beds(self) -> List[Bed]:
        """Get list of available beds"""
        return [bed for bed in self.beds if bed.is_available()]
    
    def get_available_mri_machines(self) -> List[MRI]:
        """Get list of available MRI machines"""
        return [mri for mri in self.mri_machines if mri.is_available()]
    
    def get_available_ultrasonic_machines(self) -> List[Ultrasonic]:
        """Get list of available ultrasonic machines"""
        return [ultrasonic for ultrasonic in self.ultrasonic_machines if ultrasonic.is_available()]
    
    # Hospital statistics
    def get_hospital_stats(self) -> Dict[str, int]:
        """Get comprehensive hospital statistics"""
        return {
            "total_doctors": len(self.doctors),
            "available_doctors": len(self.get_available_doctors()),
            "total_patients": len(self.patients),
            "total_beds": len(self.beds),
            "available_beds": len(self.get_available_beds()),
            "total_mri_machines": len(self.mri_machines),
            "available_mri_machines": len(self.get_available_mri_machines()),
            "total_ultrasonic_machines": len(self.ultrasonic_machines),
            "available_ultrasonic_machines": len(self.get_available_ultrasonic_machines())
        }
    
    def _add_resource_queues_to_summary(self, summary: Dict[str, Dict[str, int]], 
                                       resources: List[Any], prefix: str) -> None:
        """Helper to add resource queues to summary"""
        for resource in resources:
            summary[f"{prefix}_{resource.name}"] = resource.get_queue_status()
    
    def get_queue_summary(self) -> Dict[str, Dict[str, int]]:
        """Get summary of all resource queues"""
        summary: Dict[str, Dict[str, int]] = {}
        
        self._add_resource_queues_to_summary(summary, self.doctors, "Dr")
        self._add_resource_queues_to_summary(summary, self.beds, "Bed")
        self._add_resource_queues_to_summary(summary, self.mri_machines, "MRI")
        self._add_resource_queues_to_summary(summary, self.ultrasonic_machines, "Ultrasonic")
        
        return summary