import simpy
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Generator, Union
from numpy.typing import NDArray

from .constants import (
    RESOURCES,
    SERVICE_TIMES,
    PRIORITY,
)
from .models import Patient
from .resources import PriorityResource
from .agents import RoutingAgent
from .patient_generation import PatientFactory, PatientConfiguration
from .metrics import SimulationMetrics


@dataclass
class EDSimulation:
    """
    Main ED simulation class using SimPy for discrete-event simulation.
    """
    scenario: str
    duration: int
    arrival_rate: float
    num_doctors: int
    num_mri: int
    num_ultrasound: int
    num_beds: int
    single_llm_accuracy: float
    multi_llm_accuracy: float

    env: simpy.Environment = field(default_factory=simpy.Environment, init=False)
    patients: List[Patient] = field(default_factory=list)
    resources: Dict[str, PriorityResource] = field(init=False)
    agent: RoutingAgent = field(init=False)
    patient_factory: PatientFactory = field(init=False)
    wait_times: Dict[str, List[float]] = field(default_factory=lambda: {r: [] for r in RESOURCES})
    queue_lengths: List[List[float]] = field(default_factory=list)
    resource_busy_time: Dict[str, float] = field(default_factory=lambda: {r: 0.0 for r in RESOURCES})
    patient_id: int = 0
    urgent_mri_total: int = 0
    urgent_mri_bypassed: int = 0
    # Real-time evaluation tracking
    evaluation_results: Dict[str, Union[float, int, str]] = field(default_factory=dict)

    def __post_init__(self):
        # Initialize resources with SimPy PriorityResource
        self.resources = {
            'doctor': PriorityResource(self.env, 'doctor', self.num_doctors),
            'mri': PriorityResource(self.env, 'mri', self.num_mri),
            'ultrasound': PriorityResource(self.env, 'ultrasound', self.num_ultrasound),
            'bed': PriorityResource(self.env, 'bed', self.num_beds)
        }
        # Initialize routing agent
        self.agent = RoutingAgent(
            single_llm_accuracy=self.single_llm_accuracy,
            multi_llm_accuracy=self.multi_llm_accuracy
        )
        # Initialize patient factory with default configuration
        patient_config = PatientConfiguration()
        self.patient_factory = PatientFactory(patient_config)



    def patient_generator(self) -> Generator[simpy.Event, Any, None]:
        # Generate patients via Poisson process until duration exceeded
        while self.env.now < self.duration:
            # Create patient using factory pattern
            p = self.patient_factory.create_patient(self.patient_id)
            self.patient_id += 1
            
            # Track urgent MRI cases
            if p.triage == 'red' and p.needs_mri:
                self.urgent_mri_total += 1
            
            # Route to tasks using agent
            p.tasks = self.agent.route(p, self.scenario)
            
            # Track bypasses for urgent cases
            if p.triage == 'red' and p.needs_mri and p.tasks and p.tasks[0] == 'mri':
                self.urgent_mri_bypassed += 1
            
            self.patients.append(p)
            
            # Start patient processing process
            self.env.process(self.process_patient(p))
            
            # Advance time to next arrival (exponential interarrival)
            yield self.env.timeout(float(np.random.exponential(60 / self.arrival_rate)))
            
            # Record queue lengths at arrival times (total waiting per resource via SimPy count)
            self.queue_lengths.append([float(self.env.now)] + [float(self.resources[r].resource.count) for r in RESOURCES])

    def process_patient(self, patient: Patient) -> Generator[simpy.Event, Any, None]:
        # Process each task sequentially for the patient
        for task in patient.tasks:
            res = self.resources[task]
            # Record request time
            request_time = self.env.now
            # Request resource with priority based on triage (yields until granted)
            with res.resource.request(priority=PRIORITY[patient.triage]) as req:  # type: ignore
                yield req
                # Service starts now
                start_time = self.env.now
                # Compute wait time for this resource
                wait_time = start_time - request_time
                # Record global wait time for stats
                self.wait_times[task].append(float(wait_time))
                # Sample service time (exponential)
                service_time = float(np.random.exponential(SERVICE_TIMES[task]))
                # Accumulate busy time for utilization
                self.resource_busy_time[task] += service_time
                # Perform service
                yield self.env.timeout(service_time)
                # Service ends (release automatic via 'with')

    def run(self) -> None:
        # Run the simulation: start patient generator and advance to duration
        self.env.process(self.patient_generator())
        self.env.run(until=self.duration)
        # Perform mock LLM evaluation during simulation completion
        self.evaluation_results = self.agent.mock_llm_evaluation(self.patients, self.scenario)

    def analyze(self) -> Tuple[Dict[str, Dict[str, float]], NDArray[np.float64], Dict[str, float], Dict[str, float], Dict[str, Union[float, int, str]]]:
        # Resource capacities for metrics calculation
        resource_capacities = {
            'doctor': self.num_doctors,
            'mri': self.num_mri,
            'ultrasound': self.num_ultrasound,
            'bed': self.num_beds
        }
        
        # Use metrics service for all calculations
        metrics = SimulationMetrics.calculate_comprehensive_metrics(  # type: ignore
            wait_times=self.wait_times,
            queue_lengths=self.queue_lengths,
            resource_busy_time=self.resource_busy_time,
            duration=self.duration,
            resource_capacities=resource_capacities,
            urgent_mri_total=self.urgent_mri_total,
            urgent_mri_bypassed=self.urgent_mri_bypassed,
            patients=self.patients
        )
        
        # Extract metrics for backward compatibility with proper type casting
        stats = metrics['wait_statistics']  # type: ignore
        queue_arr = metrics['queue_array']  # type: ignore
        utilization = metrics['utilization']  # type: ignore
        urgent_stats = metrics['urgent_care_metrics']  # type: ignore
        
        # Store comprehensive metrics for future use
        self.comprehensive_metrics = metrics  # type: ignore
        
        # Return evaluation results computed during simulation
        return stats, queue_arr, utilization, urgent_stats, self.evaluation_results