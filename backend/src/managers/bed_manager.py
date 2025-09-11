from typing import List
from ..entities.equipment.bed.bed import Bed

class BedManager:
    def __init__(self):
        self.beds: List[Bed] = []

    def add_bed(self, bed: Bed):
        self.beds.append(bed)

    def remove_bed(self, bed: Bed):
        self.beds.remove(bed)

    def get_available_beds(self) -> List[Bed]:
        return [bed for bed in self.beds if bed.is_available()]

    def get_all_beds(self) -> List[Bed]:
        return self.beds
