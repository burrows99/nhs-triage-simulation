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
class DoctorMetrics:
    """
    Performance metrics for individual doctor.
    
    Tracks utilization, patient throughput, and service quality metrics
    essential for hospital resource optimization.
    """
    total_patients_served: int = 0
    total_service_time: float = 0.0
    total_idle_time: float = 0.0
    preemptions_performed: int = 0
    preemptions_received: int = 0
    current_service_start: Optional[float] = None
    
    def __post_init__(self) -> None:
        """Validate metrics to ensure data integrity."""
        if self.total_patients_served < 0:
            raise ValueError("Total patients served cannot be negative")
        if self.total_service_time < 0:
            raise ValueError("Total service time cannot be negative")
        if self.total_idle_time < 0:
            raise ValueError("Total idle time cannot be negative")
        if self.preemptions_performed < 0:
            raise ValueError("Preemptions performed cannot be negative")
        if self.preemptions_received < 0:
            raise ValueError("Preemptions received cannot be negative")
    
    @property
    def utilization_rate(self) -> float:
        """Calculate doctor utilization rate (0.0 to 1.0)."""
        total_time = self.total_service_time + self.total_idle_time
        if total_time == 0:
            return 0.0
        return self.total_service_time / total_time
    
    @property
    def average_service_time(self) -> float:
        """Calculate average service time per patient."""
        if self.total_patients_served == 0:
            return 0.0
        return self.total_service_time / self.total_patients_served
    
    @property
    def preemption_ratio(self) -> float:
        """Calculate ratio of preemptions to total patients served."""
        if self.total_patients_served == 0:
            return 0.0
        return self.preemptions_performed / self.total_patients_served


@dataclass
class Doctor:
    """
    Doctor entity representing a preemptive hospital resource.
    
    Doctors can interrupt current consultations for higher priority patients,
    following NHS emergency care protocols. Each doctor maintains detailed
    metrics for performance analysis and resource optimization.
    
    Key capabilities:
    - Preemptive service interruption
    - Patient queue management
    - Performance metrics tracking
    - Service time estimation
    
    Reference: NHS Emergency Care Standards for clinical prioritization
    """
    doctor_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = field(default="")
    specialization: str = field(default="General")
    is_available: bool = field(default=True)
    current_patient: Optional[Patient] = field(default=None)
    resource_type: ResourceType = field(default=ResourceType.DOCTOR, init=False)
    metrics: DoctorMetrics = field(default_factory=DoctorMetrics)
    service_history: List[tuple[float, str, str]] = field(default_factory=list, init=False)
    
    # SimPy resource for simulation
    simpy_resource: Optional[simpy.PreemptiveResource] = field(default=None, init=False)
    
    def __post_init__(self) -> None:
        """Initialize doctor with validation."""
        self._validate_doctor_data()
        if not self.name:
            self.name = f"Dr. {self.doctor_id[:8]}"
    
    def _validate_doctor_data(self) -> None:
        """Validate doctor data integrity."""
        if not self.doctor_id:
            raise ValueError("Doctor ID cannot be empty")
        if not self.specialization:
            raise ValueError("Specialization cannot be empty")
    
    def initialize_simpy_resource(self, env: simpy.Environment, capacity: int = 1) -> None:
        """
        Initialize SimPy preemptive resource for simulation.
        
        Args:
            env: SimPy environment
            capacity: Resource capacity (typically 1 for individual doctor)
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        self.simpy_resource = simpy.PreemptiveResource(env, capacity=capacity)
    
    def start_service(self, patient: Patient, current_time: float) -> None:
        """
        Start providing service to a patient.
        
        Args:
            patient: Patient to serve
            current_time: Current simulation time
            
        Raises:
            ValueError: If doctor is already serving or patient is invalid
        """
        if not self.is_available:
            raise ValueError(f"Doctor {self.name} is not available")
        if self.current_patient is not None:
            raise ValueError(f"Doctor {self.name} is already serving a patient")
        if current_time < 0:
            raise ValueError("Current time cannot be negative")
        
        self.current_patient = patient
        self.is_available = False
        self.metrics.current_service_start = current_time
        
        # Record service start
        self.service_history.append((
            current_time, 
            "SERVICE_START", 
            f"Patient {patient.patient_id[:8]} (Priority: {patient.priority.name})"
        ))
    
    def complete_service(self, current_time: float) -> Optional[Patient]:
        """
        Complete service for current patient.
        
        Args:
            current_time: Current simulation time
            
        Returns:
            The patient who was being served, or None if no patient
            
        Raises:
            ValueError: If no patient is being served or invalid time
        """
        if self.current_patient is None:
            raise ValueError(f"Doctor {self.name} is not serving any patient")
        if current_time < 0:
            raise ValueError("Current time cannot be negative")
        if (self.metrics.current_service_start is not None and 
            current_time < self.metrics.current_service_start):
            raise ValueError("Current time cannot be before service start")
        
        completed_patient = self.current_patient
        service_duration = 0.0
        
        if self.metrics.current_service_start is not None:
            service_duration = current_time - self.metrics.current_service_start
            self.metrics.total_service_time += service_duration
        
        # Update metrics
        self.metrics.total_patients_served += 1
        self.metrics.current_service_start = None
        
        # Reset availability
        self.current_patient = None
        self.is_available = True
        
        # Record service completion
        self.service_history.append((
            current_time,
            "SERVICE_COMPLETE",
            f"Patient {completed_patient.patient_id[:8]} (Duration: {service_duration:.1f}min)"
        ))
        
        return completed_patient
    
    def preempt_current_service(self, current_time: float, reason: str = "") -> Optional[Patient]:
        """
        Preempt current service for higher priority patient.
        
        Args:
            current_time: Current simulation time
            reason: Reason for preemption (for logging)
            
        Returns:
            The preempted patient, or None if no patient was being served
            
        Raises:
            ValueError: If invalid time or no patient to preempt
        """
        if self.current_patient is None:
            raise ValueError(f"Doctor {self.name} has no patient to preempt")
        if current_time < 0:
            raise ValueError("Current time cannot be negative")
        
        preempted_patient = self.current_patient
        partial_service_time = 0.0
        
        if self.metrics.current_service_start is not None:
            partial_service_time = current_time - self.metrics.current_service_start
            self.metrics.total_service_time += partial_service_time
        
        # Update metrics
        self.metrics.preemptions_performed += 1
        self.metrics.current_service_start = None
        
        # Reset availability
        self.current_patient = None
        self.is_available = True
        
        # Record preemption
        self.service_history.append((
            current_time,
            "PREEMPTION",
            f"Patient {preempted_patient.patient_id[:8]} preempted after {partial_service_time:.1f}min. Reason: {reason}"
        ))
        
        return preempted_patient
    
    def add_idle_time(self, idle_duration: float) -> None:
        """
        Add idle time to metrics.
        
        Args:
            idle_duration: Duration of idle time in minutes
            
        Raises:
            ValueError: If idle duration is negative
        """
        if idle_duration < 0:
            raise ValueError("Idle duration cannot be negative")
        self.metrics.total_idle_time += idle_duration
    
    def can_be_preempted_by(self, incoming_patient: Patient) -> bool:
        """
        Check if current service can be preempted by incoming patient.
        
        Args:
            incoming_patient: Patient requesting service
            
        Returns:
            True if current service can be preempted, False otherwise
        """
        if self.current_patient is None:
            return False  # No one to preempt
        
        # Higher priority (lower number) can preempt lower priority
        return incoming_patient.priority.value < self.current_patient.priority.value
    
    def estimate_remaining_service_time(self) -> float:
        """
        Estimate remaining service time for current patient.
        
        Returns:
            Estimated remaining time in minutes, 0 if no current patient
        """
        if self.current_patient is None or self.metrics.current_service_start is None:
            return 0.0
        
        # Simple estimation: assume half of estimated service time remains
        # In practice, this could use more sophisticated models
        elapsed_time = 0.0  # Would need current simulation time
        estimated_total = self.current_patient.estimated_service_time
        
        return max(0.0, estimated_total - elapsed_time)
    
    def get_performance_summary(self) -> dict[str, float]:
        """
        Get comprehensive performance summary.
        
        Returns:
            Dictionary with key performance indicators
        """
        return {
            "utilization_rate": self.metrics.utilization_rate,
            "total_patients_served": float(self.metrics.total_patients_served),
            "average_service_time": self.metrics.average_service_time,
            "preemption_ratio": self.metrics.preemption_ratio,
            "total_service_hours": self.metrics.total_service_time / 60.0,
            "total_idle_hours": self.metrics.total_idle_time / 60.0
        }
    
    @property
    def is_preemptive(self) -> bool:
        """Check if this resource supports preemption."""
        return self.resource_type.is_preemptive
    
    def __str__(self) -> str:
        status = "Available" if self.is_available else f"Serving {self.current_patient.patient_id[:8] if self.current_patient else 'Unknown'}"
        return f"{self.name} ({self.specialization}) - {status}"
    
    def __repr__(self) -> str:
        return (f"Doctor(id={self.doctor_id[:8]}, name={self.name}, "
                f"specialization={self.specialization}, available={self.is_available})")