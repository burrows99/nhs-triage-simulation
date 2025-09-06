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
class MRIMetrics:
    """
    Performance metrics for MRI machine.
    
    Tracks utilization, scan throughput, and operational efficiency
    critical for expensive imaging equipment optimization.
    """
    total_scans_completed: int = 0
    total_scan_time: float = 0.0
    total_idle_time: float = 0.0
    maintenance_time: float = 0.0
    preemptions_performed: int = 0
    preemptions_received: int = 0
    current_scan_start: Optional[float] = None
    
    def __post_init__(self) -> None:
        """Validate metrics to ensure data integrity."""
        if self.total_scans_completed < 0:
            raise ValueError("Total scans completed cannot be negative")
        if self.total_scan_time < 0:
            raise ValueError("Total scan time cannot be negative")
        if self.total_idle_time < 0:
            raise ValueError("Total idle time cannot be negative")
        if self.maintenance_time < 0:
            raise ValueError("Maintenance time cannot be negative")
        if self.preemptions_performed < 0:
            raise ValueError("Preemptions performed cannot be negative")
        if self.preemptions_received < 0:
            raise ValueError("Preemptions received cannot be negative")
    
    @property
    def utilization_rate(self) -> float:
        """Calculate MRI utilization rate (0.0 to 1.0)."""
        total_available_time = self.total_scan_time + self.total_idle_time
        if total_available_time == 0:
            return 0.0
        return self.total_scan_time / total_available_time
    
    @property
    def operational_efficiency(self) -> float:
        """
        Calculate operational efficiency including maintenance downtime.
        
        Returns efficiency as ratio of productive time to total time.
        """
        total_time = self.total_scan_time + self.total_idle_time + self.maintenance_time
        if total_time == 0:
            return 0.0
        return self.total_scan_time / total_time
    
    @property
    def average_scan_time(self) -> float:
        """Calculate average scan time per patient."""
        if self.total_scans_completed == 0:
            return 0.0
        return self.total_scan_time / self.total_scans_completed
    
    @property
    def preemption_ratio(self) -> float:
        """Calculate ratio of preemptions to total scans."""
        if self.total_scans_completed == 0:
            return 0.0
        return self.preemptions_performed / self.total_scans_completed


@dataclass
class MRIMachine:
    """
    MRI machine entity representing a preemptive imaging resource.
    
    MRI machines are expensive, high-demand resources that can interrupt
    current scans for emergency cases. Each machine maintains detailed
    operational metrics for cost-effectiveness analysis.
    
    Key capabilities:
    - Preemptive scan interruption for emergencies
    - Patient queue management
    - Operational efficiency tracking
    - Maintenance scheduling support
    
    Reference: NHS Imaging Services operational guidelines
    https://www.england.nhs.uk/publication/diagnostic-imaging-dataset/
    """
    machine_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = field(default="")
    model: str = field(default="Standard MRI")
    tesla_strength: float = field(default=1.5)  # Magnetic field strength
    is_available: bool = field(default=True)
    is_under_maintenance: bool = field(default=False)
    current_patient: Optional[Patient] = field(default=None)
    resource_type: ResourceType = field(default=ResourceType.MRI_MACHINE, init=False)
    metrics: MRIMetrics = field(default_factory=MRIMetrics)
    scan_history: List[tuple[float, str, str]] = field(default_factory=list, init=False)
    
    # SimPy resource for simulation
    simpy_resource: Optional[simpy.PreemptiveResource] = field(default=None, init=False)
    
    def __post_init__(self) -> None:
        """Initialize MRI machine with validation."""
        self._validate_machine_data()
        if not self.name:
            self.name = f"MRI-{self.machine_id[:8]}"
    
    def _validate_machine_data(self) -> None:
        """Validate MRI machine data integrity."""
        if not self.machine_id:
            raise ValueError("Machine ID cannot be empty")
        if self.tesla_strength <= 0:
            raise ValueError("Tesla strength must be positive")
        if not self.model:
            raise ValueError("Model cannot be empty")
    
    def initialize_simpy_resource(self, env: simpy.Environment, capacity: int = 1) -> None:
        """
        Initialize SimPy preemptive resource for simulation.
        
        Args:
            env: SimPy environment
            capacity: Resource capacity (typically 1 for individual machine)
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        self.simpy_resource = simpy.PreemptiveResource(env, capacity=capacity)
    
    def start_scan(self, patient: Patient, current_time: float) -> None:
        """
        Start MRI scan for a patient.
        
        Args:
            patient: Patient to scan
            current_time: Current simulation time
            
        Raises:
            ValueError: If machine is not available or patient is invalid
        """
        if not self.is_available:
            raise ValueError(f"MRI machine {self.name} is not available")
        if self.is_under_maintenance:
            raise ValueError(f"MRI machine {self.name} is under maintenance")
        if self.current_patient is not None:
            raise ValueError(f"MRI machine {self.name} is already scanning a patient")
        if current_time < 0:
            raise ValueError("Current time cannot be negative")
        
        self.current_patient = patient
        self.is_available = False
        self.metrics.current_scan_start = current_time
        
        # Record scan start
        self.scan_history.append((
            current_time,
            "SCAN_START",
            f"Patient {patient.patient_id[:8]} (Priority: {patient.priority.name})"
        ))
    
    def complete_scan(self, current_time: float) -> Optional[Patient]:
        """
        Complete MRI scan for current patient.
        
        Args:
            current_time: Current simulation time
            
        Returns:
            The patient who was being scanned, or None if no patient
            
        Raises:
            ValueError: If no patient is being scanned or invalid time
        """
        if self.current_patient is None:
            raise ValueError(f"MRI machine {self.name} is not scanning any patient")
        if current_time < 0:
            raise ValueError("Current time cannot be negative")
        if (self.metrics.current_scan_start is not None and 
            current_time < self.metrics.current_scan_start):
            raise ValueError("Current time cannot be before scan start")
        
        completed_patient = self.current_patient
        scan_duration = 0.0
        
        if self.metrics.current_scan_start is not None:
            scan_duration = current_time - self.metrics.current_scan_start
            self.metrics.total_scan_time += scan_duration
        
        # Update metrics
        self.metrics.total_scans_completed += 1
        self.metrics.current_scan_start = None
        
        # Reset availability
        self.current_patient = None
        self.is_available = True
        
        # Record scan completion
        self.scan_history.append((
            current_time,
            "SCAN_COMPLETE",
            f"Patient {completed_patient.patient_id[:8]} (Duration: {scan_duration:.1f}min)"
        ))
        
        return completed_patient
    
    def preempt_current_scan(self, current_time: float, reason: str = "") -> Optional[Patient]:
        """
        Preempt current scan for higher priority patient.
        
        Args:
            current_time: Current simulation time
            reason: Reason for preemption (for logging)
            
        Returns:
            The preempted patient, or None if no patient was being scanned
            
        Raises:
            ValueError: If invalid time or no patient to preempt
        """
        if self.current_patient is None:
            raise ValueError(f"MRI machine {self.name} has no patient to preempt")
        if current_time < 0:
            raise ValueError("Current time cannot be negative")
        
        preempted_patient = self.current_patient
        partial_scan_time = 0.0
        
        if self.metrics.current_scan_start is not None:
            partial_scan_time = current_time - self.metrics.current_scan_start
            self.metrics.total_scan_time += partial_scan_time
        
        # Update metrics
        self.metrics.preemptions_performed += 1
        self.metrics.current_scan_start = None
        
        # Reset availability
        self.current_patient = None
        self.is_available = True
        
        # Record preemption
        self.scan_history.append((
            current_time,
            "PREEMPTION",
            f"Patient {preempted_patient.patient_id[:8]} preempted after {partial_scan_time:.1f}min. Reason: {reason}"
        ))
        
        return preempted_patient
    
    def start_maintenance(self, current_time: float, reason: str = "Scheduled") -> None:
        """
        Start maintenance period.
        
        Args:
            current_time: Current simulation time
            reason: Reason for maintenance
            
        Raises:
            ValueError: If machine is currently in use
        """
        if self.current_patient is not None:
            raise ValueError(f"Cannot start maintenance while patient is being scanned")
        if self.is_under_maintenance:
            raise ValueError(f"MRI machine {self.name} is already under maintenance")
        
        self.is_under_maintenance = True
        self.is_available = False
        
        # Record maintenance start
        self.scan_history.append((
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
            ValueError: If machine is not under maintenance
        """
        if not self.is_under_maintenance:
            raise ValueError(f"MRI machine {self.name} is not under maintenance")
        if maintenance_duration < 0:
            raise ValueError("Maintenance duration cannot be negative")
        
        self.is_under_maintenance = False
        self.is_available = True
        self.metrics.maintenance_time += maintenance_duration
        
        # Record maintenance completion
        self.scan_history.append((
            current_time,
            "MAINTENANCE_COMPLETE",
            f"Maintenance completed (Duration: {maintenance_duration:.1f}min)"
        ))
    
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
        Check if current scan can be preempted by incoming patient.
        
        Args:
            incoming_patient: Patient requesting scan
            
        Returns:
            True if current scan can be preempted, False otherwise
        """
        if self.current_patient is None:
            return False  # No one to preempt
        
        if self.is_under_maintenance:
            return False  # Cannot preempt during maintenance
        
        # Higher priority (lower number) can preempt lower priority
        return incoming_patient.priority.value < self.current_patient.priority.value
    
    def estimate_remaining_scan_time(self) -> float:
        """
        Estimate remaining scan time for current patient.
        
        Returns:
            Estimated remaining time in minutes, 0 if no current patient
        """
        if self.current_patient is None or self.metrics.current_scan_start is None:
            return 0.0
        
        # Simple estimation: assume half of estimated scan time remains
        # In practice, this could use more sophisticated models based on scan type
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
            "operational_efficiency": self.metrics.operational_efficiency,
            "total_scans_completed": float(self.metrics.total_scans_completed),
            "average_scan_time": self.metrics.average_scan_time,
            "preemption_ratio": self.metrics.preemption_ratio,
            "total_scan_hours": self.metrics.total_scan_time / 60.0,
            "total_idle_hours": self.metrics.total_idle_time / 60.0,
            "maintenance_hours": self.metrics.maintenance_time / 60.0
        }
    
    @property
    def is_preemptive(self) -> bool:
        """Check if this resource supports preemption."""
        return self.resource_type.is_preemptive
    
    @property
    def is_operational(self) -> bool:
        """Check if machine is operational (not under maintenance)."""
        return not self.is_under_maintenance
    
    def __str__(self) -> str:
        if self.is_under_maintenance:
            status = "Under Maintenance"
        elif self.is_available:
            status = "Available"
        else:
            status = f"Scanning {self.current_patient.patient_id[:8] if self.current_patient else 'Unknown'}"
        
        return f"{self.name} ({self.tesla_strength}T {self.model}) - {status}"
    
    def __repr__(self) -> str:
        return (f"MRIMachine(id={self.machine_id[:8]}, name={self.name}, "
                f"model={self.model}, tesla={self.tesla_strength}T, available={self.is_available})")