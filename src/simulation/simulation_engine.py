import attr
import random
import simpy
from typing import List, Optional
from ..entities.hospital import HospitalCore
from ..entities.patient import Patient
from ..entities.preemption_agent import PreemptionAgent
from ..entities.sub_entities.preemption_decision import PreemptionDecision
from ..entities.sub_entities.simulation_state import SimulationState
from ..enums.Triage import Priority
from ..providers.patient import PatientDataProvider
from ..triage_systems.base import BaseTriageSystem
from ..handler.console_event_handler import ConsoleEventHandler as HospitalEventHandler
from ..utils.logger import get_logger, initialize_logger, EventType, LogLevel

@attr.s(auto_attribs=True)
class HospitalSimulationEngine:
    """SimPy-based simulation engine - pluggable and replaceable"""
    
    env: simpy.Environment
    hospital: HospitalCore
    
    # Plugins
    patient_provider: PatientDataProvider
    triage_system: BaseTriageSystem
    preemption_agent: Optional[PreemptionAgent]
    event_handler: HospitalEventHandler
    
    # SimPy Resources
    doctor_resources: List[simpy.PreemptiveResource] = attr.ib(factory=list)
    mri_resources: List[simpy.PreemptiveResource] = attr.ib(factory=list)
    blood_nurse_resources: List[simpy.PreemptiveResource] = attr.ib(factory=list)
    bed_resources: List[simpy.Resource] = attr.ib(factory=list)  # Non-preemptive
    triage_resources: simpy.Resource = attr.ib(init=False)
    
    # Centralized state management
    simulation_state: SimulationState = attr.ib(factory=SimulationState)
    
    def __attrs_post_init__(self):
        """Initialize simulation resources"""
        self.logger = get_logger()
        
        # Log simulation initialization
        self.logger.log_event(
            timestamp=0.0,
            event_type=EventType.SIMULATION_START,
            message=f"Simulation engine initialized with {self.hospital.num_doctors} doctors, {self.hospital.num_mri_machines} MRI machines, {self.hospital.num_blood_nurses} blood nurses, {self.hospital.num_beds} beds, and {self.hospital.triage_nurses} triage nurses",
            simulation_state=self.simulation_state,
            data={
                "num_doctors": self.hospital.num_doctors,
                "num_mri_machines": self.hospital.num_mri_machines,
                "num_blood_nurses": self.hospital.num_blood_nurses,
                "num_beds": self.hospital.num_beds,
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
                simulation_state=self.simulation_state,
                data={"doctor_resource_id": i, "capacity": 1},
                level=LogLevel.DEBUG,
                source="simulation_engine"
            )
        
        # Create MRI machine resources
        for i in range(self.hospital.num_mri_machines):
            resource = simpy.PreemptiveResource(self.env, capacity=1)
            self.mri_resources.append(resource)
            
            # Log resource creation
            self.logger.log_event(
                timestamp=0.0,
                event_type=EventType.SYSTEM_STATE,
                message=f"MRI resource {i} created (PreemptiveResource)",
                simulation_state=self.simulation_state,
                data={"mri_resource_id": i, "capacity": 1},
                level=LogLevel.DEBUG,
                source="simulation_engine"
            )
        
        # Create blood nurse resources
        for i in range(self.hospital.num_blood_nurses):
            resource = simpy.PreemptiveResource(self.env, capacity=1)
            self.blood_nurse_resources.append(resource)
            
            # Log resource creation
            self.logger.log_event(
                timestamp=0.0,
                event_type=EventType.SYSTEM_STATE,
                message=f"Blood nurse resource {i} created (PreemptiveResource)",
                simulation_state=self.simulation_state,
                data={"blood_nurse_resource_id": i, "capacity": 1},
                level=LogLevel.DEBUG,
                source="simulation_engine"
            )
        
        # Create bed resources (non-preemptive)
        for i in range(self.hospital.num_beds):
            resource = simpy.Resource(self.env, capacity=1)
            self.bed_resources.append(resource)
            
            # Log resource creation
            self.logger.log_event(
                timestamp=0.0,
                event_type=EventType.SYSTEM_STATE,
                message=f"Bed resource {i} created (Non-preemptive Resource)",
                simulation_state=self.simulation_state,
                data={"bed_resource_id": i, "capacity": 1, "preemptive": False},
                level=LogLevel.DEBUG,
                source="simulation_engine"
            )
        
        # Create triage resource
        self.triage_resources = simpy.Resource(self.env, capacity=self.hospital.triage_nurses)
        
        self.logger.log_event(
            timestamp=0.0,
            event_type=EventType.SYSTEM_STATE,
            message=f"Triage resource created with capacity {self.hospital.triage_nurses}",
            simulation_state=self.simulation_state,
            data={"triage_capacity": self.hospital.triage_nurses},
            level=LogLevel.DEBUG,
            source="simulation_engine"
        )
        
        # Test resources are managed by hospital's test_resource_manager
        # No SimPy resources needed - hospital handles allocation and preemption
        
        # Initialize simulation state with resource IDs matching hospital
        self.simulation_state.available_doctors = [doctor.id for doctor in self.hospital.doctors]
        self.simulation_state.available_mri_machines = [mri.id for mri in self.hospital.mri_machines]
        self.simulation_state.available_blood_nurses = [nurse.id for nurse in self.hospital.blood_nurses]
        self.simulation_state.available_beds = [bed.id for bed in self.hospital.beds]
        self.simulation_state.simulation_duration = 480.0  # Default duration
    
    def _sync_queue_lengths(self) -> None:
        """Sync all queue lengths from hospital to simulation state"""
        try:
            queue_lengths = {priority: len(queue) for priority, queue in self.hospital.priority_queues.items()}
            self.simulation_state.update_all_queue_lengths(queue_lengths)
        except TypeError as e:
            print(f"DEBUG: Error in _sync_queue_lengths: {e}")
            print(f"DEBUG: priority_queues type: {type(self.hospital.priority_queues)}")
            for priority, queue in self.hospital.priority_queues.items():
                print(f"DEBUG: Priority {priority}: type={type(queue)}, value={queue}")
            raise
    
    def patient_arrival_process(self):
        """Handle patient arrivals"""
        while not self.patient_provider.is_finished():
            patient = self.patient_provider.get_next_patient()
            if patient is None:
                break
            
            # Update simulation state time
            self.simulation_state.update_time(self.env.now)
            
            # Update arrival time to simulation time
            patient.arrival_time = self.env.now
            
            # Register patient in both hospital and simulation state
            self.hospital.register_patient(patient, self.env.now)
            self.simulation_state.register_patient_arrival(patient)
            self.event_handler.on_patient_arrival(patient)
            
            # Start triage process
            self.env.process(self.triage_process(patient))
            
            # Wait for next arrival
            try:
                next_time = self.patient_provider.get_next_arrival_time(self.env.now)
                yield self.env.timeout(next_time - self.env.now)
            except AttributeError:
                # Provider doesn't implement get_next_arrival_time, use default rate
                yield self.env.timeout(random.expovariate(0.3))
    
    def triage_process(self, patient: Patient):
        """Triage assessment process"""
        with self.triage_resources.request() as req:
            yield req
            
            # Update simulation state time
            self.simulation_state.update_time(self.env.now)
            
            # Triage assessment with logging
            assessment = self.triage_system.assess_patient(patient, self.env.now)
            triage_time = random.uniform(2, 5)
            
            # Log triage duration
            self.logger.log_event(
                timestamp=self.env.now,
                event_type=EventType.TRIAGE_ASSESSMENT,
                message=f"Triage process duration: {triage_time:.1f} minutes for Patient {patient.id}",
                simulation_state=self.simulation_state,
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
            
            # Sync queue lengths to simulation state
            self._sync_queue_lengths()
            
            # Check for preemption
            if assessment.priority in [Priority.RED, Priority.ORANGE]:
                yield self.env.process(self.check_preemption(patient))
    
    def check_preemption(self, new_patient: Patient):
        """Check and execute preemption if needed"""
        # Update simulation state time
        self.simulation_state.update_time(self.env.now)
        
        # Skip preemption check if agent is disabled
        if self.preemption_agent is None:
            self.logger.log_event(
                timestamp=self.env.now,
                event_type=EventType.PREEMPTION_DECISION,
                message=f"Preemption disabled - Patient {new_patient.id} will use standard queue assignment",
                simulation_state=self.simulation_state,
                data={
                    "patient_id": new_patient.id,
                    "patient_priority": new_patient.priority.name if new_patient.priority else None,
                    "preemption_mode": "disabled"
                },
                level=LogLevel.DEBUG,
                source="simulation_engine"
            )
            yield self.env.timeout(0)
            return
        
        busy_doctors = self.hospital.get_busy_doctors()
        
        # Log preemption check initiation
        self.logger.log_event(
            timestamp=self.env.now,
            event_type=EventType.PREEMPTION_DECISION,
            message=f"Preemption check initiated for Patient {new_patient.id}",
            simulation_state=self.simulation_state,
            data={
                "patient_id": new_patient.id,
                "patient_priority": new_patient.priority.name if new_patient.priority else None,
                "busy_doctors_count": len(busy_doctors)
            },
            level=LogLevel.DEBUG,
            source="simulation_engine"
        )
        
        if busy_doctors:
            # Get busy MRI machines and blood nurses
            busy_mri_machines = [mri for mri in self.hospital.mri_machines if mri.busy]
            busy_blood_nurses = [nurse for nurse in self.hospital.blood_nurses if nurse.busy]
            
            decision = self.preemption_agent.should_preempt(
                new_patient, 
                busy_doctors, 
                busy_mri_machines, 
                busy_blood_nurses, 
                self.env.now
            )
            decision.timestamp = self.env.now
            
            if decision.should_preempt and decision.doctor_to_preempt:
                yield self.env.process(self.execute_preemption(decision))
        else:
            self.logger.log_event(
                timestamp=self.env.now,
                event_type=EventType.PREEMPTION_DECISION,
                message=f"No preemption possible - no busy doctors available",
                simulation_state=self.simulation_state,
                data={"patient_id": new_patient.id},
                source="simulation_engine"
            )
        
        yield self.env.timeout(0)
    
    def execute_preemption(self, decision: PreemptionDecision):
        """Execute preemption decision"""
        # Update simulation state time
        self.simulation_state.update_time(self.env.now)
        
        affected_patients = []
        
        # Handle doctor preemption
        if decision.doctor_to_preempt:
            doctor = decision.doctor_to_preempt
            if doctor.current_patient:
                interrupted_patient = doctor.current_patient
                new_priority = self.hospital.handle_preemption(interrupted_patient, self.env.now)
                affected_patients.append(interrupted_patient)
        
        # Handle MRI machine preemption
        if decision.mri_machine_to_preempt:
            mri_machine = decision.mri_machine_to_preempt
            if mri_machine.current_patient:
                interrupted_patient = mri_machine.current_patient
                # Stop current MRI scan and requeue patient
                mri_machine.busy = False
                mri_machine.current_patient = None
                affected_patients.append(interrupted_patient)
        
        # Handle blood test nurse preemption
        if decision.blood_nurse_to_preempt:
            nurse = decision.blood_nurse_to_preempt
            if nurse.current_patient:
                interrupted_patient = nurse.current_patient
                # Stop current blood test and requeue patient
                nurse.busy = False
                nurse.current_patient = None
                affected_patients.append(interrupted_patient)
        
        # Record preemption in simulation state
        if affected_patients:
            self.simulation_state.record_preemption()
            self.event_handler.on_preemption(decision, affected_patients)
        
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
            
            # Sync queue lengths to simulation state after patient removal
            self._sync_queue_lengths()
            
            # Request resource
            with doctor_resource.request(priority=priority.value) as req:
                try:
                    yield req
                    
                    # Update simulation state time
                    self.simulation_state.update_time(self.env.now)
                    
                    # Start treatment - update both hospital and simulation state
                    self.hospital.assign_doctor_to_patient(doctor, patient, self.env.now)
                    self.simulation_state.assign_doctor_to_patient(doctor.id, patient.id)
                    self.event_handler.on_treatment_start(patient, doctor)
                    

                    
                    # Treatment time
                    yield self.env.timeout(patient.treatment_time)
                    
                    # Update simulation state time after treatment
                    self.simulation_state.update_time(self.env.now)
                    
                    # Complete treatment - update both hospital and simulation state
                    self.hospital.complete_treatment(doctor, patient, self.env.now)
                    self.simulation_state.release_doctor(doctor.id)
                    self.simulation_state.register_patient_completion(patient)
                    self.event_handler.on_treatment_complete(patient, doctor, self.env.now)
                    
                except simpy.Interrupt:
                    # Handle preemption - update simulation state
                    if doctor.current_patient:
                        doctor.current_patient = None
                        self.simulation_state.release_doctor(doctor.id)
                    doctor.busy = False
    
    def mri_process(self, mri_id: int):
        """MRI machine process"""
        mri_machine = self.hospital.mri_machines[mri_id]
        mri_resource = self.mri_resources[mri_id]
        
        while True:
            # Get next patient needing MRI
            result = self.hospital.get_next_patient_for_treatment()
            
            if result is None:
                yield self.env.timeout(1)  # Wait and try again
                continue
            
            patient, priority = result
            
            # Check if patient needs MRI test
            from ..entities.testing.mri_test import MRITest
            needs_mri = any(isinstance(test, MRITest) for test in patient.test_results) if patient.test_results else False
            
            if not needs_mri:
                # Put patient back in queue for other resources
                self.hospital.priority_queues[priority].insert(0, patient)
                yield self.env.timeout(0.1)
                continue
            
            # Sync queue lengths to simulation state after patient removal
            self._sync_queue_lengths()
            
            # Request MRI resource
            with mri_resource.request(priority=priority.value) as req:
                try:
                    yield req
                    
                    # Update simulation state time
                    self.simulation_state.update_time(self.env.now)
                    
                    # Start MRI scan
                    self.hospital.assign_mri_to_patient(mri_machine, patient, self.env.now)
                    self.simulation_state.assign_mri_to_patient(mri_machine.id, patient.id)
                    self.event_handler.on_treatment_start(patient, mri_machine)
                    
                    # MRI scan time (typically 30-60 minutes)
                    scan_time = random.uniform(30, 60)
                    yield self.env.timeout(scan_time)
                    
                    # Update simulation state time after scan
                    self.simulation_state.update_time(self.env.now)
                    
                    # Complete MRI scan
                    updated_patient = mri_machine.complete_mri_scan(patient, self.env.now, self.logger)
                    self.simulation_state.release_mri(mri_machine.id)
                    self.simulation_state.register_patient_completion(updated_patient)
                    self.event_handler.on_treatment_complete(updated_patient, mri_machine, self.env.now)
                    
                except simpy.Interrupt:
                    # Handle preemption
                    if mri_machine.current_patient:
                        mri_machine.current_patient = None
                    mri_machine.busy = False
                    self.simulation_state.release_mri(mri_machine.id)
    
    def blood_nurse_process(self, nurse_id: int):
        """Blood test nurse process"""
        blood_nurse = self.hospital.blood_nurses[nurse_id]
        nurse_resource = self.blood_nurse_resources[nurse_id]
        
        while True:
            # Get next patient needing blood test
            result = self.hospital.get_next_patient_for_treatment()
            
            if result is None:
                yield self.env.timeout(1)  # Wait and try again
                continue
            
            patient, priority = result
            
            # Check if patient needs blood test
            from ..entities.testing.blood_test import BloodTest
            needs_blood_test = any(isinstance(test, BloodTest) for test in patient.test_results) if patient.test_results else False
            
            if not needs_blood_test:
                # Put patient back in queue for other resources
                self.hospital.priority_queues[priority].insert(0, patient)
                yield self.env.timeout(0.1)
                continue
            
            # Sync queue lengths to simulation state after patient removal
            self._sync_queue_lengths()
            
            # Request blood nurse resource
            with nurse_resource.request(priority=priority.value) as req:
                try:
                    yield req
                    
                    # Update simulation state time
                    self.simulation_state.update_time(self.env.now)
                    
                    # Start blood test
                    self.hospital.assign_blood_nurse_to_patient(blood_nurse, patient, self.env.now)
                    self.simulation_state.assign_blood_nurse_to_patient(blood_nurse.id, patient.id)
                    self.event_handler.on_treatment_start(patient, blood_nurse)
                    
                    # Blood test time (typically 15-30 minutes)
                    test_time = random.uniform(15, 30)
                    yield self.env.timeout(test_time)
                    
                    # Update simulation state time after test
                    self.simulation_state.update_time(self.env.now)
                    
                    # Complete blood test
                    updated_patient = blood_nurse.complete_blood_test(patient, self.env.now, self.logger)
                    self.simulation_state.release_blood_nurse(blood_nurse.id)
                    self.simulation_state.register_patient_completion(updated_patient)
                    self.event_handler.on_treatment_complete(updated_patient, blood_nurse, self.env.now)
                    
                except simpy.Interrupt:
                    # Handle preemption
                    if blood_nurse.current_patient:
                        blood_nurse.current_patient = None
                    blood_nurse.busy = False
                    self.simulation_state.release_blood_nurse(blood_nurse.id)
    
    def bed_process(self, bed_id: int):
        """Bed process (non-preemptive)"""
        bed = self.hospital.beds[bed_id]
        bed_resource = self.bed_resources[bed_id]
        
        while True:
            # Get next patient needing bed
            result = self.hospital.get_next_patient_for_treatment()
            
            if result is None:
                yield self.env.timeout(1)  # Wait and try again
                continue
            
            patient, priority = result
            
            # Check if patient needs bed (after treatment/tests)
            needs_bed = hasattr(patient, 'needs_admission') and patient.needs_admission
            
            if not needs_bed:
                # Put patient back in queue for other resources
                self.hospital.priority_queues[priority].insert(0, patient)
                yield self.env.timeout(0.1)
                continue
            
            # Sync queue lengths to simulation state after patient removal
            self._sync_queue_lengths()
            
            # Request bed resource (non-preemptive)
            with bed_resource.request() as req:
                yield req
                
                # Update simulation state time
                self.simulation_state.update_time(self.env.now)
                
                # Assign bed to patient
                self.hospital.assign_bed_to_patient(bed, patient, self.env.now)
                self.simulation_state.assign_bed_to_patient(bed.id, patient.id)
                self.event_handler.on_treatment_start(patient, bed)
                
                # Bed stay time (varies widely, 1-24 hours)
                stay_time = random.uniform(60, 1440)  # 1-24 hours in minutes
                yield self.env.timeout(stay_time)
                
                # Update simulation state time after stay
                self.simulation_state.update_time(self.env.now)
                
                # Discharge patient from bed
                updated_patient = bed.discharge_patient(patient, self.env.now, self.logger)
                self.simulation_state.release_bed(bed.id)
                self.simulation_state.register_patient_completion(updated_patient)
                self.event_handler.on_treatment_complete(updated_patient, bed, self.env.now)
    
    def run_simulation(self, duration: int = 480):
        """Run the complete simulation"""
        # Update simulation state with duration
        self.simulation_state.simulation_duration = duration
        
        # Log simulation run start
        self.logger.log_event(
            timestamp=0.0,
            event_type=EventType.SIMULATION_START,
            message=f"Starting simulation run - Duration: {duration} minutes",
            simulation_state=self.simulation_state,
            data={
                "duration": duration,
                "num_doctors": self.hospital.num_doctors,
                "num_mri_machines": self.hospital.num_mri_machines,
                "num_blood_nurses": self.hospital.num_blood_nurses,
                "num_beds": self.hospital.num_beds,
                "triage_nurses": self.hospital.triage_nurses
            },
            source="simulation_engine"
        )
        
        # Start processes
        self.env.process(self.patient_arrival_process())
        
        # Start doctor processes
        for i in range(self.hospital.num_doctors):
            self.env.process(self.doctor_process(i))
        
        # Start MRI machine processes
        for i in range(self.hospital.num_mri_machines):
            self.env.process(self.mri_process(i))
        
        # Start blood nurse processes
        for i in range(self.hospital.num_blood_nurses):
            self.env.process(self.blood_nurse_process(i))
        
        # Start bed processes
        for i in range(self.hospital.num_beds):
            self.env.process(self.bed_process(i))
        
        # Run simulation
        self.env.run(until=duration)
        
        # Final simulation state update
        self.simulation_state.update_time(self.env.now)
        
        # Print final statistics
        self.print_statistics()
    
    def print_statistics(self):
        """Log simulation results using simulation state"""
        # Get comprehensive status from simulation state
        status = self.simulation_state.get_system_status()
        
        # Log final simulation results
        self.logger.log_event(
            timestamp=self.env.now,
            event_type=EventType.SIMULATION_END,
            message="Final simulation results",
            simulation_state=self.simulation_state,
            data={
                "simulation_time": f"{status['current_time']:.1f} / {self.simulation_state.simulation_duration} minutes",
                "patients_arrived": status['total_arrivals'],
                "patients_completed": status['total_completed'],
                "patients_in_system": status['patients_in_system'],
                "average_wait_time": status['average_wait_time'],
                "average_treatment_time": status['average_treatment_time'],
                "queue_lengths": {priority.name: length for priority, length in status['queue_lengths'].items()},
                "triage_utilization": status['triage_utilization'],
                "doctor_utilization": status['doctor_utilization'],
                "busy_doctors": status['busy_doctors'],
                "available_doctors": status['available_doctors'],
                "preemptions_count": status['preemptions_count']
            },
            source="simulation_engine"
        )

