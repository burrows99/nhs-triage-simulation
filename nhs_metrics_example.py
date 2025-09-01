import simpy
import numpy as np
import random
from collections import defaultdict
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.services.data_service import DataService

# Import the NHS Metrics Tracker
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json

@dataclass
class PatientRecord:
    """Official NHS patient record for A&E Quality Indicators tracking"""
    patient_id: str
    arrival_time: float
    age: int = 30
    gender: str = "Unknown"
    triage_category: str = ""
    
    # Official NHS timestamps for quality indicators
    initial_assessment_start: float = 0  # Time to initial assessment
    treatment_start: float = 0           # Time to treatment  
    departure_time: float = 0            # Total time in A&E
    
    # Status flags for NHS indicators
    left_without_being_seen: bool = False
    is_reattendance: bool = False
    admitted: bool = False
    
    # Additional clinical data
    presenting_complaint: str = ""
    disposal: str = ""  # discharged/admitted/transferred
    
    def total_time_in_ae(self) -> float:
        """Total time in A&E (minutes) - Official NHS Quality Indicator"""
        if self.departure_time == 0:
            return 0
        return self.departure_time - self.arrival_time
    
    def time_to_initial_assessment(self) -> float:
        """Time to initial assessment (minutes) - Official NHS Quality Indicator"""
        if self.initial_assessment_start == 0:
            return 0
        return self.initial_assessment_start - self.arrival_time
    
    def time_to_treatment(self) -> float:
        """Time to treatment (minutes) - Official NHS Quality Indicator"""
        if self.treatment_start == 0:
            return 0
        return self.treatment_start - self.arrival_time
    
    def meets_4hour_standard(self) -> bool:
        """Meets NHS 4-hour standard (95% target)"""
        return self.total_time_in_ae() <= 240

class NHSMetricsTracker:
    """
    Official NHS A&E Quality Indicators Tracker
    
    Tracks the 5 official NHS A&E Quality Indicators:
    1. Left department before being seen for treatment rate
    2. Re-attendance rate
    3. Time to initial assessment
    4. Time to treatment
    5. Total time in A&E
    
    Plus NHS 4-hour standard compliance (95% target)
    """
    
    def __init__(self, track_reattendance_window_hours: int = 72):
        # Patient data storage
        self.patients: List[PatientRecord] = []
        self.active_patients: Dict[str, PatientRecord] = {}
        
        # Re-attendance tracking (72-hour window by default)
        self.reattendance_window = track_reattendance_window_hours
        self.patient_history: Dict[str, List[float]] = defaultdict(list)  # patient_id -> arrival_times
        
        # Real-time counters
        self.total_attendances = 0
        self.lwbs_count = 0
        self.reattendance_count = 0
        self.admissions_count = 0
    
    def record_arrival(self, patient_id: str, arrival_time: float, 
                      age: int = 30, gender: str = "Unknown", 
                      presenting_complaint: str = "") -> PatientRecord:
        """Record patient arrival and return patient record"""
        
        # Check for re-attendance
        is_reattendance = self._check_reattendance(patient_id, arrival_time)
        
        patient = PatientRecord(
            patient_id=patient_id,
            arrival_time=arrival_time,
            age=age,
            gender=gender,
            is_reattendance=is_reattendance,
            presenting_complaint=presenting_complaint
        )
        
        # Store patient
        self.active_patients[patient_id] = patient
        self.total_attendances += 1
        
        if is_reattendance:
            self.reattendance_count += 1
        
        # Track arrival time for re-attendance checking
        self.patient_history[patient_id].append(arrival_time)
        
        return patient
    
    def record_initial_assessment_start(self, patient_id: str, assessment_time: float):
        """Record start of initial assessment (triage/nursing assessment)"""
        if patient_id in self.active_patients:
            self.active_patients[patient_id].initial_assessment_start = assessment_time
    
    def record_treatment_start(self, patient_id: str, treatment_time: float):
        """Record start of treatment (usually doctor consultation)"""
        if patient_id in self.active_patients:
            self.active_patients[patient_id].treatment_start = treatment_time
    
    def record_triage_category(self, patient_id: str, category: str):
        """Record Manchester Triage System category"""
        if patient_id in self.active_patients:
            self.active_patients[patient_id].triage_category = category
    
    def record_departure(self, patient_id: str, departure_time: float, 
                        disposal: str = "discharged", admitted: bool = False):
        """Record patient departure with disposal information"""
        if patient_id not in self.active_patients:
            return
        
        patient = self.active_patients[patient_id]
        patient.departure_time = departure_time
        patient.disposal = disposal
        patient.admitted = admitted
        
        if admitted:
            self.admissions_count += 1
        
        # Move to completed patients
        self.patients.append(patient)
        del self.active_patients[patient_id]
    
    def _check_reattendance(self, patient_id: str, arrival_time: float) -> bool:
        """Check if patient is a re-attendance within the specified window"""
        if patient_id not in self.patient_history:
            return False
        
        # Check if any previous attendance was within the time window
        window_start = arrival_time - (self.reattendance_window * 60)  # Convert hours to minutes
        
        for previous_arrival in self.patient_history[patient_id]:
            if previous_arrival >= window_start:
                return True
        
        return False
    
    def get_official_nhs_metrics(self) -> Dict:
        """Generate official NHS A&E Quality Indicators report"""
        completed_patients = [p for p in self.patients if p.departure_time > 0]
        
        if not completed_patients:
            return {
                'error': 'No completed patients to analyze',
                'total_attendances': self.total_attendances,
                'active_patients': len(self.active_patients)
            }
        
        # Calculate official NHS metrics
        total_times = [p.total_time_in_ae() for p in completed_patients]
        initial_assessment_times = [p.time_to_initial_assessment() for p in completed_patients 
                                  if p.initial_assessment_start > 0]
        treatment_times = [p.time_to_treatment() for p in completed_patients 
                          if p.treatment_start > 0]
        
        four_hour_compliant = sum(1 for p in completed_patients if p.meets_4hour_standard())
        
        metrics = {
            # ATTENDANCE SUMMARY
            'total_attendances': len(completed_patients),
            'active_patients_in_system': len(self.active_patients),
            
            # OFFICIAL NHS A&E QUALITY INDICATORS
            '1_left_before_being_seen_rate_pct': (self.lwbs_count / len(completed_patients)) * 100 if completed_patients else 0,
            '2_reattendance_rate_pct': (self.reattendance_count / len(completed_patients)) * 100 if completed_patients else 0,
            '3_time_to_initial_assessment_avg_minutes': np.mean(initial_assessment_times) if initial_assessment_times else 0,
            '4_time_to_treatment_avg_minutes': np.mean(treatment_times) if treatment_times else 0,
            '5_total_time_in_ae_avg_minutes': np.mean(total_times) if total_times else 0,
            
            # NHS 4-HOUR STANDARD
            '4hour_standard_compliance_pct': (four_hour_compliant / len(completed_patients)) * 100 if completed_patients else 0,
            'attendances_within_4hours': four_hour_compliant,
            'attendances_over_4hours': len(completed_patients) - four_hour_compliant,
            '95pct_target_achieved': (four_hour_compliant / len(completed_patients)) >= 0.95 if completed_patients else False,
            '76pct_interim_target_achieved': (four_hour_compliant / len(completed_patients)) >= 0.76 if completed_patients else False,
            
            # ADDITIONAL PERFORMANCE METRICS
            'median_total_time_minutes': np.median(total_times) if total_times else 0,
            '95th_percentile_time_minutes': np.percentile(total_times, 95) if total_times else 0,
            'admission_rate_pct': (self.admissions_count / len(completed_patients)) * 100 if completed_patients else 0,
            
            # TRIAGE BREAKDOWN
            'triage_category_distribution': self._get_triage_distribution(completed_patients),
        }
        
        return metrics
    
    def _get_triage_distribution(self, patients: List[PatientRecord]) -> Dict[str, int]:
        """Get distribution of triage categories"""
        categories = [p.triage_category for p in patients if p.triage_category]
        return dict(pd.Series(categories).value_counts()) if categories else {}
    
    def print_nhs_dashboard(self):
        """Print comprehensive NHS-style dashboard"""
        metrics = self.get_official_nhs_metrics()
        
        if 'error' in metrics:
            print(f"⚠️  {metrics['error']}")
            print(f"Total attendances recorded: {metrics.get('total_attendances', 0)}")
            print(f"Active patients in system: {metrics.get('active_patients', 0)}")
            return metrics
        
        print("\\n" + "="*70)
        print("OFFICIAL NHS A&E QUALITY INDICATORS DASHBOARD")
        print("Based on NHS Digital/NHS England Standards")
        print("="*70)
        
        # Attendance Overview
        print(f"\\n📊 ATTENDANCE SUMMARY:")
        print(f"   Total Attendances: {metrics['total_attendances']:,}")
        print(f"   Active Patients in System: {metrics['active_patients_in_system']:,}")
        
        # Official NHS Quality Indicators
        print(f"\\n🏥 OFFICIAL NHS A&E QUALITY INDICATORS:")
        print(f"   1️⃣  Left Before Being Seen Rate: {metrics['1_left_before_being_seen_rate_pct']:.2f}%")
        print(f"   2️⃣  Re-attendance Rate ({self.reattendance_window}h): {metrics['2_reattendance_rate_pct']:.2f}%")
        print(f"   3️⃣  Time to Initial Assessment: {metrics['3_time_to_initial_assessment_avg_minutes']:.1f} min (avg)")
        print(f"   4️⃣  Time to Treatment: {metrics['4_time_to_treatment_avg_minutes']:.1f} min (avg)")
        print(f"   5️⃣  Total Time in A&E: {metrics['5_total_time_in_ae_avg_minutes']:.1f} min (avg)")
        
        # 4-Hour Standard
        compliance = metrics['4hour_standard_compliance_pct']
        target_95_status = "✅ ACHIEVED" if metrics['95pct_target_achieved'] else "❌ MISSED"
        target_76_status = "✅ MET" if metrics['76pct_interim_target_achieved'] else "❌ MISSED"
        
        print(f"\\n🎯 NHS 4-HOUR STANDARD:")
        print(f"   Compliance Rate: {compliance:.1f}%")
        print(f"   95% Target (Official): {target_95_status}")
        print(f"   76% Interim Target: {target_76_status}")
        print(f"   Within 4 Hours: {metrics['attendances_within_4hours']:,}")
        print(f"   Over 4 Hours: {metrics['attendances_over_4hours']:,}")
        
        # Performance Distribution  
        print(f"\\n📈 PERFORMANCE DISTRIBUTION:")
        print(f"   Median Total Time: {metrics['median_total_time_minutes']:.1f} min")
        print(f"   95th Percentile: {metrics['95th_percentile_time_minutes']:.1f} min")
        
        # Clinical Outcomes
        print(f"\\n🏥 CLINICAL OUTCOMES:")
        print(f"   Admission Rate: {metrics['admission_rate_pct']:.1f}%")
        
        # Triage Distribution
        if metrics['triage_category_distribution']:
            print(f"\\n🚦 TRIAGE CATEGORY DISTRIBUTION:")
            for category, count in sorted(metrics['triage_category_distribution'].items()):
                pct = (count / metrics['total_attendances']) * 100
                print(f"   {category}: {count:,} ({pct:.1f}%)")
        
        return metrics


class SimpleHospital:
    """Simple hospital simulation with NHS metrics integration."""
    
    def __init__(self, csv_folder='./output/csv', **kwargs):
        # Simulation parameters with defaults
        self.sim_duration = kwargs.get('sim_duration', 1440)  # 24 hours
        self.arrival_rate = kwargs.get('arrival_rate', 10)    # patients/hour
        self.nurses = kwargs.get('nurses', 2)
        self.doctors = kwargs.get('doctors', 6)
        self.beds = kwargs.get('beds', 15)
        
        # Initialize NHS Metrics Tracker
        print("Initializing NHS Metrics Tracker...")
        self.nhs_metrics = NHSMetricsTracker(track_reattendance_window_hours=72)
        print("NHS Metrics Tracker ready")
        
        # Load patient data
        print(f"Loading patient data from {csv_folder}...")
        self.data_service = DataService(csv_folder)
        self.patients = self.data_service.process_all()
        self.patient_ids = list(self.patients.keys())
        self.current_index = 0
        print(f"Loaded {len(self.patient_ids)} patients")
        
        # Initialize Manchester Triage System (without telemetry)
        print("Initializing Manchester Triage System...")
        print("Manchester Triage System ready")
        
        # Simulation state
        self.env = None
        
        # Keep legacy counters for backwards compatibility
        self.patient_count = 0
        self.total_time = 0
        self.categories = []
    
    def get_patient(self):
        """Get next patient, cycling through data infinitely."""
        if not self.patient_ids:
            return None
        
        patient_id = self.patient_ids[self.current_index]
        patient_data = self.patients[patient_id]
        self.current_index = (self.current_index + 1) % len(self.patient_ids)
        
        return patient_id, patient_data
    
    def simple_triage(self):
        """Simple random triage assignment."""
        categories = ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE']
        priorities = [1, 2, 3, 4, 5]
        idx = random.choices(range(5), weights=[0.05, 0.15, 0.30, 0.40, 0.10])[0]
        return categories[idx], priorities[idx]
    
    def patient_flow(self, patient_num):
        """Simulate patient journey with NHS metrics tracking."""
        arrival_time = self.env.now
        
        # Get patient data
        patient_data = self.get_patient()
        if patient_data:
            patient_id, data = patient_data
            age = 2024 - int(data.get('BIRTHDATE', '2000').split('-')[0]) if data.get('BIRTHDATE') else 30
            gender = data.get('GENDER', 'Unknown')
            # You can add more fields from your patient data here
            presenting_complaint = data.get('REASONDESCRIPTION', 'General')
        else:
            patient_id, age, gender = f"fake_{patient_num}", 30, 'Unknown'
            presenting_complaint = 'General'
        
        # === NHS METRICS: Record Arrival ===
        self.nhs_metrics.record_arrival(
            patient_id=patient_id,
            arrival_time=arrival_time,
            age=age,
            gender=gender,
            presenting_complaint=presenting_complaint
        )
        
        # Triage using simple random triage
        category, priority = self.simple_triage()
        
        # === NHS METRICS: Record Triage Category ===
        self.nhs_metrics.record_triage_category(patient_id, category)
        
        # Triage nurse stage
        triage_start = self.env.now
        # === NHS METRICS: Record Initial Assessment Start ===
        self.nhs_metrics.record_initial_assessment_start(patient_id, triage_start)
        
        with self.triage_resource.request() as req:
            yield req
            triage_service_start = self.env.now
            yield self.env.timeout(random.uniform(5, 10))
        
        # Doctor assessment stage
        assessment_start = self.env.now
        # === NHS METRICS: Record Treatment Start ===
        self.nhs_metrics.record_treatment_start(patient_id, assessment_start)
        
        with self.doctor_resource.request(priority=priority) as req:
            yield req
            assessment_service_start = self.env.now
            yield self.env.timeout(random.uniform(20, 40))
        
        # Diagnostics (50% chance)
        if random.random() < 0.5:
            yield self.env.timeout(random.uniform(30, 60))
        
        # Disposition
        if category in ['RED', 'ORANGE'] and random.random() < 0.6:
            bed_start = self.env.now
            with self.bed_resource.request(priority=priority) as req:
                yield req
                bed_service_start = self.env.now
                yield self.env.timeout(random.uniform(40, 80))
            
            disposition = 'admitted'
            admitted = True
        else:
            yield self.env.timeout(random.uniform(10, 20))
            disposition = 'discharged'
            admitted = False
        
        # === NHS METRICS: Record Departure ===
        departure_time = self.env.now
        self.nhs_metrics.record_departure(
            patient_id=patient_id,
            departure_time=departure_time,
            disposal=disposition,
            admitted=admitted
        )
        
        # Legacy counters for backwards compatibility
        total_time = departure_time - arrival_time
        self.patient_count += 1
        self.total_time += total_time
        self.categories.append(category)
        
        print(f"Patient {patient_id} ({category}, Age: {age}, {gender}): "
              f"{total_time:.1f} min, {disposition}")
    
    def arrivals(self):
        """Generate Poisson arrivals."""
        patient_num = 0
        while True:
            # Poisson process: exponential interarrival times
            interarrival = random.expovariate(self.arrival_rate / 60)  # Convert to per-minute
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
        
        print(f"\\nSimulation Complete!")
        print(f"Legacy Results: {self.patient_count} patients, avg time: {avg_time:.1f} min")
        
        # === NHS METRICS: Generate Dashboard ===
        print("\\n" + "="*50)
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
        return self.nhs_metrics.get_official_nhs_metrics()
    
    def export_nhs_data(self, json_filepath: str = None, csv_filepath: str = None):
        """Export NHS metrics and patient data"""
        if json_filepath:
            metrics = self.nhs_metrics.get_official_nhs_metrics()
            with open(json_filepath, 'w') as f:
                json.dump(metrics, f, indent=2)
            print(f"NHS metrics exported to {json_filepath}")
        
        if csv_filepath:
            if not self.nhs_metrics.patients:
                print("No patient data to export")
                return
            
            data = []
            for p in self.nhs_metrics.patients:
                data.append({
                    'patient_id': p.patient_id,
                    'arrival_time': p.arrival_time,
                    'age': p.age,
                    'gender': p.gender,
                    'triage_category': p.triage_category,
                    'initial_assessment_start': p.initial_assessment_start,
                    'treatment_start': p.treatment_start,
                    'departure_time': p.departure_time,
                    'total_time_minutes': p.total_time_in_ae(),
                    'time_to_assessment_minutes': p.time_to_initial_assessment(),
                    'time_to_treatment_minutes': p.time_to_treatment(),
                    'meets_4hour_standard': p.meets_4hour_standard(),
                    'is_reattendance': p.is_reattendance,
                    'admitted': p.admitted,
                    'disposal': p.disposal,
                    'presenting_complaint': p.presenting_complaint
                })
            
            df = pd.DataFrame(data)
            df.to_csv(csv_filepath, index=False)
            print(f"Patient data exported to {csv_filepath}")

# Example usage demonstrating the integration
if __name__ == "__main__":
    # Your existing usage pattern works exactly the same
    hospital = SimpleHospital(
        csv_folder='./output/csv',
        sim_duration=480,  # 8 hours
        arrival_rate=12,   # patients per hour
        nurses=3,
        doctors=6,
        beds=20
    )
    
    # Run simulation - now with NHS metrics
    results = hospital.run()
    
    # Access legacy results (backwards compatible)
    print(f"\\nLegacy access: {results['total_patients']} patients processed")
    
    # Access new NHS metrics
    nhs_data = hospital.get_nhs_metrics()
    print(f"NHS 4-hour compliance: {nhs_data['4hour_standard_compliance_pct']:.1f}%")
    
    # Export data
    hospital.export_nhs_data(
        json_filepath='nhs_metrics.json',
        csv_filepath='patient_data.csv'
    )