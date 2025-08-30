import simpy
import random
from src.config.parameters import p
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

logger = logging.getLogger(__name__)

class EmergencyDepartment:
    """Emergency Department simulation model
    
    Manages the flow of patients through triage, consultation, and discharge/admission
    processes using SimPy resources for nurses, doctors, and cubicles.
    """
    def __init__(self, env, triage_system):
        self.env = env
        self.triage_system = triage_system
        self.nurses = simpy.Resource(env, p.number_nurses)
        self.doctors = simpy.PriorityResource(env, p.number_docs)
        self.cubicles = simpy.Resource(env, p.ae_cubicles)
        self.patients = []
        self.metrics = EDMetrics()

    def triage(self, patient):
        """Simulate the triage process for a patient"""
        try:
            # Simulate triage process
            yield from self.simulate_triage_assessment()
            patient.triage_time = self.env.now
            # Assign priority using the configured triage system
            patient.priority = self.triage_system.assign_priority(patient)
            patient.calculate_wait_times()
        except Exception as e:
            logger.error(LogMessages.TRIAGE_ERROR.format(patient.id, str(e)))
            patient.priority = 3  # Default to Urgent (Yellow)
            patient.calculate_wait_times()
        
    def simulate_triage_assessment(self):
        """Simulate the time taken for a nurse to assess a patient during triage
        
        This represents the initial assessment where a nurse checks vital signs,
        asks about symptoms, and determines the patient's priority level.
        """
        triage_duration = self.triage_system.estimate_triage_time()
        yield self.env.timeout(triage_duration)

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

    def _manage_resource_chain(self, resources, process, *args):
        """Unified method for sequential resource acquisition and processing"""
        requests = []
        try:
            # Request all resources
            for resource in resources:
                if hasattr(resource, 'request'):
                    req = resource.request()
                else:
                    req = resource  # Already a request object
                requests.append(req)
                yield req
            
            # Execute the process with all resources acquired
            yield from process(*args)
            
        finally:
            # Release all acquired resources
            for req in requests:
                if hasattr(req, 'release'):
                    req.release()

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