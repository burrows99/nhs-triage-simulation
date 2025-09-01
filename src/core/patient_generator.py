import simpy
import numpy as np
import random
from typing import Dict, List, Optional, Any, Callable
from ..entities.patient import Patient, Priority, PatientContext
from ..utils.csv_utils import CSVDataLoader


class PatientGenerator:
    """Patient generator for emergency department simulation using CSV data and Poisson arrival process"""
    
    def __init__(self, 
                 env: simpy.Environment,
                 ed: 'EmergencyDepartment',
                 arrival_rate: float = 0.5,  # patients per minute
                 csv_directory: str = '/Users/raunakburrows/dissertation/output/csv',
                 patient_profiles: Optional[Dict[str, Any]] = None):
        """
        Initialize patient generator
        
        Args:
            env: SimPy environment
            ed: Emergency Department instance
            arrival_rate: Average patients per minute (lambda for Poisson process)
            csv_directory: Path to directory containing CSV files
            patient_profiles: Configuration for patient characteristics distribution (for chief complaints)
        """
        self.env = env
        self.ed = ed
        self.arrival_rate = arrival_rate  # λ (lambda) for Poisson process
        self.mean_interarrival_time = 1.0 / arrival_rate  # Mean time between arrivals
        
        # Initialize CSV data loader
        self.csv_loader = CSVDataLoader(csv_directory)
        
        # Load all CSV data
        try:
            self.patient_data = self.csv_loader.load_csv_file('patients.csv')
            self.encounters_data = self.csv_loader.load_csv_file('encounters.csv')
            self.conditions_data = self.csv_loader.load_csv_file('conditions.csv')
            self.observations_data = self.csv_loader.load_csv_file('observations.csv')
            self.medications_data = self.csv_loader.load_csv_file('medications.csv')
            print(f"Loaded CSV data: {len(self.patient_data)} patients, {len(self.encounters_data)} encounters, {len(self.conditions_data)} conditions, {len(self.observations_data)} observations")
        except Exception as e:
            print(f"Warning: Could not load CSV data: {e}")
            self.patient_data = []
            self.encounters_data = []
            self.conditions_data = []
            self.observations_data = []
            self.medications_data = []
        
        # No synthetic data generation - all data comes from CSV files
        
        # Tracking
        self.generated_patients = []
        self.arrival_times = []
        self.used_patient_indices = set()  # Track which CSV patients we've used
        
        # Start the patient generation process
        self.generation_process = env.process(self._generate_patients())
    
    def _generate_patients(self):
        """Main patient generation process using Poisson arrival distribution"""
        patient_id = 1
        
        while True:
            # Generate inter-arrival time using exponential distribution
            # This creates a Poisson arrival process
            interarrival_time = np.random.exponential(self.mean_interarrival_time)
            
            # Wait for the next arrival
            yield self.env.timeout(interarrival_time)
            
            # Generate patient
            patient = self._create_patient(patient_id, self.env.now)
            self.generated_patients.append(patient)
            self.arrival_times.append(self.env.now)
            
            # Start patient journey in ED
            self.env.process(self.ed.patient_arrival(patient))
            
            patient_id += 1
    
    def _create_patient(self, patient_id: int, arrival_time: float) -> Patient:
        """Create a patient using only CSV data - no synthetic generation"""
        
        # Get patient context from CSV data
        patient_context = self._get_patient_context_from_csv()
        
        if not patient_context:
            # If no CSV data available, create minimal patient
            return Patient(
                patient_id=f"P{patient_id:06d}",
                arrival_time=arrival_time
            )
        
        # Get chief complaint from encounters data
        chief_complaint = self._get_chief_complaint_from_csv(patient_context.id)
        
        # Create patient with context
        patient = Patient(
            patient_id=f"P{patient_id:06d}",
            arrival_time=arrival_time,
            chief_complaint=chief_complaint,
            patient_context=patient_context
        )
        
        # Load vital signs from observations CSV
        self._load_vital_signs_from_csv(patient, patient_context.id)
        
        # Load medical history from conditions and medications CSV
        self._load_medical_history_from_csv(patient, patient_context.id)
        
        return patient
    
    def _get_patient_context_from_csv(self) -> Optional[PatientContext]:
        """Get patient context from CSV data, cycling through available records"""
        if not self.patient_data:
            return None
            
        # If we've used all patients, reset the tracking (allows reuse)
        if len(self.used_patient_indices) >= len(self.patient_data):
            self.used_patient_indices.clear()
            
        # Find an unused patient record
        available_indices = set(range(len(self.patient_data))) - self.used_patient_indices
        
        if not available_indices:
            # Fallback: use random patient if somehow no available indices
            patient_index = random.randint(0, len(self.patient_data) - 1)
        else:
            patient_index = random.choice(list(available_indices))
            
        self.used_patient_indices.add(patient_index)
        
        # Get the patient record and create context
        patient_record = self.patient_data[patient_index]
        return PatientContext.from_csv_row(patient_record)
    
    def _get_chief_complaint_from_csv(self, patient_id: str) -> Optional[str]:
        """Get chief complaint from encounters CSV data"""
        if not self.encounters_data:
            return None
            
        # Find encounters for this patient
        patient_encounters = [enc for enc in self.encounters_data if enc.get('PATIENT') == patient_id]
        
        if not patient_encounters:
            return None
            
        # Get the most recent encounter description
        # Sort by START date if available
        try:
            patient_encounters.sort(key=lambda x: x.get('START', ''), reverse=True)
        except:
            pass
            
        return patient_encounters[0].get('DESCRIPTION')
    
    def _load_vital_signs_from_csv(self, patient: Patient, patient_id: str) -> None:
        """Load vital signs from observations CSV data"""
        if not self.observations_data:
            return
            
        # Find observations for this patient
        patient_observations = [obs for obs in self.observations_data if obs.get('PATIENT') == patient_id]
        
        # Map observation codes to vital sign names
        vital_sign_mapping = {
            '8480-6': 'systolic_bp',
            '8462-4': 'diastolic_bp', 
            '8867-4': 'heart_rate',
            '9279-1': 'respiratory_rate',
            '8310-5': 'temperature',
            '2708-6': 'oxygen_saturation',
            '72514-3': 'pain_score'
        }
        
        for obs in patient_observations:
            code = obs.get('CODE')
            if code in vital_sign_mapping:
                vital_name = vital_sign_mapping[code]
                value = obs.get('VALUE')
                if value:
                    try:
                        # Convert to appropriate type
                        if vital_name == 'pain_score':
                            patient.add_vital_sign(vital_name, float(value))
                        else:
                            patient.add_vital_sign(vital_name, float(value))
                    except (ValueError, TypeError):
                        pass
    
    def _load_medical_history_from_csv(self, patient: Patient, patient_id: str) -> None:
        """Load medical history from conditions and medications CSV data"""
        medical_history = {
            'conditions': [],
            'medications': [],
            'allergies': []
        }
        
        # Load conditions
        if self.conditions_data:
            patient_conditions = [cond for cond in self.conditions_data if cond.get('PATIENT') == patient_id]
            medical_history['conditions'] = [cond.get('DESCRIPTION') for cond in patient_conditions if cond.get('DESCRIPTION')]
        
        # Load medications
        if self.medications_data:
            patient_medications = [med for med in self.medications_data if med.get('PATIENT') == patient_id]
            medical_history['medications'] = [med.get('DESCRIPTION') for med in patient_medications if med.get('DESCRIPTION')]
        
        # Set medical history if any data found
        if any(medical_history.values()):
            patient.medical_history = medical_history
    
    # All synthetic generation methods removed - using only CSV data
    
    def set_arrival_rate(self, new_rate: float) -> None:
        """Update the patient arrival rate"""
        self.arrival_rate = new_rate
        self.mean_interarrival_time = 1.0 / new_rate
    
    def get_arrival_statistics(self) -> Dict[str, Any]:
        """Get statistics about patient arrivals"""
        if len(self.arrival_times) < 2:
            return {}
        
        interarrival_times = np.diff(self.arrival_times)
        
        return {
            'total_patients_generated': len(self.generated_patients),
            'simulation_duration': self.arrival_times[-1] - self.arrival_times[0] if self.arrival_times else 0,
            'actual_arrival_rate': len(self.generated_patients) / (self.arrival_times[-1] - self.arrival_times[0]) if len(self.arrival_times) > 1 else 0,
            'target_arrival_rate': self.arrival_rate,
            'mean_interarrival_time': np.mean(interarrival_times),
            'std_interarrival_time': np.std(interarrival_times),
            'min_interarrival_time': np.min(interarrival_times),
            'max_interarrival_time': np.max(interarrival_times)
        }
    
    def verify_poisson_process(self) -> Dict[str, Any]:
        """Verify that arrivals follow Poisson distribution"""
        if len(self.arrival_times) < 10:
            return {'error': 'Insufficient data for verification'}
        
        # Test inter-arrival times for exponential distribution
        interarrival_times = np.diff(self.arrival_times)
        
        # Kolmogorov-Smirnov test for exponential distribution
        from scipy import stats
        
        # Test if inter-arrival times follow exponential distribution
        ks_statistic, ks_p_value = stats.kstest(interarrival_times, 
                                               lambda x: stats.expon.cdf(x, scale=self.mean_interarrival_time))
        
        # Count arrivals in fixed time intervals for Poisson test
        if self.arrival_times:
            total_time = self.arrival_times[-1] - self.arrival_times[0]
            interval_length = 60  # 1 hour intervals
            num_intervals = int(total_time / interval_length)
            
            if num_intervals > 5:
                interval_counts = []
                for i in range(num_intervals):
                    start_time = self.arrival_times[0] + i * interval_length
                    end_time = start_time + interval_length
                    count = sum(1 for t in self.arrival_times if start_time <= t < end_time)
                    interval_counts.append(count)
                
                # Test if counts follow Poisson distribution
                expected_lambda = self.arrival_rate * interval_length
                poisson_ks_stat, poisson_p_value = stats.kstest(interval_counts,
                                                               lambda x: stats.poisson.cdf(x, expected_lambda))
                
                return {
                    'interarrival_exponential_test': {
                        'ks_statistic': ks_statistic,
                        'p_value': ks_p_value,
                        'is_exponential': ks_p_value > 0.05
                    },
                    'arrival_poisson_test': {
                        'ks_statistic': poisson_ks_stat,
                        'p_value': poisson_p_value,
                        'is_poisson': poisson_p_value > 0.05,
                        'expected_lambda': expected_lambda,
                        'observed_mean': np.mean(interval_counts),
                        'interval_counts': interval_counts
                    }
                }
        
        return {
            'interarrival_exponential_test': {
                'ks_statistic': ks_statistic,
                'p_value': ks_p_value,
                'is_exponential': ks_p_value > 0.05
            }
        }