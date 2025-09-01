import simpy
import numpy as np
import random
from collections import defaultdict
from scipy.stats import truncnorm

class FakeHospital:
    def __init__(self, triage_nurse_capacity=2, doctor_capacity=6, bed_capacity=15,
                 sim_duration=1440, arrival_peak_rate=15, arrival_offpeak_rate=5):
        self.triage_nurse_capacity = triage_nurse_capacity
        self.doctor_capacity = doctor_capacity
        self.bed_capacity = bed_capacity
        self.sim_duration = sim_duration
        self.arrival_peak_rate = arrival_peak_rate
        self.arrival_offpeak_rate = arrival_offpeak_rate
        self.env = None
        self.metrics = None

    def mts_triage(self, numeric_inputs, symptoms):
        categories = ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE']
        wait_times = ['0 min', '10 min', '60 min', '120 min', '240 min']
        # FIXED: SimPy priority system uses LOWER numbers for HIGHER priority
        # RED (most urgent) = 1, BLUE (least urgent) = 5
        priorities = [1, 2, 3, 4, 5]  # RED=1 (highest), ORANGE=2, YELLOW=3, GREEN=4, BLUE=5 (lowest)
        # Realistic category distribution: 5% RED, 15% ORANGE, 30% YELLOW, 40% GREEN, 10% BLUE
        idx = random.choices(range(5), weights=[0.05, 0.15, 0.30, 0.40, 0.10])[0]
        return {
            'flowchart_used': 'chest_pain',  # Can be dynamic
            'triage_category': np.str_(categories[idx]),
            'wait_time': np.str_(wait_times[idx]),
            'fuzzy_score': random.uniform(1, 5),
            'symptoms_processed': symptoms,
            'numeric_inputs': numeric_inputs,
            'priority_score': np.int64(priorities[idx])  # Now correctly: 1=highest, 5=lowest
        }

    def arrival_rate(self, hour):
        if 8 <= hour < 20:  # Peak daytime
            return self.arrival_peak_rate
        else:  # Off-peak
            return self.arrival_offpeak_rate

    def truncated_normal(self, mean, std):
        a = -mean / std  # Lower bound at 0
        return truncnorm(a, np.inf, loc=mean, scale=std).rvs()

    def patient(self, patient_id, triage_nurses, doctors, beds):
        arrival_time = self.env.now
        
        # Simulate inputs for MTS
        numeric_inputs = [random.uniform(0, 10) for _ in range(5)]  # e.g., pain levels
        symptoms = {
            'severe_pain': random.choice(['none', 'moderate', 'severe', 'very_severe']),
            'crushing_sensation': random.choice(['none', 'moderate', 'severe']),
            # Add more symptoms as needed for your MTS
        }
        
        # Run custom triage
        triage_result = self.mts_triage(numeric_inputs, symptoms)
        category = str(triage_result['triage_category'])
        priority = int(triage_result['priority_score'])  # Higher = more urgent
        max_wait_min = int(triage_result['wait_time'].split()[0])
        
        # Triage process
        with triage_nurses.request() as req:
            yield req
            triage_start = self.env.now
            yield self.env.timeout(self.truncated_normal(7, 2))  # Triage time ~5-10 min
        self.metrics['triage_wait'].append(self.env.now - arrival_time)
        
        # Assessment (priority queue for doctors)
        assess_start = self.env.now
        with doctors.request(priority=priority) as req:  # FIXED: Use priority directly (1=highest, 5=lowest)
            yield req
            yield self.env.timeout(self.truncated_normal(30, 10))  # Consult ~20-40 min
        assess_wait = self.env.now - assess_start
        self.metrics['assess_wait'][category].append(assess_wait)
        if assess_wait > max_wait_min:
            self.metrics['mts_breaches'].append(1)
        
        # Diagnostics (probabilistic)
        if random.random() < 0.5:  # 50% chance
            yield self.env.timeout(self.truncated_normal(45, 15))  # Labs/imaging ~30-60 min
        
        # Disposition
        if random.random() < 0.2:  # 20% admission
            with beds.request(priority=priority) as req:  # FIXED: Use priority directly (1=highest, 5=lowest)
                yield req
                yield self.env.timeout(self.truncated_normal(60, 20))  # Admission ~40-80 min
            disposition = 'admitted'
        else:  # Discharge
            yield self.env.timeout(self.truncated_normal(15, 5))  # Final steps ~10-20 min
            disposition = 'discharged'
        
        total_time = self.env.now - arrival_time
        self.metrics['total_time'].append(total_time)
        self.metrics['four_hour_breaches'] += 1 if total_time > 240 else 0
        print(f"Patient {patient_id} ({category}): Total time {total_time:.1f} min, Disposition: {disposition}")

    def arrivals(self, triage_nurses, doctors, beds):
        """
        SimPy process to generate patient arrivals.
        """
        patient_id = 0
        while True:
            hour = (self.env.now // 60) % 24
            interarrival = random.expovariate(self.arrival_rate(hour) / 60)  # Min between arrivals
            yield self.env.timeout(interarrival)
            patient_id += 1
            self.env.process(self.patient(patient_id, triage_nurses, doctors, beds))

    def run_simulation(self):
        """
        Run the full simulation and collect metrics.
        
        :return: Dict of simulation metrics
        """
        self.env = simpy.Environment()
        triage_nurses = simpy.Resource(self.env, capacity=self.triage_nurse_capacity)
        doctors = simpy.PriorityResource(self.env, capacity=self.doctor_capacity)
        beds = simpy.PriorityResource(self.env, capacity=self.bed_capacity)
        
        self.metrics = {
            'triage_wait': [],
            'assess_wait': defaultdict(list),
            'total_time': [],
            'mts_breaches': [],
            'four_hour_breaches': 0
        }
        
        self.env.process(self.arrivals(triage_nurses, doctors, beds))
        self.env.run(until=self.sim_duration)
        
        return self.get_metrics()

    def get_metrics(self):
        """
        Compute and return averaged metrics after simulation.
        
        :return: Dict with averaged results
        """
        if self.metrics is None:
            raise ValueError("Simulation must be run first.")
        
        results = {
            'avg_triage_wait': np.mean(self.metrics['triage_wait']) if self.metrics['triage_wait'] else 0,
            'avg_assess_wait_by_category': {cat: np.mean(waits) if waits else 0 for cat, waits in self.metrics['assess_wait'].items()},
            'avg_total_time': np.mean(self.metrics['total_time']) if self.metrics['total_time'] else 0,
            'mts_breach_count': len(self.metrics['mts_breaches']),
            'four_hour_breach_count': self.metrics['four_hour_breaches'],
            'four_hour_breach_pct': (self.metrics['four_hour_breaches'] / len(self.metrics['total_time'])) * 100 if self.metrics['total_time'] else 0,
            'total_patients': len(self.metrics['total_time'])
        }
        return results

# Example usage:
if __name__ == "__main__":
    hospital = FakeHospital()
    metrics = hospital.run_simulation()
    print("\nSimulation Metrics:")
    print(f"Average Triage Wait: {metrics['avg_triage_wait']:.1f} min")
    print("Average Assessment Wait by Category:")
    for cat, avg in metrics['avg_assess_wait_by_category'].items():
        print(f"  {cat}: {avg:.1f} min")
    print(f"Average Total Time: {metrics['avg_total_time']:.1f} min")
    print(f"MTS Target Breaches: {metrics['mts_breach_count']}")
    print(f"4-Hour Breaches: {metrics['four_hour_breach_count']} ({metrics['four_hour_breach_pct']:.1f}%)")
    print(f"Total Patients: {metrics['total_patients']}")