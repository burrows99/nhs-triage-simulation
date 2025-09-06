from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Union
import uuid
import copy
import simpy

try:
    from ..entities.patient import Patient
    from ..entities.doctor import Doctor
    from ..entities.mri_machine import MRIMachine
    from ..entities.bed import Bed
    from ..entities.triage_nurse import TriageNurse
    from ..enums.resource_type import ResourceType
    from ..enums.patient_status import PatientStatus
    # TriagePriority imported through other modules
    from ..services.preemption_agent import (
        PreemptionAgent, HospitalOperationsState, ResourceState, PreemptionResponse, PreemptionDecision
    )
    from ..services.time_service import TimeService
except ImportError:
    from entities.patient import Patient
    from entities.doctor import Doctor
    from entities.mri_machine import MRIMachine
    from entities.bed import Bed
    from entities.triage_nurse import TriageNurse
    from enums.resource_type import ResourceType
    from enums.patient_status import PatientStatus
    # TriagePriority imported through other modules
    from services.preemption_agent import (
        PreemptionAgent, HospitalOperationsState, ResourceState, PreemptionResponse, PreemptionDecision
    )
    from services.time_service import TimeService


@dataclass
class HospitalMetrics:
    """
    Comprehensive hospital performance metrics.
    
    Tracks system-wide KPIs essential for operational analysis
    and performance optimization.
    """
    total_patients_processed: int = 0
    total_patients_discharged: int = 0
    total_preemptions_executed: int = 0
    average_wait_time: float = 0.0
    average_system_time: float = 0.0
    current_system_load: float = 0.0
    peak_system_load: float = 0.0
    resource_utilization: Dict[ResourceType, float] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Initialize resource utilization tracking."""
        if not self.resource_utilization:
            self.resource_utilization = {resource_type: 0.0 for resource_type in ResourceType}
        self._validate_metrics()
    
    def _validate_metrics(self) -> None:
        """Validate metrics data integrity."""
        if self.total_patients_processed < 0:
            raise ValueError("Total patients processed cannot be negative")
        if self.total_patients_discharged < 0:
            raise ValueError("Total patients discharged cannot be negative")
        if self.total_preemptions_executed < 0:
            raise ValueError("Total preemptions executed cannot be negative")
        if self.average_wait_time < 0:
            raise ValueError("Average wait time cannot be negative")
        if not 0.0 <= self.current_system_load <= 1.0:
            raise ValueError("Current system load must be between 0.0 and 1.0")


@dataclass
class OperationsState:
    """
    Current operational state of the hospital.
    
    Immutable snapshot of all resources, queues, and system metrics
    at a specific point in time. Used for decision making and analysis.
    """
    timestamp: float
    doctors: Dict[str, Doctor]
    mri_machines: Dict[str, MRIMachine]
    beds: Dict[str, Bed]
    triage_nurses: Dict[str, TriageNurse]
    patient_queues: Dict[ResourceType, List[Patient]]
    patients_in_system: Set[str]
    metrics: HospitalMetrics
    
    def __post_init__(self) -> None:
        """Validate operations state."""
        if self.timestamp < 0:
            raise ValueError("Timestamp cannot be negative")
        # Type validation handled by dataclass field types
    
    def get_total_resources(self, resource_type: ResourceType) -> int:
        """Get total number of resources of specified type."""
        if resource_type == ResourceType.DOCTOR:
            return len(self.doctors)
        elif resource_type == ResourceType.MRI_MACHINE:
            return len(self.mri_machines)
        elif resource_type == ResourceType.BED:
            return len(self.beds)
        elif resource_type == ResourceType.TRIAGE_NURSE:
            return len(self.triage_nurses)
        return 0
    
    def get_available_resources(self, resource_type: ResourceType) -> int:
        """Get number of available resources of specified type."""
        if resource_type == ResourceType.DOCTOR:
            return sum(1 for doctor in self.doctors.values() if doctor.is_available)
        elif resource_type == ResourceType.MRI_MACHINE:
            return sum(1 for mri in self.mri_machines.values() if mri.is_available)
        elif resource_type == ResourceType.BED:
            return sum(1 for bed in self.beds.values() if bed.is_available)
        elif resource_type == ResourceType.TRIAGE_NURSE:
            return sum(1 for nurse in self.triage_nurses.values() if nurse.is_available)
        return 0
    
    def get_queue_length(self, resource_type: ResourceType) -> int:
        """Get current queue length for resource type."""
        return len(self.patient_queues.get(resource_type, []))


class Hospital:
    """
    Main hospital entity managing all resources and patient flow.
    
    Coordinates patient care through triage, resource allocation,
    and preemption decisions. Maintains comprehensive operational
    state and metrics for analysis and optimization.
    
    Key responsibilities:
    - Patient admission and discharge
    - Resource allocation and management
    - Preemption decision execution
    - Operational state tracking
    - Performance metrics collection
    
    Reference: NHS Hospital Management Standards
    """
    
    def __init__(
        self,
        name: str,
        num_doctors: int = 3,
        num_mri_machines: int = 2,
        num_beds: int = 10,
        num_triage_nurses: int = 2,
        env: Optional[simpy.Environment] = None,
        time_service: Optional[TimeService] = None,
        preemption_agent: Optional[PreemptionAgent] = None
    ) -> None:
        """Initialize hospital with specified resources."""
        self._validate_initialization_params(name, num_doctors, num_mri_machines, num_beds, num_triage_nurses)
        
        self.hospital_id = str(uuid.uuid4())
        self.name = name
        self.env = env
        self.time_service = time_service or TimeService()
        self.preemption_agent = preemption_agent or PreemptionAgent()
        
        # Initialize resources
        self.doctors = self._initialize_doctors(num_doctors)
        self.mri_machines = self._initialize_mri_machines(num_mri_machines)
        self.beds = self._initialize_beds(num_beds)
        self.triage_nurses = self._initialize_triage_nurses(num_triage_nurses)
        
        # Initialize patient queues
        self.patient_queues: Dict[ResourceType, List[Patient]] = {
            resource_type: [] for resource_type in ResourceType
        }
        
        # Track patients in system
        self.patients_in_system: Set[str] = set()
        self.discharged_patients: List[Patient] = []
        
        # Operational state management
        self.current_operations_state: Optional[OperationsState] = None
        self.operations_state_history: List[OperationsState] = []
        
        # Performance metrics
        self.metrics = HospitalMetrics()
        
        # Initialize SimPy resources if environment provided
        if self.env:
            self._initialize_simpy_resources()
        
        # Update initial state
        self._update_operations_state(0.0)
    
    def _validate_initialization_params(self, name: str, num_doctors: int, num_mri_machines: int, num_beds: int, num_triage_nurses: int) -> None:
        """Validate hospital initialization parameters."""
        if not name:
            raise ValueError("Hospital name cannot be empty")
        if num_doctors <= 0:
            raise ValueError("Number of doctors must be positive")
        if num_mri_machines <= 0:
            raise ValueError("Number of MRI machines must be positive")
        if num_beds <= 0:
            raise ValueError("Number of beds must be positive")
        if num_triage_nurses <= 0:
            raise ValueError("Number of triage nurses must be positive")
    
    def _initialize_doctors(self, count: int) -> dict[str, Doctor]:
        """Initialize doctor resources."""
        doctors: dict[str, Doctor] = {}
        specializations = ["Emergency Medicine", "Internal Medicine", "Surgery", "Cardiology", "Neurology"]
        
        for i in range(count):
            doctor = Doctor(
                name=f"Dr. Smith-{i+1}",
                specialization=specializations[i % len(specializations)]
            )
            doctors[doctor.doctor_id] = doctor
        
        return doctors
    
    def _initialize_mri_machines(self, count: int) -> dict[str, MRIMachine]:
        """Initialize MRI machine resources."""
        machines: dict[str, MRIMachine] = {}
        models = ["Siemens Magnetom", "GE Signa", "Philips Ingenia"]
        tesla_strengths = [1.5, 3.0]
        
        for i in range(count):
            machine = MRIMachine(
                name=f"MRI-{i+1}",
                model=models[i % len(models)],
                tesla_strength=tesla_strengths[i % len(tesla_strengths)]
            )
            machines[machine.machine_id] = machine
        
        return machines
    
    def _initialize_beds(self, count: int) -> dict[str, Bed]:
        """Initialize bed resources."""
        beds: dict[str, Bed] = {}
        wards = ["Emergency", "General", "ICU", "Cardiology"]
        bed_types = ["Standard", "ICU", "Isolation"]
        
        for i in range(count):
            bed = Bed(
                bed_number=f"BED-{i+1:03d}",
                ward_name=wards[i % len(wards)],
                bed_type=bed_types[i % len(bed_types)]
            )
            beds[bed.bed_id] = bed
        
        return beds
    
    def _initialize_triage_nurses(self, count: int) -> dict[str, TriageNurse]:
        """Initialize triage nurse resources."""
        nurses: dict[str, TriageNurse] = {}
        certifications = ["RN", "ANP", "CNS"]
        
        for i in range(count):
            nurse = TriageNurse(
                name=f"Nurse Johnson-{i+1}",
                experience_years=5 + (i * 2),
                certification_level=certifications[i % len(certifications)]
            )
            nurses[nurse.nurse_id] = nurse
        
        return nurses
    
    def _initialize_simpy_resources(self) -> None:
        """Initialize SimPy resources for simulation."""
        if not self.env:
            return
        
        for doctor in self.doctors.values():
            doctor.initialize_simpy_resource(self.env)
        
        for machine in self.mri_machines.values():
            machine.initialize_simpy_resource(self.env)
        
        for bed in self.beds.values():
            bed.initialize_simpy_resource(self.env)
        
        for nurse in self.triage_nurses.values():
            nurse.initialize_simpy_resource(self.env)
    
    def admit_patient(self, patient: Patient, current_time: float) -> None:
        """
        Admit patient to hospital system.
        
        Args:
            patient: Patient to admit
            current_time: Current simulation time
            
        Raises:
            ValueError: If patient is invalid or already in system
        """
        if not patient:
            raise ValueError("Patient cannot be None")
        if patient.patient_id in self.patients_in_system:
            raise ValueError(f"Patient {patient.patient_id} is already in the system")
        if current_time < 0:
            raise ValueError("Current time cannot be negative")
        
        # Add patient to system
        self.patients_in_system.add(patient.patient_id)
        patient.update_status(PatientStatus.WAITING_TRIAGE, current_time)
        
        # Add to triage queue
        self.patient_queues[ResourceType.TRIAGE_NURSE].append(patient)
        
        # Update metrics
        self.metrics.total_patients_processed += 1
        
        # Update operations state
        self._update_operations_state(current_time)
    
    def process_triage(self, current_time: float) -> Optional[Patient]:
        """
        Process next patient in triage queue.
        
        Args:
            current_time: Current simulation time
            
        Returns:
            Patient after triage assessment, or None if no patients or nurses available
        """
        # Check if there are patients waiting for triage
        triage_queue = self.patient_queues[ResourceType.TRIAGE_NURSE]
        if not triage_queue:
            return None
        
        # Find available triage nurse
        available_nurse = self._find_available_resource(ResourceType.TRIAGE_NURSE)
        if not available_nurse or not isinstance(available_nurse, TriageNurse):
            return None
        
        # Get next patient
        patient = triage_queue.pop(0)
        
        # Start triage assessment
        available_nurse.start_assessment(patient, current_time)
        
        # Simulate triage time
        triage_time = self.time_service.generate_triage_time()
        
        # Complete triage assessment
        assessed_patient = available_nurse.complete_assessment(current_time + triage_time)
        
        if assessed_patient:
            # Make preemption decision
            preemption_response = self.preemption_agent.make_preemption_decision(
                assessed_patient, self._create_hospital_operations_state(current_time + triage_time)
            )
            
            # Execute preemption decision
            self._execute_preemption_decision(preemption_response, assessed_patient, current_time + triage_time)
        
        # Update operations state
        self._update_operations_state(current_time + triage_time)
        
        return assessed_patient
    
    def _find_available_resource(self, resource_type: ResourceType) -> Optional[Union[Doctor, MRIMachine, Bed, TriageNurse]]:
        """Find available resource of specified type."""
        if resource_type == ResourceType.DOCTOR:
            return next((doctor for doctor in self.doctors.values() if doctor.is_available), None)
        elif resource_type == ResourceType.MRI_MACHINE:
            return next((mri for mri in self.mri_machines.values() if mri.is_available), None)
        elif resource_type == ResourceType.BED:
            return next((bed for bed in self.beds.values() if bed.can_admit_patient(Patient())), None)
        elif resource_type == ResourceType.TRIAGE_NURSE:
            return next((nurse for nurse in self.triage_nurses.values() if nurse.is_available), None)
        return None
    
    def _execute_preemption_decision(self, response: PreemptionResponse, patient: Patient, current_time: float) -> None:
        """
        Execute preemption decision from agent.
        
        Args:
            response: Preemption decision response
            patient: Patient requiring service
            current_time: Current simulation time
        """
        if response.decision == PreemptionDecision.NO_PREEMPTION:
            # Add patient to appropriate queue
            self.patient_queues[patient.required_resource].append(patient)
        
        elif response.decision == PreemptionDecision.PREEMPT_RESOURCE:
            if response.resource_id_to_preempt:
                preempted_patient = self._execute_resource_preemption(
                    response.resource_id_to_preempt, patient, current_time
                )
                if preempted_patient:
                    # Add preempted patient back to queue with higher priority
                    self._add_patient_to_priority_queue(preempted_patient, patient.required_resource)
        
        elif response.decision == PreemptionDecision.QUEUE_PATIENT:
            # Insert patient at specified queue position
            queue = self.patient_queues[patient.required_resource]
            position = min(response.target_queue_position or 0, len(queue))
            queue.insert(position, patient)
    
    def _execute_resource_preemption(self, resource_id: str, incoming_patient: Patient, current_time: float) -> Optional[Patient]:
        """
        Execute preemption on specified resource.
        
        Args:
            resource_id: ID of resource to preempt
            incoming_patient: Patient requiring the resource
            current_time: Current simulation time
            
        Returns:
            Preempted patient, or None if preemption failed
        """
        # Find resource by ID
        resource = self._find_resource_by_id(resource_id)
        if not resource:
            return None
        
        # Execute preemption based on resource type
        preempted_patient = None
        
        if isinstance(resource, Doctor):
            preempted_patient = resource.preempt_current_service(
                current_time, f"Preempted for {incoming_patient.priority.name} priority patient"
            )
            if preempted_patient:
                preempted_patient.update_status(PatientStatus.PREEMPTED, current_time)
                resource.start_service(incoming_patient, current_time)
                incoming_patient.update_status(PatientStatus.IN_SERVICE, current_time)
        
        elif isinstance(resource, MRIMachine):
            preempted_patient = resource.preempt_current_scan(
                current_time, f"Preempted for {incoming_patient.priority.name} priority patient"
            )
            if preempted_patient:
                preempted_patient.update_status(PatientStatus.PREEMPTED, current_time)
                resource.start_scan(incoming_patient, current_time)
                incoming_patient.update_status(PatientStatus.IN_SERVICE, current_time)
        
        # Update metrics
        if preempted_patient:
            self.metrics.total_preemptions_executed += 1
        
        return preempted_patient
    
    def _find_resource_by_id(self, resource_id: str) -> Optional[Union[Doctor, MRIMachine, Bed, TriageNurse]]:
        """Find resource by ID across all resource types."""
        # Check doctors
        if resource_id in self.doctors:
            return self.doctors[resource_id]
        
        # Check MRI machines
        if resource_id in self.mri_machines:
            return self.mri_machines[resource_id]
        
        # Check beds
        if resource_id in self.beds:
            return self.beds[resource_id]
        
        # Check triage nurses
        if resource_id in self.triage_nurses:
            return self.triage_nurses[resource_id]
        
        return None
    
    def _add_patient_to_priority_queue(self, patient: Patient, resource_type: ResourceType) -> None:
        """
        Add patient to queue with priority-based positioning.
        
        Args:
            patient: Patient to add to queue
            resource_type: Type of resource queue
        """
        queue = self.patient_queues[resource_type]
        
        # Find insertion position based on priority
        insert_position = 0
        for i, queued_patient in enumerate(queue):
            if patient.priority.value < queued_patient.priority.value:
                insert_position = i
                break
            insert_position = i + 1
        
        queue.insert(insert_position, patient)
    
    def discharge_patient(self, patient: Patient, current_time: float) -> None:
        """
        Discharge patient from hospital.
        
        Args:
            patient: Patient to discharge
            current_time: Current simulation time
            
        Raises:
            ValueError: If patient is not in system
        """
        if patient.patient_id not in self.patients_in_system:
            raise ValueError(f"Patient {patient.patient_id} is not in the system")
        
        # Update patient status
        patient.update_status(PatientStatus.DISCHARGED, current_time)
        
        # Remove from system
        self.patients_in_system.remove(patient.patient_id)
        self.discharged_patients.append(patient)
        
        # Update metrics
        self.metrics.total_patients_discharged += 1
        
        # Update operations state
        self._update_operations_state(current_time)
    
    def _create_hospital_operations_state(self, current_time: float) -> HospitalOperationsState:
        """
        Create HospitalOperationsState for preemption agent.
        
        Args:
            current_time: Current simulation time
            
        Returns:
            Current hospital operations state
        """
        # Create resource states
        resource_states: Dict[str, ResourceState] = {}
        
        # Add doctor states
        for doctor in self.doctors.values():
            resource_states[doctor.doctor_id] = ResourceState(
                resource_id=doctor.doctor_id,
                resource_type=ResourceType.DOCTOR,
                is_available=doctor.is_available,
                current_patient_id=doctor.current_patient.patient_id if doctor.current_patient else None,
                current_patient_priority=doctor.current_patient.priority if doctor.current_patient else None,
                estimated_remaining_time=doctor.estimate_remaining_service_time(),
                queue_length=len(self.patient_queues[ResourceType.DOCTOR])
            )
        
        # Add MRI machine states
        for mri in self.mri_machines.values():
            resource_states[mri.machine_id] = ResourceState(
                resource_id=mri.machine_id,
                resource_type=ResourceType.MRI_MACHINE,
                is_available=mri.is_available,
                current_patient_id=mri.current_patient.patient_id if mri.current_patient else None,
                current_patient_priority=mri.current_patient.priority if mri.current_patient else None,
                estimated_remaining_time=mri.estimate_remaining_scan_time(),
                queue_length=len(self.patient_queues[ResourceType.MRI_MACHINE])
            )
        
        # Create queue states
        queue_states = {
            resource_type: [patient.patient_id for patient in queue]
            for resource_type, queue in self.patient_queues.items()
        }
        
        # Calculate system metrics
        total_resources = sum(len(resources) for resources in [
            self.doctors, self.mri_machines, self.beds, self.triage_nurses
        ])
        busy_resources = sum(1 for resources in [
            self.doctors.values(), self.mri_machines.values(), 
            self.beds.values(), self.triage_nurses.values()
        ] for resource in resources if not resource.is_available)
        
        system_load = busy_resources / total_resources if total_resources > 0 else 0.0
        
        return HospitalOperationsState(
            timestamp=current_time,
            total_patients_in_system=len(self.patients_in_system),
            average_wait_time=self.metrics.average_wait_time,
            resource_states=resource_states,
            queue_states=queue_states,
            system_load=system_load
        )
    
    def _update_operations_state(self, current_time: float) -> None:
        """
        Update current operations state and add to history.
        
        Args:
            current_time: Current simulation time
        """
        # Save current state to history before updating
        if self.current_operations_state:
            self.operations_state_history.append(copy.deepcopy(self.current_operations_state))
        
        # Create new operations state (avoiding deepcopy of SimPy resources)
        self.current_operations_state = OperationsState(
            timestamp=current_time,
            doctors={k: self._create_doctor_snapshot(v) for k, v in self.doctors.items()},
            mri_machines={k: self._create_mri_snapshot(v) for k, v in self.mri_machines.items()},
            beds={k: self._create_bed_snapshot(v) for k, v in self.beds.items()},
            triage_nurses={k: self._create_nurse_snapshot(v) for k, v in self.triage_nurses.items()},
            patient_queues=copy.deepcopy(self.patient_queues),
            patients_in_system=self.patients_in_system.copy(),
            metrics=copy.deepcopy(self.metrics)
        )
        
        # Update system metrics
        self._update_system_metrics(current_time)
        
        # Limit history size to prevent memory issues
        if len(self.operations_state_history) > 1000:
            self.operations_state_history = self.operations_state_history[-500:]
    
    def _create_doctor_snapshot(self, doctor: Doctor) -> Doctor:
        """Create a snapshot of doctor without SimPy resource."""
        snapshot = Doctor(
            name=doctor.name,
            specialization=doctor.specialization
        )
        snapshot.doctor_id = doctor.doctor_id
        snapshot.is_available = doctor.is_available
        snapshot.current_patient = doctor.current_patient
        snapshot.metrics = copy.deepcopy(doctor.metrics)
        return snapshot
    
    def _create_mri_snapshot(self, mri: MRIMachine) -> MRIMachine:
        """Create a snapshot of MRI machine without SimPy resource."""
        snapshot = MRIMachine(
            name=mri.name,
            model=mri.model,
            tesla_strength=mri.tesla_strength
        )
        snapshot.machine_id = mri.machine_id
        snapshot.is_available = mri.is_available
        snapshot.is_under_maintenance = mri.is_under_maintenance
        snapshot.current_patient = mri.current_patient
        snapshot.metrics = copy.deepcopy(mri.metrics)
        return snapshot
    
    def _create_bed_snapshot(self, bed: Bed) -> Bed:
        """Create a snapshot of bed without SimPy resource."""
        snapshot = Bed(
            bed_number=bed.bed_number,
            ward_name=bed.ward_name,
            bed_type=bed.bed_type
        )
        snapshot.bed_id = bed.bed_id
        snapshot.is_available = bed.is_available
        snapshot.is_under_maintenance = bed.is_under_maintenance
        snapshot.needs_cleaning = bed.needs_cleaning
        snapshot.current_patient = bed.current_patient
        snapshot.metrics = copy.deepcopy(bed.metrics)
        return snapshot
    
    def _create_nurse_snapshot(self, nurse: TriageNurse) -> TriageNurse:
        """Create a snapshot of triage nurse without SimPy resource."""
        snapshot = TriageNurse(
            name=nurse.name,
            experience_years=nurse.experience_years,
            certification_level=nurse.certification_level
        )
        snapshot.nurse_id = nurse.nurse_id
        snapshot.is_available = nurse.is_available
        snapshot.current_patient = nurse.current_patient
        snapshot.metrics = copy.deepcopy(nurse.metrics)
        return snapshot
    
    def _update_system_metrics(self, current_time: float) -> None:
        """
        Update system-wide performance metrics.
        
        Args:
            current_time: Current simulation time
        """
        # Calculate current system load
        total_resources = sum([
            len(self.doctors), len(self.mri_machines), 
            len(self.beds), len(self.triage_nurses)
        ])
        
        busy_resources = sum([
            sum(1 for doctor in self.doctors.values() if not doctor.is_available),
            sum(1 for mri in self.mri_machines.values() if not mri.is_available),
            sum(1 for bed in self.beds.values() if not bed.is_available),
            sum(1 for nurse in self.triage_nurses.values() if not nurse.is_available)
        ])
        
        self.metrics.current_system_load = busy_resources / total_resources if total_resources > 0 else 0.0
        self.metrics.peak_system_load = max(self.metrics.peak_system_load, self.metrics.current_system_load)
        
        # Update resource utilization
        for resource_type in ResourceType:
            if resource_type == ResourceType.DOCTOR:
                total = len(self.doctors)
                busy = sum(1 for doctor in self.doctors.values() if not doctor.is_available)
            elif resource_type == ResourceType.MRI_MACHINE:
                total = len(self.mri_machines)
                busy = sum(1 for mri in self.mri_machines.values() if not mri.is_available)
            elif resource_type == ResourceType.BED:
                total = len(self.beds)
                busy = sum(1 for bed in self.beds.values() if not bed.is_available)
            elif resource_type == ResourceType.TRIAGE_NURSE:
                total = len(self.triage_nurses)
                busy = sum(1 for nurse in self.triage_nurses.values() if not nurse.is_available)
            else:
                total = busy = 0
            
            self.metrics.resource_utilization[resource_type] = busy / total if total > 0 else 0.0
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive hospital performance summary.
        
        Returns:
            Dictionary with key performance indicators
        """
        return {
            "hospital_name": self.name,
            "total_patients_processed": self.metrics.total_patients_processed,
            "total_patients_discharged": self.metrics.total_patients_discharged,
            "patients_currently_in_system": len(self.patients_in_system),
            "total_preemptions_executed": self.metrics.total_preemptions_executed,
            "current_system_load": self.metrics.current_system_load,
            "peak_system_load": self.metrics.peak_system_load,
            "resource_utilization": {
                resource_type.name: utilization 
                for resource_type, utilization in self.metrics.resource_utilization.items()
            },
            "queue_lengths": {
                resource_type.name: len(queue)
                for resource_type, queue in self.patient_queues.items()
            },
            "resource_counts": {
                "doctors": len(self.doctors),
                "mri_machines": len(self.mri_machines),
                "beds": len(self.beds),
                "triage_nurses": len(self.triage_nurses)
            }
        }
    
    def __str__(self) -> str:
        return f"{self.name} (Patients: {len(self.patients_in_system)}, Load: {self.metrics.current_system_load:.1%})"
    
    def __repr__(self) -> str:
        return (f"Hospital(name={self.name}, doctors={len(self.doctors)}, "
                f"mri={len(self.mri_machines)}, beds={len(self.beds)}, "
                f"nurses={len(self.triage_nurses)})")