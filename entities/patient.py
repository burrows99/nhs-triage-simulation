from dataclasses import dataclass, field
from typing import Optional, List, Set
import uuid

try:
    from ..enums.priority import TriagePriority
    from ..enums.patient_status import PatientStatus
    from ..enums.resource_type import ResourceType
except ImportError:
    from enums.priority import TriagePriority
    from enums.patient_status import PatientStatus
    from enums.resource_type import ResourceType


@dataclass
class PatientMetrics:
    """
    Metrics tracking for individual patient journey.
    
    Strict validation ensures data integrity for analysis.
    All times are in minutes from simulation start.
    """
    arrival_time: float
    triage_start_time: Optional[float] = None
    triage_end_time: Optional[float] = None
    service_start_time: Optional[float] = None
    service_end_time: Optional[float] = None
    discharge_time: Optional[float] = None
    preemption_count: int = 0
    total_wait_time: float = 0.0
    
    def __post_init__(self) -> None:
        """Validate metrics to ensure temporal consistency."""
        if self.arrival_time < 0:
            raise ValueError("Arrival time cannot be negative")
        if self.preemption_count < 0:
            raise ValueError("Preemption count cannot be negative")
        if self.total_wait_time < 0:
            raise ValueError("Total wait time cannot be negative")
    
    @property
    def total_system_time(self) -> Optional[float]:
        """Total time spent in hospital system."""
        if self.discharge_time is None:
            return None
        return self.discharge_time - self.arrival_time
    
    @property
    def triage_wait_time(self) -> Optional[float]:
        """Time waited for triage assessment."""
        if self.triage_start_time is None:
            return None
        return self.triage_start_time - self.arrival_time
    
    @property
    def service_wait_time(self) -> Optional[float]:
        """Time waited for main service after triage."""
        if self.service_start_time is None or self.triage_end_time is None:
            return None
        return self.service_start_time - self.triage_end_time


@dataclass
class Patient:
    """
    Individual patient entity in the hospital simulation.
    
    Each patient has:
    - Unique identifier for tracking
    - Priority level assigned by triage
    - Current status in the system
    - Required resource type
    - Comprehensive metrics tracking
    
    Strict validation prevents invalid state transitions and ensures
    data integrity throughout the simulation.
    """
    patient_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    arrival_time: float = field(default=0.0)
    priority: TriagePriority = field(default=TriagePriority.STANDARD)
    status: PatientStatus = field(default=PatientStatus.ARRIVED)
    required_resource: ResourceType = field(default=ResourceType.DOCTOR)
    estimated_service_time: float = field(default=0.0)
    actual_service_time: float = field(default=0.0)
    metrics: PatientMetrics = field(init=False)
    status_history: List[tuple[float, PatientStatus]] = field(default_factory=list, init=False)
    
    def __post_init__(self) -> None:
        """Initialize patient with validation and metrics setup."""
        self._validate_patient_data()
        self.metrics = PatientMetrics(arrival_time=self.arrival_time)
        self._record_status_change(self.arrival_time, self.status)
    
    def _validate_patient_data(self) -> None:
        """Validate patient data integrity."""
        if self.arrival_time < 0:
            raise ValueError("Arrival time cannot be negative")
        if self.estimated_service_time < 0:
            raise ValueError("Estimated service time cannot be negative")
        if self.actual_service_time < 0:
            raise ValueError("Actual service time cannot be negative")
        # Type validation handled by dataclass field types
    
    def update_status(self, new_status: PatientStatus, current_time: float) -> None:
        """
        Update patient status with validation and history tracking.
        
        Args:
            new_status: New status to transition to
            current_time: Current simulation time
            
        Raises:
            ValueError: If status transition is invalid
            TypeError: If parameters are wrong type
        """
        # Type validation handled by parameter annotation
        if current_time < 0:
            raise ValueError("Current time cannot be negative")
        if current_time < self.arrival_time:
            raise ValueError("Current time cannot be before arrival time")
        
        # Validate status transition
        if not self._is_valid_status_transition(self.status, new_status):
            raise ValueError(f"Invalid status transition from {self.status} to {new_status}")
        
        self.status = new_status
        self._record_status_change(current_time, new_status)
        self._update_metrics_on_status_change(current_time, new_status)
    
    def _is_valid_status_transition(self, from_status: PatientStatus, to_status: PatientStatus) -> bool:
        """
        Validate if status transition is allowed.
        
        Based on typical patient flow in emergency departments.
        """
        valid_transitions: dict[PatientStatus, Set[PatientStatus]] = {
            PatientStatus.ARRIVED: {PatientStatus.WAITING_TRIAGE},
            PatientStatus.WAITING_TRIAGE: {PatientStatus.IN_TRIAGE},
            PatientStatus.IN_TRIAGE: {PatientStatus.WAITING_RESOURCE, PatientStatus.DISCHARGED},
            PatientStatus.WAITING_RESOURCE: {PatientStatus.IN_SERVICE},
            PatientStatus.IN_SERVICE: {PatientStatus.COMPLETED, PatientStatus.PREEMPTED},
            PatientStatus.PREEMPTED: {PatientStatus.WAITING_RESOURCE, PatientStatus.IN_SERVICE},
            PatientStatus.COMPLETED: {PatientStatus.DISCHARGED},
            PatientStatus.DISCHARGED: set()  # Terminal state
        }
        
        return to_status in valid_transitions.get(from_status, set())
    
    def _record_status_change(self, time: float, status: PatientStatus) -> None:
        """Record status change in history."""
        self.status_history.append((time, status))
    
    def _update_metrics_on_status_change(self, current_time: float, new_status: PatientStatus) -> None:
        """Update metrics based on status change."""
        if new_status == PatientStatus.IN_TRIAGE:
            self.metrics.triage_start_time = current_time
        elif new_status == PatientStatus.WAITING_RESOURCE and self.metrics.triage_end_time is None:
            self.metrics.triage_end_time = current_time
        elif new_status == PatientStatus.IN_SERVICE:
            if self.metrics.service_start_time is None:
                self.metrics.service_start_time = current_time
        elif new_status == PatientStatus.COMPLETED:
            self.metrics.service_end_time = current_time
        elif new_status == PatientStatus.PREEMPTED:
            self.metrics.preemption_count += 1
        elif new_status == PatientStatus.DISCHARGED:
            self.metrics.discharge_time = current_time
            self._calculate_total_wait_time()
    
    def _calculate_total_wait_time(self) -> None:
        """Calculate total waiting time across all stages."""
        total_wait = 0.0
        
        # Triage wait time
        if self.metrics.triage_wait_time is not None:
            total_wait += self.metrics.triage_wait_time
        
        # Service wait time
        if self.metrics.service_wait_time is not None:
            total_wait += self.metrics.service_wait_time
        
        self.metrics.total_wait_time = total_wait
    
    def set_priority(self, priority: TriagePriority) -> None:
        """
        Set patient priority with validation.
        
        Args:
            priority: New priority level
            
        Raises:
            TypeError: If priority is not TriagePriority enum
        """
        # Type validation handled by parameter annotation
        self.priority = priority
    
    def set_required_resource(self, resource: ResourceType) -> None:
        """
        Set required resource type with validation.
        
        Args:
            resource: Required resource type
            
        Raises:
            TypeError: If resource is not ResourceType enum
        """
        # Type validation handled by parameter annotation
        self.required_resource = resource
    
    def set_estimated_service_time(self, time: float) -> None:
        """
        Set estimated service time with validation.
        
        Args:
            time: Estimated service time in minutes
            
        Raises:
            ValueError: If time is negative
        """
        if time < 0:
            raise ValueError("Estimated service time cannot be negative")
        self.estimated_service_time = time
    
    @property
    def is_high_priority(self) -> bool:
        """Check if patient has high priority (1 or 2)."""
        return self.priority.value <= 2
    
    @property
    def current_wait_time(self) -> float:
        """Get current waiting time based on status."""
        if self.status.is_waiting and self.status_history:
            # Find when current waiting started
            for time, status in reversed(self.status_history):
                if status.is_waiting:
                    continue
                # This is the last non-waiting status
                return max(0.0, time)
        return 0.0
    
    def __str__(self) -> str:
        return f"Patient({self.patient_id[:8]}, {self.priority.name}, {self.status.name})"
    
    def __repr__(self) -> str:
        return (f"Patient(id={self.patient_id[:8]}, priority={self.priority.name}, "
                f"status={self.status.name}, resource={self.required_resource.name})")