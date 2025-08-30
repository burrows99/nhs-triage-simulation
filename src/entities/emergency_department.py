import simpy
import random
import os
from typing import List, Dict, Any
from src.entities.patient import Patient
from src.utils.time_utils import (
    estimate_triage_time,
    estimate_consult_time,
    estimate_admission_wait_time,
    generate_patient_priority
)
from src.visualization.metrics import EDMetrics
import logging
from src.config.constants import LogMessages
from src.config.config_manager import (
    get_resource_config, 
    get_simulation_config, 
    get_patient_generation_config,
    get_output_paths,
    create_output_directories
)

logger = logging.getLogger(__name__)

class EmergencyDepartment:
    """Emergency Department simulation model
    
    Manages the flow of patients through triage, consultation, and discharge/admission
    processes using SimPy resources for nurses, doctors, and cubicles.
    """
    def __init__(self, env, triage_system):
        self.env = env
        self.triage_system = triage_system
        
        # Initialize resources using centralized configuration
        resource_config = get_resource_config()
        self.nurses = simpy.Resource(env, resource_config['nurses'])
        self.doctors = simpy.PriorityResource(env, resource_config['doctors'])
        self.cubicles = simpy.Resource(env, resource_config['cubicles'])
        self.patients = []
        self.metrics = EDMetrics()

    def triage(self, patient):
        """Simulate the triage process for a patient"""
        try:
            logger.debug(f"Starting triage assessment for Patient {patient.id}")
            logger.debug(f"Patient {patient.id} data: {patient.__dict__}")
            
            # Simulate triage process
            yield from self.simulate_triage_assessment()
            patient.triage_time = self.env.now
            
            # Log triage system input
            logger.debug(f"Calling triage system {self.triage_system.get_triage_system_name()} for Patient {patient.id}")
            
            # Assign priority using the configured triage system
            patient.priority = self.triage_system.assign_priority(patient)
            
            logger.info(f"Patient {patient.id} assigned priority {patient.priority} by {self.triage_system.get_triage_system_name()}")
            patient.calculate_wait_times()
            
        except Exception as e:
            logger.error(f"Triage error for Patient {patient.id}: {str(e)}")
            logger.error(f"Patient data causing error: {patient.__dict__}")
            logger.exception("Full traceback:")
            # Use configured default priority
            patient_config = get_patient_generation_config()
            patient.priority = patient_config['default_priority']
            patient.calculate_wait_times()
        
    def simulate_triage_assessment(self):
        """Simulate the time taken for a nurse to assess a patient during triage
        
        This represents the initial assessment where a nurse checks vital signs,
        asks about symptoms, and determines the patient's priority level.
        """
        logger.debug(f"About to call estimate_triage_time() on {self.triage_system.get_triage_system_name()}")
        triage_duration = self.triage_system.estimate_triage_time()
        logger.debug(f"Triage duration estimated: {triage_duration} minutes")
        yield self.env.timeout(triage_duration)
        logger.debug(f"Triage assessment timeout completed")

    def consult(self, patient):
        """Simulate the doctor consultation process"""
        # Simulate consultation process
        yield from self.simulate_doctor_consultation(patient)
        patient.consult_time = self.env.now
        patient.calculate_wait_times()
        
        # Determine if patient needs admission
        if random.random() < 0.2:  # 20% chance to admit
            patient.admitted = True
            yield from self.simulate_admission_process()
            
        # Complete patient journey - set discharge time and add to metrics
        patient.discharge_time = self.env.now
        patient.calculate_wait_times()
        self.metrics.add_patient_data(patient)
        logger.info(LogMessages.DISCHARGE.format(patient.id, patient.wait_for_consult, patient.admitted))
            
    def simulate_doctor_consultation(self, patient):
        """Simulate the time taken for a doctor to examine and treat a patient
        
        The consultation duration varies based on the patient's priority level,
        with higher priority patients typically requiring more intensive care.
        """
        consultation_duration = self.triage_system.estimate_consult_time(patient.priority)
        yield self.env.timeout(consultation_duration)
        
    def simulate_admission_process(self):
        """Simulate the time taken to arrange hospital admission for a patient
        
        This represents the waiting period for a hospital bed to become available
        and the administrative processes required for admission.
        """
        admission_duration = estimate_admission_wait_time()
        yield self.env.timeout(admission_duration)

    def patient_generator(self, deep_context: bool = False):
        """Generate patients from CSV data arriving at the emergency department
        
        Loads actual patient data using Patient.get_all() and simulates their arrival
        following a Poisson process for realistic ED simulation.
        
        Args:
            deep_context: If True, preload comprehensive medical context for each patient
        """
        # Load all patients using Patient.get_all() method
        csv_patients = Patient.get_all(deep=deep_context)
        
        if not csv_patients:
            logger.warning("No patients found in CSV file, simulation will have no patients")
            return
        
        logger.info(f"Loaded {len(csv_patients)} patients from CSV for simulation (deep_context={deep_context})")
        
        # Process each patient with realistic inter-arrival times
        for patient in csv_patients:
            # Generate realistic inter-arrival time
            from src.utils.time_utils import generate_interarrival_time
            yield self.env.timeout(generate_interarrival_time())
            
            # Update patient arrival time to current simulation time
            patient.arrival_time = self.env.now
            self.patients.append(patient)
            self.env.process(self.patient_process(patient))
            
            context_info = " (with deep context)" if deep_context else ""
            logger.debug(f"Patient {patient.id} (Age: {patient.age}, Gender: {patient.gender}) arrived at time {self.env.now}{context_info}")
    


    def patient_process(self, patient):
        """Orchestrate patient flow through triage and consultation"""
        yield self.env.process(self._triage_process(patient))
        yield self.env.process(self._consultation_process(patient))

    def _triage_process(self, patient):
        """Handle triage phase resource acquisition and timing"""
        try:
            yield from self._manage_resource_chain(
                [self.nurses, self.cubicles],
                self._execute_triage,
                patient
            )
        except Exception as e:
            yield from self._handle_triage_error(patient, e)

    def _manage_resource_chain(self, resources, process_func, patient):
        """Manage acquisition and release of multiple resources for a process"""
        acquired_resources = []
        resource_names = []
        
        try:
            logger.debug(f"Patient {patient.id} requesting resources: {[type(r).__name__ for r in resources]}")
            
            # Request all resources
            for i, resource in enumerate(resources):
                if hasattr(resource, 'request'):  # It's a resource object
                    resource_name = f"{type(resource).__name__}({resource.capacity})"
                    resource_names.append(resource_name)
                    logger.debug(f"Patient {patient.id} requesting {resource_name}")
                    
                    req = resource.request()
                    acquired_resources.append(req)
                    yield req
                    
                    logger.debug(f"Patient {patient.id} acquired {resource_name}")
                else:  # It's already a request object
                    resource_name = f"PreRequest({type(resource).__name__})"
                    resource_names.append(resource_name)
                    logger.debug(f"Patient {patient.id} using pre-created request {resource_name}")
                    
                    acquired_resources.append(resource)
                    yield resource
                    
                    logger.debug(f"Patient {patient.id} acquired {resource_name}")
            
            logger.info(f"Patient {patient.id} acquired all resources: {resource_names}")
            
            # Execute the process with acquired resources
            yield self.env.process(process_func(patient))
            
        except GeneratorExit:
            # Handle simulation termination gracefully
            logger.debug(f"Patient {patient.id} process terminated by simulation end")
        except Exception as e:
            logger.error(f"Error in resource chain for Patient {patient.id}: {str(e)}")
            logger.exception("Full traceback:")
        finally:
            # Release all acquired resources
            try:
                logger.debug(f"Patient {patient.id} releasing {len(acquired_resources)} resources")
                for i, req in enumerate(acquired_resources):
                    try:
                        if hasattr(req, 'resource'):
                            req.resource.release(req)
                            logger.debug(f"Patient {patient.id} released {resource_names[i] if i < len(resource_names) else 'resource'}")
                    except Exception as e:
                        logger.error(f"Error releasing resource for Patient {patient.id}: {str(e)}")
                
                logger.info(f"Patient {patient.id} released all resources: {resource_names}")
            except Exception as e:
                logger.error(f"Error in resource cleanup for Patient {patient.id}: {str(e)}")

    def _execute_triage(self, patient):
        """Perform actual triage procedure"""
        start_triage = self.env.now
        logger.info(LogMessages.PATIENT_ARRIVAL.format(patient.id, start_triage))
        logger.debug(f"Starting triage for Patient {patient.id} | Queue time: {start_triage - patient.arrival_time:.1f} min")
        yield self.env.process(self.triage(patient))
        logger.info(LogMessages.TRIAGE_COMPLETE.format(patient.id, patient.priority, self.env.now - start_triage))

    def _consultation_process(self, patient):
        """Manage consultation phase resources"""
        # Create a priority request for doctors
        doctor_req = self.doctors.request(priority=patient.priority)
        yield from self._manage_resource_chain(
            [doctor_req, self.cubicles],
            self.consult,
            patient
        )

    def _handle_triage_error(self, patient, error):
        """Log and process triage phase errors"""
        logger.error(f"Critical error in patient process {patient.id}: {str(error)}")
        patient.discharge_time = self.env.now
        patient.calculate_wait_times()
        self.metrics.add_patient_data(patient)
        
        # Record discharge time and add to metrics
        patient.discharge_time = self.env.now
        patient.calculate_wait_times()
        self.metrics.add_patient_data(patient)
        logger.info(LogMessages.DISCHARGE.format(patient.id, patient.wait_for_consult, patient.admitted))
    
    def export_patient_data_to_csv(self, triage_system_name: str = None) -> str:
        """Export all patient data to CSV file"""
        if not triage_system_name:
            triage_system_name = self.triage_system.get_triage_system_name()
        
        # Get output paths and create directories
        paths = get_output_paths(triage_system_name)
        create_output_directories(triage_system_name)
        
        # Create CSV file path
        csv_filepath = os.path.join(paths['csv'], 'patient_data.csv')
        
        # Export patients to CSV
        Patient.export_patients_to_csv(self.patients, csv_filepath)
        
        logger.info(f"Exported {len(self.patients)} patients to CSV: {csv_filepath}")
        return csv_filepath
    
    def get_patient_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of all patients processed"""
        if not self.patients:
            return {'total_patients': 0, 'summary': 'No patients processed'}
        
        # Calculate summary statistics
        total_patients = len(self.patients)
        admitted_count = sum(1 for p in self.patients if p.admitted)
        
        # Age statistics
        ages = [p.age for p in self.patients]
        avg_age = sum(ages) / len(ages) if ages else 0
        
        # Priority distribution
        priority_dist = {}
        for p in self.patients:
            priority_dist[p.priority] = priority_dist.get(p.priority, 0) + 1
        
        # Gender distribution
        gender_dist = {}
        for p in self.patients:
            gender_dist[p.gender] = gender_dist.get(p.gender, 0) + 1
        
        # Chief complaint distribution
        complaint_dist = {}
        for p in self.patients:
            complaint_dist[p.chief_complaint] = complaint_dist.get(p.chief_complaint, 0) + 1
        
        # Timing statistics
        wait_times = [p.wait_for_triage for p in self.patients if p.wait_for_triage > 0]
        consult_waits = [p.wait_for_consult for p in self.patients if p.wait_for_consult > 0]
        total_times = [p.total_time for p in self.patients if p.total_time > 0]
        
        return {
            'total_patients': total_patients,
            'admitted_count': admitted_count,
            'admission_rate': admitted_count / total_patients if total_patients > 0 else 0,
            'average_age': round(avg_age, 1),
            'age_range': {'min': min(ages) if ages else 0, 'max': max(ages) if ages else 0},
            'priority_distribution': priority_dist,
            'gender_distribution': gender_dist,
            'top_complaints': dict(sorted(complaint_dist.items(), key=lambda x: x[1], reverse=True)[:5]),
            'timing_stats': {
                'avg_wait_for_triage': round(sum(wait_times) / len(wait_times), 2) if wait_times else 0,
                'avg_wait_for_consult': round(sum(consult_waits) / len(consult_waits), 2) if consult_waits else 0,
                'avg_total_time': round(sum(total_times) / len(total_times), 2) if total_times else 0
            },
            'triage_system': self.triage_system.get_triage_system_name()
        }
    
    def print_patient_summary(self) -> None:
        """Print a comprehensive summary of patient data"""
        summary = self.get_patient_summary()
        
        print(f"\n{'='*60}")
        print(f"PATIENT DATA SUMMARY - {summary['triage_system']}")
        print(f"{'='*60}")
        print(f"Total Patients Processed: {summary['total_patients']}")
        print(f"Patients Admitted: {summary['admitted_count']} ({summary['admission_rate']:.1%})")
        print(f"Average Age: {summary['average_age']} years (Range: {summary['age_range']['min']}-{summary['age_range']['max']})")
        
        print(f"\nPriority Distribution:")
        for priority, count in sorted(summary['priority_distribution'].items()):
            print(f"  Priority {priority}: {count} patients")
        
        print(f"\nGender Distribution:")
        for gender, count in summary['gender_distribution'].items():
            print(f"  {gender}: {count} patients")
        
        print(f"\nTop Chief Complaints:")
        for complaint, count in list(summary['top_complaints'].items())[:5]:
            print(f"  {complaint}: {count} patients")
        
        timing = summary['timing_stats']
        print(f"\nTiming Statistics:")
        print(f"  Average Wait for Triage: {timing['avg_wait_for_triage']:.1f} minutes")
        print(f"  Average Wait for Consultation: {timing['avg_wait_for_consult']:.1f} minutes")
        print(f"  Average Total Time in ED: {timing['avg_total_time']:.1f} minutes")
        print(f"{'='*60}")