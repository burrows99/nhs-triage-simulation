from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum
import uuid
from datetime import datetime


class PatientStatus(Enum):
    """Enum for patient status throughout the ED journey"""
    ARRIVED = "arrived"
    WAITING_TRIAGE = "waiting_triage"
    IN_TRIAGE = "in_triage"
    WAITING_CONSULTATION = "waiting_consultation"
    IN_CONSULTATION = "in_consultation"
    WAITING_ADMISSION = "waiting_admission"
    ADMITTED = "admitted"
    DISCHARGED = "discharged"
    LEFT_WITHOUT_BEING_SEEN = "lwbs"


class Priority(Enum):
    """NHS Manchester Triage System Priority Levels"""
    IMMEDIATE = 1  # Red - Life threatening
    VERY_URGENT = 2  # Orange - Imminently life threatening
    URGENT = 3  # Yellow - Urgent
    STANDARD = 4  # Green - Less urgent
    NON_URGENT = 5  # Blue - Non-urgent


@dataclass
class PatientMetrics:
    """Data class to store patient journey metrics"""
    arrival_time: float = 0.0
    triage_start_time: Optional[float] = None
    triage_end_time: Optional[float] = None
    consultation_start_time: Optional[float] = None
    consultation_end_time: Optional[float] = None
    departure_time: Optional[float] = None
    
    @property
    def triage_wait_time(self) -> Optional[float]:
        """Time waited before triage started"""
        if self.triage_start_time is not None:
            return self.triage_start_time - self.arrival_time
        return None
    
    @property
    def triage_duration(self) -> Optional[float]:
        """Duration of triage process"""
        if self.triage_start_time is not None and self.triage_end_time is not None:
            return self.triage_end_time - self.triage_start_time
        return None
    
    @property
    def consultation_wait_time(self) -> Optional[float]:
        """Time waited before consultation started"""
        if self.consultation_start_time is not None and self.triage_end_time is not None:
            return self.consultation_start_time - self.triage_end_time
        return None
    
    @property
    def consultation_duration(self) -> Optional[float]:
        """Duration of consultation process"""
        if self.consultation_start_time is not None and self.consultation_end_time is not None:
            return self.consultation_end_time - self.consultation_start_time
        return None
    
    @property
    def total_time_in_system(self) -> Optional[float]:
        """Total time from arrival to departure"""
        if self.departure_time is not None:
            return self.departure_time - self.arrival_time
        return None


class Patient:
    """Patient entity for emergency department simulation"""
    
    def __init__(self, 
                 patient_id: Optional[str] = None,
                 arrival_time: float = 0.0,
                 age: Optional[int] = None,
                 gender: Optional[str] = None,
                 chief_complaint: Optional[str] = None,
                 vital_signs: Optional[Dict[str, Any]] = None,
                 medical_history: Optional[Dict[str, Any]] = None):
        """
        Initialize a patient entity
        
        Args:
            patient_id: Unique identifier for the patient
            arrival_time: Simulation time when patient arrived
            age: Patient age
            gender: Patient gender
            chief_complaint: Primary reason for ED visit
            vital_signs: Dictionary of vital signs (BP, HR, temp, etc.)
            medical_history: Dictionary of relevant medical history
        """
        self.patient_id = patient_id or str(uuid.uuid4())
        self.arrival_time = arrival_time
        self.age = age
        self.gender = gender
        self.chief_complaint = chief_complaint
        self.vital_signs = vital_signs or {}
        self.medical_history = medical_history or {}
        
        # Triage and priority information
        self.priority: Optional[Priority] = None
        self.triage_score: Optional[float] = None
        self.triage_notes: str = ""
        
        # Status tracking
        self.status = PatientStatus.ARRIVED
        self.status_history = [(PatientStatus.ARRIVED, arrival_time)]
        
        # Metrics tracking
        self.metrics = PatientMetrics(arrival_time=arrival_time)
        
        # Treatment information
        self.assigned_doctor: Optional[str] = None
        self.assigned_nurse: Optional[str] = None
        self.assigned_cubicle: Optional[str] = None
        self.treatment_plan: Optional[str] = None
        self.discharge_disposition: Optional[str] = None
        
        # Additional attributes for simulation
        self.requires_admission: bool = False
        self.estimated_consultation_time: Optional[float] = None
        self.custom_attributes: Dict[str, Any] = {}
    
    def update_status(self, new_status: PatientStatus, timestamp: float) -> None:
        """Update patient status and record timestamp"""
        self.status = new_status
        self.status_history.append((new_status, timestamp))
        
        # Update metrics based on status changes
        if new_status == PatientStatus.IN_TRIAGE:
            self.metrics.triage_start_time = timestamp
        elif new_status == PatientStatus.WAITING_CONSULTATION:
            self.metrics.triage_end_time = timestamp
        elif new_status == PatientStatus.IN_CONSULTATION:
            self.metrics.consultation_start_time = timestamp
        elif new_status in [PatientStatus.ADMITTED, PatientStatus.DISCHARGED, PatientStatus.LEFT_WITHOUT_BEING_SEEN]:
            if self.metrics.consultation_start_time is not None:
                self.metrics.consultation_end_time = timestamp
            self.metrics.departure_time = timestamp
    
    def set_priority(self, priority: Priority, score: Optional[float] = None, notes: str = "") -> None:
        """Set patient priority from triage assessment"""
        self.priority = priority
        self.triage_score = score
        self.triage_notes = notes
    
    def add_vital_sign(self, name: str, value: Any, timestamp: Optional[float] = None) -> None:
        """Add or update a vital sign measurement"""
        if timestamp is not None:
            # Store with timestamp for trending
            if name not in self.vital_signs:
                self.vital_signs[name] = []
            self.vital_signs[name].append((value, timestamp))
        else:
            # Store single value
            self.vital_signs[name] = value
    
    def get_current_vital_sign(self, name: str) -> Any:
        """Get the most recent value of a vital sign"""
        if name not in self.vital_signs:
            return None
        
        value = self.vital_signs[name]
        if isinstance(value, list) and value:
            # Return most recent value from timestamped list
            return value[-1][0]
        return value
    
    def add_custom_attribute(self, key: str, value: Any) -> None:
        """Add custom attribute for simulation-specific data"""
        self.custom_attributes[key] = value
    
    def get_custom_attribute(self, key: str, default: Any = None) -> Any:
        """Get custom attribute value"""
        return self.custom_attributes.get(key, default)
    
    def get_time_in_current_status(self, current_time: float) -> float:
        """Get time spent in current status"""
        if self.status_history:
            last_status_change = self.status_history[-1][1]
            return current_time - last_status_change
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert patient to dictionary for serialization"""
        return {
            'patient_id': self.patient_id,
            'arrival_time': self.arrival_time,
            'age': self.age,
            'gender': self.gender,
            'chief_complaint': self.chief_complaint,
            'vital_signs': self.vital_signs,
            'medical_history': self.medical_history,
            'priority': self.priority.value if self.priority else None,
            'triage_score': self.triage_score,
            'triage_notes': self.triage_notes,
            'status': self.status.value,
            'status_history': [(status.value, timestamp) for status, timestamp in self.status_history],
            'assigned_doctor': self.assigned_doctor,
            'assigned_nurse': self.assigned_nurse,
            'assigned_cubicle': self.assigned_cubicle,
            'treatment_plan': self.treatment_plan,
            'discharge_disposition': self.discharge_disposition,
            'requires_admission': self.requires_admission,
            'estimated_consultation_time': self.estimated_consultation_time,
            'custom_attributes': self.custom_attributes,
            'metrics': {
                'arrival_time': self.metrics.arrival_time,
                'triage_start_time': self.metrics.triage_start_time,
                'triage_end_time': self.metrics.triage_end_time,
                'consultation_start_time': self.metrics.consultation_start_time,
                'consultation_end_time': self.metrics.consultation_end_time,
                'departure_time': self.metrics.departure_time,
                'triage_wait_time': self.metrics.triage_wait_time,
                'triage_duration': self.metrics.triage_duration,
                'consultation_wait_time': self.metrics.consultation_wait_time,
                'consultation_duration': self.metrics.consultation_duration,
                'total_time_in_system': self.metrics.total_time_in_system
            }
        }
    
    def __str__(self) -> str:
        priority_str = f"P{self.priority.value}" if self.priority else "No Priority"
        return f"Patient {self.patient_id[:8]} ({priority_str}) - {self.status.value}"
    
    def __repr__(self) -> str:
        return f"Patient(id={self.patient_id}, priority={self.priority}, status={self.status})"