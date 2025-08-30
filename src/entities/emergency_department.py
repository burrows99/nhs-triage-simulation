import simpy
import random
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
from src.config.config_manager import get_resource_config, get_simulation_config, get_patient_generation_config

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

    def patient_generator(self):
        """Generate patients arriving at the emergency department following a Poisson process
        
        In queuing theory, a Poisson arrival process means:
        - The number of arrivals in any time interval follows a Poisson distribution
        - Inter-arrival times follow an exponential distribution
        - Arrivals occur independently of each other
        """
        patient_id = 1
        while True:
            # Generate patients with exponentially distributed inter-arrival times
            # This ensures arrivals follow a Poisson process as required by queuing theory
            from src.utils.time_utils import generate_interarrival_time
            yield self.env.timeout(generate_interarrival_time())
            
            # Create and process the new patient
            patient = Patient(patient_id, self.env.now)
            self.patients.append(patient)
            self.env.process(self.patient_process(patient))
            patient_id += 1

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