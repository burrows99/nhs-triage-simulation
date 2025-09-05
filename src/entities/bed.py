import attr
from typing import Optional
from .patient import Patient

@attr.s(auto_attribs=True)
class Bed:
    """Hospital bed resource for patient accommodation (non-preemptive)"""
    id: int
    name: str
    bed_type: str = "General"
    ward: str = "General Ward"
    current_patient: Optional[Patient] = None
    busy: bool = False
    total_patients_treated: int = 0
    preemptive: bool = False  # Beds are non-preemptive resources
    
    def admit_patient(self, patient: Patient, current_time: float) -> Patient:
        """Admit patient to bed (non-preemptive allocation)"""
        self.current_patient = patient
        self.busy = True
        patient.bed_admission_time = current_time
        
        return patient
    
    def discharge_patient(self, patient: Patient, current_time: float, logger=None) -> Patient:
        """Discharge patient from bed and release resources"""
        # Release bed resources
        self.busy = False
        self.current_patient = None
        self.total_patients_treated += 1
        
        # Calculate bed stay duration
        bed_stay_duration = current_time - (patient.bed_admission_time or current_time)
        
        # Log discharge if logger provided
        if logger:
            from ..utils.logger import EventType
            logger.log_event(
                timestamp=current_time,
                event_type=EventType.BED_DISCHARGE,
                message=f"Patient {patient.id} discharged from Bed {self.id}",
                data={
                    "patient_id": patient.id,
                    "bed_id": self.id,
                    "bed_name": self.name,
                    "bed_type": self.bed_type,
                    "ward": self.ward,
                    "bed_stay_duration": bed_stay_duration,
                    "bed_total_patients": self.total_patients_treated
                },
                source="bed"
            )
        
        return patient
    
    @staticmethod
    def get_busy_beds(beds: list) -> list:
        """Get list of currently occupied beds"""
        return [bed for bed in beds if bed.busy and bed.current_patient is not None]
    
    @staticmethod
    def get_available_beds(beds: list) -> list:
        """Get list of available beds for patient admission"""
        return [bed for bed in beds if not bed.busy and bed.current_patient is None]
    
    def is_available(self) -> bool:
        """Check if bed is available for new patient"""
        return not self.busy and self.current_patient is None
    
    def get_bed_status(self) -> dict:
        """Get current bed status information"""
        return {
            "id": self.id,
            "name": self.name,
            "bed_type": self.bed_type,
            "ward": self.ward,
            "busy": self.busy,
            "current_patient_id": self.current_patient.id if self.current_patient else None,
            "total_patients_treated": self.total_patients_treated,
            "preemptive": self.preemptive
        }