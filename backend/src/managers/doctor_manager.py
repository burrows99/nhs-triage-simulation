from typing import List
from ..entities.doctor.doctor import Doctor

class DoctorManager:
    def __init__(self):
        self.doctors: List[Doctor] = []

    def add_doctor(self, doctor: Doctor):
        self.doctors.append(doctor)

    def remove_doctor(self, doctor: Doctor):
        self.doctors.remove(doctor)

    def get_available_doctors(self) -> List[Doctor]:
        return [doctor for doctor in self.doctors if doctor.is_available()]

    def get_doctors_by_specialty(self, specialty: str) -> List[Doctor]:
        return [doctor for doctor in self.doctors if doctor.specialty.lower() == specialty.lower()]

    def get_all_doctors(self) -> List[Doctor]:
        return self.doctors
