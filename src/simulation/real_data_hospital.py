import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import sys
import os
import logging

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Import centralized logger
from src.logger import logger

from src.services.data_service import DataService
from src.services.nhs_metrics import NHSMetrics
from src.services.operation_metrics import OperationMetrics
from src.services.plotting_service import PlottingService
from src.services.random_service import RandomService
from src.triage.manchester_triage_system import ManchesterTriageSystem
from .simulation_engine import SimulationEngine
# Patient models now come from Synthea data service
from src.triage.triage_constants import (
    TriageFlowcharts, FlowchartSymptomMapping, TriageCategories,
    SymptomKeys, MedicalConditions, CommonStrings, DiagnosticTestTypes, SymptomNames,
    ComplaintToFlowchartMapping
)


class SimpleHospital:
    """Simple hospital simulation with Poisson arrivals and real patient data."""
    
    def __init__(self, csv_folder='./output/csv', output_dir='./output/hospital_simulation', 
                 triage_system=None, **kwargs):
        """Initialize hospital simulation with all required services and data.
        
        Args:
            csv_folder: Path to CSV data files
            output_dir: Directory for simulation outputs (metrics, plots, etc.)
            triage_system: Triage system instance (required - no string support)
            **kwargs: Simulation parameters (sim_duration, arrival_rate, etc.)
        
        Raises:
            ValueError: If triage_system is None or not a valid triage system object
        """
        # Validate triage system is provided and is a ManchesterTriageSystem instance
        if not isinstance(triage_system, ManchesterTriageSystem):
            raise ValueError("triage_system parameter must be an instance of ManchesterTriageSystem. Please provide a ManchesterTriageSystem() object.")
        
        # Store triage system for later initialization
        self.triage_system_param = triage_system
        self.output_dir = output_dir
        self._ensure_output_directory()
        self._setup_simulation_parameters(**kwargs)
        self._load_patient_data(csv_folder)
        self._initialize_services(**kwargs)
        
        # Initialize simulation engine
        resources = {
            'nurses': self.nurses,
            'doctors': self.doctors,
            'beds': self.beds
        }
        # Specify which resources should use priority queues (for triage categories)
        priority_resources = ['doctors', 'beds']
        self.simulation_engine = SimulationEngine(
            duration=self.sim_duration,
            arrival_rate=self.arrival_rate,
            resources=resources,
            priority_resources=priority_resources
        )
        
        self.simulation_engine.log_with_sim_time(logging.INFO, "Hospital simulation initialized successfully")
        self.simulation_engine.log_with_sim_time(logging.INFO, f"Parameters: duration={self.sim_duration}min, arrival_rate={self.arrival_rate}/hr, nurses={self.nurses}, doctors={self.doctors}, beds={self.beds}")
        self.simulation_engine.log_with_sim_time(logging.INFO, f"Output directory: {self.output_dir}")
    
    def _ensure_output_directory(self):
        """Ensure output directory exists, create if necessary"""
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            os.makedirs(os.path.join(self.output_dir, 'metrics'), exist_ok=True)
            os.makedirs(os.path.join(self.output_dir, 'plots'), exist_ok=True)
            logger.info(f"📁 Output directory ready: {self.output_dir}")
        except Exception as e:
            logger.warning(f"⚠️  Warning: Could not create output directory {self.output_dir}: {str(e)}")
            logger.info(f"📁 Using default directory: ./output/hospital_simulation")
            self.output_dir = './output/hospital_simulation'
            os.makedirs(self.output_dir, exist_ok=True)
            os.makedirs(os.path.join(self.output_dir, 'metrics'), exist_ok=True)
            os.makedirs(os.path.join(self.output_dir, 'plots'), exist_ok=True)
    
    def _setup_simulation_parameters(self, **kwargs):
        """Setup simulation parameters with defaults."""
        self.sim_duration = kwargs.get('sim_duration', 1440)  # 24 hours
        self.arrival_rate = kwargs.get('arrival_rate', 10)    # patients/hour
        self.nurses = kwargs.get('nurses', 2)
        self.doctors = kwargs.get('doctors', 6)
        self.beds = kwargs.get('beds', 15)
        self.delay_scaling = kwargs.get('delay_scaling', 0.2)  # Default: 1 real second = 0.2 simulation minutes
    
    def _scale_delay(self, real_time_seconds: float, delay_type: str = 'triage') -> float:
        """General-purpose method to scale real-world delays to simulation time.
        
        Args:
            real_time_seconds: Real-world processing time in seconds
            delay_type: Type of delay for future extensibility (currently only 'triage' is used)
            
        Returns:
            Scaled delay in simulation minutes
        """
        if delay_type == 'triage':
            return real_time_seconds * self.delay_scaling
        else:
            # For future delay types, can add different scaling factors
            return real_time_seconds * self.delay_scaling
    
    def _load_patient_data(self, csv_folder: str):
        """Load and process patient data from CSV files."""
        logger.info(f"Loading patient data from {csv_folder}...")
        self.data_service = DataService(csv_folder)
        self.patients = self.data_service.get_all_patients(deep=True)
        self.current_index = 0
        logger.info(f"Loaded {len(self.patients)} patients with full relationships")
    
    def _initialize_services(self, **kwargs):
        """Initialize all required services for the simulation."""
        # Initialize NHS Metrics Service
        logger.info("Initializing NHS Metrics Service...")
        self.nhs_metrics = NHSMetrics(reattendance_window_hours=72)
        logger.info("NHS Metrics Service ready")
        
        # Initialize Operation Metrics Service
        logger.info("Initializing Operation Metrics Service...")
        self.operation_metrics = OperationMetrics()
        logger.info("Operation Metrics Service ready")
        
        # Initialize Plotting Service and register metric services
        logger.info("Initializing Plotting Service...")
        self.plotting_service = PlottingService()
        self.plotting_service.register_metric_service('nhs', self.nhs_metrics)
        self.plotting_service.register_metric_service('operations', self.operation_metrics)
        logger.info("Plotting Service ready with registered metrics")
        
        # Data cleanup is now handled by the enhanced DataService
        
        # Initialize Triage System (object only - validation already done in constructor)
        self.triage_system = self.triage_system_param
        logger.info(f"Using provided triage system: {type(self.triage_system).__name__}")
        
        # Triage system validation removed
        
        # Initialize Random Service for centralized random data generation
        logger.info("Initializing Random Service...")
        self.random_service = RandomService(seed=kwargs.get('random_seed'))
        logger.info("Random Service ready")
    
    def get_patient(self):
        """Get next patient - returns fully prepared Synthea Patient model."""
        if not self.patients:
            return None
        
        # Return Synthea patient model (already fully populated with relationships)
        synthea_patient = self.patients[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.patients)
        
        return synthea_patient
    
    def perform_triage(self, patient=None):
        """Perform triage using paper-based Manchester Triage System approach with real patient data.
        
        Returns:
            tuple: (category, priority, triage_result, processing_delay_seconds)
        
        Note: This method now measures and returns the actual processing time for 
        integration with SimPy's discrete event simulation.
        """
        # Paper-based approach: Nurse selects appropriate flowchart based on patient presentation
        # FMTS paper: "decision aid system for the ER nurses to properly categorize patients based on their symptoms"
        
        if patient is None:
            raise ValueError("Patient object is required for triage. Cannot perform triage without real patient information.")
        
        # Measure actual triage processing time
        import time
        triage_start_time = time.time()
        
        # Use real patient data for triage
        # Map chief complaint to appropriate flowchart
        flowchart_reason = ComplaintToFlowchartMapping.get_flowchart_for_complaint(patient.presenting_complaint)
        
        # Use real patient symptoms from the processed data
        raw_symptoms = patient.symptoms
        
        # Convert real patient symptoms to MTS format
        # Use symptoms directly from triage constants instead of custom mapping
        expected_symptoms = FlowchartSymptomMapping.get_symptoms_for_flowchart(flowchart_reason)
        symptoms_input = {k: v for k, v in raw_symptoms.items() if k in expected_symptoms}
        
        # Ensure we have real patient symptoms - no random fallback
        if not symptoms_input:
            raise ValueError(f"No real patient symptoms available for flowchart '{flowchart_reason}'. Patient ID: {patient.patient_id}")
        
        # Use triage system with patient-based inputs
        result = self.triage_system.triage_patient(
            flowchart_reason=flowchart_reason,
            symptoms_input=symptoms_input,
            patient_id=patient.patient_id
        )
        
        # Calculate processing delay
        triage_end_time = time.time()
        processing_delay = triage_end_time - triage_start_time
        
        # Extract category from MTS result - no fallback, must be present
        # Check for both possible field names for compatibility
        if 'category' in result:
            category = result['category']
        elif 'triage_category' in result:
            category = result['triage_category']
        else:
            raise ValueError(f"MTS result missing required 'category' or 'triage_category' field: {result}")
        
        # Ensure category is properly formatted
        if hasattr(category, 'item'):  # Handle numpy types
            category = category.item()
        category = str(category).strip()
        
        # Convert category to priority using centralized mapping - no fallback
        priority_map = TriageCategories.get_priority_mapping()
        if category not in priority_map:
            raise ValueError(f"Unknown triage category '{category}'. Valid categories: {list(priority_map.keys())}")
        
        priority = priority_map[category]
        
        # Occasionally simulate emergency cases (RED priority) since real data lacks them
        # This represents walk-in emergencies or deteriorating patients
        if self.random_service.should_escalate_to_emergency():
            category = 'RED'
            priority = 1
            result['category'] = 'RED'
            result['emergency_escalation'] = True
            logger.info(f"🚨 Patient {patient.patient_id}: Emergency escalation - upgraded to RED priority")
        
        # Return full MTS result for timing information
        return category, priority, result, processing_delay
    
    def patient_flow(self, patient_num):
        """Simulate patient journey with NHS metrics tracking."""
        arrival_time = self.simulation_engine.env.now
        
        self.simulation_engine.log_with_sim_time(logging.INFO, f"🚶 Patient #{patient_num} ARRIVED at {self.simulation_engine.format_sim_time(arrival_time)}")
        
        # Setup patient and record arrival
        patient = self._setup_patient_arrival(arrival_time)
        
        self.simulation_engine.log_with_sim_time(logging.INFO, f"👤 Patient #{patient_num}: Age {patient.age}, {patient.gender}, Complaint: '{patient.presenting_complaint}'")
        
        # Triage nurse assessment stage - this is where triage category/priority is determined
        self.simulation_engine.log_with_sim_time(logging.INFO, f"👩‍⚕️ Patient #{patient_num}: Entering triage nurse assessment at {self.simulation_engine.format_sim_time(self.simulation_engine.env.now)}")
        category, priority, triage_result = yield from self._process_triage_stage(patient.patient_id, patient, patient_num)
        
        # Record triage result in patient object and NHS metrics
        patient.set_triage_result(category, priority, triage_result)
        self.nhs_metrics.record_triage_category(patient.patient_id, category)
        self.simulation_engine.log_with_sim_time(logging.INFO, f"🏷️  Patient #{patient_num}: Triaged as {category} (Priority: {priority}) at {self.simulation_engine.format_sim_time(self.simulation_engine.env.now)}")
        
        # Doctor assessment stage
        self.simulation_engine.log_with_sim_time(logging.INFO, f"👨‍⚕️ Patient #{patient_num}: Entering doctor assessment stage at {self.simulation_engine.format_sim_time(self.simulation_engine.env.now)}")
        yield from self._process_doctor_assessment(patient, category, priority, triage_result, patient_num)
        
        # Diagnostics stage (optional)
        diagnostics_start = self.simulation_engine.env.now
        self.simulation_engine.log_with_sim_time(logging.INFO, f"🔬 Patient #{patient_num}: Checking for diagnostics at {self.simulation_engine.format_sim_time(diagnostics_start)}")
        yield from self._process_diagnostics(category)
        
        if self.simulation_engine.env.now > diagnostics_start:
            self.simulation_engine.log_with_sim_time(logging.INFO, f"🧪 Patient #{patient_num}: Completed diagnostics at {self.simulation_engine.format_sim_time(self.simulation_engine.env.now)} (Duration: {self.simulation_engine.env.now - diagnostics_start:.1f}min)")
        else:
            self.simulation_engine.log_with_sim_time(logging.INFO, f"⏭️  Patient #{patient_num}: No diagnostics required")
        
        # Disposition stage
        disposition_start = self.simulation_engine.env.now
        self.simulation_engine.log_with_sim_time(logging.INFO, f"📋 Patient #{patient_num}: Starting disposition at {self.simulation_engine.format_sim_time(disposition_start)}")
        disposition, admitted = yield from self._process_disposition(category, priority)
        
        self.simulation_engine.log_with_sim_time(logging.INFO, f"🏥 Patient #{patient_num}: Disposition decided - {disposition.upper()} at {self.simulation_engine.format_sim_time(self.simulation_engine.env.now)}")
        
        # Complete patient journey - NHS metrics updated through direct metric recording
        # (Synthea Patient models don't have record_departure method)
        
        self._complete_patient_journey(patient.patient_id, arrival_time, disposition, admitted, 
                                     category, patient.age, patient.gender, patient_num)
    
    def _setup_patient_arrival(self, arrival_time):
        """Setup patient data and record arrival metrics."""
        patient = self.get_patient()
        
        # Record patient arrival in NHS metrics using Synthea patient data
        self.nhs_metrics.add_patient_arrival(
            patient_id=patient.Id,
            arrival_time=arrival_time,
            age=self._calculate_age_from_birthdate(patient.BIRTHDATE),
            gender=patient.GENDER,
            presenting_complaint=self._extract_presenting_complaint(patient)
        )
        
        return patient
    
    def _calculate_age_from_birthdate(self, birthdate_str: str) -> int:
        """Calculate age from Synthea birthdate string."""
        try:
            from datetime import datetime
            birthdate = datetime.strptime(birthdate_str, '%Y-%m-%d')
            today = datetime.now()
            age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
            return max(0, age)
        except:
            return 30  # Default age if parsing fails
    
    def _extract_presenting_complaint(self, patient) -> str:
        """Extract presenting complaint from Synthea patient encounters."""
        if patient.encounters:
            # Use the first encounter's description as presenting complaint
            return patient.encounters[0].DESCRIPTION
        return 'General visit'
    
    def _process_triage_stage(self, patient_id, patient, patient_num):
        """Process triage nurse assessment stage and determine category/priority."""
        triage_start = self.simulation_engine.env.now
        patient.record_initial_assessment(triage_start)
        self.nhs_metrics.record_initial_assessment(patient_id, triage_start)
        
        triage_resource = self.simulation_engine.get_resource('nurses')
        self.simulation_engine.log_with_sim_time(logging.INFO, f"⏳ Patient #{patient_num}: Waiting for triage nurse at {self.simulation_engine.format_sim_time(triage_start)} (Queue: {len(triage_resource.queue)} waiting)")
        
        # Triage system resource updates removed (HospitalResources class not available)
        
        with triage_resource.request() as req:
            # Record resource request event
            self.simulation_engine.record_resource_event(
                'request', 'triage', patient_id, self._record_hospital_event, 
                queue_length=len(triage_resource.queue))
            
            yield req
            triage_service_start = self.simulation_engine.env.now
            wait_time = triage_service_start - triage_start
            
            # Record resource acquisition event
            self.simulation_engine.record_resource_event(
                'acquire', 'triage', patient_id, self._record_hospital_event, wait_time=wait_time)
            
            # Capture monitoring snapshot right after triage resource acquisition
            self._capture_monitoring_snapshot("triage resource acquired")
            
            self.simulation_engine.log_with_sim_time(logging.INFO, f"👩‍⚕️ Patient #{patient_num}: Started triage assessment at {self.simulation_engine.format_sim_time(triage_service_start)} (Waited: {wait_time:.1f}min)")
            
            # Perform triage assessment during nurse consultation
            self.simulation_engine.log_with_sim_time(logging.INFO, f"🔍 Patient #{patient_num}: Nurse performing triage assessment")
            category, priority, triage_result, processing_delay_seconds = self.perform_triage(patient)
            
            # Apply processing delay and calculate total triage time
            triage_processing_delay = self._scale_delay(processing_delay_seconds, delay_type='triage')
            
            # Determine complexity based on triage category for evidence-based timing
            if category in [TriageCategories.RED]:
                complexity = "complex"  # Immediate cases are complex
            elif category in [TriageCategories.ORANGE, TriageCategories.YELLOW]:
                complexity = "standard"  # Urgent cases are standard
            else:
                complexity = "simple"  # Less urgent cases are simpler
                
            base_triage_time = self.random_service.get_triage_process_time(complexity)
            total_triage_time = base_triage_time + triage_processing_delay
            
            self.simulation_engine.log_with_sim_time(logging.INFO, f"⏱️  Patient #{patient_num}: Triage assessment will take {total_triage_time:.1f}min (assessment: {base_triage_time:.1f}min + processing: {triage_processing_delay:.1f}min)")
            
            yield from self.simulation_engine.enhanced_yield_with_monitoring(
            total_triage_time, "triage assessment", self._capture_monitoring_snapshot)
            
            triage_end = self.simulation_engine.env.now
            
            # Capture monitoring snapshot right before triage resource release
            self._capture_monitoring_snapshot("triage resource before release")
            
            # Record resource release event
            self.simulation_engine.record_resource_event(
                'release', 'triage', patient_id, self._record_hospital_event, service_time=total_triage_time)
            
            self.simulation_engine.log_with_sim_time(logging.INFO, f"✅ Patient #{patient_num}: Completed triage assessment at {self.simulation_engine.format_sim_time(triage_end)} (Total triage time: {triage_end - triage_start:.1f}min)")
            
            return category, priority, triage_result
    
    def _process_doctor_assessment(self, patient, category, priority, triage_result, patient_num):
        """Process doctor assessment stage."""
        assessment_start = self.simulation_engine.env.now
        patient.record_treatment_start(assessment_start)
        self.nhs_metrics.record_treatment_start(patient.patient_id, assessment_start)
        
        doctor_resource = self.simulation_engine.get_resource('doctors')
        self.simulation_engine.log_with_sim_time(logging.INFO, f"⏳ Patient #{patient_num}: Waiting for doctor at {self.simulation_engine.format_sim_time(assessment_start)} (Priority: {priority}, Queue: {len(doctor_resource.queue)} waiting)")
        
        # Triage system resource updates removed (HospitalResources class not available)
        
        with doctor_resource.request(priority=priority) as req:
            # Record resource request event
            self.simulation_engine.record_resource_event(
                'request', 'doctor', patient.patient_id, self._record_hospital_event, 
                priority=priority, queue_length=len(doctor_resource.queue))
            
            yield req
            assessment_service_start = self.simulation_engine.env.now
            wait_time = assessment_service_start - assessment_start
            
            # Record resource acquisition event
            self.simulation_engine.record_resource_event(
                'acquire', 'doctor', patient.patient_id, self._record_hospital_event, 
                wait_time=wait_time, priority=priority)
            
            # Capture monitoring snapshot right after doctor resource acquisition
            self._capture_monitoring_snapshot("doctor resource acquired")
            
            self.simulation_engine.log_with_sim_time(logging.INFO, f"👨‍⚕️ Patient #{patient_num}: Started doctor assessment at {self.simulation_engine.format_sim_time(assessment_service_start)} (Waited: {wait_time:.1f}min)")
        
        # Calculate assessment time using NHS evidence-based ranges
        assessment_time = self.random_service.get_doctor_assessment_time(category)
        self.simulation_engine.log_with_sim_time(logging.INFO, f"⏱️  Patient #{patient_num}: Doctor assessment will take {assessment_time:.1f}min")
        
        yield from self.simulation_engine.enhanced_yield_with_monitoring(
                assessment_time, "doctor assessment", self._capture_monitoring_snapshot)
        
        assessment_end = self.simulation_engine.env.now
        
        # Capture monitoring snapshot right before doctor resource release
        self._capture_monitoring_snapshot("doctor resource before release")
        
        # Record resource release event
        self.simulation_engine.record_resource_event(
            'release', 'doctor', patient.patient_id, self._record_hospital_event, 
            service_time=assessment_time, priority=priority)
        
        self.simulation_engine.log_with_sim_time(logging.INFO, f"✅ Patient #{patient_num}: Completed doctor assessment at {self.simulation_engine.format_sim_time(assessment_end)} (Total assessment time: {assessment_end - assessment_start:.1f}min)")
    
    def _process_diagnostics(self, category):
        """Process optional diagnostics stage with specific test types.
        
        Uses NHS official timing data for different diagnostic procedures.
        """
        if self.random_service.should_perform_diagnostics():
            # Determine diagnostic type based on triage category and clinical needs
            diagnostic_type = self._determine_diagnostic_type(category)
            diagnostics_time = self.random_service.get_diagnostics_time(diagnostic_type)
            
            self.simulation_engine.log_with_sim_time(logging.INFO, f"🔬 Performing {diagnostic_type} diagnostics (Duration: {diagnostics_time:.1f}min)")
            yield from self.simulation_engine.enhanced_yield_with_monitoring(
                diagnostics_time, "diagnostics", self._capture_monitoring_snapshot)
    
    def _determine_diagnostic_type(self, category):
        """Determine appropriate diagnostic test type based on triage category.
        
        Returns specific test type for NHS evidence-based timing.
        """
        # Use RandomService for consistent diagnostic test selection
        return self.random_service.get_diagnostic_test_type(category)
    
    def _process_disposition(self, category, priority):
        """Process patient disposition using NHS evidence-based timing.
        
        Uses official NHS sources for admission and discharge processing times.
        """
        # Determine admission decision using NHS-based logic
        admitted = self.random_service.should_admit_patient(category)
        
        if admitted:
            # Admission process with NHS evidence-based timing
            disposition = 'admitted'
            processing_time = self.random_service.get_admission_processing_time()
            
            self.simulation_engine.log_with_sim_time(logging.INFO, f"🏥 Patient requires admission - processing time: {processing_time:.1f}min")
            
            # Bed allocation process
            bed_start = self.simulation_engine.env.now
            bed_resource = self.simulation_engine.get_resource('beds')
            self.simulation_engine.log_with_sim_time(logging.INFO, f"🛏️  Waiting for bed at {self.simulation_engine.format_sim_time(bed_start)} (Priority: {priority}, Available beds: {bed_resource.capacity - bed_resource.count})")
            
            with bed_resource.request(priority=priority) as req:
                yield req
                bed_service_start = self.simulation_engine.env.now
                bed_wait_time = bed_service_start - bed_start
                
                self.simulation_engine.log_with_sim_time(logging.INFO, f"🛏️  Bed allocated at {self.simulation_engine.format_sim_time(bed_service_start)} (Waited: {bed_wait_time:.1f}min)")
                
                yield from self.simulation_engine.enhanced_yield_with_monitoring(
                processing_time, "admission processing", self._capture_monitoring_snapshot)
                
                bed_end = self.simulation_engine.env.now
                self.simulation_engine.log_with_sim_time(logging.INFO, f"✅ Admission processing completed at {self.simulation_engine.format_sim_time(bed_end)} (Total bed process: {bed_end - bed_start:.1f}min)")
        else:
            # Discharge process with NHS evidence-based timing
            disposition = 'discharged'
            processing_time = self.random_service.get_discharge_processing_time()
            
            self.simulation_engine.log_with_sim_time(logging.INFO, f"🚪 Patient being discharged - processing time: {processing_time:.1f}min")
            yield from self.simulation_engine.enhanced_yield_with_monitoring(
                processing_time, "discharge processing", self._capture_monitoring_snapshot)
            
            discharge_end = self.simulation_engine.env.now
            self.simulation_engine.log_with_sim_time(logging.INFO, f"✅ Discharge processing completed at {self.simulation_engine.format_sim_time(discharge_end)}")
        
        return disposition, admitted
    
    def _complete_patient_journey(self, patient_id, arrival_time, disposition, admitted, 
                                category, age, gender, patient_num):
        """Complete patient journey with metrics and logging."""
        departure_time = self.simulation_engine.env.now
        
        # Record patient departure in NHS metrics
        self.nhs_metrics.record_patient_departure(
            patient_id=patient_id,
            departure_time=departure_time,
            disposal=disposition,
            admitted=admitted,
            left_without_being_seen=False
        )
        
        # Update simulation counters
        total_time = departure_time - arrival_time
        self.patient_count += 1
        self.total_time += total_time
        self.categories.append(category)
        
        # Update simulation engine counters
        self.simulation_engine.update_entity_completion(total_time, category)
        
        # Log patient completion with detailed summary
        self.simulation_engine.log_with_sim_time(logging.INFO, f"🎯 Patient #{patient_num} COMPLETED JOURNEY at {self.simulation_engine.format_sim_time(departure_time)}")
        self.simulation_engine.log_with_sim_time(logging.INFO, f"📊 Patient #{patient_num} Summary: {category} | Age {age} | {gender} | Total time: {total_time:.1f}min | {disposition.upper()}")
        self.simulation_engine.log_with_sim_time(logging.INFO, f"📈 Running totals: {self.patient_count} patients processed, avg time: {self.total_time/self.patient_count:.1f}min")
        self.simulation_engine.log_with_sim_time(logging.INFO, f"{'='*80}")
    
    def arrivals(self):
        """Generate Poisson arrivals."""
        patient_num = 0
        self.simulation_engine.log_with_sim_time(logging.INFO, f"🚀 Starting patient arrivals process at {self.simulation_engine.format_sim_time(self.simulation_engine.env.now)}")
        
        while True:
            # Poisson process: exponential interarrival times
            interarrival = self.random_service.get_patient_arrival_interval(self.arrival_rate)
            
            self.simulation_engine.log_with_sim_time(logging.DEBUG, f"⏰ Next patient arrival in {interarrival:.1f}min (at {self.simulation_engine.format_sim_time(self.simulation_engine.env.now + interarrival)})")
            yield self.simulation_engine.env.timeout(interarrival)
            
            patient_num += 1
            self.simulation_engine.log_with_sim_time(logging.INFO, f"🆕 Generating patient #{patient_num} at {self.simulation_engine.format_sim_time(self.simulation_engine.env.now)}")
            self.simulation_engine.env.process(self.patient_flow(patient_num))
    
    def run(self):
        """Run simulation using the simulation engine."""
        # Initialize the simulation engine
        self.simulation_engine.initialize_environment()
        
        # Initialize counters
        self.patient_count = 0
        self.total_time = 0
        self.categories = []
        
        # Schedule arrivals (monitoring is now synchronized with patient processes)
        self.simulation_engine.schedule_arrivals(self.arrivals)
        
        # Run the simulation
        results = self.simulation_engine.run_simulation()
        
        # Update counters from simulation engine results
        if 'total_entities' in results:
            self.patient_count = results['total_entities']
        if 'avg_time' in results:
            avg_time = results['avg_time']
        else:
            avg_time = self.total_time / self.patient_count if self.patient_count > 0 else 0
        
        self.simulation_engine.log_with_sim_time(logging.INFO, f"🏁 SIMULATION COMPLETE at {self.simulation_engine.format_sim_time(self.simulation_engine.env.now)}!")
        self.simulation_engine.log_with_sim_time(logging.INFO, f"📊 Final Results: {self.patient_count} patients processed, average time: {avg_time:.1f}min")
        
        # Get final resource states from simulation engine
        triage_resource = self.simulation_engine.get_resource('nurses')
        doctor_resource = self.simulation_engine.get_resource('doctors')
        bed_resource = self.simulation_engine.get_resource('beds')
        self.simulation_engine.log_with_sim_time(logging.INFO, f"🏥 Final resource state: Triage: {triage_resource.count}/{self.nurses}, Doctors: {doctor_resource.count}/{self.doctors}, Beds: {bed_resource.count}/{self.beds}")
        
        logger.info(f"Simulation Complete!")
        logger.info(f"Legacy Results: {self.patient_count} patients, avg time: {avg_time:.1f} min")
        
        # === NHS METRICS: Generate Dashboard ===
        logger.info("=" * 50)
        logger.info("GENERATING NHS QUALITY INDICATORS REPORT...")
        logger.info("=" * 50)
        nhs_metrics = self.nhs_metrics.print_nhs_dashboard()
        
        # === OPERATIONAL METRICS: Display operational performance ===
        logger.info("=" * 50)
        logger.info("OPERATIONAL METRICS SUMMARY")
        logger.info("=" * 50)
        operation_metrics = self.operation_metrics.calculate_metrics()
        
        if 'error' not in operation_metrics:
            logger.info(f"📊 Monitoring Data Points: {operation_metrics.get('monitoring_points', 0)}")
            logger.info(f"⏱️  Simulation Duration: {operation_metrics.get('total_duration_minutes', 0):.1f} minutes")
            
            # Resource Utilization
            if 'utilization' in operation_metrics:
                logger.info(f"📈 Average Resource Utilization:")
                for resource, data in operation_metrics['utilization'].items():
                    avg_util = data.get('average_utilization_pct', 0)
                    peak_util = data.get('peak_utilization_pct', 0)
                    logger.info(f"   {resource.title()}: {avg_util:.1f}% avg, {peak_util:.1f}% peak")
            
            # Queue Performance
            if 'queues' in operation_metrics:
                logger.info(f"📋 Queue Performance:")
                for resource, data in operation_metrics['queues'].items():
                    avg_queue = data.get('average_queue_length', 0)
                    peak_queue = data.get('peak_queue_length', 0)
                    logger.info(f"   {resource.title()}: {avg_queue:.1f} avg, {peak_queue} peak queue length")
            
            # Wait Times
            if 'wait_times' in operation_metrics:
                logger.info(f"⏰ Wait Time Analysis:")
                for resource, data in operation_metrics['wait_times'].items():
                    avg_wait = data.get('average_wait_time_minutes', 0)
                    max_wait = data.get('max_wait_time_minutes', 0)
                    logger.info(f"   {resource.title()}: {avg_wait:.1f} min avg, {max_wait:.1f} min max")
        
        # === LEGACY MONITORING SUMMARY: Display SimPy monitoring results ===
        logger.info("=" * 50)
        logger.info("LEGACY SIMPY MONITORING SUMMARY (Documentation Pattern)")
        logger.info("=" * 50)
        monitoring_summary = self.get_monitoring_summary()
        
        if 'error' not in monitoring_summary:
            logger.info(f"📊 Legacy Monitoring Data Points: {monitoring_summary['monitoring_points']}")
            logger.info(f"⏱️  Legacy Simulation Duration: {monitoring_summary['simulation_duration']:.1f} minutes")
            logger.info(f"📈 Legacy Average Resource Utilization:")
            logger.info(f"   Triage: {monitoring_summary['average_utilization']['triage']:.1f}%")
            logger.info(f"   Doctors: {monitoring_summary['average_utilization']['doctors']:.1f}%")
            logger.info(f"   Beds: {monitoring_summary['average_utilization']['beds']:.1f}%")
            logger.info(f"🚦 Average Queue Lengths:")
            logger.info(f"   Triage: {monitoring_summary['average_queue_lengths']['triage']:.1f}")
            logger.info(f"   Doctors: {monitoring_summary['average_queue_lengths']['doctors']:.1f}")
            logger.info(f"   Beds: {monitoring_summary['average_queue_lengths']['beds']:.1f}")
            logger.info(f"⚡ Peak Utilization:")
            logger.info(f"   Triage: {monitoring_summary['peak_utilization']['triage']:.1f}%")
            logger.info(f"   Doctors: {monitoring_summary['peak_utilization']['doctors']:.1f}%")
            logger.info(f"   Beds: {monitoring_summary['peak_utilization']['beds']:.1f}%")
            logger.info(f"📝 Total Resource Events: {monitoring_summary['total_resource_events']}")
        else:
            logger.warning(f"⚠️  {monitoring_summary.get('error', 'Unknown monitoring error')}")
        
        # === GENERATE CHARTS AND PLOTS ===
        logger.info("=" * 50)
        logger.info("GENERATING CHARTS AND VISUALIZATIONS...")
        logger.info("=" * 50)
        
        try:
            # Generate all charts using the plotting service
            plots_dir = os.path.join(self.output_dir, 'plots')
            generated_charts = self.plotting_service.generate_all_charts(output_dir=plots_dir)
            
            logger.info(f"📊 Generated {len(generated_charts)} charts:")
            for chart_name, file_path in generated_charts.items():
                logger.info(f"   {chart_name}: {file_path}")
        except Exception as e:
            logger.error(f"Error generating charts: {e}")
        
        # === EXPORT DATA ===
        logger.info("=" * 50)
        logger.info("EXPORTING METRICS DATA...")
        logger.info("=" * 50)
        
        try:
            # Export NHS metrics
            nhs_json_path = os.path.join(self.output_dir, 'metrics', 'nhs_metrics.json')
            nhs_csv_path = os.path.join(self.output_dir, 'metrics', 'nhs_patient_data.csv')
            os.makedirs(os.path.dirname(nhs_json_path), exist_ok=True)
            self.nhs_metrics.export_data(json_filepath=nhs_json_path, csv_filepath=nhs_csv_path)
            
            # Export operational metrics
            op_json_path = os.path.join(self.output_dir, 'metrics', 'operational_metrics.json')
            op_csv_path = os.path.join(self.output_dir, 'metrics', 'operational_events.csv')
            self.operation_metrics.export_data(json_filepath=op_json_path, csv_filepath=op_csv_path)
            
            logger.info(f"📁 Metrics data exported to {os.path.join(self.output_dir, 'metrics')}")
        except Exception as e:
            logger.error(f"Error exporting metrics data: {e}")
        
        # Return both legacy and NHS metrics for compatibility
        return {
            # Legacy format for backwards compatibility
            'total_patients': self.patient_count,
            'avg_time': avg_time,
            'times': [],
            'categories': self.categories,
            
            # New NHS metrics
             'nhs_metrics': nhs_metrics
         }
    
    def _capture_monitoring_snapshot(self, context: str = ""):
        """Hospital-specific monitoring snapshot using generalized simulation engine method.
        
        Args:
            context: Context description for debugging
        """
        # Hospital-specific resource mappings
        resource_mapping = {
            'triage': 'nurses',  # Triage is performed by nurses
            'nurse': 'nurses',   # Nurse resource utilization
            'doctor': 'doctors',
            'bed': 'beds'
        }
        
        capacity_mapping = {
            'triage': self.nurses,
            'nurse': self.nurses,
            'doctor': self.doctors,
            'bed': self.beds
        }
        
        # Use generalized monitoring from simulation engine
        self.simulation_engine.capture_monitoring_snapshot(
            context=context,
            resource_mapping=resource_mapping,
            capacity_mapping=capacity_mapping,
            metrics_recorder=self._record_hospital_metrics,
            entity_count=self.patient_count
        )
    
    def _record_hospital_metrics(self, snapshot_data: dict):
        """Hospital-specific metrics recording callback.
        
        Args:
            snapshot_data: Snapshot data from simulation engine
        """
        # Record the snapshot in hospital operation metrics
        self.operation_metrics.record_system_snapshot(
            timestamp=snapshot_data['timestamp'],
            resource_usage=snapshot_data['resource_usage'],
            resource_capacity=snapshot_data['resource_capacity'],
            queue_lengths=snapshot_data['queue_lengths'],
            entities_processed=snapshot_data['entities_processed']
        )
    
    def _get_simpy_resource_name(self, metrics_resource_name: str) -> str:
        """Map metrics resource names to SimPy resource names.
        
        Args:
            metrics_resource_name: Resource name used in metrics ('triage', 'doctor', 'bed')
            
        Returns:
            SimPy resource name ('nurses', 'doctors', 'beds')
        """
        mapping = {
            'triage': 'nurses',  # Triage is performed by nurses
            'doctor': 'doctors',
            'bed': 'beds'
        }
        return mapping.get(metrics_resource_name, metrics_resource_name)
    
    def _record_hospital_event(self, event_record: dict):
        """Hospital-specific event recording callback.
        
        Args:
            event_record: Event record from simulation engine
        """
        # Record in operation metrics
        self.operation_metrics.record_resource_event(
            event_type=event_record['event_type'],
            resource_name=event_record['resource'],
            entity_id=event_record['entity_id'] or 'unknown',
            timestamp=event_record['time'],
            **{k: v for k, v in event_record.items() if k not in ['time', 'event_type', 'resource', 'entity_id']}
        )
        
        # Additional logging for utilization tracking issues
        if event_record['event_type'] == 'acquire':
            actual_resource = self.simulation_engine.get_resource(self._get_simpy_resource_name(event_record['resource']))
            if actual_resource:
                logger.debug(f"📊 UTILIZATION DEBUG | {event_record['resource']} | In Use: {actual_resource.count} | "
                           f"Capacity: {actual_resource.capacity} | Queue: {len(actual_resource.queue)}")
            else:
                logger.warning(f"⚠️  RESOURCE NOT FOUND | {event_record['resource']} | SimPy resource mapping issue")
    

    
    def get_monitoring_summary(self):
        """Get summary of monitoring data collected during simulation.
        
        Returns:
            Dict containing monitoring statistics and utilization data
        """
        # Legacy monitoring data no longer collected with synchronized monitoring
        return {'error': 'No monitoring data collected'}
    
    def export_nhs_data(self, json_filepath: str = None, csv_filepath: str = None):
        """Export NHS metrics and patient data to configured output directory
        
        Args:
            json_filepath: Custom JSON file path (optional)
            csv_filepath: Custom CSV file path (optional)
        """
        # Use configured output directory if no custom paths provided
        if json_filepath is None:
            json_filepath = os.path.join(self.output_dir, 'metrics', 'nhs_metrics.json')
        if csv_filepath is None:
            csv_filepath = os.path.join(self.output_dir, 'metrics', 'patient_data.csv')
            
        self.nhs_metrics.export_data(json_filepath=json_filepath, csv_filepath=csv_filepath)