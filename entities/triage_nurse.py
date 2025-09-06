from dataclasses import dataclass, field
from typing import Optional, List, Dict
import uuid
import random
import simpy

try:
    from ..enums.priority import TriagePriority
    from ..enums.resource_type import ResourceType
    from ..enums.patient_status import PatientStatus
    from .patient import Patient
except ImportError:
    from enums.priority import TriagePriority
    from enums.resource_type import ResourceType
    from enums.patient_status import PatientStatus
    from entities.patient import Patient


@dataclass
class TriageMetrics:
    """
    Performance metrics for triage nurse.
    
    Tracks assessment efficiency, accuracy, and patient throughput
    critical for emergency department flow optimization.
    """
    total_assessments: int = 0
    total_assessment_time: float = 0.0
    total_idle_time: float = 0.0
    priority_distribution: Dict[TriagePriority, int] = field(default_factory=dict)
    current_assessment_start: Optional[float] = None
    
    def __post_init__(self) -> None:
        """Initialize priority distribution tracking."""
        if not self.priority_distribution:
            self.priority_distribution = {priority: 0 for priority in TriagePriority}
        self._validate_metrics()
    
    def _validate_metrics(self) -> None:
        """Validate metrics to ensure data integrity."""
        if self.total_assessments < 0:
            raise ValueError("Total assessments cannot be negative")
        if self.total_assessment_time < 0:
            raise ValueError("Total assessment time cannot be negative")
        if self.total_idle_time < 0:
            raise ValueError("Total idle time cannot be negative")
    
    @property
    def utilization_rate(self) -> float:
        """Calculate nurse utilization rate (0.0 to 1.0)."""
        total_time = self.total_assessment_time + self.total_idle_time
        if total_time == 0:
            return 0.0
        return self.total_assessment_time / total_time
    
    @property
    def average_assessment_time(self) -> float:
        """Calculate average assessment time per patient."""
        if self.total_assessments == 0:
            return 0.0
        return self.total_assessment_time / self.total_assessments
    
    @property
    def high_priority_ratio(self) -> float:
        """Calculate ratio of high priority (1-2) assessments."""
        if self.total_assessments == 0:
            return 0.0
        high_priority_count = (self.priority_distribution.get(TriagePriority.IMMEDIATE, 0) +
                              self.priority_distribution.get(TriagePriority.VERY_URGENT, 0))
        return high_priority_count / self.total_assessments


@dataclass
class MTSCriteria:
    """
    Manchester Triage System criteria for priority assignment.
    
    Simplified implementation of MTS decision logic based on
    presenting symptoms and vital signs.
    
    Reference: Manchester Triage Group. Emergency Triage. 3rd ed.
    """
    # Vital signs thresholds (simplified)
    critical_heart_rate_high: int = 150
    critical_heart_rate_low: int = 40
    critical_blood_pressure_systolic: int = 200
    critical_temperature: float = 39.5
    
    # Symptom severity indicators
    life_threatening_symptoms: List[str] = field(default_factory=lambda: [
        "cardiac_arrest", "respiratory_arrest", "severe_trauma", "unconscious"
    ])
    
    very_urgent_symptoms: List[str] = field(default_factory=lambda: [
        "chest_pain", "difficulty_breathing", "severe_bleeding", "stroke_symptoms"
    ])
    
    urgent_symptoms: List[str] = field(default_factory=lambda: [
        "moderate_pain", "fever", "vomiting", "minor_trauma"
    ])


@dataclass
class TriageNurse:
    """
    Triage nurse entity for initial patient assessment and prioritization.
    
    Implements simplified Manchester Triage System (MTS) for priority assignment
    based on presenting symptoms and basic vital signs. The nurse assesses
    patients and assigns appropriate priority levels according to clinical protocols.
    
    Key capabilities:
    - MTS-based priority assessment
    - Patient symptom evaluation
    - Resource requirement determination
    - Performance metrics tracking
    
    Reference: NHS Emergency Care Standards and Manchester Triage System
    https://www.england.nhs.uk/publication/emergency-care-data-set/
    """
    nurse_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = field(default="")
    experience_years: int = field(default=5)
    certification_level: str = field(default="RN")  # RN, ANP, etc.
    is_available: bool = field(default=True)
    current_patient: Optional[Patient] = field(default=None)
    resource_type: ResourceType = field(default=ResourceType.TRIAGE_NURSE, init=False)
    metrics: TriageMetrics = field(default_factory=TriageMetrics)
    mts_criteria: MTSCriteria = field(default_factory=MTSCriteria)
    assessment_history: List[tuple[float, str, str]] = field(default_factory=list, init=False)
    
    # SimPy resource for simulation
    simpy_resource: Optional[simpy.Resource] = field(default=None, init=False)
    
    def __post_init__(self) -> None:
        """Initialize triage nurse with validation."""
        self._validate_nurse_data()
        if not self.name:
            self.name = f"Nurse {self.nurse_id[:8]}"
    
    def _validate_nurse_data(self) -> None:
        """Validate nurse data integrity."""
        if not self.nurse_id:
            raise ValueError("Nurse ID cannot be empty")
        if self.experience_years < 0:
            raise ValueError("Experience years cannot be negative")
        if not self.certification_level:
            raise ValueError("Certification level cannot be empty")
    
    def initialize_simpy_resource(self, env: simpy.Environment, capacity: int = 1) -> None:
        """
        Initialize SimPy resource for simulation.
        
        Args:
            env: SimPy environment
            capacity: Resource capacity (typically 1 for individual nurse)
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive")
        self.simpy_resource = simpy.Resource(env, capacity=capacity)
    
    def start_assessment(self, patient: Patient, current_time: float) -> None:
        """
        Start triage assessment for a patient.
        
        Args:
            patient: Patient to assess
            current_time: Current simulation time
            
        Raises:
            ValueError: If nurse is not available or patient is invalid
        """
        if not self.is_available:
            raise ValueError(f"Triage nurse {self.name} is not available")
        if self.current_patient is not None:
            raise ValueError(f"Triage nurse {self.name} is already assessing a patient")
        if current_time < 0:
            raise ValueError("Current time cannot be negative")
        
        self.current_patient = patient
        self.is_available = False
        self.metrics.current_assessment_start = current_time
        
        # Update patient status
        patient.update_status(PatientStatus.IN_TRIAGE, current_time)
        
        # Record assessment start
        self.assessment_history.append((
            current_time,
            "ASSESSMENT_START",
            f"Patient {patient.patient_id[:8]} assessment started"
        ))
    
    def complete_assessment(self, current_time: float) -> Optional[Patient]:
        """
        Complete triage assessment and assign priority.
        
        Args:
            current_time: Current simulation time
            
        Returns:
            The assessed patient with assigned priority
            
        Raises:
            ValueError: If no patient is being assessed or invalid time
        """
        if self.current_patient is None:
            raise ValueError(f"Triage nurse {self.name} is not assessing any patient")
        if current_time < 0:
            raise ValueError("Current time cannot be negative")
        if (self.metrics.current_assessment_start is not None and 
            current_time < self.metrics.current_assessment_start):
            raise ValueError("Current time cannot be before assessment start")
        
        assessed_patient = self.current_patient
        assessment_duration = 0.0
        
        if self.metrics.current_assessment_start is not None:
            assessment_duration = current_time - self.metrics.current_assessment_start
            self.metrics.total_assessment_time += assessment_duration
        
        # Perform MTS-based priority assignment
        assigned_priority = self._assess_patient_priority(assessed_patient)
        assessed_patient.set_priority(assigned_priority)
        
        # Determine required resource based on priority and symptoms
        required_resource = self._determine_required_resource(assessed_patient)
        assessed_patient.set_required_resource(required_resource)
        
        # Update patient status
        assessed_patient.update_status(PatientStatus.WAITING_RESOURCE, current_time)
        
        # Update metrics
        self.metrics.total_assessments += 1
        self.metrics.priority_distribution[assigned_priority] += 1
        self.metrics.current_assessment_start = None
        
        # Reset availability
        self.current_patient = None
        self.is_available = True
        
        # Record assessment completion
        self.assessment_history.append((
            current_time,
            "ASSESSMENT_COMPLETE",
            f"Patient {assessed_patient.patient_id[:8]} assigned {assigned_priority.name} priority, requires {required_resource.name} (Duration: {assessment_duration:.1f}min)"
        ))
        
        return assessed_patient
    
    def _assess_patient_priority(self, patient: Patient) -> TriagePriority:
        """
        Assess patient priority using simplified MTS criteria.
        
        This is a simplified implementation. In reality, MTS uses
        complex decision trees based on presenting complaints,
        vital signs, and clinical observations.
        
        Args:
            patient: Patient to assess
            
        Returns:
            Assigned priority level
        """
        # Simulate patient presentation (in real system, this would come from patient data)
        simulated_symptoms = self._simulate_patient_symptoms()
        simulated_vitals = self._simulate_vital_signs()
        
        # Priority 1 (Immediate) - Life-threatening conditions
        if any(symptom in self.mts_criteria.life_threatening_symptoms for symptom in simulated_symptoms):
            return TriagePriority.IMMEDIATE
        
        # Check critical vital signs
        if (simulated_vitals['heart_rate'] > self.mts_criteria.critical_heart_rate_high or
            simulated_vitals['heart_rate'] < self.mts_criteria.critical_heart_rate_low or
            simulated_vitals['systolic_bp'] > self.mts_criteria.critical_blood_pressure_systolic or
            simulated_vitals['temperature'] > self.mts_criteria.critical_temperature):
            return TriagePriority.IMMEDIATE
        
        # Priority 2 (Very Urgent) - Potentially life-threatening
        if any(symptom in self.mts_criteria.very_urgent_symptoms for symptom in simulated_symptoms):
            return TriagePriority.VERY_URGENT
        
        # Priority 3 (Urgent) - Serious conditions
        if any(symptom in self.mts_criteria.urgent_symptoms for symptom in simulated_symptoms):
            return TriagePriority.URGENT
        
        # Priority assignment based on experience and clinical judgment
        # More experienced nurses may be more conservative (assign higher priority)
        experience_factor = min(self.experience_years / 10.0, 1.0)
        
        # Random factor to simulate clinical variation
        random_factor = random.random()
        
        if random_factor < 0.1 + (experience_factor * 0.1):  # 10-20% chance based on experience
            return TriagePriority.URGENT
        elif random_factor < 0.4:
            return TriagePriority.STANDARD
        else:
            return TriagePriority.NON_URGENT
    
    def _simulate_patient_symptoms(self) -> List[str]:
        """
        Simulate patient symptoms for demonstration.
        
        In a real system, this would come from patient intake data.
        """
        all_symptoms = (self.mts_criteria.life_threatening_symptoms +
                       self.mts_criteria.very_urgent_symptoms +
                       self.mts_criteria.urgent_symptoms +
                       ["minor_pain", "headache", "nausea", "fatigue"])
        
        # Randomly select 1-3 symptoms
        num_symptoms = random.randint(1, 3)
        return random.sample(all_symptoms, min(num_symptoms, len(all_symptoms)))
    
    def _simulate_vital_signs(self) -> Dict[str, float]:
        """
        Simulate patient vital signs for demonstration.
        
        In a real system, this would come from patient monitoring equipment.
        """
        return {
            'heart_rate': random.normalvariate(80, 20),  # Normal: 60-100 bpm
            'systolic_bp': random.normalvariate(120, 20),  # Normal: 90-140 mmHg
            'temperature': random.normalvariate(37.0, 1.0),  # Normal: 36-38°C
            'respiratory_rate': random.normalvariate(16, 4)  # Normal: 12-20 breaths/min
        }
    
    def _determine_required_resource(self, patient: Patient) -> ResourceType:
        """
        Determine required resource based on patient priority and condition.
        
        Args:
            patient: Assessed patient
            
        Returns:
            Required resource type
        """
        # Simplified resource assignment logic
        # In reality, this would be based on clinical protocols and resource availability
        
        if patient.priority == TriagePriority.IMMEDIATE:
            # Immediate cases might need multiple resources, but for simplicity, assign doctor
            return ResourceType.DOCTOR
        elif patient.priority == TriagePriority.VERY_URGENT:
            # Very urgent cases typically need doctor consultation
            return ResourceType.DOCTOR
        else:
            # For demonstration, randomly assign resource type
            # In practice, this would be based on presenting complaint
            resource_weights = {
                ResourceType.DOCTOR: 0.6,  # Most patients see doctor
                ResourceType.MRI_MACHINE: 0.2,  # Some need imaging
                ResourceType.BED: 0.2  # Some need admission
            }
            
            rand_val = random.random()
            cumulative = 0.0
            for resource, weight in resource_weights.items():
                cumulative += weight
                if rand_val <= cumulative:
                    return resource
            
            return ResourceType.DOCTOR  # Default fallback
    
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
    
    def get_performance_summary(self) -> dict[str, float]:
        """
        Get comprehensive performance summary.
        
        Returns:
            Dictionary with key performance indicators
        """
        return {
            "utilization_rate": self.metrics.utilization_rate,
            "total_assessments": float(self.metrics.total_assessments),
            "average_assessment_time": self.metrics.average_assessment_time,
            "high_priority_ratio": self.metrics.high_priority_ratio,
            "total_assessment_hours": self.metrics.total_assessment_time / 60.0,
            "total_idle_hours": self.metrics.total_idle_time / 60.0,
            "assessments_per_hour": (self.metrics.total_assessments / 
                                    max(self.metrics.total_assessment_time / 60.0, 0.1))
        }
    
    @property
    def is_preemptive(self) -> bool:
        """Check if this resource supports preemption (triage nurses do not)."""
        return self.resource_type.is_preemptive
    
    def __str__(self) -> str:
        status = "Available" if self.is_available else f"Assessing {self.current_patient.patient_id[:8] if self.current_patient else 'Unknown'}"
        return f"{self.name} ({self.certification_level}, {self.experience_years}y exp) - {status}"
    
    def __repr__(self) -> str:
        return (f"TriageNurse(id={self.nurse_id[:8]}, name={self.name}, "
                f"experience={self.experience_years}y, available={self.is_available})")