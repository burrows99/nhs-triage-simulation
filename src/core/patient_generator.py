import simpy
import numpy as np
from typing import Dict, List, Optional, Any, Callable
from ..entities.patient import Patient, Priority


class PatientGenerator:
    """Patient generator for emergency department simulation using Poisson arrival process"""
    
    def __init__(self, 
                 env: simpy.Environment,
                 ed: 'EmergencyDepartment',
                 arrival_rate: float = 0.5,  # patients per minute
                 patient_profiles: Optional[Dict[str, Any]] = None):
        """
        Initialize patient generator
        
        Args:
            env: SimPy environment
            ed: Emergency Department instance
            arrival_rate: Average patients per minute (lambda for Poisson process)
            patient_profiles: Configuration for patient characteristics distribution
        """
        self.env = env
        self.ed = ed
        self.arrival_rate = arrival_rate  # λ (lambda) for Poisson process
        self.mean_interarrival_time = 1.0 / arrival_rate  # Mean time between arrivals
        
        # Patient characteristic distributions
        self.patient_profiles = patient_profiles or self._default_patient_profiles()
        
        # Tracking
        self.generated_patients = []
        self.arrival_times = []
        
        # Start the patient generation process
        self.generation_process = env.process(self._generate_patients())
    
    def _default_patient_profiles(self) -> Dict[str, Any]:
        """Default patient characteristic distributions based on typical ED demographics"""
        return {
            'age_distribution': {
                'type': 'mixed',
                'distributions': [
                    {'type': 'normal', 'mean': 5, 'std': 2, 'weight': 0.15, 'min': 0, 'max': 18},  # Pediatric
                    {'type': 'normal', 'mean': 35, 'std': 15, 'weight': 0.50, 'min': 18, 'max': 65},  # Adult
                    {'type': 'normal', 'mean': 75, 'std': 8, 'weight': 0.35, 'min': 65, 'max': 100}  # Elderly
                ]
            },
            'gender_distribution': {
                'male': 0.48,
                'female': 0.52
            },
            'chief_complaints': {
                'chest pain': 0.15,
                'difficulty breathing': 0.12,
                'abdominal pain': 0.10,
                'head injury': 0.08,
                'fever': 0.08,
                'nausea and vomiting': 0.07,
                'back pain': 0.06,
                'wound/laceration': 0.06,
                'dizziness': 0.05,
                'allergic reaction': 0.04,
                'anxiety': 0.04,
                'cold symptoms': 0.03,
                'skin rash': 0.03,
                'joint pain': 0.03,
                'other': 0.06
            },
            'vital_signs_ranges': {
                'systolic_bp': {'normal_mean': 120, 'normal_std': 15, 'abnormal_prob': 0.25},
                'heart_rate': {'normal_mean': 75, 'normal_std': 12, 'abnormal_prob': 0.20},
                'respiratory_rate': {'normal_mean': 16, 'normal_std': 3, 'abnormal_prob': 0.15},
                'temperature': {'normal_mean': 36.8, 'normal_std': 0.5, 'abnormal_prob': 0.30},
                'oxygen_saturation': {'normal_mean': 98, 'normal_std': 2, 'abnormal_prob': 0.10},
                'pain_score': {'mean': 4, 'std': 2.5, 'min': 0, 'max': 10}
            },
            'medical_history_prob': 0.40,  # Probability of having significant medical history
            'medical_conditions': {
                'diabetes': 0.174,
                'hypertension': 0.261,
                'heart disease': 0.116,
                'asthma': 0.145,
                'copd': 0.087,
                'cancer': 0.058,
                'kidney disease': 0.043,
                'mental health': 0.116
            }
        }
    
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
        """Create a patient with realistic characteristics"""
        # Generate basic demographics
        age = self._generate_age()
        gender = self._generate_gender()
        chief_complaint = self._generate_chief_complaint()
        
        # Create patient
        patient = Patient(
            patient_id=f"P{patient_id:06d}",
            arrival_time=arrival_time,
            age=age,
            gender=gender,
            chief_complaint=chief_complaint
        )
        
        # Generate vital signs
        self._generate_vital_signs(patient)
        
        # Generate medical history
        self._generate_medical_history(patient)
        
        return patient
    
    def _generate_age(self) -> int:
        """Generate patient age based on mixed distribution"""
        age_config = self.patient_profiles['age_distribution']
        
        if age_config['type'] == 'mixed':
            # Choose distribution based on weights
            distributions = age_config['distributions']
            weights = [d['weight'] for d in distributions]
            chosen_dist = np.random.choice(distributions, p=weights)
            
            if chosen_dist['type'] == 'normal':
                age = np.random.normal(chosen_dist['mean'], chosen_dist['std'])
                age = np.clip(age, chosen_dist['min'], chosen_dist['max'])
                return int(age)
        
        # Fallback to uniform distribution
        return np.random.randint(0, 100)
    
    def _generate_gender(self) -> str:
        """Generate patient gender"""
        gender_dist = self.patient_profiles['gender_distribution']
        return np.random.choice(list(gender_dist.keys()), p=list(gender_dist.values()))
    
    def _generate_chief_complaint(self) -> str:
        """Generate chief complaint based on probability distribution"""
        complaints = self.patient_profiles['chief_complaints']
        return np.random.choice(list(complaints.keys()), p=list(complaints.values()))
    
    def _generate_vital_signs(self, patient: Patient) -> None:
        """Generate realistic vital signs for the patient"""
        vital_ranges = self.patient_profiles['vital_signs_ranges']
        
        for vital_name, config in vital_ranges.items():
            if vital_name == 'pain_score':
                # Pain score uses different distribution
                value = np.random.normal(config['mean'], config['std'])
                value = np.clip(value, config['min'], config['max'])
                patient.add_vital_sign(vital_name, round(value))
            else:
                # Other vitals can be normal or abnormal
                if np.random.random() < config['abnormal_prob']:
                    # Generate abnormal value
                    value = self._generate_abnormal_vital(vital_name, config)
                else:
                    # Generate normal value
                    value = np.random.normal(config['normal_mean'], config['normal_std'])
                
                # Apply age-based adjustments
                value = self._adjust_vital_for_age(vital_name, value, patient.age)
                
                # Round appropriately
                if vital_name in ['systolic_bp', 'heart_rate', 'respiratory_rate', 'oxygen_saturation']:
                    patient.add_vital_sign(vital_name, int(round(value)))
                else:
                    patient.add_vital_sign(vital_name, round(value, 1))
    
    def _generate_abnormal_vital(self, vital_name: str, config: Dict[str, Any]) -> float:
        """Generate abnormal vital sign values"""
        normal_mean = config['normal_mean']
        normal_std = config['normal_std']
        
        # Generate either high or low abnormal value
        if np.random.random() < 0.5:
            # High abnormal
            if vital_name == 'systolic_bp':
                return np.random.normal(160, 20)  # Hypertensive
            elif vital_name == 'heart_rate':
                return np.random.normal(110, 15)  # Tachycardic
            elif vital_name == 'respiratory_rate':
                return np.random.normal(24, 4)    # Tachypneic
            elif vital_name == 'temperature':
                return np.random.normal(38.5, 0.8)  # Febrile
            else:
                return normal_mean + 2 * normal_std
        else:
            # Low abnormal
            if vital_name == 'systolic_bp':
                return np.random.normal(85, 10)   # Hypotensive
            elif vital_name == 'heart_rate':
                return np.random.normal(55, 8)    # Bradycardic
            elif vital_name == 'respiratory_rate':
                return np.random.normal(10, 2)    # Bradypneic
            elif vital_name == 'temperature':
                return np.random.normal(35.5, 0.5)  # Hypothermic
            elif vital_name == 'oxygen_saturation':
                return np.random.normal(92, 3)    # Hypoxic
            else:
                return normal_mean - 2 * normal_std
    
    def _adjust_vital_for_age(self, vital_name: str, value: float, age: Optional[int]) -> float:
        """Adjust vital signs based on patient age"""
        if age is None:
            return value
        
        # Pediatric adjustments (age < 18)
        if age < 18:
            if vital_name == 'heart_rate':
                if age < 2:
                    return value + 40  # Infants have higher HR
                elif age < 12:
                    return value + 20  # Children have higher HR
            elif vital_name == 'respiratory_rate':
                if age < 2:
                    return value + 14  # Infants breathe faster
                elif age < 12:
                    return value + 6   # Children breathe faster
            elif vital_name == 'systolic_bp':
                if age < 12:
                    return value - 20  # Children have lower BP
        
        # Elderly adjustments (age > 65)
        elif age > 65:
            if vital_name == 'systolic_bp':
                return value + 10  # Elderly tend to have higher BP
        
        return value
    
    def _generate_medical_history(self, patient: Patient) -> None:
        """Generate medical history for the patient"""
        if np.random.random() < self.patient_profiles['medical_history_prob']:
            conditions = self.patient_profiles['medical_conditions']
            
            # Generate 1-3 conditions
            num_conditions = np.random.choice([1, 2, 3], p=[0.6, 0.3, 0.1])
            
            patient_conditions = []
            for _ in range(num_conditions):
                condition = np.random.choice(list(conditions.keys()), p=list(conditions.values()))
                if condition not in patient_conditions:
                    patient_conditions.append(condition)
            
            patient.medical_history = {
                'conditions': patient_conditions,
                'medications': self._generate_medications(patient_conditions),
                'allergies': self._generate_allergies()
            }
    
    def _generate_medications(self, conditions: List[str]) -> List[str]:
        """Generate medications based on medical conditions"""
        medication_map = {
            'diabetes': ['metformin', 'insulin'],
            'hypertension': ['lisinopril', 'amlodipine'],
            'heart disease': ['aspirin', 'atorvastatin'],
            'asthma': ['albuterol', 'fluticasone'],
            'copd': ['tiotropium', 'prednisone'],
            'mental health': ['sertraline', 'lorazepam']
        }
        
        medications = []
        for condition in conditions:
            if condition in medication_map:
                meds = medication_map[condition]
                medications.extend(np.random.choice(meds, size=np.random.randint(1, len(meds)+1), replace=False))
        
        return list(set(medications))  # Remove duplicates
    
    def _generate_allergies(self) -> List[str]:
        """Generate patient allergies"""
        common_allergies = ['penicillin', 'sulfa', 'latex', 'shellfish', 'nuts']
        
        if np.random.random() < 0.15:  # 15% chance of having allergies
            num_allergies = np.random.choice([1, 2], p=[0.8, 0.2])
            return list(np.random.choice(common_allergies, size=num_allergies, replace=False))
        
        return []
    
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