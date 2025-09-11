from dataclasses import dataclass, field
from typing import List, Dict, Any
from ..entity import Entity
from ..doctor.doctor import Doctor
from ..patient.patient import Patient
from ..equipment.bed.bed import Bed
from ..equipment.MRI.MRI import MRI
from ..equipment.ultrasonic.ultrasonic import Ultrasonic
from ..triage.triage import FuzzyManchesterTriage
from ...enums.priority import Priority
from ...managers.doctor_manager import DoctorManager
from ...managers.bed_manager import BedManager
from ...managers.equipment_manager import EquipmentManager

@dataclass
class Hospital(Entity):
    patients: List[Patient] = field(default_factory=list)
    triage_system: FuzzyManchesterTriage = field(default_factory=FuzzyManchesterTriage)
    doctor_manager: DoctorManager = field(default_factory=DoctorManager)
    bed_manager: BedManager = field(default_factory=BedManager)
    equipment_manager: EquipmentManager = field(default_factory=EquipmentManager)

    # Doctor management
    def add_doctor(self, doctor: Doctor) -> None:
        """Add a doctor to the hospital"""
        self.doctor_manager.add_doctor(doctor)
        print(f"Dr. {doctor.name} ({doctor.specialty}) added to {self.name}")

    def remove_doctor(self, doctor: Doctor) -> None:
        """Remove a doctor from the hospital"""
        self.doctor_manager.remove_doctor(doctor)
        print(f"Dr. {doctor.name} removed from {self.name}")

    def get_available_doctors(self) -> List[Doctor]:
        """Get list of available doctors"""
        return self.doctor_manager.get_available_doctors()

    def get_doctors_by_specialty(self, specialty: str) -> List[Doctor]:
        """Get doctors by specialty"""
        return self.doctor_manager.get_doctors_by_specialty(specialty)

    # Private helper methods
    def _perform_triage(self, patient: Patient) -> Priority:
        """Perform triage and display results"""
        priority = self.triage_system.determine_priority(patient)
        print(f"Triage Priority: {priority.name_display} ({priority.value.upper()})")
        print(f"Max wait time: {priority.max_wait_time}")
        return priority

    # Patient management
    def admit_patient(self, patient: Patient) -> None:
        """Admit a patient to the hospital with automatic triage"""
        self.patients.append(patient)
        print(f"Patient {patient.name} admitted to {self.name}")

        self._perform_triage(patient)

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

    # Equipment management
    def add_bed(self, bed: Bed) -> None:
        """Add a bed to the hospital"""
        self.bed_manager.add_bed(bed)
        print(f"Bed {bed.name} added to {self.name}")

    def add_mri_machine(self, mri: MRI) -> None:
        """Add an MRI machine to the hospital"""
        self.equipment_manager.add_mri_machine(mri)
        print(f"MRI {mri.name} added to {self.name}")

    def add_ultrasonic_machine(self, ultrasonic: Ultrasonic) -> None:
        """Add an ultrasonic machine to the hospital"""
        self.equipment_manager.add_ultrasonic_machine(ultrasonic)
        print(f"Ultrasonic {ultrasonic.name} added to {self.name}")

    def get_available_beds(self) -> List[Bed]:
        """Get list of available beds"""
        return self.bed_manager.get_available_beds()

    def get_available_mri_machines(self) -> List[MRI]:
        """Get list of available MRI machines"""
        return self.equipment_manager.get_available_mri_machines()

    def get_available_ultrasonic_machines(self) -> List[Ultrasonic]:
        """Get list of available ultrasonic machines"""
        return self.equipment_manager.get_available_ultrasonic_machines()

    # Hospital statistics
    def get_hospital_stats(self) -> Dict[str, int]:
        """Get comprehensive hospital statistics"""
        return {
            "total_doctors": len(self.doctor_manager.get_all_doctors()),
            "available_doctors": len(self.get_available_doctors()),
            "total_patients": len(self.patients),
            "total_beds": len(self.bed_manager.get_all_beds()),
            "available_beds": len(self.get_available_beds()),
            "total_mri_machines": len(self.equipment_manager.get_all_mri_machines()),
            "available_mri_machines": len(self.get_available_mri_machines()),
            "total_ultrasonic_machines": len(self.equipment_manager.get_all_ultrasonic_machines()),
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

        self._add_resource_queues_to_summary(summary, self.doctor_manager.get_all_doctors(), "Dr")
        self._add_resource_queues_to_summary(summary, self.bed_manager.get_all_beds(), "Bed")
        self._add_resource_queues_to_summary(summary, self.equipment_manager.get_all_mri_machines(), "MRI")
        self._add_resource_queues_to_summary(summary, self.equipment_manager.get_all_ultrasonic_machines(), "Ultrasonic")

        return summary
