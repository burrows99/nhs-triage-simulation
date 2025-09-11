
from ..entities.hospital.hospital import Hospital
from ..entities.doctor.doctor import Doctor
from ..entities.equipment.bed.bed import Bed
from ..entities.equipment.MRI.MRI import MRI
from ..entities.equipment.ultrasonic.ultrasonic import Ultrasonic

class HospitalFactory:
    @staticmethod
    def create_hospital(name: str = "City General Hospital", num_doctors: int = 4, num_beds: int = 5, num_mri: int = 2, num_ultrasonic: int = 2) -> Hospital:
        hospital = Hospital(id=1, name=name)

        # Add doctors
        doctors = [
            Doctor(id=101, name="Dr. Smith", specialty="Emergency Medicine"),
            Doctor(id=102, name="Dr. Johnson", specialty="Cardiology"),
            Doctor(id=103, name="Dr. Williams", specialty="General Practice"),
            Doctor(id=104, name="Dr. Brown", specialty="Surgery")
        ]
        for i in range(num_doctors):
            hospital.add_doctor(doctors[i])

        # Add beds
        for i in range(num_beds):
            hospital.add_bed(Bed(id=201 + i, name=f"Bed-{i+1}"))

        # Add MRI machines
        for i in range(num_mri):
            hospital.add_mri_machine(MRI(id=301 + i, name=f"MRI-{i+1}"))

        # Add ultrasonic machines
        for i in range(num_ultrasonic):
            hospital.add_ultrasonic_machine(Ultrasonic(id=401 + i, name=f"Ultrasonic-{i+1}"))

        return hospital

    @staticmethod
    def create_sample_hospital() -> Hospital:
        """Create a sample hospital for simulation"""
        hospital = Hospital(id=1, name="SimPy General Hospital")

        # Add doctors
        doctors = [
            Doctor(id=101, name="Dr. Emergency", specialty="Emergency Medicine"),
            Doctor(id=102, name="Dr. Heart", specialty="Cardiology"),
            Doctor(id=103, name="Dr. General", specialty="General Practice")
        ]

        for doctor in doctors:
            hospital.add_doctor(doctor)

        # Add beds
        beds = [
            Bed(id=201, name="ICU-1"),
            Bed(id=202, name="Ward-A1"),
            Bed(id=203, name="Ward-A2")
        ]

        for bed in beds:
            hospital.add_bed(bed)

        return hospital
