import attr
import random
import simpy
from typing import List
from ..entities.hospital import HospitalCore
from ..entities.patient import Patient
from ..entities.preemption_agent import PreemptionAgent
from ..entities.sub_entities.preemption_decision import PreemptionDecision
from ..enums.Triage import Priority
from ..providers.patient import PatientDataProvider
from ..triage_systems.base import TriageSystem
from ..handler.console_event_handler import ConsoleEventHandler as HospitalEventHandler
from ..utils.logger import get_logger, initialize_logger, EventType, LogLevel

@attr.s(auto_attribs=True)
class HospitalSimulationEngine:
    """SimPy-based simulation engine - pluggable and replaceable"""
    
    env: simpy.Environment
    hospital: HospitalCore
    
    # Plugins
    patient_provider: PatientDataProvider
    triage_system: TriageSystem
    preemption_agent: PreemptionAgent
    event_handler: HospitalEventHandler
    
    # SimPy Resources
    doctor_resources: List[simpy.PreemptiveResource] = attr.ib(factory=list)
    triage_resources: simpy.Resource = attr.ib(init=False)
    
    def __attrs_post_init__(self):
        """Initialize simulation resources"""
        self.logger = get_logger()
        
        # Log simulation initialization
        self.logger.log_event(
            timestamp=0.0,
            event_type=EventType.SIMULATION_START,
            message=f"Simulation engine initialized with {self.hospital.num_doctors} doctors and {self.hospital.triage_nurses} triage nurses",
            data={
                "num_doctors": self.hospital.num_doctors,
                "triage_nurses": self.hospital.triage_nurses,
                "simulation_engine": "HospitalSimulationEngine"
            },
            source="simulation_engine"
        )
        
        # Create doctor resources
        for i in range(self.hospital.num_doctors):
            resource = simpy.PreemptiveResource(self.env, capacity=1)
            self.doctor_resources.append(resource)
            
            # Log resource creation
            self.logger.log_event(
                timestamp=0.0,
                event_type=EventType.SYSTEM_STATE,
                message=f"Doctor resource {i} created (PreemptiveResource)",
                data={"doctor_resource_id": i, "capacity": 1},
                level=LogLevel.DEBUG,
                source="simulation_engine"
            )
        
        # Create triage resource
        self.triage_resources = simpy.Resource(self.env, capacity=self.hospital.triage_nurses)
        
        self.logger.log_event(
            timestamp=0.0,
            event_type=EventType.SYSTEM_STATE,
            message=f"Triage resource created with capacity {self.hospital.triage_nurses}",
            data={"triage_capacity": self.hospital.triage_nurses},
            level=LogLevel.DEBUG,
            source="simulation_engine"
        )
    
    def patient_arrival_process(self):
        """Handle patient arrivals"""
        while not self.patient_provider.is_finished():
            patient = self.patient_provider.get_next_patient()
            if patient is None:
                break
            
            # Update arrival time to simulation time
            patient.arrival_time = self.env.now
            
            # Register patient
            self.hospital.register_patient(patient, self.env.now)
            self.event_handler.on_patient_arrival(patient)
            
            # Start triage process
            self.env.process(self.triage_process(patient))
            
            # Wait for next arrival
            if hasattr(self.patient_provider, 'get_next_arrival_time'):
                next_time = self.patient_provider.get_next_arrival_time(self.env.now)
                yield self.env.timeout(next_time - self.env.now)
            else:
                yield self.env.timeout(random.expovariate(0.3))  # Default rate
    
    def triage_process(self, patient: Patient):
        """Triage assessment process"""
        with self.triage_resources.request() as req:
            yield req
            
            # Triage assessment with logging
            assessment = self.triage_system.assess_patient(patient, self.env.now)
            triage_time = random.uniform(2, 5)
            
            # Log triage duration
            self.logger.log_event(
                timestamp=self.env.now,
                event_type=EventType.TRIAGE_ASSESSMENT,
                message=f"Triage process duration: {triage_time:.1f} minutes for Patient {patient.id}",
                data={
                    "patient_id": patient.id,
                    "triage_duration": triage_time,
                    "triage_start_time": self.env.now
                },
                level=LogLevel.DEBUG,
                source="simulation_engine"
            )
            
            yield self.env.timeout(triage_time)
            
            self.event_handler.on_triage_complete(patient, assessment, self.env.now)
            
            # Assign to queue with current time
            self.hospital.assign_patient_to_queue(patient, assessment, self.env.now)
            
            # Check for preemption
            if assessment.priority in [Priority.RED, Priority.ORANGE]:
                yield self.env.process(self.check_preemption(patient))
    
    def check_preemption(self, new_patient: Patient):
        """Check and execute preemption if needed"""
        busy_doctors = self.hospital.get_busy_doctors()
        
        # Log preemption check initiation
        self.logger.log_event(
            timestamp=self.env.now,
            event_type=EventType.PREEMPTION_DECISION,
            message=f"Preemption check initiated for Patient {new_patient.id}",
            data={
                "patient_id": new_patient.id,
                "patient_priority": new_patient.priority.name if new_patient.priority else None,
                "busy_doctors_count": len(busy_doctors)
            },
            level=LogLevel.DEBUG,
            source="simulation_engine"
        )
        
        if busy_doctors:
            decision = self.preemption_agent.should_preempt(new_patient, busy_doctors, self.env.now)
            decision.timestamp = self.env.now
            
            if decision.should_preempt and decision.doctor_to_preempt:
                yield self.env.process(self.execute_preemption(decision))
        else:
            self.logger.log_event(
                timestamp=self.env.now,
                event_type=EventType.PREEMPTION_DECISION,
                message=f"No preemption possible - no busy doctors available",
                data={"patient_id": new_patient.id},
                source="simulation_engine"
            )
        
        yield self.env.timeout(0)
    
    def execute_preemption(self, decision: PreemptionDecision):
        """Execute preemption decision"""
        doctor_id = decision.doctor_to_preempt
        doctor = next((d for d in self.hospital.doctors if d.id == doctor_id), None)
        
        if doctor and doctor.current_patient:
            interrupted_patient = doctor.current_patient
            new_priority = self.hospital.handle_preemption(interrupted_patient, self.env.now)
            
            self.event_handler.on_preemption(decision, [interrupted_patient])
        
        yield self.env.timeout(0)
    
    def doctor_process(self, doctor_id: int):
        """Doctor treatment process"""
        doctor = self.hospital.doctors[doctor_id]
        doctor_resource = self.doctor_resources[doctor_id]
        
        while True:
            # Get next patient
            result = self.hospital.get_next_patient_for_treatment()
            
            if result is None:
                yield self.env.timeout(1)  # Wait and try again
                continue
            
            patient, priority = result
            
            # Request resource
            with doctor_resource.request(priority=priority.value) as req:
                try:
                    yield req
                    
                    # Start treatment
                    self.hospital.assign_doctor_to_patient(doctor, patient, self.env.now)
                    self.event_handler.on_treatment_start(patient, doctor)
                    
                    # Treatment time
                    yield self.env.timeout(patient.treatment_time)
                    
                    # Complete treatment
                    self.hospital.complete_treatment(doctor, patient, self.env.now)
                    self.event_handler.on_treatment_complete(patient, doctor, self.env.now)
                    
                except simpy.Interrupt:
                    # Handle preemption
                    if doctor.current_patient:
                        doctor.current_patient = None
                    doctor.busy = False
    
    def run_simulation(self, duration: int = 480):
        """Run the complete simulation"""
        print(f"Starting simulation - Duration: {duration} minutes")
        print(f"Hospital: {self.hospital.num_doctors} doctors, {self.hospital.triage_nurses} triage nurses")
        print("-" * 80)
        
        # Start processes
        self.env.process(self.patient_arrival_process())
        
        for i in range(self.hospital.num_doctors):
            self.env.process(self.doctor_process(i))
        
        # Run simulation
        self.env.run(until=duration)
        
        # Print final statistics
        self.print_statistics()
    
    def print_statistics(self):
        """Print simulation results"""
        status = self.hospital.get_hospital_status()
        
        print("\n" + "="*80)
        print("FINAL SIMULATION RESULTS")
        print("="*80)
        
        print(f"Patients: {status['total_arrivals']} arrived, {status['total_completed']} completed")
        print(f"Still in system: {status['patients_in_system']}")
        
        if self.hospital.completed_patients:
            avg_wait = sum(p.wait_time for p in self.hospital.completed_patients) / len(self.hospital.completed_patients)
            print(f"Average wait time: {avg_wait:.1f} minutes")
        
        print("\nQueue lengths:")
        for priority, length in status['queue_lengths'].items():
            print(f"  {priority}: {length}")
        
        print("\nDoctor performance:")
        for doctor_id, stats in status['doctor_status'].items():
            print(f"  {doctor_id}: {stats['patients_treated']} patients")

