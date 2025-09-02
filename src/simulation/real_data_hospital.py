import simpy
import numpy as np
import random
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import sys
import os
import logging

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.services.data_service import DataService
from src.services.data_cleanup_service import DataCleanupService
from src.services.nhs_metrics_service import NHSMetricsService
from src.services.random_service import RandomService
from src.triage.manchester_triage_system import ManchesterTriageSystem
from src.triage.triage_constants import (
    TriageFlowcharts, FlowchartSymptomMapping, TriageCategories,
    SymptomKeys, MedicalConditions, CommonStrings, DiagnosticTestTypes, SymptomNames,
    ComplaintToFlowchartMapping
)


class SimpleHospital:
    """Simple hospital simulation with Poisson arrivals and real patient data."""
    
    def __init__(self, csv_folder='./output/csv', **kwargs):
        """Initialize hospital simulation with all required services and data.
        
        Args:
            csv_folder: Path to CSV data files
            **kwargs: Simulation parameters (sim_duration, arrival_rate, etc.)
        """
        self._setup_logging(**kwargs)
        self._setup_simulation_parameters(**kwargs)
        self._load_patient_data(csv_folder)
        self._initialize_services(**kwargs)
        
        # Simulation state
        self.env = None
        
        self._log_with_sim_time(logging.INFO, "Hospital simulation initialized successfully")
        self._log_with_sim_time(logging.INFO, f"Parameters: duration={self.sim_duration}min, arrival_rate={self.arrival_rate}/hr, nurses={self.nurses}, doctors={self.doctors}, beds={self.beds}")
    
    def _setup_logging(self, **kwargs):
        """Setup logging configuration for detailed simulation tracking."""
        log_level = kwargs.get('log_level', logging.INFO)
        
        # Create logger for this simulation instance
        self.logger = logging.getLogger(f'HospitalSim_{id(self)}')
        self.logger.setLevel(log_level)
        
        # Avoid duplicate handlers if logger already exists
        if not self.logger.handlers:
            # Create console handler with formatting
            handler = logging.StreamHandler()
            handler.setLevel(log_level)
            
            # Create detailed formatter with real time and simulation time
            formatter = logging.Formatter(
                '%(message)s at simulation %(sim_time)s and real time %(asctime)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _log_with_sim_time(self, level, message):
        """Log message with simulation time included in the record."""
        if self.env is not None:
            sim_time_str = self._format_sim_time(self.env.now)
        else:
            sim_time_str = "00:00 (0.0min)"
        
        # Create log record with simulation time
        record = self.logger.makeRecord(
            self.logger.name, level, __file__, 0, message, (), None
        )
        record.sim_time = sim_time_str
        self.logger.handle(record)
    
    def _format_sim_time(self, sim_time: float) -> str:
        """Format simulation time for logging.
        
        Args:
            sim_time: SimPy simulation time in minutes
            
        Returns:
            Formatted time string (e.g., "Day 1, 14:30 (870.0min)")
        """
        hours = int(sim_time // 60)
        minutes = int(sim_time % 60)
        days = hours // 24
        hour_of_day = hours % 24
        
        if days > 0:
            return f"Day {days + 1}, {hour_of_day:02d}:{minutes:02d} ({sim_time:.1f}min)"
        else:
            return f"{hour_of_day:02d}:{minutes:02d} ({sim_time:.1f}min)"
    
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
        print(f"Loading patient data from {csv_folder}...")
        self.data_service = DataService(csv_folder)
        self.patients = self.data_service.process_all()
        self.patient_ids = list(self.patients.keys())
        self.current_index = 0
        print(f"Loaded {len(self.patient_ids)} patients")
    
    def _initialize_services(self, **kwargs):
        """Initialize all required services for the simulation."""
        # Initialize NHS Metrics Service
        print("Initializing NHS Metrics Service...")
        self.nhs_metrics = NHSMetricsService(reattendance_window_hours=72)
        print("NHS Metrics Service ready")
        
        # Initialize Data Cleanup Service for patient data processing
        print("Initializing Data Cleanup Service...")
        self.data_cleanup = DataCleanupService()
        print("Data Cleanup Service ready")
        
        # Initialize Manchester Triage System
        print("Initializing Manchester Triage System...")
        self.mts = ManchesterTriageSystem()
        print("Manchester Triage System ready")
        
        # Initialize Random Service for centralized random data generation
        print("Initializing Random Service...")
        self.random_service = RandomService(seed=kwargs.get('random_seed'))
        print("Random Service ready")
    
    def get_patient(self):
        """Get next patient with processed data, cycling through data infinitely."""
        if not self.patient_ids:
            return None
        
        patient_id = self.patient_ids[self.current_index]
        raw_patient_data = self.patients[patient_id]
        self.current_index = (self.current_index + 1) % len(self.patient_ids)
        
        # Process patient data using DataCleanupService
        patient_summary = self.data_cleanup.get_patient_summary(raw_patient_data)
        
        # Return processed patient information
        processed_data = {
            'patient_id': patient_id,
            'age': patient_summary['age'],
            'gender': patient_summary['gender'],
            'presenting_complaint': patient_summary['chief_complaint'],
            'symptoms': patient_summary['symptoms'],  # Include extracted symptoms
            'vital_signs': patient_summary['vital_signs'],  # Include vital signs
            'raw_data': raw_patient_data  # Keep raw data for other uses if needed
        }
        
        return processed_data
    
    def perform_triage(self, patient_data=None):
        """Perform triage using paper-based Manchester Triage System approach with real patient data.
        
        Returns:
            tuple: (category, priority, mts_result, processing_delay_seconds)
        
        Note: This method now measures and returns the actual processing time for 
        integration with SimPy's discrete event simulation.
        """
        # Paper-based approach: Nurse selects appropriate flowchart based on patient presentation
        # FMTS paper: "decision aid system for the ER nurses to properly categorize patients based on their symptoms"
        
        if patient_data is None:
            raise ValueError("Patient data is required for triage. Cannot perform triage without real patient information.")
        
        # Measure actual triage processing time
        import time
        triage_start_time = time.time()
        
        # Use real patient data for triage
        # Map chief complaint to appropriate flowchart
        flowchart_reason = ComplaintToFlowchartMapping.get_flowchart_for_complaint(patient_data.get('presenting_complaint', ''))
        
        # Use real patient symptoms from the processed data
        raw_symptoms = patient_data.get('symptoms', {})
        
        # Convert real patient symptoms to MTS format
        symptoms_input = self._convert_symptoms_to_mts_format(raw_symptoms, flowchart_reason)
        
        # Ensure we have real patient symptoms - no random fallback
        if not symptoms_input:
            raise ValueError(f"No real patient symptoms available for flowchart '{flowchart_reason}'. Patient ID: {patient_data.get('patient_id', 'Unknown')}")
        
        # Use MTS directly with patient-based inputs
        result = self.mts.triage_patient(flowchart_reason, symptoms_input)
        
        # Calculate processing delay
        triage_end_time = time.time()
        processing_delay = triage_end_time - triage_start_time
        
        # Extract category from MTS result - no fallback, must be present
        if 'triage_category' not in result:
            raise ValueError(f"MTS result missing required 'triage_category' field: {result}")
        
        category = result['triage_category']
        if hasattr(category, 'item'):  # Handle numpy types
            category = category.item()
        category = str(category).strip()
        
        # Convert category to priority using centralized mapping - no fallback
        priority_map = TriageCategories.get_priority_mapping()
        if category not in priority_map:
            raise ValueError(f"Unknown triage category '{category}'. Valid categories: {list(priority_map.keys())}")
        
        priority = priority_map[category]
        
        # Return full MTS result for timing information
        return category, priority, result, processing_delay
    
    def _convert_symptoms_to_mts_format(self, raw_symptoms: Dict[str, str], flowchart_reason: str) -> Dict[str, str]:
        """Convert real patient symptoms to MTS flowchart format.
        
        Args:
            raw_symptoms: Symptoms from extract_patient_symptoms
            flowchart_reason: Selected flowchart identifier
            
        Returns:
            Dictionary of symptoms in MTS format for the specific flowchart
        """
        if not raw_symptoms:
            return {}
        
        # Get expected symptoms for this flowchart
        expected_symptoms = FlowchartSymptomMapping.get_symptoms_for_flowchart(flowchart_reason)
        mts_symptoms = {}
        
        # Map common symptom keys from extract_patient_symptoms to MTS format
        symptom_mapping = {
            # From SymptomKeys to MTS flowchart symptoms
            SymptomKeys.PAIN_LEVEL: 'severe_pain',
            SymptomKeys.CRUSHING_SENSATION: 'crushing_sensation', 
            SymptomKeys.BREATHING_DIFFICULTY: 'breathless',
            SymptomKeys.SWEATING: 'sweating',
            SymptomKeys.RADIATION: 'radiation',
            SymptomKeys.WHEEZE: 'wheeze',
            SymptomKeys.CYANOSIS: 'cyanosis',
            SymptomKeys.CONSCIOUSNESS: 'consciousness_level',
            SymptomKeys.TEMPERATURE: 'temperature',
            SymptomKeys.BLEEDING: 'bleeding',
            SymptomKeys.CONFUSION_LEVEL: 'confusion',
            SymptomKeys.DEFORMITY: 'deformity',
            SymptomKeys.MECHANISM: 'mechanism',
            # From SymptomNames to MTS symptoms
            SymptomNames.NAUSEA: 'nausea',
            SymptomNames.HEADACHE: 'pain_severity',
            SymptomNames.DIZZINESS: 'dizziness',
            SymptomNames.CHEST_PAIN: 'chest_pain'
        }
        
        # Convert symptoms that exist in both raw_symptoms and expected_symptoms
        for raw_key, raw_value in raw_symptoms.items():
            # Map the key to MTS format
            mts_key = symptom_mapping.get(raw_key, raw_key)
            
            # Only include if this symptom is expected for the flowchart
            if mts_key in expected_symptoms:
                mts_symptoms[mts_key] = raw_value
        
        return mts_symptoms
    
    def patient_flow(self, patient_num):
        """Simulate patient journey with NHS metrics tracking."""
        arrival_time = self.env.now
        
        self._log_with_sim_time(logging.INFO, f"🚶 Patient #{patient_num} ARRIVED at {self._format_sim_time(arrival_time)}")
        
        # Setup patient and record arrival
        patient_data = self._setup_patient_arrival(arrival_time)
        patient_id = patient_data['patient_id']
        
        self._log_with_sim_time(logging.INFO, f"👤 Patient {patient_id}: Age {patient_data['age']}, {patient_data['gender']}, Complaint: '{patient_data['presenting_complaint']}'")
        
        # Perform triage and get category/priority with processing delay handled internally
        self._log_with_sim_time(logging.INFO, f"🔍 Patient {patient_id}: Starting triage assessment at {self._format_sim_time(self.env.now)}")
        
        # Get triage result with processing delay from perform_triage method
        category, priority, mts_result, processing_delay_seconds = self.perform_triage(patient_data)
        
        # Apply the delay using general-purpose scaling (delay measurement handled in perform_triage)
        triage_processing_delay = self._scale_delay(processing_delay_seconds, delay_type='triage')
        self._log_with_sim_time(logging.INFO, f"⏳ Patient {patient_id}: Triage processing took {processing_delay_seconds:.1f} real seconds, converting to {triage_processing_delay:.1f} simulation minutes")
        yield self.env.timeout(triage_processing_delay)
        
        # Record triage result and log completion
        self.nhs_metrics.record_triage_category(patient_data['patient_id'], category)
        self._log_with_sim_time(logging.INFO, f"🏷️  Patient {patient_id}: Triaged as {category} (Priority: {priority}) at {self._format_sim_time(self.env.now)} (Processing delay: {triage_processing_delay:.1f}min)")
        
        # Triage nurse stage
        self._log_with_sim_time(logging.INFO, f"👩‍⚕️ Patient {patient_id}: Entering triage nurse stage at {self._format_sim_time(self.env.now)}")
        yield from self._process_triage_stage(patient_data['patient_id'], category, mts_result)
        
        # Doctor assessment stage
        self._log_with_sim_time(logging.INFO, f"👨‍⚕️ Patient {patient_id}: Entering doctor assessment stage at {self._format_sim_time(self.env.now)}")
        yield from self._process_doctor_assessment(patient_data['patient_id'], category, priority, mts_result)
        
        # Diagnostics stage (optional)
        diagnostics_start = self.env.now
        self._log_with_sim_time(logging.INFO, f"🔬 Patient {patient_id}: Checking for diagnostics at {self._format_sim_time(diagnostics_start)}")
        yield from self._process_diagnostics(category)
        
        if self.env.now > diagnostics_start:
            self._log_with_sim_time(logging.INFO, f"🧪 Patient {patient_id}: Completed diagnostics at {self._format_sim_time(self.env.now)} (Duration: {self.env.now - diagnostics_start:.1f}min)")
        else:
            self._log_with_sim_time(logging.INFO, f"⏭️  Patient {patient_id}: No diagnostics required")
        
        # Disposition stage
        disposition_start = self.env.now
        self._log_with_sim_time(logging.INFO, f"📋 Patient {patient_id}: Starting disposition at {self._format_sim_time(disposition_start)}")
        disposition, admitted = yield from self._process_disposition(category, priority)
        
        self._log_with_sim_time(logging.INFO, f"🏥 Patient {patient_id}: Disposition decided - {disposition.upper()} at {self._format_sim_time(self.env.now)}")
        
        # Complete patient journey
        self._complete_patient_journey(patient_data['patient_id'], arrival_time, disposition, admitted, 
                                     category, patient_data['age'], patient_data['gender'])
    
    def _setup_patient_arrival(self, arrival_time):
        """Setup patient data and record arrival metrics."""
        patient_data = self.get_patient()
        
        # Record patient arrival in NHS metrics
        self.nhs_metrics.add_patient_arrival(
            patient_id=patient_data['patient_id'],
            arrival_time=arrival_time,
            age=patient_data['age'],
            gender=patient_data['gender'],
            presenting_complaint=patient_data['presenting_complaint']
        )
        
        return patient_data
    
    def _process_triage_stage(self, patient_id, category, mts_result):
        """Process triage nurse assessment stage."""
        triage_start = self.env.now
        self.nhs_metrics.record_initial_assessment(patient_id, triage_start)
        
        self._log_with_sim_time(logging.INFO, f"⏳ Patient {patient_id}: Waiting for triage nurse at {self._format_sim_time(triage_start)} (Queue: {len(self.triage_resource.queue)} waiting)")
        
        with self.triage_resource.request() as req:
            yield req
            triage_service_start = self.env.now
            wait_time = triage_service_start - triage_start
            
            self._log_with_sim_time(logging.INFO, f"👩‍⚕️ Patient {patient_id}: Started triage assessment at {self._format_sim_time(triage_service_start)} (Waited: {wait_time:.1f}min)")
            
            # Calculate triage time using MTS or fallback
            triage_time = self._calculate_triage_time(category, mts_result)
            self._log_with_sim_time(logging.INFO, f"⏱️  Patient {patient_id}: Triage assessment will take {triage_time:.1f}min")
            
            yield self.env.timeout(triage_time)
            
            triage_end = self.env.now
            self._log_with_sim_time(logging.INFO, f"✅ Patient {patient_id}: Completed triage assessment at {self._format_sim_time(triage_end)} (Total triage time: {triage_end - triage_start:.1f}min)")
    
    def _calculate_triage_time(self, category, mts_result):
        """Calculate triage assessment time using evidence-based NHS timing.
        
        Uses official MTS research and NHS sources for realistic triage duration.
        """
        if not mts_result:
            raise ValueError("MTS result is required for triage time calculation")
        
        # Determine complexity based on triage category
        if category in [TriageCategories.RED]:
            complexity = "complex"  # Immediate cases are complex
        elif category in [TriageCategories.ORANGE, TriageCategories.YELLOW]:
            complexity = "standard"  # Urgent cases are standard
        else:
            complexity = "simple"  # Less urgent cases are simpler
        
        # Use evidence-based triage process time (NHS official sources)
        return self.random_service.get_triage_process_time(complexity)
    
    def _process_doctor_assessment(self, patient_id, category, priority, mts_result):
        """Process doctor assessment stage."""
        assessment_start = self.env.now
        self.nhs_metrics.record_treatment_start(patient_id, assessment_start)
        
        self._log_with_sim_time(logging.INFO, f"⏳ Patient {patient_id}: Waiting for doctor at {self._format_sim_time(assessment_start)} (Priority: {priority}, Queue: {len(self.doctor_resource.queue)} waiting)")
        
        with self.doctor_resource.request(priority=priority) as req:
            yield req
            assessment_service_start = self.env.now
            wait_time = assessment_service_start - assessment_start
            
            self._log_with_sim_time(logging.INFO, f"👨‍⚕️ Patient {patient_id}: Started doctor assessment at {self._format_sim_time(assessment_service_start)} (Waited: {wait_time:.1f}min)")
            
            # Calculate assessment time using MTS or fallback
            assessment_time = self._calculate_assessment_time(category, mts_result)
            self._log_with_sim_time(logging.INFO, f"⏱️  Patient {patient_id}: Doctor assessment will take {assessment_time:.1f}min")
            
            yield self.env.timeout(assessment_time)
            
            assessment_end = self.env.now
            self._log_with_sim_time(logging.INFO, f"✅ Patient {patient_id}: Completed doctor assessment at {self._format_sim_time(assessment_end)} (Total assessment time: {assessment_end - assessment_start:.1f}min)")
    
    def _calculate_assessment_time(self, category, mts_result):
        """Calculate doctor assessment time based on MTS result."""
        if not mts_result:
            raise ValueError("MTS result is required for assessment time calculation")
        
        if 'wait_time' not in mts_result:
            raise ValueError(f"MTS result missing required 'wait_time' field: {mts_result}")
        
        # Use MTS wait time with category-specific percentages
        mts_wait_minutes = self.data_cleanup.convert_wait_time_to_minutes(mts_result['wait_time'], self.random_service)
        if category == TriageCategories.RED:
            return min(mts_wait_minutes * 0.3, 30)
        elif category == TriageCategories.ORANGE:
            return min(mts_wait_minutes * 0.4, 40)
        else:
            return min(mts_wait_minutes * 0.5, 50)
    
    def _process_diagnostics(self, category):
        """Process optional diagnostics stage with specific test types.
        
        Uses NHS official timing data for different diagnostic procedures.
        """
        if self.random_service.should_perform_diagnostics():
            # Determine diagnostic type based on triage category and clinical needs
            diagnostic_type = self._determine_diagnostic_type(category)
            diagnostics_time = self.random_service.get_diagnostics_time(diagnostic_type)
            
            self._log_with_sim_time(logging.INFO, f"🔬 Performing {diagnostic_type} diagnostics (Duration: {diagnostics_time:.1f}min)")
            yield self.env.timeout(diagnostics_time)
    
    def _determine_diagnostic_type(self, category):
        """Determine appropriate diagnostic test type based on triage category.
        
        Returns specific test type for NHS evidence-based timing.
        """
        if category == TriageCategories.RED:
            # Critical patients often need immediate ECG and blood work
            return random.choice([DiagnosticTestTypes.ECG, DiagnosticTestTypes.BLOOD, DiagnosticTestTypes.MIXED])
        elif category == TriageCategories.ORANGE:
            # Very urgent patients may need various diagnostics
            return random.choice([DiagnosticTestTypes.BLOOD, DiagnosticTestTypes.XRAY, DiagnosticTestTypes.MIXED])
        elif category == TriageCategories.YELLOW:
            # Urgent patients typically need standard diagnostics
            return random.choice([DiagnosticTestTypes.XRAY, DiagnosticTestTypes.BLOOD])
        else:
            # Less urgent patients usually need simple diagnostics
            return random.choice([DiagnosticTestTypes.XRAY, DiagnosticTestTypes.ECG])
    
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
            
            self._log_with_sim_time(logging.INFO, f"🏥 Patient requires admission - processing time: {processing_time:.1f}min")
            
            # Bed allocation process
            bed_start = self.env.now
            self._log_with_sim_time(logging.INFO, f"🛏️  Waiting for bed at {self._format_sim_time(bed_start)} (Priority: {priority}, Available beds: {self.bed_resource.capacity - self.bed_resource.count})")
            
            with self.bed_resource.request(priority=priority) as req:
                yield req
                bed_service_start = self.env.now
                bed_wait_time = bed_service_start - bed_start
                
                self._log_with_sim_time(logging.INFO, f"🛏️  Bed allocated at {self._format_sim_time(bed_service_start)} (Waited: {bed_wait_time:.1f}min)")
                
                yield self.env.timeout(processing_time)
                
                bed_end = self.env.now
                self._log_with_sim_time(logging.INFO, f"✅ Admission processing completed at {self._format_sim_time(bed_end)} (Total bed process: {bed_end - bed_start:.1f}min)")
        else:
            # Discharge process with NHS evidence-based timing
            disposition = 'discharged'
            processing_time = self.random_service.get_discharge_processing_time()
            
            self._log_with_sim_time(logging.INFO, f"🚪 Patient being discharged - processing time: {processing_time:.1f}min")
            yield self.env.timeout(processing_time)
            
            discharge_end = self.env.now
            self._log_with_sim_time(logging.INFO, f"✅ Discharge processing completed at {self._format_sim_time(discharge_end)}")
        
        return disposition, admitted
    
    def _complete_patient_journey(self, patient_id, arrival_time, disposition, admitted, 
                                category, age, gender):
        """Complete patient journey with metrics and logging."""
        departure_time = self.env.now
        
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
        
        # Log patient completion with detailed summary
        self._log_with_sim_time(logging.INFO, f"🎯 Patient {patient_id} COMPLETED JOURNEY at {self._format_sim_time(departure_time)}")
        self._log_with_sim_time(logging.INFO, f"📊 Patient {patient_id} Summary: {category} | Age {age} | {gender} | Total time: {total_time:.1f}min | {disposition.upper()}")
        self._log_with_sim_time(logging.INFO, f"📈 Running totals: {self.patient_count} patients processed, avg time: {self.total_time/self.patient_count:.1f}min")
        self._log_with_sim_time(logging.INFO, f"{'='*80}")
    
    def arrivals(self):
        """Generate Poisson arrivals."""
        patient_num = 0
        self._log_with_sim_time(logging.INFO, f"🚀 Starting patient arrivals process at {self._format_sim_time(self.env.now)}")
        
        while True:
            # Poisson process: exponential interarrival times
            interarrival = self.random_service.get_patient_arrival_interval(self.arrival_rate)
            
            self._log_with_sim_time(logging.DEBUG, f"⏰ Next patient arrival in {interarrival:.1f}min (at {self._format_sim_time(self.env.now + interarrival)})")
            yield self.env.timeout(interarrival)
            
            patient_num += 1
            self._log_with_sim_time(logging.INFO, f"🆕 Generating patient #{patient_num} at {self._format_sim_time(self.env.now)}")
            self.env.process(self.patient_flow(patient_num))
    
    def run(self):
        """Run simulation with NHS metrics tracking."""
        self._log_with_sim_time(logging.INFO, f"🏥 STARTING SIMULATION: {self.sim_duration/60:.1f}h duration with {self.arrival_rate} patients/hour")
        
        # Initialize simple counters
        self.patient_count = 0
        self.total_time = 0
        self.categories = []
        
        # Setup simulation
        self.env = simpy.Environment()
        self.triage_resource = simpy.Resource(self.env, capacity=self.nurses)
        self.doctor_resource = simpy.PriorityResource(self.env, capacity=self.doctors)
        self.bed_resource = simpy.PriorityResource(self.env, capacity=self.beds)
        
        self._log_with_sim_time(logging.INFO, f"🏗️  Resources initialized: {self.nurses} nurses, {self.doctors} doctors, {self.beds} beds")
        
        # Start arrivals
        self.env.process(self.arrivals())
        self._log_with_sim_time(logging.INFO, f"▶️  Simulation started at {self._format_sim_time(self.env.now)}")
        
        # Run simulation with periodic progress updates
        start_time = self.env.now
        progress_interval = self.sim_duration / 10  # Log progress every 10% of simulation
        next_progress = progress_interval
        
        while self.env.now < self.sim_duration:
            # Run until next progress point or end
            run_until = min(next_progress, self.sim_duration)
            
            # Only run if we haven't reached the end yet
            if self.env.now < run_until:
                self.env.run(until=run_until)
            
            # Log progress if we hit a progress milestone
            if self.env.now >= next_progress and self.env.now < self.sim_duration:
                progress_pct = (self.env.now / self.sim_duration) * 100
                self._log_with_sim_time(logging.INFO, f"📊 PROGRESS: {progress_pct:.0f}% complete at {self._format_sim_time(self.env.now)} | Patients processed: {self.patient_count}")
                self._log_with_sim_time(logging.INFO, f"📈 Resource utilization: Triage queue: {len(self.triage_resource.queue)}, Doctor queue: {len(self.doctor_resource.queue)}, Bed queue: {len(self.bed_resource.queue)}")
                next_progress += progress_interval
            
            # Break if we've reached the end
            if self.env.now >= self.sim_duration:
                break
        
        # Calculate simple results
        avg_time = self.total_time / self.patient_count if self.patient_count > 0 else 0
        
        self._log_with_sim_time(logging.INFO, f"🏁 SIMULATION COMPLETE at {self._format_sim_time(self.env.now)}!")
        self._log_with_sim_time(logging.INFO, f"📊 Final Results: {self.patient_count} patients processed, average time: {avg_time:.1f}min")
        self._log_with_sim_time(logging.INFO, f"🏥 Final resource state: Triage: {self.triage_resource.count}/{self.nurses}, Doctors: {self.doctor_resource.count}/{self.doctors}, Beds: {self.bed_resource.count}/{self.beds}")
        
        print(f"\nSimulation Complete!")
        print(f"Legacy Results: {self.patient_count} patients, avg time: {avg_time:.1f} min")
        
        # === NHS METRICS: Generate Dashboard ===
        print("\n" + "="*50)
        print("GENERATING NHS QUALITY INDICATORS REPORT...")
        print("="*50)
        nhs_metrics = self.nhs_metrics.print_nhs_dashboard()
        
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
    
    def get_nhs_metrics(self):
        """Get NHS metrics directly"""
        return self.nhs_metrics.calculate_nhs_metrics()
    
    def export_nhs_data(self, json_filepath: str = None, csv_filepath: str = None):
        """Export NHS metrics and patient data"""
        self.nhs_metrics.export_data(json_filepath=json_filepath, csv_filepath=csv_filepath)