#!/usr/bin/env python3
"""
Hospital Simulation with Preemptive Resource Management

A comprehensive SimPy-based hospital simulation implementing:
- Manchester Triage System (MTS) for patient prioritization
- Preemptive resource allocation for doctors and MRI machines
- Non-preemptive bed management
- AI-driven preemption decision making
- Comprehensive metrics collection and analysis

Author: Hospital Operations Research Team
Reference: NHS Emergency Care Standards and SimPy Documentation
"""

import simpy
import argparse
import logging
from typing import Generator, Optional
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from entities.hospital import Hospital
from entities.patient import Patient
from services.time_service import TimeService
from services.preemption_agent import PreemptionAgent
from services.metrics_service import MetricsService
from enums.patient_status import PatientStatus
from enums.priority import TriagePriority
from enums.resource_type import ResourceType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hospital_simulation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class HospitalSimulation:
    """
    Main hospital simulation orchestrator.
    
    Coordinates patient arrivals, resource allocation, and system operations
    using SimPy discrete event simulation framework.
    """
    
    def __init__(
        self,
        hospital_name: str = "General Hospital",
        num_doctors: int = 3,
        num_mri_machines: int = 2,
        num_beds: int = 10,
        num_triage_nurses: int = 2,
        simulation_duration: float = 480.0,  # 8 hours in minutes
        random_seed: Optional[int] = None
    ) -> None:
        """Initialize hospital simulation."""
        self.simulation_duration = simulation_duration
        self.random_seed = random_seed
        
        # Initialize SimPy environment
        self.env = simpy.Environment()
        
        # Initialize services
        self.time_service = TimeService(random_seed=random_seed)
        self.preemption_agent = PreemptionAgent()
        self.metrics_service = MetricsService()
        
        # Initialize hospital
        self.hospital = Hospital(
            name=hospital_name,
            num_doctors=num_doctors,
            num_mri_machines=num_mri_machines,
            num_beds=num_beds,
            num_triage_nurses=num_triage_nurses,
            env=self.env,
            time_service=self.time_service,
            preemption_agent=self.preemption_agent
        )
        
        # Simulation state
        self.total_patients_generated = 0
        self.patients_in_progress: dict[str, Patient] = {}
        
        logger.info(f"Initialized simulation: {hospital_name}")
        logger.info(f"Resources: {num_doctors} doctors, {num_mri_machines} MRI, {num_beds} beds, {num_triage_nurses} nurses")
        logger.info(f"Duration: {simulation_duration} minutes, Seed: {random_seed}")
    
    def patient_generator(self) -> Generator[simpy.Event, None, None]:
        """
        Generate patient arrivals using log-normal distribution.
        
        Yields:
            SimPy timeout events for patient arrivals
        """
        while True:
            # Generate inter-arrival time
            inter_arrival_time = self.time_service.generate_arrival_time()
            
            # Wait for next arrival
            yield self.env.timeout(inter_arrival_time)
            
            # Create new patient
            patient = Patient(
                arrival_time=self.env.now,
                # Initial priority will be assigned by triage
                priority=TriagePriority.STANDARD,
                # Initial resource will be assigned by triage
                required_resource=ResourceType.DOCTOR
            )
            
            self.total_patients_generated += 1
            self.patients_in_progress[patient.patient_id] = patient
            
            logger.info(f"Patient {patient.patient_id[:8]} arrived at time {self.env.now:.1f}")
            
            # Admit patient to hospital
            self.hospital.admit_patient(patient, self.env.now)
            
            # Start patient care process
            self.env.process(self.patient_care_process(patient))
    
    def patient_care_process(self, patient: Patient) -> Generator[simpy.Event, None, None]:
        """
        Process individual patient through hospital system.
        
        Args:
            patient: Patient to process
            
        Yields:
            SimPy events for patient care stages
        """
        try:
            # Stage 1: Triage Assessment
            yield from self.triage_process(patient)
            
            # Stage 2: Main Service (Doctor, MRI, or Bed)
            yield from self.main_service_process(patient)
            
            # Stage 3: Discharge
            self.discharge_patient(patient)
            
        except Exception as e:
            logger.error(f"Error processing patient {patient.patient_id[:8]}: {e}")
            # Ensure patient is removed from system even if error occurs
            if patient.patient_id in self.patients_in_progress:
                del self.patients_in_progress[patient.patient_id]
    
    def triage_process(self, patient: Patient) -> Generator[simpy.Event, None, None]:
        """
        Handle triage assessment process.
        
        Args:
            patient: Patient to triage
            
        Yields:
            SimPy events for triage process
        """
        # Find available triage nurse
        triage_nurse = None
        for nurse in self.hospital.triage_nurses.values():
            if nurse.is_available:
                triage_nurse = nurse
                break
        
        if not triage_nurse:
            # Wait for triage nurse to become available
            available_nurse = next(iter(self.hospital.triage_nurses.values()))
            with available_nurse.simpy_resource.request() as request:  # type: ignore
                yield request
                triage_nurse = next(nurse for nurse in self.hospital.triage_nurses.values() if nurse.is_available)
        
        # Start triage assessment
        triage_nurse.start_assessment(patient, self.env.now)
        
        # Generate triage time
        triage_time = self.time_service.generate_triage_time()
        
        # Wait for triage completion
        yield self.env.timeout(triage_time)
        
        # Complete triage assessment
        assessed_patient = triage_nurse.complete_assessment(self.env.now)
        
        if assessed_patient:
            # Generate estimated service time based on assigned priority and resource
            priority_multiplier = self.time_service.calculate_priority_multiplier(assessed_patient.priority.value)
            
            if assessed_patient.required_resource == ResourceType.DOCTOR:
                service_time = self.time_service.generate_doctor_time(priority_multiplier)
            elif assessed_patient.required_resource == ResourceType.MRI_MACHINE:
                service_time = self.time_service.generate_mri_time()
            elif assessed_patient.required_resource == ResourceType.BED:
                service_time = self.time_service.generate_bed_time(priority_multiplier)
            else:
                service_time = 30.0  # Default service time
            
            assessed_patient.set_estimated_service_time(service_time)
            
            logger.info(f"Patient {patient.patient_id[:8]} triaged: {assessed_patient.priority.name} priority, requires {assessed_patient.required_resource.name}")
    
    def main_service_process(self, patient: Patient) -> Generator[simpy.Event, None, None]:
        """
        Handle main service process (Doctor, MRI, or Bed).
        
        Args:
            patient: Patient requiring service
            
        Yields:
            SimPy events for service process
        """
        resource_type = patient.required_resource
        
        if resource_type == ResourceType.DOCTOR:
            yield from self.doctor_service_process(patient)
        elif resource_type == ResourceType.MRI_MACHINE:
            yield from self.mri_service_process(patient)
        elif resource_type == ResourceType.BED:
            yield from self.bed_service_process(patient)
        else:
            logger.warning(f"Unknown resource type for patient {patient.patient_id[:8]}: {resource_type}")
    
    def doctor_service_process(self, patient: Patient) -> Generator[simpy.Event, None, None]:
        """
        Handle doctor consultation process.
        
        Args:
            patient: Patient requiring doctor consultation
            
        Yields:
            SimPy events for doctor service
        """
        # Find available doctor or wait in queue
        doctor = None
        
        # Check for immediate availability
        for doc in self.hospital.doctors.values():
            if doc.is_available:
                doctor = doc
                break
        
        if not doctor:
            # Check if preemption is possible
            operations_state = self.hospital._create_hospital_operations_state(self.env.now)  # type: ignore
            preemption_response = self.preemption_agent.make_preemption_decision(patient, operations_state)
            
            if preemption_response.decision.value == "preempt_resource" and preemption_response.resource_id_to_preempt:
                # Execute preemption
                preempted_patient = self.hospital._execute_resource_preemption(  # type: ignore
                    preemption_response.resource_id_to_preempt, patient, self.env.now
                )
                
                if preempted_patient:
                    logger.info(f"Patient {patient.patient_id[:8]} preempted patient {preempted_patient.patient_id[:8]}")
                    doctor = self.hospital.doctors[preemption_response.resource_id_to_preempt]
                    
                    # Restart preempted patient process
                    self.env.process(self.main_service_process(preempted_patient))
        
        if not doctor:
            # Wait in queue for available doctor
            available_doctor = next(iter(self.hospital.doctors.values()))
            with available_doctor.simpy_resource.request(priority=patient.priority.value) as request:  # type: ignore
                yield request
                doctor = available_doctor
        
        # Start doctor consultation
        doctor.start_service(patient, self.env.now)
        patient.update_status(PatientStatus.IN_SERVICE, self.env.now)
        
        # Wait for consultation completion
        yield self.env.timeout(patient.estimated_service_time)
        
        # Complete consultation
        completed_patient = doctor.complete_service(self.env.now)
        if completed_patient:
            completed_patient.update_status(PatientStatus.COMPLETED, self.env.now)
            completed_patient.actual_service_time = patient.estimated_service_time
            
            logger.info(f"Patient {patient.patient_id[:8]} completed doctor consultation")
    
    def mri_service_process(self, patient: Patient) -> Generator[simpy.Event, None, None]:
        """
        Handle MRI scan process.
        
        Args:
            patient: Patient requiring MRI scan
            
        Yields:
            SimPy events for MRI service
        """
        # Similar logic to doctor service but for MRI machines
        mri_machine = None
        
        # Check for immediate availability
        for mri in self.hospital.mri_machines.values():
            if mri.is_available and mri.is_operational:
                mri_machine = mri
                break
        
        if not mri_machine:
            # Check for preemption possibility
            operations_state = self.hospital._create_hospital_operations_state(self.env.now)  # type: ignore
            preemption_response = self.preemption_agent.make_preemption_decision(patient, operations_state)
            
            if preemption_response.decision.value == "preempt_resource" and preemption_response.resource_id_to_preempt:
                preempted_patient = self.hospital._execute_resource_preemption(  # type: ignore
                    preemption_response.resource_id_to_preempt, patient, self.env.now
                )
                
                if preempted_patient:
                    logger.info(f"Patient {patient.patient_id[:8]} preempted MRI patient {preempted_patient.patient_id[:8]}")
                    mri_machine = self.hospital.mri_machines[preemption_response.resource_id_to_preempt]
                    
                    # Restart preempted patient process
                    self.env.process(self.main_service_process(preempted_patient))
        
        if not mri_machine:
            # Wait in queue
            available_mri = next(iter(self.hospital.mri_machines.values()))
            with available_mri.simpy_resource.request(priority=patient.priority.value) as request:  # type: ignore
                yield request
                mri_machine = available_mri
        
        # Start MRI scan
        mri_machine.start_scan(patient, self.env.now)
        patient.update_status(PatientStatus.IN_SERVICE, self.env.now)
        
        # Wait for scan completion
        yield self.env.timeout(patient.estimated_service_time)
        
        # Complete scan
        completed_patient = mri_machine.complete_scan(self.env.now)
        if completed_patient:
            completed_patient.update_status(PatientStatus.COMPLETED, self.env.now)
            completed_patient.actual_service_time = patient.estimated_service_time
            
            logger.info(f"Patient {patient.patient_id[:8]} completed MRI scan")
    
    def bed_service_process(self, patient: Patient) -> Generator[simpy.Event, None, None]:
        """
        Handle bed admission process (non-preemptive).
        
        Args:
            patient: Patient requiring bed admission
            
        Yields:
            SimPy events for bed service
        """
        # Find available bed
        bed = None
        for b in self.hospital.beds.values():
            if b.can_admit_patient(patient):
                bed = b
                break
        
        if not bed:
            # Wait for bed availability (non-preemptive)
            available_bed = next(iter(self.hospital.beds.values()))
            with available_bed.simpy_resource.request() as request:  # type: ignore
                yield request
                bed = available_bed
        
        # Admit patient to bed
        bed.admit_patient(patient, self.env.now)
        patient.update_status(PatientStatus.IN_SERVICE, self.env.now)
        
        # Wait for stay completion
        yield self.env.timeout(patient.estimated_service_time)
        
        # Discharge from bed
        discharged_patient = bed.discharge_patient(self.env.now)
        if discharged_patient:
            discharged_patient.update_status(PatientStatus.COMPLETED, self.env.now)
            discharged_patient.actual_service_time = patient.estimated_service_time
            
            logger.info(f"Patient {patient.patient_id[:8]} discharged from bed")
            
            # Simulate bed cleaning
            bed.start_cleaning(self.env.now)
            yield self.env.timeout(15.0)  # 15 minutes cleaning time
            bed.complete_cleaning(self.env.now, 15.0)
    
    def discharge_patient(self, patient: Patient) -> None:
        """
        Discharge patient from hospital system.
        
        Args:
            patient: Patient to discharge
        """
        self.hospital.discharge_patient(patient, self.env.now)
        
        # Remove from tracking
        if patient.patient_id in self.patients_in_progress:
            del self.patients_in_progress[patient.patient_id]
        
        logger.info(f"Patient {patient.patient_id[:8]} discharged at time {self.env.now:.1f}")
    
    def metrics_collection_process(self) -> Generator[simpy.Event, None, None]:
        """
        Periodic metrics collection process.
        
        Yields:
            SimPy timeout events for metrics collection
        """
        while True:
            # Collect metrics every 30 minutes
            yield self.env.timeout(30.0)
            
            # Collect hospital metrics
            self.metrics_service.collect_hospital_metrics(self.hospital, self.env.now)
            
            # Collect patient metrics from discharged patients
            self.metrics_service.collect_patient_metrics(self.hospital.discharged_patients)
            
            logger.debug(f"Metrics collected at time {self.env.now:.1f}")
    
    def run_simulation(self) -> None:
        """
        Run the complete hospital simulation.
        """
        logger.info("Starting hospital simulation...")
        
        # Start patient generator
        self.env.process(self.patient_generator())
        
        # Start metrics collection
        self.env.process(self.metrics_collection_process())
        
        # Run simulation
        self.env.run(until=self.simulation_duration)
        
        logger.info(f"Simulation completed after {self.simulation_duration} minutes")
        logger.info(f"Total patients generated: {self.total_patients_generated}")
        logger.info(f"Patients discharged: {len(self.hospital.discharged_patients)}")
        logger.info(f"Patients still in system: {len(self.patients_in_progress)}")
    
    def generate_reports(self) -> None:
        """
        Generate comprehensive simulation reports.
        """
        logger.info("Generating simulation reports...")
        
        # Final metrics collection
        self.metrics_service.collect_hospital_metrics(self.hospital, self.env.now)
        self.metrics_service.collect_patient_metrics(self.hospital.discharged_patients)
        
        # Generate plots
        try:
            self.metrics_service.plot_wait_time_distribution()
            self.metrics_service.plot_resource_utilization()
            self.metrics_service.plot_system_performance()
        except Exception as e:
            logger.warning(f"Error generating plots: {e}")
        
        # Generate summary report
        summary_report = self.metrics_service.generate_summary_report()
        
        # Print key metrics
        print("\n" + "="*60)
        print("HOSPITAL SIMULATION SUMMARY REPORT")
        print("="*60)
        
        hospital_summary = self.hospital.get_performance_summary()
        print(f"\nHospital: {hospital_summary['hospital_name']}")
        print(f"Simulation Duration: {self.simulation_duration} minutes")
        print(f"Total Patients Processed: {hospital_summary['total_patients_processed']}")
        print(f"Patients Discharged: {hospital_summary['total_patients_discharged']}")
        print(f"Patients in System: {hospital_summary['patients_currently_in_system']}")
        print(f"Preemptions Executed: {hospital_summary['total_preemptions_executed']}")
        print(f"Peak System Load: {hospital_summary['peak_system_load']:.1%}")
        
        print("\nResource Utilization:")
        for resource, utilization in hospital_summary['resource_utilization'].items():
            print(f"  {resource}: {utilization:.1%}")
        
        print("\nQueue Lengths (at end):")
        for resource, length in hospital_summary['queue_lengths'].items():
            print(f"  {resource}: {length} patients")
        
        # Wait time analysis
        if summary_report['wait_time_analysis'].get('overall', {}).get('sample_size', 0) > 0:
            overall_wait = summary_report['wait_time_analysis']['overall']
            print(f"\nWait Time Analysis:")
            print(f"  Mean Wait Time: {overall_wait['mean_minutes']:.1f} minutes")
            print(f"  Median Wait Time: {overall_wait['median_minutes']:.1f} minutes")
            print(f"  95th Percentile: {overall_wait['95th_percentile_minutes']:.1f} minutes")
        
        # Export data
        export_path = self.metrics_service.export_data()
        print(f"\nDetailed data exported to: {export_path}")
        
        print("\n" + "="*60)


def main() -> None:
    """
    Main entry point for hospital simulation.
    """
    parser = argparse.ArgumentParser(description="Hospital Simulation with Preemptive Resource Management")
    parser.add_argument("--name", default="General Hospital", help="Hospital name")
    parser.add_argument("--doctors", type=int, default=3, help="Number of doctors")
    parser.add_argument("--mri", type=int, default=2, help="Number of MRI machines")
    parser.add_argument("--beds", type=int, default=10, help="Number of beds")
    parser.add_argument("--nurses", type=int, default=2, help="Number of triage nurses")
    parser.add_argument("--duration", type=float, default=480.0, help="Simulation duration in minutes")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Create and run simulation
        simulation = HospitalSimulation(
            hospital_name=args.name,
            num_doctors=args.doctors,
            num_mri_machines=args.mri,
            num_beds=args.beds,
            num_triage_nurses=args.nurses,
            simulation_duration=args.duration,
            random_seed=args.seed
        )
        
        simulation.run_simulation()
        simulation.generate_reports()
        
    except KeyboardInterrupt:
        logger.info("Simulation interrupted by user")
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise


if __name__ == "__main__":
    main()