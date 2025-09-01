import simpy
import numpy as np
import random
from collections import defaultdict
from scipy.stats import truncnorm
from datetime import datetime
# Add the project root to Python path to enable absolute imports
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.services.data_service import DataService


class RealDataHospital:
    """Hospital simulation using real patient data from Synthea CSV files."""
    
    def __init__(self, csv_folder='./output/csv', triage_nurse_capacity=2, doctor_capacity=6, 
                 bed_capacity=15, sim_duration=1440, arrival_peak_rate=15, arrival_offpeak_rate=5):
        self.csv_folder = csv_folder
        self.triage_nurse_capacity = triage_nurse_capacity
        self.doctor_capacity = doctor_capacity
        self.bed_capacity = bed_capacity
        self.sim_duration = sim_duration
        self.arrival_peak_rate = arrival_peak_rate
        self.arrival_offpeak_rate = arrival_offpeak_rate
        self.env = None
        self.metrics = None
        
        # Initialize data service and load patient data
        self.data_service = DataService(csv_folder)
        self.patient_records = {}
        self.patient_ids = []
        self.current_patient_index = 0
        
        self._load_patient_data()
    
    def _load_patient_data(self):
        """Load patient data from CSV files."""
        print(f"Loading patient data from {self.csv_folder}...")
        try:
            self.patient_records = self.data_service.process_all()
            self.patient_ids = list(self.patient_records.keys())
            print(f"Loaded {len(self.patient_ids)} patients for simulation")
        except Exception as e:
            print(f"Error loading patient data: {e}")
            print("Falling back to fake patient generation")
            self.patient_records = {}
            self.patient_ids = []
    
    def get_next_patient_data(self):
        """Get the next patient from the real data, cycling through the list."""
        if not self.patient_ids:
            return None
        
        patient_id = self.patient_ids[self.current_patient_index]
        patient_data = self.patient_records[patient_id]
        
        # Move to next patient, cycling back to start if needed
        self.current_patient_index = (self.current_patient_index + 1) % len(self.patient_ids)
        
        return patient_id, patient_data
    
    def extract_patient_symptoms(self, patient_data):
        """Extract symptoms and medical history from real patient data."""
        symptoms = {
            'severe_pain': 'none',
            'crushing_sensation': 'none',
            'shortness_of_breath': 'none',
            'chest_pain': 'none',
            'nausea': 'none'
        }
        
        numeric_inputs = [0.0] * 5  # Default values
        
        # Extract from observations
        observations = patient_data.get('observations', [])
        for obs in observations:
            description = obs.get('DESCRIPTION', '').lower()
            value = obs.get('VALUE', '')
            
            # Map observations to symptoms
            if 'pain' in description and 'severity' in description:
                try:
                    pain_score = float(value)
                    numeric_inputs[0] = pain_score
                    if pain_score >= 7:
                        symptoms['severe_pain'] = 'severe'
                    elif pain_score >= 4:
                        symptoms['severe_pain'] = 'moderate'
                except (ValueError, TypeError):
                    pass
            
            elif 'blood pressure' in description:
                try:
                    # Extract systolic BP
                    if '/' in str(value):
                        systolic = float(str(value).split('/')[0])
                        numeric_inputs[1] = systolic
                except (ValueError, TypeError):
                    pass
            
            elif 'heart rate' in description or 'pulse' in description:
                try:
                    heart_rate = float(value)
                    numeric_inputs[2] = heart_rate
                except (ValueError, TypeError):
                    pass
            
            elif 'temperature' in description:
                try:
                    temp = float(value)
                    numeric_inputs[3] = temp
                except (ValueError, TypeError):
                    pass
            
            elif 'respiratory rate' in description:
                try:
                    resp_rate = float(value)
                    numeric_inputs[4] = resp_rate
                except (ValueError, TypeError):
                    pass
        
        # Extract from conditions
        conditions = patient_data.get('conditions', [])
        for condition in conditions:
            description = condition.get('DESCRIPTION', '').lower()
            
            if 'chest pain' in description or 'angina' in description:
                symptoms['chest_pain'] = 'moderate'
            elif 'myocardial infarction' in description or 'heart attack' in description:
                symptoms['chest_pain'] = 'severe'
                symptoms['crushing_sensation'] = 'severe'
            elif 'hypertension' in description:
                # Already handled in observations
                pass
            elif 'asthma' in description or 'copd' in description:
                symptoms['shortness_of_breath'] = 'moderate'
        
        return numeric_inputs, symptoms
    
    def determine_triage_from_real_data(self, patient_data, numeric_inputs, symptoms):
        """Determine triage category based on real patient data."""
        categories = ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE']
        wait_times = ['0 min', '10 min', '60 min', '120 min', '240 min']
        priorities = [1, 2, 3, 4, 5]  # RED=1 (highest), BLUE=5 (lowest)
        
        # Start with default GREEN (routine)
        triage_index = 3
        
        # Check conditions for higher acuity
        conditions = patient_data.get('conditions', [])
        for condition in conditions:
            description = condition.get('DESCRIPTION', '').lower()
            
            # RED conditions (immediate)
            if any(term in description for term in ['myocardial infarction', 'cardiac arrest', 
                                                   'stroke', 'severe trauma', 'respiratory failure']):
                triage_index = 0
                break
            
            # ORANGE conditions (very urgent)
            elif any(term in description for term in ['chest pain', 'angina', 'pneumonia',
                                                     'severe asthma', 'diabetic ketoacidosis']):
                triage_index = min(triage_index, 1)
            
            # YELLOW conditions (urgent)
            elif any(term in description for term in ['hypertension', 'moderate asthma',
                                                     'urinary tract infection', 'cellulitis']):
                triage_index = min(triage_index, 2)
        
        # Check vital signs for escalation
        if len(numeric_inputs) >= 5:
            pain_score, systolic_bp, heart_rate, temperature, resp_rate = numeric_inputs[:5]
            
            # Critical vital signs -> RED
            if (systolic_bp > 200 or systolic_bp < 80 or 
                heart_rate > 150 or heart_rate < 40 or
                temperature > 104 or resp_rate > 30 or resp_rate < 8):
                triage_index = 0
            
            # Concerning vital signs -> ORANGE
            elif (systolic_bp > 180 or systolic_bp < 90 or
                  heart_rate > 120 or heart_rate < 50 or
                  temperature > 102 or resp_rate > 24):
                triage_index = min(triage_index, 1)
            
            # Severe pain -> ORANGE
            elif pain_score >= 8:
                triage_index = min(triage_index, 1)
            elif pain_score >= 6:
                triage_index = min(triage_index, 2)
        
        # Check symptoms
        if symptoms.get('severe_pain') == 'severe' or symptoms.get('crushing_sensation') == 'severe':
            triage_index = min(triage_index, 1)
        elif symptoms.get('chest_pain') == 'severe':
            triage_index = min(triage_index, 1)
        
        # Age-based adjustments
        birth_date = patient_data.get('BIRTHDATE', '')
        if birth_date:
            try:
                birth_year = int(birth_date.split('-')[0])
                age = 2024 - birth_year
                
                # Elderly patients get priority bump for certain conditions
                if age >= 75 and triage_index >= 2:
                    triage_index = max(0, triage_index - 1)
                # Very young patients also get priority
                elif age <= 2 and triage_index >= 2:
                    triage_index = max(0, triage_index - 1)
            except (ValueError, IndexError):
                pass
        
        return {
            'flowchart_used': 'real_data_triage',
            'triage_category': np.str_(categories[triage_index]),
            'wait_time': np.str_(wait_times[triage_index]),
            'fuzzy_score': 5 - triage_index,  # Higher score for more urgent
            'symptoms_processed': symptoms,
            'numeric_inputs': numeric_inputs,
            'priority_score': np.int64(priorities[triage_index]),
            'patient_conditions': [c.get('DESCRIPTION', '') for c in patient_data.get('conditions', [])],
            'patient_age': self._calculate_age(patient_data.get('BIRTHDATE', '')),
            'patient_gender': patient_data.get('GENDER', 'Unknown')
        }
    
    def _calculate_age(self, birth_date):
        """Calculate age from birth date string."""
        if not birth_date:
            return None
        try:
            birth_year = int(birth_date.split('-')[0])
            return 2024 - birth_year
        except (ValueError, IndexError):
            return None
    
    def arrival_rate(self, hour):
        """Calculate arrival rate based on time of day."""
        if 8 <= hour < 20:  # Peak daytime
            return self.arrival_peak_rate
        else:  # Off-peak
            return self.arrival_offpeak_rate
    
    def truncated_normal(self, mean, std):
        """Generate truncated normal distribution."""
        a = -mean / std  # Lower bound at 0
        return truncnorm(a, np.inf, loc=mean, scale=std).rvs()
    
    def patient(self, patient_counter, triage_nurses, doctors, beds):
        """Simulate a patient journey through the hospital."""
        arrival_time = self.env.now
        
        # Get real patient data
        patient_data_result = self.get_next_patient_data()
        
        if patient_data_result is None:
            # Fallback to fake patient if no real data available
            patient_id = f"fake_{patient_counter}"
            numeric_inputs = [random.uniform(0, 10) for _ in range(5)]
            symptoms = {
                'severe_pain': random.choice(['none', 'moderate', 'severe']),
                'crushing_sensation': random.choice(['none', 'moderate', 'severe']),
            }
            # Use simple random triage for fake patients
            categories = ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE']
            priorities = [1, 2, 3, 4, 5]
            wait_times = ['0 min', '10 min', '60 min', '120 min', '240 min']
            idx = random.choices(range(5), weights=[0.05, 0.15, 0.30, 0.40, 0.10])[0]
            triage_result = {
                'flowchart_used': 'fake_patient',
                'triage_category': np.str_(categories[idx]),
                'wait_time': np.str_(wait_times[idx]),
                'fuzzy_score': random.uniform(1, 5),
                'symptoms_processed': symptoms,
                'numeric_inputs': numeric_inputs,
                'priority_score': np.int64(priorities[idx])
            }
        else:
            real_patient_id, patient_data = patient_data_result
            patient_id = f"real_{real_patient_id[:8]}"  # Truncate for display
            
            # Extract symptoms and medical data
            numeric_inputs, symptoms = self.extract_patient_symptoms(patient_data)
            
            # Determine triage based on real medical data
            triage_result = self.determine_triage_from_real_data(patient_data, numeric_inputs, symptoms)
        
        category = str(triage_result['triage_category'])
        priority = int(triage_result['priority_score'])
        max_wait_min = int(triage_result['wait_time'].split()[0])
        
        # Triage process
        with triage_nurses.request() as req:
            yield req
            triage_start = self.env.now
            yield self.env.timeout(self.truncated_normal(7, 2))  # Triage time ~5-10 min
        self.metrics['triage_wait'].append(self.env.now - arrival_time)
        
        # Assessment (priority queue for doctors)
        assess_start = self.env.now
        with doctors.request(priority=priority) as req:
            yield req
            yield self.env.timeout(self.truncated_normal(30, 10))  # Consult ~20-40 min
        assess_wait = self.env.now - assess_start
        self.metrics['assess_wait'][category].append(assess_wait)
        if assess_wait > max_wait_min:
            self.metrics['mts_breaches'].append(1)
        
        # Diagnostics (based on patient complexity)
        diagnostic_probability = 0.3  # Default
        if patient_data_result:
            # Higher probability for patients with more conditions
            _, patient_data = patient_data_result
            condition_count = len(patient_data.get('conditions', []))
            diagnostic_probability = min(0.8, 0.2 + (condition_count * 0.1))
        
        if random.random() < diagnostic_probability:
            yield self.env.timeout(self.truncated_normal(45, 15))  # Labs/imaging ~30-60 min
        
        # Disposition (based on patient acuity and conditions)
        admission_probability = 0.2  # Default
        if patient_data_result and category in ['RED', 'ORANGE']:
            admission_probability = 0.6  # Higher admission rate for urgent patients
        elif category == 'YELLOW':
            admission_probability = 0.3
        
        if random.random() < admission_probability:
            with beds.request(priority=priority) as req:
                yield req
                yield self.env.timeout(self.truncated_normal(60, 20))  # Admission ~40-80 min
            disposition = 'admitted'
        else:
            yield self.env.timeout(self.truncated_normal(15, 5))  # Final steps ~10-20 min
            disposition = 'discharged'
        
        total_time = self.env.now - arrival_time
        self.metrics['total_time'].append(total_time)
        self.metrics['four_hour_breaches'] += 1 if total_time > 240 else 0
        
        # Enhanced logging for real patients
        if patient_data_result:
            _, patient_data = patient_data_result
            age = triage_result.get('patient_age', 'Unknown')
            gender = triage_result.get('patient_gender', 'Unknown')
            conditions = triage_result.get('patient_conditions', [])
            condition_summary = ', '.join(conditions[:2]) if conditions else 'None'
            print(f"Patient {patient_id} ({category}, Age: {age}, {gender}): "
                  f"Total time {total_time:.1f} min, Conditions: {condition_summary}, "
                  f"Disposition: {disposition}")
        else:
            print(f"Patient {patient_id} ({category}): Total time {total_time:.1f} min, "
                  f"Disposition: {disposition}")
    
    def arrivals(self, triage_nurses, doctors, beds):
        """Generate patient arrivals using real patient data."""
        patient_counter = 0
        while True:
            hour = (self.env.now // 60) % 24
            interarrival = random.expovariate(self.arrival_rate(hour) / 60)
            yield self.env.timeout(interarrival)
            patient_counter += 1
            self.env.process(self.patient(patient_counter, triage_nurses, doctors, beds))
    
    def run_simulation(self):
        """Run the hospital simulation with real patient data."""
        self.env = simpy.Environment()
        triage_nurses = simpy.Resource(self.env, capacity=self.triage_nurse_capacity)
        doctors = simpy.PriorityResource(self.env, capacity=self.doctor_capacity)
        beds = simpy.PriorityResource(self.env, capacity=self.bed_capacity)
        
        # Initialize metrics
        self.metrics = {
            'triage_wait': [],
            'assess_wait': defaultdict(list),
            'total_time': [],
            'mts_breaches': [],
            'four_hour_breaches': 0
        }
        
        # Start arrival process
        self.env.process(self.arrivals(triage_nurses, doctors, beds))
        
        # Run simulation
        print(f"Starting simulation with real patient data for {self.sim_duration} minutes...")
        self.env.run(until=self.sim_duration)
        
        return self.get_metrics()
    
    def get_metrics(self):
        """Calculate and return simulation metrics."""
        if not self.metrics['total_time']:
            return {}
        
        # Calculate averages
        avg_triage_wait = np.mean(self.metrics['triage_wait'])
        avg_total_time = np.mean(self.metrics['total_time'])
        
        avg_assess_wait_by_category = {}
        for category, waits in self.metrics['assess_wait'].items():
            if waits:
                avg_assess_wait_by_category[category] = np.mean(waits)
        
        total_patients = len(self.metrics['total_time'])
        mts_breach_count = len(self.metrics['mts_breaches'])
        four_hour_breach_count = self.metrics['four_hour_breaches']
        four_hour_breach_pct = (four_hour_breach_count / total_patients * 100) if total_patients > 0 else 0
        
        return {
            'avg_triage_wait': avg_triage_wait,
            'avg_assess_wait_by_category': avg_assess_wait_by_category,
            'avg_total_time': avg_total_time,
            'mts_breach_count': mts_breach_count,
            'four_hour_breach_count': four_hour_breach_count,
            'four_hour_breach_pct': four_hour_breach_pct,
            'total_patients': total_patients,
            'real_patients_used': len(self.patient_ids),
            'data_source': 'real_synthea_data' if self.patient_ids else 'fake_fallback'
        }


if __name__ == "__main__":
    # Run simulation with real patient data
    hospital = RealDataHospital(csv_folder='./output/csv')
    metrics = hospital.run_simulation()
    
    print("\n" + "="*50)
    print("REAL DATA HOSPITAL SIMULATION RESULTS")
    print("="*50)
    print(f"Data Source: {metrics.get('data_source', 'unknown')}")
    print(f"Real Patients Available: {metrics.get('real_patients_used', 0)}")
    print(f"Total Patients Processed: {metrics.get('total_patients', 0)}")
    print(f"Average Triage Wait: {metrics.get('avg_triage_wait', 0):.1f} min")
    print("Average Assessment Wait by Category:")
    for cat, avg in metrics.get('avg_assess_wait_by_category', {}).items():
        print(f"  {cat}: {avg:.1f} min")
    print(f"Average Total Time: {metrics.get('avg_total_time', 0):.1f} min")
    print(f"MTS Target Breaches: {metrics.get('mts_breach_count', 0)}")
    print(f"4-Hour Breaches: {metrics.get('four_hour_breach_count', 0)} "
          f"({metrics.get('four_hour_breach_pct', 0):.1f}%)")