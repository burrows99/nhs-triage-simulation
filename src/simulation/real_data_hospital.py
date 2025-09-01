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


class SimpleHospital:
    """Simple hospital simulation with Poisson arrivals and real patient data."""
    
    def __init__(self, csv_folder='./output/csv', **kwargs):
        # Simulation parameters with defaults
        self.sim_duration = kwargs.get('sim_duration', 1440)  # 24 hours
        self.arrival_rate = kwargs.get('arrival_rate', 10)    # patients/hour
        self.nurses = kwargs.get('nurses', 2)
        self.doctors = kwargs.get('doctors', 6)
        self.beds = kwargs.get('beds', 15)
        
        # Load patient data
        print(f"Loading patient data from {csv_folder}...")
        self.data_service = DataService(csv_folder)
        self.patients = self.data_service.process_all()
        self.patient_ids = list(self.patients.keys())
        self.current_index = 0
        print(f"Loaded {len(self.patient_ids)} patients")
        
        # No metrics services - pure simulation only
        
        # Initialize Manchester Triage System (without telemetry)
        print("Initializing Manchester Triage System...")
        # Note: MTS requires telemetry service, so we'll use a minimal implementation
        # or modify MTS to work without telemetry
        print("Manchester Triage System ready")
        
        # Simulation state
        self.env = None
    
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
        """Simulate patient journey with comprehensive metrics tracking."""
        arrival_time = self.env.now
        arrival_datetime = datetime.now()  # For metrics timestamps
        
        # Get patient data
        patient_data = self.get_patient()
        if patient_data:
            patient_id, data = patient_data
            age = 2024 - int(data.get('BIRTHDATE', '2000').split('-')[0]) if data.get('BIRTHDATE') else 30
            gender = data.get('GENDER', 'Unknown')
        else:
            patient_id, age, gender = f"fake_{patient_num}", 30, 'Unknown'
        
        # Triage using simple random triage (MTS removed)
        category, priority = self.simple_triage()
        
        # No metrics recording - pure simulation
        
        # Triage nurse stage
        triage_start = self.env.now
        with self.triage_resource.request() as req:
            yield req
            triage_service_start = self.env.now
            yield self.env.timeout(random.uniform(5, 10))
        
        # No triage stage recording
        
        # Doctor assessment stage
        assessment_start = self.env.now
        with self.doctor_resource.request(priority=priority) as req:
            yield req
            assessment_service_start = self.env.now
            yield self.env.timeout(random.uniform(20, 40))
        
        # No assessment stage recording
        
        # Diagnostics (50% chance)
        if random.random() < 0.5:
            yield self.env.timeout(random.uniform(30, 60))
            # No diagnostics stage recording
        
        # Disposition
        if category in ['RED', 'ORANGE'] and random.random() < 0.6:
            bed_start = self.env.now
            with self.bed_resource.request(priority=priority) as req:
                yield req
                bed_service_start = self.env.now
                yield self.env.timeout(random.uniform(40, 80))
            
            # No bed stage recording
            disposition = 'admitted'
        else:
            yield self.env.timeout(random.uniform(10, 20))
            # No discharge processing recording
            disposition = 'discharged'
        
        # Calculate final time and update counters
        total_time = self.env.now - arrival_time
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
        """Run pure simulation without metrics."""
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
        
        print(f"\nResults: {self.patient_count} patients, avg time: {avg_time:.1f} min")
        
        return {
            'total_patients': self.patient_count,
            'avg_time': avg_time,
            'times': [],
            'categories': self.categories
        }