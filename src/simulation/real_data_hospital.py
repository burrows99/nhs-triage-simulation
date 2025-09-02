import simpy
import numpy as np
import random
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import sys
import os

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
    SymptomKeys, MedicalConditions, CommonStrings, DiagnosticTestTypes, SymptomNames
)


class SimpleHospital:
    """Simple hospital simulation with Poisson arrivals and real patient data."""
    
    def __init__(self, csv_folder='./output/csv', **kwargs):
        """Initialize hospital simulation with all required services and data.
        
        Args:
            csv_folder: Path to CSV data files
            **kwargs: Simulation parameters (sim_duration, arrival_rate, etc.)
        """
        self._setup_simulation_parameters(**kwargs)
        self._load_patient_data(csv_folder)
        self._initialize_services(**kwargs)
        
        # Simulation state
        self.env = None
    
    def _setup_simulation_parameters(self, **kwargs):
        """Setup simulation parameters with defaults."""
        self.sim_duration = kwargs.get('sim_duration', 1440)  # 24 hours
        self.arrival_rate = kwargs.get('arrival_rate', 10)    # patients/hour
        self.nurses = kwargs.get('nurses', 2)
        self.doctors = kwargs.get('doctors', 6)
        self.beds = kwargs.get('beds', 15)
    
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
        """Perform triage using paper-based Manchester Triage System approach with real patient data."""
        # Paper-based approach: Nurse selects appropriate flowchart based on patient presentation
        # FMTS paper: "decision aid system for the ER nurses to properly categorize patients based on their symptoms"
        
        if patient_data is None:
            raise ValueError("Patient data is required for triage. Cannot perform triage without real patient information.")
        
        # Use real patient data for triage
        # Map chief complaint to appropriate flowchart
        flowchart_reason = self._map_complaint_to_flowchart(patient_data.get('presenting_complaint', ''))
        
        # Use real patient symptoms from the processed data
        raw_symptoms = patient_data.get('symptoms', {})
        
        # Convert real patient symptoms to MTS format
        symptoms_input = self._convert_symptoms_to_mts_format(raw_symptoms, flowchart_reason)
        
        # Ensure we have real patient symptoms - no random fallback
        if not symptoms_input:
            raise ValueError(f"No real patient symptoms available for flowchart '{flowchart_reason}'. Patient ID: {patient_data.get('patient_id', 'Unknown')}")
        
        # Use MTS directly with patient-based inputs
        result = self.mts.triage_patient(flowchart_reason, symptoms_input)
        
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
        return category, priority, result
    
    def _map_complaint_to_flowchart(self, chief_complaint: str) -> str:
        """Map chief complaint to appropriate MTS flowchart.
        
        Args:
            chief_complaint: Patient's presenting complaint
            
        Returns:
            Appropriate flowchart identifier for the complaint
        """
        if not chief_complaint:
            return TriageFlowcharts.CHEST_PAIN.value  # Default to most common presentation
        
        complaint_lower = chief_complaint.lower()
        
        # Map common complaints to flowcharts
        complaint_mapping = {
            'chest pain': TriageFlowcharts.CHEST_PAIN.value,
            'chest': TriageFlowcharts.CHEST_PAIN.value,
            'cardiac': TriageFlowcharts.CHEST_PAIN.value,
            'heart': TriageFlowcharts.CHEST_PAIN.value,
            'shortness of breath': TriageFlowcharts.SHORTNESS_OF_BREATH.value,
            'breathing': TriageFlowcharts.SHORTNESS_OF_BREATH.value,
            'breathless': TriageFlowcharts.SHORTNESS_OF_BREATH.value,
            'respiratory': TriageFlowcharts.SHORTNESS_OF_BREATH.value,
            'asthma': TriageFlowcharts.ASTHMA.value,
            'abdominal pain': TriageFlowcharts.ABDOMINAL_PAIN.value,
            'abdominal': TriageFlowcharts.ABDOMINAL_PAIN.value,
            'stomach': TriageFlowcharts.ABDOMINAL_PAIN.value,
            'appendicitis': TriageFlowcharts.ABDOMINAL_PAIN.value,
            'headache': TriageFlowcharts.HEADACHE.value,
            'head': TriageFlowcharts.HEADACHE.value,
            'migraine': TriageFlowcharts.HEADACHE.value,
            'neurological': TriageFlowcharts.HEADACHE.value,
            'nausea': TriageFlowcharts.VOMITING.value,
            'vomiting': TriageFlowcharts.VOMITING.value,
            'injury': TriageFlowcharts.LIMB_INJURIES.value,
            'trauma': TriageFlowcharts.LIMB_INJURIES.value,
            'fracture': TriageFlowcharts.LIMB_INJURIES.value,
            'wound': TriageFlowcharts.WOUNDS.value,
            'cut': TriageFlowcharts.WOUNDS.value,
            'burn': TriageFlowcharts.BURNS.value,
            'stroke': TriageFlowcharts.STROKE.value,
            'seizure': TriageFlowcharts.FITS.value,
            'confusion': TriageFlowcharts.CONFUSION.value,
            'unconscious': TriageFlowcharts.UNCONSCIOUS_ADULT.value,
            'fever': TriageFlowcharts.CHILD_FEVER.value,
            'infection': TriageFlowcharts.CHILD_FEVER.value
        }
        
        # Find matching flowchart
        for keyword, flowchart in complaint_mapping.items():
            if keyword in complaint_lower:
                return flowchart
        
        # Default to chest pain if no match found (most common presentation)
        return TriageFlowcharts.CHEST_PAIN.value
    
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
        
        # Setup patient and record arrival
        patient_data, patient_id, age, gender, presenting_complaint = self._setup_patient_arrival(arrival_time)
        
        # Perform triage and get category/priority
        category, priority, mts_result = self.perform_triage(patient_data)
        self.nhs_metrics.record_triage_category(patient_id, category)
        
        # Triage nurse stage
        yield from self._process_triage_stage(patient_id, category, mts_result)
        
        # Doctor assessment stage
        yield from self._process_doctor_assessment(patient_id, category, priority, mts_result)
        
        # Diagnostics stage (optional)
        yield from self._process_diagnostics(category)
        
        # Disposition stage
        disposition, admitted = yield from self._process_disposition(category, priority)
        
        # Complete patient journey
        self._complete_patient_journey(patient_id, arrival_time, disposition, admitted, 
                                     category, age, gender)
    
    def _setup_patient_arrival(self, arrival_time):
        """Setup patient data and record arrival metrics."""
        patient_data = self.get_patient()
        patient_id = patient_data['patient_id']
        age = patient_data['age']
        gender = patient_data['gender']
        presenting_complaint = patient_data['presenting_complaint']
        
        # Record patient arrival in NHS metrics
        self.nhs_metrics.add_patient_arrival(
            patient_id=patient_id,
            arrival_time=arrival_time,
            age=age,
            gender=gender,
            presenting_complaint=presenting_complaint
        )
        
        return patient_data, patient_id, age, gender, presenting_complaint
    
    def _process_triage_stage(self, patient_id, category, mts_result):
        """Process triage nurse assessment stage."""
        triage_start = self.env.now
        self.nhs_metrics.record_initial_assessment(patient_id, triage_start)
        
        with self.triage_resource.request() as req:
            yield req
            triage_service_start = self.env.now
            
            # Calculate triage time using MTS or fallback
            triage_time = self._calculate_triage_time(category, mts_result)
            yield self.env.timeout(triage_time)
    
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
        
        with self.doctor_resource.request(priority=priority) as req:
            yield req
            assessment_service_start = self.env.now
            
            # Calculate assessment time using MTS or fallback
            assessment_time = self._calculate_assessment_time(category, mts_result)
            yield self.env.timeout(assessment_time)
    
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
            
            # Bed allocation process
            bed_start = self.env.now
            with self.bed_resource.request(priority=priority) as req:
                yield req
                bed_service_start = self.env.now
                yield self.env.timeout(processing_time)
        else:
            # Discharge process with NHS evidence-based timing
            disposition = 'discharged'
            processing_time = self.random_service.get_discharge_processing_time()
            yield self.env.timeout(processing_time)
        
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
        
        # Log patient completion
        print(f"Patient {patient_id} ({category}, Age: {age}, {gender}): "
              f"{total_time:.1f} min, {disposition}")
    
    def arrivals(self):
        """Generate Poisson arrivals."""
        patient_num = 0
        while True:
            # Poisson process: exponential interarrival times
            interarrival = self.random_service.get_patient_arrival_interval(self.arrival_rate)
            yield self.env.timeout(interarrival)
            patient_num += 1
            self.env.process(self.patient_flow(patient_num))
    
    def run(self):
        """Run simulation with NHS metrics tracking."""
        print(f"Starting {self.sim_duration/60:.1f}h simulation with {self.arrival_rate} patients/hour...")
        
        # Initialize simple counters
        self.patient_count = 0
        self.total_time = 0
        self.categories = []
        
        # Setup simulation
        self.env = simpy.Environment()
        self.triage_resource = simpy.Resource(self.env, capacity=self.nurses)
        self.doctor_resource = simpy.PriorityResource(self.env, capacity=self.doctors)
        self.bed_resource = simpy.PriorityResource(self.env, capacity=self.beds)
        
        # Start arrivals
        self.env.process(self.arrivals())
        
        # Run simulation
        self.env.run(until=self.sim_duration)
        
        # Calculate simple results
        avg_time = self.total_time / self.patient_count if self.patient_count > 0 else 0
        
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