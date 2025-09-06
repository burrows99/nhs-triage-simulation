from dataclasses import dataclass, field
from typing import Optional, List
import uuid
import simpy

try:
    from ..enums.resource_type import ResourceType
    from .patient import Patient
except ImportError:
    from enums.resource_type import ResourceType
    from entities.patient import Patient


@dataclass
class BedMetrics:
    """
    Performance metrics for hospital bed.
    
    Tracks occupancy, patient throughput, and bed management efficiency
    essential for capacity planning and patient flow optimization.
    """
    total_patients_admitted: int = 0
    total_occupancy_time: float = 0.0
    total_vacant_time: float = 0.0
    cleaning_time: float = 0.0
    maintenance_time: float = 0.0
    current_admission_start: Optional[float] = None
    
    def __post_init__(self) -> None:
        """Validate metrics to ensure data integrity."""
        if self.total_patients_admitted < 0:
            raise ValueError("Total patients admitted cannot be negative")
        if self.total_occupancy_time < 0:
            raise ValueError("Total occupancy time cannot be negative")
        if self.total_vacant_time < 0:
            raise ValueError("Total vacant time cannot be negative")
        if self.cleaning_time < 0:
            raise ValueError("Cleaning time cannot be negative")
        if self.maintenance_time < 0:
            raise ValueError("Maintenance time cannot be negative")
    
    @property
    def occupancy_rate(self) -> float:
        """Calculate bed occupancy rate (0.0 to 1.0)."""
        total_available_time = self.total_occupancy_time + self.total_vacant_time
        if total_available_time == 0:
            return 0.0
        return self.total_occupancy_time / total_available_time
    
    @property
    def operational_efficiency(self) -> float:
        """
        Calculate operational efficiency including cleaning and maintenance.
        
        Returns efficiency as ratio of patient occupancy to total time.
        """
        total_time = (self.total_occupancy_time + self.total_vacant_time + 
                     self.cleaning_time + self.maintenance_time)
        if total_time == 0:
            return 0.0
        return self.total_occupancy_time / total_time
    
    @property
    def average_stay_duration(self) -> float:
        """Calculate average patient stay duration."""
        if self.total_patients_admitted == 0:
            return 0.0
        return self.total_occupancy_time / self.total_patients_admitted
    
    @property
    def turnover_rate(self) -> float:
        """Calculate bed turnover rate (patients per day)."""
        total_days = (self.total_occupancy_time + self.total_vacant_time) / (24 * 60)  # Convert to days
        if total_days == 0:
            return 0.0
        return self.total_patients_admitted / total_days


@dataclass
class Bed:
    """
    Hospital bed entity representing a non-preemptive resource.
    
    Beds are non-preemptive resources - once a patient is admitted,
    they cannot be displaced until their stay is complete. This reflects
    the reality of hospital bed management where patient displacement
    is medically and ethically problematic.
    
    Key capabilities:
    - Non-preemptive patient admission
    - Occupancy tracking and metrics
    - Cleaning and maintenance scheduling
    - Capacity planning support
    
    Reference: NHS Bed Management Guidelines
    https://www.england.nhs.uk/publication/bed-availability-and-occupancy/
    """
    bed_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    bed_number: str = field(default="")
    ward_name: str = field(default="General Ward")
    bed_type: str = field(default="Standard")  # Standard, ICU, Isolation, etc.
    is_available: bool = field(default=True)
    is_under_maintenance: bool = field(default=False)
    needs_cleaning: bool = field(default=False)
    current_patient: Optional[Patient] = field(default=None)
    resource_type: ResourceType = field(default=ResourceType.BED, init=False)
    metrics: BedMetrics = field(default_factory=BedMetrics)
    occupancy_history: List[tuple[float, str, str]] = field(default_factory=list, init=False)
    
    # SimPy resource for simulation (non-preemptive)
    simpy_resource: Optional[simpy.Resource] = field(default=None, init=False)
    
    def __post_init__(self) -> None:
        """Initialize bed with validation."""
        self._validate_bed_data()
        if not self.bed_number:
            self.bed_number = f"BED-{self.bed_id[:8]}"
    
    def _validate_bed_data(self) -> None:
        """Validate bed data integrity."""
        if not self.bed_id:
            raise ValueError("Bed ID cannot be empty")
        if not self.ward_name:
            raise ValueError("Ward name cannot be empty")
        if not self.bed_type:
            raise ValueError("Bed type cannot be empty")
    
    def initialize_simpy_resource(self, env: simpy.Environment, capacity: int = 1) -> None:
        """
        Initialize SimPy non-preemptive resource for simulation.
        
        Args:
            env: SimPy environment
            capacity: Resource capacity (typically 1 for individual bed)
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        # Note: Using regular Resource, not PreemptiveResource
        self.simpy_resource = simpy.Resource(env, capacity=capacity)
    
    def admit_patient(self, patient: Patient, current_time: float) -> None:
        """
        Admit a patient to the bed.
        
        Args:
            patient: Patient to admit
            current_time: Current simulation time
            
        Raises:
            ValueError: If bed is not available or patient is invalid
        """
        if not self.is_available:
            raise ValueError(f"Bed {self.bed_number} is not available")
        if self.is_under_maintenance:
            raise ValueError(f"Bed {self.bed_number} is under maintenance")
        if self.needs_cleaning:
            raise ValueError(f"Bed {self.bed_number} needs cleaning")
        if self.current_patient is not None:
            raise ValueError(f"Bed {self.bed_number} is already occupied")
        if current_time < 0:
            raise ValueError("Current time cannot be negative")
        
        self.current_patient = patient
        self.is_available = False
        self.metrics.current_admission_start = current_time
        
        # Record admission
        self.occupancy_history.append((
            current_time,
            "ADMISSION",
            f"Patient {patient.patient_id[:8]} admitted (Priority: {patient.priority.name})"
        ))
    
    def discharge_patient(self, current_time: float) -> Optional[Patient]:
        """
        Discharge current patient from the bed.
        
        Args:
            current_time: Current simulation time
            
        Returns:
            The discharged patient, or None if no patient
            
        Raises:
            ValueError: If no patient is admitted or invalid time
        """
        if self.current_patient is None:
            raise ValueError(f"Bed {self.bed_number} has no patient to discharge")
        if current_time < 0:
            raise ValueError("Current time cannot be negative")
        if (self.metrics.current_admission_start is not None and 
            current_time < self.metrics.current_admission_start):
            raise ValueError("Current time cannot be before admission start")
        
        discharged_patient = self.current_patient
        stay_duration = 0.0
        
        if self.metrics.current_admission_start is not None:
            stay_duration = current_time - self.metrics.current_admission_start
            self.metrics.total_occupancy_time += stay_duration
        
        # Update metrics
        self.metrics.total_patients_admitted += 1
        self.metrics.current_admission_start = None
        
        # Reset bed state
        self.current_patient = None
        self.needs_cleaning = True  # Bed needs cleaning after discharge
        # Note: is_available remains False until cleaning is complete
        
        # Record discharge
        self.occupancy_history.append((
            current_time,
            "DISCHARGE",
            f"Patient {discharged_patient.patient_id[:8]} discharged (Stay: {stay_duration:.1f}min)"
        ))
        
        return discharged_patient
    
    def start_cleaning(self, current_time: float) -> None:
        """
        Start bed cleaning process.
        
        Args:
            current_time: Current simulation time
            
        Raises:
            ValueError: If bed doesn't need cleaning or is occupied
        """
        if not self.needs_cleaning:
            raise ValueError(f"Bed {self.bed_number} doesn't need cleaning")
        if self.current_patient is not None:
            raise ValueError(f"Cannot clean occupied bed {self.bed_number}")
        
        # Record cleaning start
        self.occupancy_history.append((
            current_time,
            "CLEANING_START",
            "Bed cleaning started"
        ))
    
    def complete_cleaning(self, current_time: float, cleaning_duration: float) -> None:
        """
        Complete bed cleaning process.
        
        Args:
            current_time: Current simulation time
            cleaning_duration: Duration of cleaning in minutes
            
        Raises:
            ValueError: If bed doesn't need cleaning or invalid duration
        """
        if not self.needs_cleaning:
            raise ValueError(f"Bed {self.bed_number} doesn't need cleaning")
        if cleaning_duration < 0:
            raise ValueError("Cleaning duration cannot be negative")
        
        self.needs_cleaning = False
        self.is_available = True  # Bed is now available for new patient
        self.metrics.cleaning_time += cleaning_duration
        
        # Record cleaning completion
        self.occupancy_history.append((
            current_time,
            "CLEANING_COMPLETE",
            f"Bed cleaning completed (Duration: {cleaning_duration:.1f}min)"
        ))
    
    def start_maintenance(self, current_time: float, reason: str = "Scheduled") -> None:
        """
        Start maintenance period.
        
        Args:
            current_time: Current simulation time
            reason: Reason for maintenance
            
        Raises:
            ValueError: If bed is currently occupied
        """
        if self.current_patient is not None:
            raise ValueError(f"Cannot start maintenance while bed is occupied")
        if self.is_under_maintenance:
            raise ValueError(f"Bed {self.bed_number} is already under maintenance")
        
        self.is_under_maintenance = True
        self.is_available = False
        
        # Record maintenance start
        self.occupancy_history.append((
            current_time,
            "MAINTENANCE_START",
            f"Maintenance started: {reason}"
        ))
    
    def complete_maintenance(self, current_time: float, maintenance_duration: float) -> None:
        """
        Complete maintenance period.
        
        Args:
            current_time: Current simulation time
            maintenance_duration: Duration of maintenance in minutes
            
        Raises:
            ValueError: If bed is not under maintenance
        """
        if not self.is_under_maintenance:
            raise ValueError(f"Bed {self.bed_number} is not under maintenance")
        if maintenance_duration < 0:
            raise ValueError("Maintenance duration cannot be negative")
        
        self.is_under_maintenance = False
        self.is_available = True
        self.metrics.maintenance_time += maintenance_duration
        
        # Record maintenance completion
        self.occupancy_history.append((
            current_time,
            "MAINTENANCE_COMPLETE",
            f"Maintenance completed (Duration: {maintenance_duration:.1f}min)"
        ))
    
    def add_vacant_time(self, vacant_duration: float) -> None:
        """
        Add vacant time to metrics.
        
        Args:
            vacant_duration: Duration of vacant time in minutes
            
        Raises:
            ValueError: If vacant duration is negative
        """
        if vacant_duration < 0:
            raise ValueError("Vacant duration cannot be negative")
        self.metrics.total_vacant_time += vacant_duration
    
    def can_admit_patient(self, patient: Patient) -> bool:
        """
        Check if bed can admit the given patient.
        
        Args:
            patient: Patient requesting admission
            
        Returns:
            True if bed can admit patient, False otherwise
        """
        if not self.is_available:
            return False
        if self.is_under_maintenance:
            return False
        if self.needs_cleaning:
            return False
        if self.current_patient is not None:
            return False
        
        # Additional checks could be added here for bed type compatibility
        # e.g., ICU patients need ICU beds, isolation patients need isolation beds
        return True
    
    def get_performance_summary(self) -> dict[str, float]:
        """
        Get comprehensive performance summary.
        
        Returns:
            Dictionary with key performance indicators
        """
        return {
            "occupancy_rate": self.metrics.occupancy_rate,
            "operational_efficiency": self.metrics.operational_efficiency,
            "total_patients_admitted": float(self.metrics.total_patients_admitted),
            "average_stay_duration_hours": self.metrics.average_stay_duration / 60.0,
            "turnover_rate_per_day": self.metrics.turnover_rate,
            "total_occupancy_hours": self.metrics.total_occupancy_time / 60.0,
            "total_vacant_hours": self.metrics.total_vacant_time / 60.0,
            "cleaning_hours": self.metrics.cleaning_time / 60.0,
            "maintenance_hours": self.metrics.maintenance_time / 60.0
        }
    
    @property
    def is_preemptive(self) -> bool:
        """Check if this resource supports preemption (beds do not)."""
        return self.resource_type.is_preemptive
    
    @property
    def is_operational(self) -> bool:
        """Check if bed is operational (not under maintenance and clean)."""
        return not self.is_under_maintenance and not self.needs_cleaning
    
    @property
    def current_status(self) -> str:
        """Get current bed status as string."""
        if self.is_under_maintenance:
            return "Under Maintenance"
        elif self.needs_cleaning:
            return "Needs Cleaning"
        elif self.current_patient is not None:
            return f"Occupied by {self.current_patient.patient_id[:8]}"
        elif self.is_available:
            return "Available"
        else:
            return "Unavailable"
    
    def __str__(self) -> str:
        return f"{self.bed_number} ({self.ward_name}, {self.bed_type}) - {self.current_status}"
    
    def __repr__(self) -> str:
        return (f"Bed(id={self.bed_id[:8]}, number={self.bed_number}, "
                f"ward={self.ward_name}, type={self.bed_type}, available={self.is_available})")