from typing import List
from ..entities.equipment.MRI.MRI import MRI
from ..entities.equipment.ultrasonic.ultrasonic import Ultrasonic

class EquipmentManager:
    def __init__(self):
        self.mri_machines: List[MRI] = []
        self.ultrasonic_machines: List[Ultrasonic] = []

    def add_mri_machine(self, mri: MRI):
        self.mri_machines.append(mri)

    def remove_mri_machine(self, mri: MRI):
        self.mri_machines.remove(mri)

    def get_available_mri_machines(self) -> List[MRI]:
        return [mri for mri in self.mri_machines if mri.is_available()]

    def get_all_mri_machines(self) -> List[MRI]:
        return self.mri_machines

    def add_ultrasonic_machine(self, ultrasonic: Ultrasonic):
        self.ultrasonic_machines.append(ultrasonic)

    def remove_ultrasonic_machine(self, ultrasonic: Ultrasonic):
        self.ultrasonic_machines.remove(ultrasonic)

    def get_available_ultrasonic_machines(self) -> List[Ultrasonic]:
        return [ultrasonic for ultrasonic in self.ultrasonic_machines if ultrasonic.is_available()]

    def get_all_ultrasonic_machines(self) -> List[Ultrasonic]:
        return self.ultrasonic_machines
