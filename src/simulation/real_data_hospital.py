import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import sys
import os
import logging
import random

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.logger import logger

from src.services.data_service import DataService
from src.services.nhs_metrics import NHSMetrics
from src.services.operation_metrics import OperationMetrics
from src.services.plotting_service import PlottingService
from src.services.random_service import RandomService
from src.triage.manchester_triage_system import ManchesterTriageSystem
from src.triage.llm_triage_system.llm_triage_system import LLMTriageSystem
from .simulation_engine import SimulationEngine
from src.triage.triage_constants import (
    TriageFlowcharts, FlowchartSymptomMapping, TriageCategories,
    SymptomKeys, MedicalConditions, CommonStrings, DiagnosticTestTypes, SymptomNames,
    ComplaintToFlowchartMapping
)


class SimpleHospital:
    """Simple hospital simulation with Poisson arrivals and real patient data."""
    
    def __init__(self, csv_folder='./output/csv', output_dir='./output/hospital_simulation', 
                 triage_system=None, **kwargs):
        logger.info(f"🏥 Initializing Hospital Simulation...")
        logger.info(f"📁 CSV folder: {csv_folder}")
        logger.info(f"📂 Output directory: {output_dir}")
        logger.info(f"🩺 Triage system: {type(triage_system).__name__ if triage_system else 'None'}")
        """Initialize hospital simulation with all required services and data.
        
        Args:
            csv_folder: Path to CSV data files
            output_dir: Directory for simulation outputs (metrics, plots, etc.)
            triage_system: Triage system instance (required - no string support)
            **kwargs: Simulation parameters (sim_duration, arrival_rate, etc.)
        
        Raises:
            ValueError: If triage_system is None or not a valid triage system object
        """

        if not isinstance(triage_system, (ManchesterTriageSystem, LLMTriageSystem)):
            raise ValueError("triage_system parameter must be an instance of ManchesterTriageSystem or LLMTriageSystem. Please provide a valid triage system object.")
        
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
        logger.info(f"📊 Loading patient data from {csv_folder}...")
        logger.info(f"📁 Checking if CSV folder exists: {os.path.exists(csv_folder)}")
        
        if os.path.exists(csv_folder):
            csv_files = [f for f in os.listdir(csv_folder) if f.endswith('.csv')]
            logger.info(f"📄 Found {len(csv_files)} CSV files: {csv_files}")
        else:
            logger.error(f"❌ CSV folder does not exist: {csv_folder}")
        
        self.data_service = DataService(csv_folder)
        self.patients = self.data_service.get_all_patients(deep=True)
        self.current_index = 0
        
        logger.info(f"✅ Loaded {len(self.patients)} patients with full relationships")
        if len(self.patients) == 0:
            logger.error(f"⚠️  WARNING: No patients loaded! Simulation will not run properly.")
        else:
            logger.info(f"👥 First patient ID: {self.patients[0].Id if self.patients else 'None'}")
            logger.info(f"👥 Sample patient data: {type(self.patients[0]).__name__ if self.patients else 'None'}")
    
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
        logger.info(f"🔍 GET_PATIENT CALLED - Retrieving patient...")
        logger.info(f"📊 Total patients available: {len(self.patients) if self.patients else 0}")
        logger.info(f"📍 Current index: {self.current_index}")
        
        if not self.patients:
            logger.error(f"❌ No patients available! Returning None.")
            return None
        
        # Return Synthea patient model (already fully populated with relationships)
        synthea_patient = self.patients[self.current_index]
        logger.info(f"✅ Retrieved patient: ID={synthea_patient.Id}, Index={self.current_index}")
        
        self.current_index = (self.current_index + 1) % len(self.patients)
        logger.info(f"📍 Updated index to: {self.current_index}")
        
        return synthea_patient

    def _generate_manual_test_symptoms(self, patient, flowchart_reason: str) -> Dict[str, str]:
        """Generate clinically accurate symptoms using actual MTS flowchart mappings.
        
        Acts as a virtual triage nurse with clinical knowledge, using the actual
        Manchester Triage System flowchart symptoms and linguistic values.
        
        Args:
            patient: Synthea patient object
            flowchart_reason: MTS flowchart identifier
            
        Returns:
            Dictionary of symptom_name -> linguistic_value for MTS
        """
        from src.triage.triage_constants import (
            LinguisticValues, FlowchartSymptomMapping, SymptomKeys,
            TriageFlowcharts, SymptomNames
        )
        
        # Extract patient context for clinical assessment
        age = self._calculate_age_from_birthdate(patient.BIRTHDATE)
        complaint = self._extract_presenting_complaint(patient)
        encounter_type = complaint.lower()
        
        # Get actual flowchart symptoms from MTS constants
        flowchart_symptoms = FlowchartSymptomMapping.get_symptoms_for_flowchart(flowchart_reason)
        
        # Clinical severity distribution based on ED statistics
        # Adjusted for more realistic emergency department presentations
        severity_weights = {
            LinguisticValues.NONE: 0.25,        # 25% - No significant symptoms
            LinguisticValues.MILD: 0.35,        # 35% - Minor presentations
            LinguisticValues.MODERATE: 0.25,    # 25% - Standard cases
            LinguisticValues.SEVERE: 0.12,      # 12% - Urgent cases
            LinguisticValues.VERY_SEVERE: 0.03  # 3% - Critical cases
        }
        
        # Special severity weights for high-acuity encounters
        if any(keyword in encounter_type for keyword in ['emergency', 'urgent', 'acute', 'severe', 'critical']):
            severity_weights = {
                LinguisticValues.NONE: 0.10,
                LinguisticValues.MILD: 0.20,
                LinguisticValues.MODERATE: 0.35,
                LinguisticValues.SEVERE: 0.25,
                LinguisticValues.VERY_SEVERE: 0.10
            }
        
        def clinical_severity_assessment(symptom_key: str) -> str:
            """Clinical severity assessment based on symptom type and patient context."""
            # Base severity selection
            rand = random.random()
            cumulative = 0
            for severity, weight in severity_weights.items():
                cumulative += weight
                if rand <= cumulative:
                    base_severity = severity
                    break
            else:
                base_severity = LinguisticValues.MILD
            
            # Clinical modifications based on symptom type
            if symptom_key in [SymptomKeys.CONSCIOUSNESS, 'consciousness_level']:
                # Consciousness levels use specific values
                consciousness_levels = LinguisticValues.get_consciousness_levels()
                if base_severity == LinguisticValues.NONE:
                    return LinguisticValues.ALERT
                elif base_severity in [LinguisticValues.MILD, LinguisticValues.MODERATE]:
                    return random.choice([LinguisticValues.ALERT, LinguisticValues.CONFUSED])
                elif base_severity == LinguisticValues.SEVERE:
                    return random.choice([LinguisticValues.CONFUSED, LinguisticValues.DROWSY])
                else:  # VERY_SEVERE
                    return random.choice([LinguisticValues.DROWSY, LinguisticValues.UNCONSCIOUS])
            
            elif symptom_key == SymptomKeys.TEMPERATURE or 'temperature' in symptom_key:
                # Temperature levels use specific values
                if base_severity == LinguisticValues.NONE:
                    return LinguisticValues.NORMAL
                elif base_severity == LinguisticValues.MILD:
                    return random.choice([LinguisticValues.NORMAL, LinguisticValues.ELEVATED])
                elif base_severity == LinguisticValues.MODERATE:
                    return LinguisticValues.ELEVATED
                elif base_severity == LinguisticValues.SEVERE:
                    return LinguisticValues.HIGH
                else:  # VERY_SEVERE
                    return LinguisticValues.VERY_HIGH
            
            # For pain and other severity-based symptoms, return as-is
            return base_severity
        
        # Generate symptoms using actual MTS flowchart mappings
        symptoms = {}
        
        # Use actual flowchart symptoms if available
        if flowchart_symptoms:
            for symptom_key, possible_values in flowchart_symptoms.items():
                symptoms[symptom_key] = clinical_severity_assessment(symptom_key)
        else:
            # Fallback to common symptoms if flowchart not found
            logger.warning(f"Flowchart '{flowchart_reason}' not found in mappings, using common symptoms")
            common_symptoms = {
                SymptomKeys.PAIN_LEVEL: clinical_severity_assessment(SymptomKeys.PAIN_LEVEL),
                SymptomKeys.CONSCIOUSNESS: clinical_severity_assessment(SymptomKeys.CONSCIOUSNESS),
                SymptomKeys.TEMPERATURE: clinical_severity_assessment(SymptomKeys.TEMPERATURE)
            }
            symptoms.update(common_symptoms)
        
        # Clinical modifications based on patient demographics
        self._apply_demographic_clinical_adjustments(symptoms, age, encounter_type)
        
        # Clinical pattern recognition - adjust symptom combinations
        self._apply_clinical_pattern_adjustments(symptoms, flowchart_reason, encounter_type)
        
        # Ensure clinical validity - no patient presents with all 'none' symptoms
        self._ensure_clinical_validity(symptoms)
        
        # Clinical logging for triage documentation
        self._log_clinical_assessment(flowchart_reason, symptoms, age, encounter_type)
        
        return symptoms
    
    def _apply_demographic_clinical_adjustments(self, symptoms: Dict[str, str], age: int, encounter_type: str):
        """Apply clinical adjustments based on patient demographics."""
        from src.triage.triage_constants import LinguisticValues
        
        # Elderly patients (65+) - increased severity due to frailty
        if age >= 65:
            for symptom_key, severity in symptoms.items():
                if severity == LinguisticValues.MILD and random.random() < 0.25:
                    symptoms[symptom_key] = LinguisticValues.MODERATE
                elif severity == LinguisticValues.MODERATE and random.random() < 0.15:
                    symptoms[symptom_key] = LinguisticValues.SEVERE
        
        # Pediatric patients (≤5) - rapid deterioration risk
        elif age <= 5:
            if random.random() < 0.15:  # 15% chance of escalation
                # Escalate the most severe symptom
                max_severity_symptom = max(symptoms.items(), 
                                         key=lambda x: LinguisticValues.get_numeric_mapping().get(x[1], 0))
                if max_severity_symptom[1] in [LinguisticValues.MILD, LinguisticValues.MODERATE]:
                    symptoms[max_severity_symptom[0]] = LinguisticValues.SEVERE
        
        # Young adults (18-30) - typically more resilient
        elif 18 <= age <= 30:
            for symptom_key, severity in symptoms.items():
                if severity == LinguisticValues.SEVERE and random.random() < 0.10:
                    symptoms[symptom_key] = LinguisticValues.MODERATE
    
    def _apply_clinical_pattern_adjustments(self, symptoms: Dict[str, str], flowchart_reason: str, encounter_type: str):
        """Apply clinical pattern recognition adjustments."""
        from src.triage.triage_constants import LinguisticValues, SymptomKeys
        
        # Chest pain patterns - cardiac vs non-cardiac
        if flowchart_reason == 'chest_pain':
            # Classic cardiac presentation pattern
            if (symptoms.get(SymptomKeys.PAIN_LEVEL) in [LinguisticValues.SEVERE, LinguisticValues.VERY_SEVERE] and
                random.random() < 0.3):  # 30% chance of classic presentation
                symptoms[SymptomKeys.CRUSHING_SENSATION] = random.choice([LinguisticValues.MODERATE, LinguisticValues.SEVERE])
                symptoms[SymptomKeys.RADIATION] = random.choice([LinguisticValues.MILD, LinguisticValues.MODERATE])
                symptoms[SymptomKeys.SWEATING] = random.choice([LinguisticValues.MODERATE, LinguisticValues.SEVERE])
        
        # Respiratory distress patterns
        elif flowchart_reason == 'shortness_of_breath':
            # Severe respiratory distress pattern
            if symptoms.get(SymptomKeys.BREATHING_DIFFICULTY) == LinguisticValues.VERY_SEVERE:
                symptoms[SymptomKeys.CONSCIOUSNESS] = random.choice([LinguisticValues.CONFUSED, LinguisticValues.DROWSY])
                if SymptomKeys.CYANOSIS in symptoms:
                    symptoms[SymptomKeys.CYANOSIS] = random.choice([LinguisticValues.MODERATE, LinguisticValues.SEVERE])
        
        # Neurological emergency patterns
        elif flowchart_reason == 'headache':
            # Meningitis/SAH pattern
            if (symptoms.get(SymptomKeys.PAIN_LEVEL) == LinguisticValues.VERY_SEVERE and
                random.random() < 0.2):  # 20% chance of serious headache
                symptoms[SymptomKeys.TEMPERATURE] = random.choice([LinguisticValues.HIGH, LinguisticValues.VERY_HIGH])
                symptoms[SymptomKeys.CONSCIOUSNESS] = random.choice([LinguisticValues.CONFUSED, LinguisticValues.DROWSY])
        
        # Trauma patterns
        elif flowchart_reason == 'limb_injuries':
            # Significant trauma pattern
            if symptoms.get(SymptomKeys.PAIN_LEVEL) in [LinguisticValues.SEVERE, LinguisticValues.VERY_SEVERE]:
                if random.random() < 0.4:  # 40% chance of associated findings
                    symptoms[SymptomKeys.DEFORMITY] = random.choice([LinguisticValues.MODERATE, LinguisticValues.SEVERE])
                    symptoms[SymptomKeys.BLEEDING] = random.choice([LinguisticValues.MILD, LinguisticValues.MODERATE])
    
    def _ensure_clinical_validity(self, symptoms: Dict[str, str]):
        """Ensure clinical validity - no completely asymptomatic patients in ED."""
        from src.triage.triage_constants import LinguisticValues
        
        # Check if all symptoms are 'none' or equivalent
        non_none_symptoms = [s for s in symptoms.values() 
                           if s not in [LinguisticValues.NONE, LinguisticValues.NORMAL, LinguisticValues.ALERT]]
        
        if not non_none_symptoms:
            # Ensure at least one presenting symptom
            primary_symptom = list(symptoms.keys())[0]
            symptoms[primary_symptom] = LinguisticValues.MILD
            logger.debug(f"Clinical validity: Ensured presenting symptom {primary_symptom} = {LinguisticValues.MILD}")
    
    def _log_clinical_assessment(self, flowchart_reason: str, symptoms: Dict[str, str], age: int, encounter_type: str):
        """Log clinical assessment for triage documentation."""
        from src.triage.triage_constants import LinguisticValues
        
        # Calculate clinical severity score
        severity_score = sum(LinguisticValues.get_numeric_mapping().get(severity, 0) 
                           for severity in symptoms.values())
        
        # Count symptoms by severity
        severity_counts = {}
        for severity in symptoms.values():
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Clinical documentation
        logger.debug(f"CLINICAL ASSESSMENT | Flowchart: {flowchart_reason} | Age: {age} | Encounter: {encounter_type}")
        logger.debug(f"SYMPTOMS ASSESSED | {dict(symptoms)}")
        logger.debug(f"SEVERITY PROFILE | {dict(severity_counts)} | Total Score: {severity_score:.1f}")
        
        # Flag high-acuity cases for clinical review
        high_severity_count = severity_counts.get(LinguisticValues.SEVERE, 0) + severity_counts.get(LinguisticValues.VERY_SEVERE, 0)
        if high_severity_count >= 2:
            logger.info(f"HIGH ACUITY CASE | Patient Age {age} | {high_severity_count} severe symptoms | Flowchart: {flowchart_reason}")

    def perform_triage(self, patient=None):
        """Perform triage using paper-based Manchester Triage System approach with real patient data.
        
        Returns:
            tuple: (category, priority, triage_result, processing_delay_seconds)
        
        Note: This method now measures and returns the actual processing time for 
        integration with SimPy's discrete event simulation.
        """
        logger.info(f"🩺 PERFORM_TRIAGE CALLED - Starting triage assessment...")
        logger.info(f"👤 Patient ID: {patient.Id if patient else 'None'}")
        logger.info(f"🔧 Triage system type: {type(self.triage_system).__name__}")
        
        # Paper-based approach: Nurse selects appropriate flowchart based on patient presentation
        # FMTS paper: "decision aid system for the ER nurses to properly categorize patients based on their symptoms"
        
        if patient is None:
            logger.error(f"❌ No patient provided for triage!")
            raise ValueError("Patient object is required for triage. Cannot perform triage without real patient information.")
        
        # Measure actual triage processing time
        import time
        triage_start_time = time.time()
        logger.info(f"⏱️  Triage processing started at {triage_start_time}")
        
        # Use real patient data for triage
        # Map chief complaint to appropriate flowchart
        flowchart_reason = ComplaintToFlowchartMapping.get_flowchart_for_complaint(self._extract_presenting_complaint(patient))
        
        # Extract symptoms from patient observations using patient method
        raw_symptoms = patient.extract_symptoms_from_observations()
        
        # OPTION 3: Generate manual symptoms for comprehensive MTS testing
        # This creates diverse symptom combinations to test all triage categories
        symptoms_input = self._generate_manual_test_symptoms(patient, flowchart_reason)
        
        # Use triage system with patient-based inputs
        # Handle different triage system interfaces
        from src.triage.llm_triage_system.llm_triage_system import LLMTriageSystem
        
        if isinstance(self.triage_system, LLMTriageSystem):
            # LLM triage system expects symptoms as a string
            logger.info(f"🤖 Using LLM Triage System for patient {patient.Id}")
            complaint = self._extract_presenting_complaint(patient)
            symptoms_text = f"Patient presents with {complaint}. "
            
            # Convert symptoms dictionary to descriptive text
            symptom_descriptions = []
            for symptom_name, severity in symptoms_input.items():
                if severity != 'none':
                    symptom_descriptions.append(f"{symptom_name}: {severity}")
            
            if symptom_descriptions:
                symptoms_text += "Symptoms include: " + ", ".join(symptom_descriptions)
            
            logger.info(f"📝 Sending to LLM: '{symptoms_text[:100]}{'...' if len(symptoms_text) > 100 else ''}'")
            logger.info(f"🔄 Calling triage_system.triage_patient()...")
            
            result = self.triage_system.triage_patient(symptoms_text)
            
            logger.info(f"✅ LLM triage completed. Result: {result}")
        else:
            # Manchester Triage System expects structured inputs
            result = self.triage_system.triage_patient(
                flowchart_reason=flowchart_reason,
                symptoms_input=symptoms_input,
                patient_id=patient.Id
            )
        
        # Calculate processing delay
        triage_end_time = time.time()
        processing_delay = triage_end_time - triage_start_time
        
        # Handle triage result based on system type
        from src.models.triage_result import TriageResult
        
        if isinstance(self.triage_system, LLMTriageSystem):
            # LLM system already returns TriageResult object
            triage_result = result
        else:
            # MTS system returns dictionary, convert to TriageResult
            triage_result = TriageResult.from_raw_result(result, "MTS")
        
        # Extract core values for backward compatibility
        category = triage_result.triage_category
        priority = triage_result.priority_score
        
        # Return standardized result
        return category, priority, triage_result, processing_delay
    
    def patient_flow(self, patient_num):
        """Simulate patient journey with NHS metrics tracking."""
        arrival_time = self.simulation_engine.env.now
        
        self.simulation_engine.log_with_sim_time(logging.INFO, f"🚶 Patient #{patient_num} arrived")
        
        patient = self._setup_patient_arrival(arrival_time)
        
        self.simulation_engine.log_with_sim_time(logging.DEBUG, f"👤 Patient #{patient_num}: Age {self._calculate_age_from_birthdate(patient.BIRTHDATE)}, {patient.GENDER}, Complaint: '{self._extract_presenting_complaint(patient)}'")
        
        self.simulation_engine.log_with_sim_time(logging.DEBUG, f"👩‍⚕️ Patient #{patient_num}: Entering triage assessment")
        category, priority, triage_result = yield from self._process_triage_stage(patient.Id, patient, patient_num)
        
        self.nhs_metrics.record_triage_category(patient, category)
        self.simulation_engine.log_with_sim_time(logging.INFO, f"🏷️ Patient #{patient_num}: {category} (P{priority})")
        
        self.simulation_engine.log_with_sim_time(logging.DEBUG, f"👨‍⚕️ Patient #{patient_num}: Entering doctor assessment")
        yield from self._process_doctor_assessment(patient, category, priority, triage_result, patient_num)
        
        diagnostics_start = self.simulation_engine.env.now
        self.simulation_engine.log_with_sim_time(logging.DEBUG, f"🔬 Patient #{patient_num}: Checking diagnostics")
        yield from self._process_diagnostics(triage_result)
        
        if self.simulation_engine.env.now > diagnostics_start:
            self.simulation_engine.log_with_sim_time(logging.DEBUG, f"🧪 Patient #{patient_num}: Diagnostics completed ({self.simulation_engine.env.now - diagnostics_start:.1f}min)")
        else:
            self.simulation_engine.log_with_sim_time(logging.DEBUG, f"⏭️ Patient #{patient_num}: No diagnostics required")
        
        disposition_start = self.simulation_engine.env.now
        self.simulation_engine.log_with_sim_time(logging.DEBUG, f"📋 Patient #{patient_num}: Starting disposition")
        disposition, admitted = yield from self._process_disposition(triage_result)
        
        self.simulation_engine.log_with_sim_time(logging.INFO, f"🏥 Patient #{patient_num}: Disposition decided - {disposition.upper()} at {self.simulation_engine.format_sim_time(self.simulation_engine.env.now)}")
        
        # Complete patient journey - NHS metrics updated through direct metric recording
        # (Synthea Patient models don't have record_departure method)
        
        self._complete_patient_journey(patient.Id, arrival_time, disposition, admitted, 
                                     category, self._calculate_age_from_birthdate(patient.BIRTHDATE), patient.GENDER, patient_num)
    
    def _setup_patient_arrival(self, arrival_time):
        """Setup patient data and record arrival metrics."""
        patient = self.get_patient()
        
        # Record patient arrival in NHS metrics using Synthea patient object
        self.nhs_metrics.add_patient_arrival(patient, arrival_time)
        
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
        # Record initial assessment (Synthea models don't have record_initial_assessment method)
        # Assessment timing is tracked in NHS metrics instead
        self.nhs_metrics.record_initial_assessment(patient, triage_start)
        
        triage_resource = self.simulation_engine.get_resource('nurses')
        if len(triage_resource.queue) > 5:  # Only log if significant queue
            self.simulation_engine.log_with_sim_time(logging.INFO, f"⏳ Patient #{patient_num}: Queue: {len(triage_resource.queue)} waiting")
        else:
            self.simulation_engine.log_with_sim_time(logging.DEBUG, f"⏳ Patient #{patient_num}: Waiting for triage (Queue: {len(triage_resource.queue)})")
        
        # Triage system resource updates removed (HospitalResources class not available)
        
        with triage_resource.request() as req:
            # Record resource request event
            self.simulation_engine.record_resource_event(
                'request', 'triage', patient_id, self._record_hospital_event, 
                queue_length=len(triage_resource.queue))
            
            yield req
            resource_acquired_time = self.simulation_engine.env.now
            queue_wait_time = resource_acquired_time - triage_start
            
            # Add realistic triage setup delay even when nurse is immediately available
            triage_setup_delay = self.random_service.get_resource_allocation_delay('triage')
            yield from self.simulation_engine.enhanced_yield_with_monitoring(
                triage_setup_delay, "triage setup", self._capture_monitoring_snapshot)
            
            triage_service_start = self.simulation_engine.env.now
            total_wait_time = triage_service_start - triage_start
            
            # Record resource acquisition event with total wait time
            self.simulation_engine.record_resource_event(
                'acquire', 'triage', patient_id, self._record_hospital_event, wait_time=total_wait_time)
            
            # Capture monitoring snapshot right after triage resource acquisition
            self._capture_monitoring_snapshot("triage resource acquired")
            
            if queue_wait_time > 0.1:
                self.simulation_engine.log_with_sim_time(logging.INFO, f"👩‍⚕️ Patient #{patient_num}: Started triage assessment at {self.simulation_engine.format_sim_time(triage_service_start)} (Queue wait: {queue_wait_time:.1f}min + Setup: {triage_setup_delay:.1f}min = Total: {total_wait_time:.1f}min)")
            else:
                self.simulation_engine.log_with_sim_time(logging.INFO, f"👩‍⚕️ Patient #{patient_num}: Started triage assessment at {self.simulation_engine.format_sim_time(triage_service_start)} (Setup delay: {triage_setup_delay:.1f}min)")
            
            # Perform triage assessment during nurse consultation
            self.simulation_engine.log_with_sim_time(logging.INFO, f"🔍 Patient #{patient_num}: Nurse performing triage assessment")
            category, priority, triage_result, processing_delay_seconds = self.perform_triage(patient)
            
            # Apply processing delay and calculate total triage time
            triage_processing_delay = self._scale_delay(processing_delay_seconds, delay_type='triage')
            
            # Use triage result wait_time data for more accurate triage timing
            # TriageResult provides standardized wait_time access
            wait_minutes = triage_result.get_wait_time_minutes()
            
            # Convert MTS wait time to actual triage processing time (much shorter than wait time)
            # Triage processing is typically 3-15 minutes regardless of final wait time
            if category in [TriageCategories.RED]:
                base_triage_time = self.random_service.get_triage_process_time("complex")
            elif category in [TriageCategories.ORANGE, TriageCategories.YELLOW]:
                base_triage_time = self.random_service.get_triage_process_time("standard")
            else:
                base_triage_time = self.random_service.get_triage_process_time("simple")
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
        self.nhs_metrics.record_treatment_start(patient, assessment_start)
        
        # Acquire doctor resource
        yield from self._acquire_doctor_resource(patient, triage_result, patient_num, assessment_start)
        
        # Calculate and perform assessment
        assessment_time = self._calculate_assessment_time(triage_result)
        self.simulation_engine.log_with_sim_time(logging.INFO, f"⏱️  Patient #{patient_num}: Doctor assessment will take {assessment_time:.1f}min")
        
        yield from self._perform_doctor_assessment(assessment_time, patient, triage_result, patient_num, assessment_start)
    
    def _acquire_doctor_resource(self, patient, triage_result, patient_num, assessment_start):
        """Acquire doctor resource with proper logging and delays."""
        doctor_resource = self.simulation_engine.get_resource('doctors')
        priority = triage_result.priority_score
        self.simulation_engine.log_with_sim_time(logging.INFO, f"⏳ Patient #{patient_num}: Waiting for doctor at {self.simulation_engine.format_sim_time(assessment_start)} (Priority: {priority}, Queue: {len(doctor_resource.queue)} waiting)")
        
        with doctor_resource.request(priority=priority) as req:
            self.simulation_engine.record_resource_event(
                'request', 'doctor', patient.Id, self._record_hospital_event, 
                priority=priority, queue_length=len(doctor_resource.queue))
            
            yield req
            yield from self._handle_doctor_handover(patient, triage_result, patient_num, assessment_start)
    
    def _handle_doctor_handover(self, patient, triage_result, patient_num, assessment_start):
        """Handle doctor handover process with delays and logging."""
        resource_acquired_time = self.simulation_engine.env.now
        queue_wait_time = resource_acquired_time - assessment_start
        
        # Add realistic handover delay
        handover_delay = self.random_service.get_handover_delay('doctor', triage_result)
        yield from self.simulation_engine.enhanced_yield_with_monitoring(
            handover_delay, "doctor handover", self._capture_monitoring_snapshot)
        
        assessment_service_start = self.simulation_engine.env.now
        total_wait_time = assessment_service_start - assessment_start
        priority = triage_result.priority_score
        
        self.simulation_engine.record_resource_event(
            'acquire', 'doctor', patient.Id, self._record_hospital_event, 
            wait_time=total_wait_time, priority=priority)
        
        self._capture_monitoring_snapshot("doctor resource acquired")
        self._log_doctor_start(patient_num, assessment_service_start, queue_wait_time, handover_delay, total_wait_time)
    
    def _log_doctor_start(self, patient_num, start_time, queue_wait, handover_delay, total_wait):
        """Log doctor assessment start with appropriate detail level."""
        if queue_wait > 0.1:
            self.simulation_engine.log_with_sim_time(logging.INFO, 
                f"👨‍⚕️ Patient #{patient_num}: Started doctor assessment at {self.simulation_engine.format_sim_time(start_time)} "
                f"(Queue wait: {queue_wait:.1f}min + Handover: {handover_delay:.1f}min = Total: {total_wait:.1f}min)")
        else:
            self.simulation_engine.log_with_sim_time(logging.INFO, 
                f"👨‍⚕️ Patient #{patient_num}: Started doctor assessment at {self.simulation_engine.format_sim_time(start_time)} "
                f"(Handover delay: {handover_delay:.1f}min)")
    
    def _calculate_assessment_time(self, triage_result):
        """Calculate doctor assessment time based on triage result."""
        priority = triage_result.priority_score
        fuzzy_score = triage_result.fuzzy_score if triage_result.fuzzy_score is not None else 5.0
        
        # Base assessment times by priority (higher priority = more complex = more time)
        time_ranges = {
            1: (60, 120), # RED - Critical (most complex, longest time)
            2: (45, 90),  # ORANGE - Very urgent
            3: (30, 60),  # YELLOW - Urgent
            4: (20, 40),  # GREEN - Standard
            5: (15, 30)   # BLUE - Non-urgent (simplest, shortest time)
        }
        
        min_time, max_time = time_ranges.get(priority, (20, 40))
        assessment_time = random.uniform(min_time, max_time)
        
        # Adjust based on fuzzy score for more precision
        urgency_factor = max(0.5, (6.0 - fuzzy_score) / 5.0)
        return assessment_time * urgency_factor
    
    def _perform_doctor_assessment(self, assessment_time, patient, triage_result, patient_num, assessment_start):
        """Perform the actual doctor assessment with monitoring."""
        yield from self.simulation_engine.enhanced_yield_with_monitoring(
            assessment_time, "doctor assessment", self._capture_monitoring_snapshot)
        
        assessment_end = self.simulation_engine.env.now
        priority = triage_result.priority_score
        
        self._capture_monitoring_snapshot("doctor resource before release")
        self.simulation_engine.record_resource_event(
            'release', 'doctor', patient.Id, self._record_hospital_event, 
            service_time=assessment_time, priority=priority)
        
        self.simulation_engine.log_with_sim_time(logging.INFO, 
            f"✅ Patient #{patient_num}: Completed doctor assessment at {self.simulation_engine.format_sim_time(assessment_end)} "
            f"(Total assessment time: {assessment_end - assessment_start:.1f}min)")
    
    def _process_diagnostics(self, triage_result):
        """Process optional diagnostics stage with specific test types.
        
        Uses NHS official timing data for different diagnostic procedures.
        """
        if self.random_service.should_perform_diagnostics():
            # Determine diagnostic type based on triage result and clinical needs
            diagnostic_type = self._determine_diagnostic_type(triage_result)
            diagnostics_time = self.random_service.get_diagnostics_time(diagnostic_type)
            
            self.simulation_engine.log_with_sim_time(logging.INFO, f"🔬 Performing {diagnostic_type} diagnostics (Duration: {diagnostics_time:.1f}min)")
            yield from self.simulation_engine.enhanced_yield_with_monitoring(
                diagnostics_time, "diagnostics", self._capture_monitoring_snapshot)
    
    def _determine_diagnostic_type(self, triage_result):
        """Determine appropriate diagnostic test type based on triage result.
        
        Returns specific test type for NHS evidence-based timing.
        """
        # Use RandomService for consistent diagnostic test selection with TriageResult
        return self.random_service.get_diagnostic_test_type(triage_result)
    
    def _process_disposition(self, triage_result):
        """Process patient disposition using NHS evidence-based timing.
        
        Uses official NHS sources for admission and discharge processing times.
        """
        # Determine admission decision using NHS-based logic with TriageResult
        admitted = self.random_service.should_admit_patient(triage_result)
        
        if admitted:
            # Admission process with NHS evidence-based timing
            disposition = 'admitted'
            processing_time = self.random_service.get_admission_processing_time()
            
            self.simulation_engine.log_with_sim_time(logging.INFO, f"🏥 Patient requires admission - processing time: {processing_time:.1f}min")
            
            # Bed allocation process
            bed_start = self.simulation_engine.env.now
            bed_resource = self.simulation_engine.get_resource('beds')
            self.simulation_engine.log_with_sim_time(logging.INFO, f"🛏️  Waiting for bed at {self.simulation_engine.format_sim_time(bed_start)} (Priority: {triage_result.priority_score}, Available beds: {bed_resource.capacity - bed_resource.count})")
            
            with bed_resource.request(priority=triage_result.priority_score) as req:
                yield req
                resource_acquired_time = self.simulation_engine.env.now
                queue_wait_time = resource_acquired_time - bed_start
                
                # Add realistic bed preparation delay even when bed is immediately available
                bed_prep_delay = self.random_service.get_handover_delay('bed', triage_result)
                yield from self.simulation_engine.enhanced_yield_with_monitoring(
                    bed_prep_delay, "bed preparation", self._capture_monitoring_snapshot)
                
                bed_service_start = self.simulation_engine.env.now
                total_wait_time = bed_service_start - bed_start
                
                if queue_wait_time > 0.1:
                    self.simulation_engine.log_with_sim_time(logging.INFO, f"🛏️  Bed allocated at {self.simulation_engine.format_sim_time(bed_service_start)} (Queue wait: {queue_wait_time:.1f}min + Preparation: {bed_prep_delay:.1f}min = Total: {total_wait_time:.1f}min)")
                else:
                    self.simulation_engine.log_with_sim_time(logging.INFO, f"🛏️  Bed allocated at {self.simulation_engine.format_sim_time(bed_service_start)} (Bed preparation: {bed_prep_delay:.1f}min)")
                
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
        
        # Log patient completion
        self.simulation_engine.log_with_sim_time(logging.INFO, f"🎯 Patient #{patient_num} completed: {total_time:.1f}min | {disposition.upper()}")
        
        # Log running totals every 10 patients
        if self.patient_count % 10 == 0:
            self.simulation_engine.log_with_sim_time(logging.INFO, f"📈 Progress: {self.patient_count} patients, avg time: {self.total_time/self.patient_count:.1f}min")
    
    def arrivals(self):
        """Generate Poisson arrivals."""
        patient_num = 0
        self.simulation_engine.log_with_sim_time(logging.INFO, f"🚀 Starting patient arrivals process at {self.simulation_engine.format_sim_time(self.simulation_engine.env.now)}")
        
        while True:
            # Poisson process: exponential interarrival times
            interarrival = self.random_service.get_patient_arrival_interval(self.arrival_rate)
            
            self.simulation_engine.log_with_sim_time(logging.DEBUG, f"⏰ Next patient arrival in {interarrival:.1f}min (at {self.simulation_engine.format_sim_time(self.simulation_engine.env.now + interarrival)})")
            yield from self.simulation_engine.enhanced_yield_with_monitoring(
                interarrival, "patient arrival interval", self._capture_monitoring_snapshot)
            
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