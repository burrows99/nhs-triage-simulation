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

# Import centralized logger
from src.logger import logger

from src.services.data_service import DataService
from src.services.data_cleanup_service import DataCleanupService
from src.services.nhs_metrics import NHSMetrics
from src.services.operation_metrics import OperationMetrics
from src.services.plotting_service import PlottingService
from src.services.random_service import RandomService
from src.triage.base_triage_system import TriageSystemFactory
from .simulation_engine import SimulationEngine
from src.triage.triage_constants import (
    TriageFlowcharts, FlowchartSymptomMapping, TriageCategories,
    SymptomKeys, MedicalConditions, CommonStrings, DiagnosticTestTypes, SymptomNames,
    ComplaintToFlowchartMapping
)


class SimpleHospital:
    """Simple hospital simulation with Poisson arrivals and real patient data."""
    
    def __init__(self, csv_folder='./output/csv', output_dir='./output/hospital_simulation', **kwargs):
        """Initialize hospital simulation with all required services and data.
        
        Args:
            csv_folder: Path to CSV data files
            output_dir: Directory for simulation outputs (metrics, plots, etc.)
            **kwargs: Simulation parameters (sim_duration, arrival_rate, etc.)
        """
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
        self.patients = self.data_service.process_all()
        self.patient_ids = list(self.patients.keys())
        self.current_index = 0
        logger.info(f"Loaded {len(self.patient_ids)} patients")
    
    def _initialize_services(self, **kwargs):
        """Initialize all required services for the simulation."""
        # Initialize NHS Metrics Service
        logger.info("Initializing NHS Metrics Service...")
        self.nhs_metrics = NHSMetrics(reattendance_window_hours=72)
        logger.info("NHS Metrics Service ready")
        
        # Initialize Operation Metrics Service
        logger.info("Initializing Operation Metrics Service...")
        self.operation_metrics = OperationMetrics(snapshot_interval=5.0)
        logger.info("Operation Metrics Service ready")
        
        # Initialize Plotting Service and register metric services
        logger.info("Initializing Plotting Service...")
        self.plotting_service = PlottingService()
        self.plotting_service.register_metric_service('nhs', self.nhs_metrics)
        self.plotting_service.register_metric_service('operations', self.operation_metrics)
        logger.info("Plotting Service ready with registered metrics")
        
        # Initialize Data Cleanup Service for patient data processing
        logger.info("Initializing Data Cleanup Service...")
        self.data_cleanup = DataCleanupService()
        logger.info("Data Cleanup Service ready")
        
        # Initialize Triage System (configurable)
        triage_type = kwargs.get('triage_system', 'manchester')  # Default to Manchester
        self.triage_system = self._initialize_triage_system(triage_type, **kwargs)
        self._validate_triage_system_connection()
        
        # Initialize Random Service for centralized random data generation
        logger.info("Initializing Random Service...")
        self.random_service = RandomService(seed=kwargs.get('random_seed'))
        logger.info("Random Service ready")
    
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
            tuple: (category, priority, triage_result, processing_delay_seconds)
        
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
        
        # Use triage system with patient-based inputs
        result = self.triage_system.triage_patient(
            flowchart_reason=flowchart_reason,
            symptoms_input=symptoms_input,
            patient_id=patient_data.get('patient_id')
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
        
        # Return full MTS result for timing information
        return category, priority, result, processing_delay
    
    def _update_triage_system_resources(self):
        """Update triage system with comprehensive current SimPy resource availability and status"""
        try:
            # Create HospitalResources object from current SimPy resource state
            from src.triage.llm_triage_system import HospitalResources
            
            # Calculate detailed queue information
            triage_queue_length = len(self.triage_resource.queue)
            doctor_queue_length = len(self.doctor_resource.queue)
            bed_queue_length = len(self.bed_resource.queue) if hasattr(self.bed_resource, 'queue') else 0
            total_queue_length = triage_queue_length + doctor_queue_length + bed_queue_length
            
            # Calculate resource utilization
            doctors_in_use = self.doctor_resource.count
            nurses_in_use = self.triage_resource.count
            beds_in_use = self.bed_resource.count
            
            current_resources = HospitalResources(
                doctors_available=self.doctor_resource.capacity - doctors_in_use,
                nurses_available=self.triage_resource.capacity - nurses_in_use,
                beds_available=self.bed_resource.capacity - beds_in_use,
                total_doctors=self.doctor_resource.capacity,
                total_nurses=self.triage_resource.capacity,
                total_beds=self.bed_resource.capacity,
                current_queue_length=total_queue_length
            )
            
            # Add additional queue status information as attributes
            current_resources.triage_queue_length = triage_queue_length
            current_resources.doctor_queue_length = doctor_queue_length
            current_resources.bed_queue_length = bed_queue_length
            current_resources.doctors_in_use = doctors_in_use
            current_resources.nurses_in_use = nurses_in_use
            current_resources.beds_in_use = beds_in_use
            current_resources.simulation_time = self.env.now if self.env else 0
            
            # Update triage system with current resources
            self.triage_system.update_resources(current_resources)
            
        except Exception as e:
             # Silently continue if resource update fails (e.g., for Manchester system)
             pass
    
    def _initialize_triage_system(self, triage_type: str, **kwargs):
        """Initialize the appropriate triage system based on configuration
        
        Args:
            triage_type: Type of triage system ('manchester' or 'llm')
            **kwargs: Configuration parameters
            
        Returns:
            Configured triage system instance
        """
        logger.info(f"Initializing {triage_type.title()} Triage System...")
        
        if triage_type.lower() == 'llm':
            return self._create_llm_triage_system(**kwargs)
        else:
            return self._create_manchester_triage_system(**kwargs)
    
    def _create_llm_triage_system(self, **kwargs):
        """Create and configure LLM Triage System
        
        Args:
            **kwargs: Configuration parameters
            
        Returns:
            Configured LLM triage system
        """
        # Configure LLM system parameters
        llm_params = {
            'num_agents_per_type': kwargs.get('num_agents_per_type', 2),
            'model': kwargs.get('llm_model', 'llama3.2:1b'),
            'ollama_url': kwargs.get('ollama_url', 'http://localhost:11434')
        }
        
        # Validate Ollama connection before creating system
        if not self._validate_ollama_connection(llm_params['ollama_url'], llm_params['model']):
            logger.warning("⚠️  Warning: Ollama validation failed, but continuing with LLM system creation")
        
        triage_system = TriageSystemFactory.create_llm_triage_system(**llm_params)
        logger.info(f"{triage_system.get_system_info()['system_name']} ready")
        return triage_system
    
    def _create_manchester_triage_system(self, **kwargs):
        """Create and configure Manchester Triage System
        
        Args:
            **kwargs: Configuration parameters
            
        Returns:
            Configured Manchester triage system
        """
        triage_system = TriageSystemFactory.create_manchester_triage_system()
        logger.info(f"{triage_system.get_system_info()['system_name']} ready")
        return triage_system
    
    def _validate_ollama_connection(self, ollama_url: str, model: str) -> bool:
        """Validate Ollama service connection and model availability
        
        Args:
            ollama_url: Ollama service URL
            model: Model name to validate
            
        Returns:
            True if connection and model are valid, False otherwise
        """
        try:
            from src.services.ollama_service import OllamaService
            
            logger.info(f"🔌 Validating Ollama connection to {ollama_url}...")
            ollama = OllamaService(base_url=ollama_url)
            
            # Test health check
            if not ollama.health_check():
                logger.error(f"❌ Ollama service at {ollama_url} is not responding")
                return False
            
            logger.info(f"✅ Ollama service is running")
            
            # Test model availability
            models = ollama.list_models()
            if 'models' in models:
                available_models = [m.get('name', '') for m in models['models']]
                if model in available_models:
                    logger.info(f"✅ Model '{model}' is available")
                    return True
                else:
                    logger.warning(f"⚠️  Model '{model}' not found. Available: {available_models}")
                    return False
            else:
                logger.warning(f"⚠️  Could not retrieve model list from Ollama")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ollama validation failed: {str(e)}")
            return False
    
    def _validate_triage_system_connection(self):
        """Validate the initialized triage system connection"""
        logger.info("🔍 Validating triage system connection...")
        
        try:
            if self.triage_system.validate_connection():
                logger.info("✅ Triage system validated successfully")
            else:
                logger.warning("⚠️  Warning: Triage system connection validation failed")
        except Exception as e:
            logger.warning(f"⚠️  Warning: Triage system validation error: {str(e)}")
    
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
        arrival_time = self.simulation_engine.env.now
        
        self.simulation_engine.log_with_sim_time(logging.INFO, f"🚶 Patient #{patient_num} ARRIVED at {self.simulation_engine.format_sim_time(arrival_time)}")
        
        # Setup patient and record arrival
        patient_data = self._setup_patient_arrival(arrival_time)
        patient_id = patient_data['patient_id']
        
        self.simulation_engine.log_with_sim_time(logging.INFO, f"👤 Patient #{patient_num}: Age {patient_data['age']}, {patient_data['gender']}, Complaint: '{patient_data['presenting_complaint']}'")
        
        # Triage nurse assessment stage - this is where triage category/priority is determined
        self.simulation_engine.log_with_sim_time(logging.INFO, f"👩‍⚕️ Patient #{patient_num}: Entering triage nurse assessment at {self.simulation_engine.format_sim_time(self.simulation_engine.env.now)}")
        category, priority, triage_result = yield from self._process_triage_stage(patient_data['patient_id'], patient_data, patient_num)
        
        # Record triage result and log completion
        self.nhs_metrics.record_triage_category(patient_data['patient_id'], category)
        self.simulation_engine.log_with_sim_time(logging.INFO, f"🏷️  Patient #{patient_num}: Triaged as {category} (Priority: {priority}) at {self.simulation_engine.format_sim_time(self.simulation_engine.env.now)}")
        
        # Doctor assessment stage
        self.simulation_engine.log_with_sim_time(logging.INFO, f"👨‍⚕️ Patient #{patient_num}: Entering doctor assessment stage at {self.simulation_engine.format_sim_time(self.simulation_engine.env.now)}")
        yield from self._process_doctor_assessment(patient_data['patient_id'], category, priority, triage_result, patient_num)
        
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
        
        # Complete patient journey
        self._complete_patient_journey(patient_data['patient_id'], arrival_time, disposition, admitted, 
                                     category, patient_data['age'], patient_data['gender'], patient_num)
    
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
    
    def _process_triage_stage(self, patient_id, patient_data, patient_num):
        """Process triage nurse assessment stage and determine category/priority."""
        triage_start = self.simulation_engine.env.now
        self.nhs_metrics.record_initial_assessment(patient_id, triage_start)
        
        triage_resource = self.simulation_engine.get_resource('nurses')
        self.simulation_engine.log_with_sim_time(logging.INFO, f"⏳ Patient #{patient_num}: Waiting for triage nurse at {self.simulation_engine.format_sim_time(triage_start)} (Queue: {len(triage_resource.queue)} waiting)")
        
        # Update triage system with current resource availability (including real queue lengths)
        self._update_triage_system_resources()
        
        with triage_resource.request() as req:
            # Record resource request event
            self.record_resource_event('request', 'triage', patient_id, queue_length=len(triage_resource.queue))
            
            yield req
            triage_service_start = self.simulation_engine.env.now
            wait_time = triage_service_start - triage_start
            
            # Record resource acquisition event
            self.record_resource_event('acquire', 'triage', patient_id, wait_time=wait_time)
            
            self.simulation_engine.log_with_sim_time(logging.INFO, f"👩‍⚕️ Patient #{patient_num}: Started triage assessment at {self.simulation_engine.format_sim_time(triage_service_start)} (Waited: {wait_time:.1f}min)")
            
            # Perform triage assessment during nurse consultation
            self.simulation_engine.log_with_sim_time(logging.INFO, f"🔍 Patient #{patient_num}: Nurse performing triage assessment")
            category, priority, triage_result, processing_delay_seconds = self.perform_triage(patient_data)
            
            # Apply processing delay and calculate total triage time
            triage_processing_delay = self._scale_delay(processing_delay_seconds, delay_type='triage')
            base_triage_time = self._calculate_triage_time(category, triage_result)
            total_triage_time = base_triage_time + triage_processing_delay
            
            self.simulation_engine.log_with_sim_time(logging.INFO, f"⏱️  Patient #{patient_num}: Triage assessment will take {total_triage_time:.1f}min (assessment: {base_triage_time:.1f}min + processing: {triage_processing_delay:.1f}min)")
            
            yield self.simulation_engine.env.timeout(total_triage_time)
            
            triage_end = self.simulation_engine.env.now
            
            # Record resource release event
            self.record_resource_event('release', 'triage', patient_id, service_time=total_triage_time)
            
            self.simulation_engine.log_with_sim_time(logging.INFO, f"✅ Patient #{patient_num}: Completed triage assessment at {self.simulation_engine.format_sim_time(triage_end)} (Total triage time: {triage_end - triage_start:.1f}min)")
            
            return category, priority, triage_result
    
    def _calculate_triage_time(self, category, triage_result):
        """Calculate triage assessment time using evidence-based NHS timing.
        
        Uses official MTS research and NHS sources for realistic triage duration.
        """
        if not triage_result:
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
    
    def _process_doctor_assessment(self, patient_id, category, priority, triage_result, patient_num):
        """Process doctor assessment stage."""
        assessment_start = self.simulation_engine.env.now
        self.nhs_metrics.record_treatment_start(patient_id, assessment_start)
        
        doctor_resource = self.simulation_engine.get_resource('doctors')
        self.simulation_engine.log_with_sim_time(logging.INFO, f"⏳ Patient #{patient_num}: Waiting for doctor at {self.simulation_engine.format_sim_time(assessment_start)} (Priority: {priority}, Queue: {len(doctor_resource.queue)} waiting)")
        
        # Update triage system with current resource availability (including doctor queue lengths)
        self._update_triage_system_resources()
        
        with doctor_resource.request(priority=priority) as req:
            # Record resource request event
            self.record_resource_event('request', 'doctor', patient_id, priority=priority, queue_length=len(doctor_resource.queue))
            
            yield req
            assessment_service_start = self.simulation_engine.env.now
            wait_time = assessment_service_start - assessment_start
            
            # Record resource acquisition event
            self.record_resource_event('acquire', 'doctor', patient_id, wait_time=wait_time, priority=priority)
            
            self.simulation_engine.log_with_sim_time(logging.INFO, f"👨‍⚕️ Patient #{patient_num}: Started doctor assessment at {self.simulation_engine.format_sim_time(assessment_service_start)} (Waited: {wait_time:.1f}min)")
        
        # Calculate assessment time using NHS evidence-based ranges
        assessment_time = self.random_service.get_doctor_assessment_time(category)
        self.simulation_engine.log_with_sim_time(logging.INFO, f"⏱️  Patient #{patient_num}: Doctor assessment will take {assessment_time:.1f}min")
        
        yield self.simulation_engine.env.timeout(assessment_time)
        
        assessment_end = self.simulation_engine.env.now
        
        # Record resource release event
        self.record_resource_event('release', 'doctor', patient_id, service_time=assessment_time, priority=priority)
        
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
            yield self.simulation_engine.env.timeout(diagnostics_time)
    
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
                
                yield self.simulation_engine.env.timeout(processing_time)
                
                bed_end = self.simulation_engine.env.now
                self.simulation_engine.log_with_sim_time(logging.INFO, f"✅ Admission processing completed at {self.simulation_engine.format_sim_time(bed_end)} (Total bed process: {bed_end - bed_start:.1f}min)")
        else:
            # Discharge process with NHS evidence-based timing
            disposition = 'discharged'
            processing_time = self.random_service.get_discharge_processing_time()
            
            self.simulation_engine.log_with_sim_time(logging.INFO, f"🚪 Patient being discharged - processing time: {processing_time:.1f}min")
            yield self.simulation_engine.env.timeout(processing_time)
            
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
        
        # Schedule arrivals and monitoring processes
        self.simulation_engine.schedule_arrivals(self.arrivals)
        self.simulation_engine.schedule_monitoring(self.monitor_simulation)
        
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
    

    
    def monitor_simulation(self):
        """Official SimPy monitoring process pattern for real-time tracking.
        
        This follows the SimPy documentation approach for continuous monitoring
        of resource utilization and system state during simulation.
        """
        while True:
            # Use simulation engine's monitoring capabilities
            current_state = self.simulation_engine.collect_monitoring_data()
            
            # Update patient count in the monitoring data
            current_state['patients_processed'] = self.patient_count
            
            # Record system snapshot in operation metrics
            resource_usage = {
                'triage': current_state.get('nurses_usage', 0),
                'doctor': current_state.get('doctors_usage', 0),
                'bed': current_state.get('beds_usage', 0)
            }
            resource_capacity = {
                'triage': self.nurses,
                'doctor': self.doctors,
                'bed': self.beds
            }
            queue_lengths = {
                'triage': current_state.get('nurses_queue', 0),
                'doctor': current_state.get('doctors_queue', 0),
                'bed': current_state.get('beds_queue', 0)
            }
            
            self.operation_metrics.record_system_snapshot(
                timestamp=self.simulation_engine.env.now,
                resource_usage=resource_usage,
                resource_capacity=resource_capacity,
                queue_lengths=queue_lengths,
                entities_processed=self.patient_count
            )
            
            # Get current resource states from simulation engine
            triage_resource = self.simulation_engine.get_resource('nurses')
            doctor_resource = self.simulation_engine.get_resource('doctors')
            bed_resource = self.simulation_engine.get_resource('beds')
            
            # Log current state (following SimPy documentation pattern)
            logger.info(f"Monitor | Time: {self.simulation_engine.env.now:6.1f} | "
                       f"Triage: {triage_resource.count}/{self.nurses} (Q:{len(triage_resource.queue)}) | "
                       f"Doctors: {doctor_resource.count}/{self.doctors} (Q:{len(doctor_resource.queue)}) | "
                       f"Beds: {bed_resource.count}/{self.beds} (Q:{len(bed_resource.queue)}) | "
                       f"Patients: {self.patient_count}")
            
            # Calculate and log utilization rates
            triage_util = (triage_resource.count / self.nurses) * 100
            doctor_util = (doctor_resource.count / self.doctors) * 100
            bed_util = (bed_resource.count / self.beds) * 100
            
            logger.debug(f"Utilization | Triage: {triage_util:.1f}% | "
                        f"Doctors: {doctor_util:.1f}% | Beds: {bed_util:.1f}%")
            
            # Wait before next monitoring cycle (every 5 simulation minutes)
            yield self.simulation_engine.env.timeout(5)
    
    def record_resource_event(self, event_type: str, resource_name: str, patient_id: str = None, **kwargs):
        """Record resource usage events for detailed analysis.
        
        Args:
            event_type: Type of event ('request', 'acquire', 'release')
            resource_name: Name of the resource ('triage', 'doctor', 'bed')
            patient_id: Optional patient identifier
            **kwargs: Additional event data
        """
        # Modern event recording using simulation engine
        event_record = {
            'time': self.simulation_engine.env.now,
            'event_type': event_type,
            'resource': resource_name,
            'patient_id': patient_id,
            **kwargs
        }
        self.simulation_engine.resource_usage_log.append(event_record)
        
        # Record in operation metrics
        self.operation_metrics.record_resource_event(
            event_type=event_type,
            resource_name=resource_name,
            entity_id=patient_id or 'unknown',
            timestamp=self.simulation_engine.env.now,
            **kwargs
        )
        
        # Log significant events
        if event_type in ['acquire', 'release']:
            logger.debug(f"Resource Event | {event_type.upper()} {resource_name} | "
                        f"Patient: {patient_id} | Time: {self.simulation_engine.env.now}")
    
    def get_monitoring_summary(self):
        """Get summary of monitoring data collected during simulation.
        
        Returns:
            Dict containing monitoring statistics and utilization data
        """
        # Use simulation engine's monitoring summary if available
        if hasattr(self, 'simulation_engine'):
            summary = self.simulation_engine.get_monitoring_summary()
            # Map resource names for backward compatibility
            if 'average_utilization' in summary:
                if 'nurses' in summary['average_utilization']:
                    summary['average_utilization']['triage'] = summary['average_utilization']['nurses']
                if 'average_queue_lengths' in summary and 'nurses' in summary['average_queue_lengths']:
                    summary['average_queue_lengths']['triage'] = summary['average_queue_lengths']['nurses']
                if 'peak_utilization' in summary and 'nurses' in summary['peak_utilization']:
                    summary['peak_utilization']['triage'] = summary['peak_utilization']['nurses']
            return summary
        
        # Fallback to legacy implementation
        if not self.monitoring_data:
            return {'error': 'No monitoring data collected'}
        
        # Calculate average utilization rates
        avg_triage_util = sum(d['triage_usage'] / d['triage_capacity'] for d in self.monitoring_data) / len(self.monitoring_data) * 100
        avg_doctor_util = sum(d['doctor_usage'] / d['doctor_capacity'] for d in self.monitoring_data) / len(self.monitoring_data) * 100
        avg_bed_util = sum(d['bed_usage'] / d['bed_capacity'] for d in self.monitoring_data) / len(self.monitoring_data) * 100
        
        # Calculate average queue lengths
        avg_triage_queue = sum(d['triage_queue'] for d in self.monitoring_data) / len(self.monitoring_data)
        avg_doctor_queue = sum(d['doctor_queue'] for d in self.monitoring_data) / len(self.monitoring_data)
        avg_bed_queue = sum(d['bed_queue'] for d in self.monitoring_data) / len(self.monitoring_data)
        
        return {
            'monitoring_points': len(self.monitoring_data),
            'simulation_duration': self.monitoring_data[-1]['time'] if self.monitoring_data else 0,
            'average_utilization': {
                'triage': avg_triage_util,
                'doctors': avg_doctor_util,
                'beds': avg_bed_util
            },
            'average_queue_lengths': {
                'triage': avg_triage_queue,
                'doctors': avg_doctor_queue,
                'beds': avg_bed_queue
            },
            'peak_utilization': {
                'triage': max(d['triage_usage'] / d['triage_capacity'] for d in self.monitoring_data) * 100,
                'doctors': max(d['doctor_usage'] / d['doctor_capacity'] for d in self.monitoring_data) * 100,
                'beds': max(d['bed_usage'] / d['bed_capacity'] for d in self.monitoring_data) * 100
            },
            'total_resource_events': len(self.resource_usage_log)
        }
    
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