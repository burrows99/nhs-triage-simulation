import random
import math
from typing import Optional
from ..entities.patient import Patient
from ..entities.sub_entities.vital_signs import VitalSigns

class RandomService:
    """Default random patient generator"""
    
    CONDITIONS = [
        ("chest_pain", ["shortness_of_breath", "sweating", "nausea"]),
        ("abdominal_pain", ["nausea", "vomiting", "fever"]),
        ("headache", ["dizziness", "light_sensitivity", "nausea"]),
        ("minor_laceration", ["bleeding", "pain"]),
        ("fever", ["chills", "fatigue", "body_aches"]),
        ("cardiac_arrest", ["unconscious", "no_pulse", "cyanosis"]),
        ("stroke_symptoms", ["confusion", "weakness", "speech_difficulty"]),
        ("routine_checkup", []),
        ("allergic_reaction", ["rash", "swelling", "difficulty_breathing"]),
        ("broken_bone", ["severe_pain", "deformity", "swelling"])
    ]
    
    def __init__(self, arrival_rate: float = 0.3):
        self.arrival_rate = arrival_rate
        self.patient_count = 0
        self.next_arrival_time = 0.0
    
    def get_next_patient(self) -> Optional[Patient]:
        condition, symptoms = random.choice(self.CONDITIONS)
        
        # Generate realistic vital signs
        vital_signs = VitalSigns(
            bp_systolic=max(60, random.gauss(120, 25)),
            bp_diastolic=max(40, random.gauss(80, 15)),
            heart_rate=max(40, random.gauss(75, 20)),
            temperature=max(35, random.gauss(36.8, 1.2)),
            oxygen_saturation=min(100, max(85, random.gauss(98, 3)))
        )
        
        self.patient_count += 1
        return Patient(
            id=f"PAT_{self.patient_count:05d}",
            arrival_time=self.next_arrival_time,
            condition=condition,
            symptoms=symptoms,
            vital_signs=vital_signs
        )
    
    def get_next_arrival_time(self, current_time: float) -> float:
        """Time-dependent Poisson arrival process with realistic peak hours"""
        # Calculate time-dependent arrival rate with daily periodicity
        # Peak at 10:00 AM (600 minutes from midnight) with 24-hour cycle
        daily_minutes = 1440  # 24 hours = 1440 minutes
        peak_time = 600  # 10:00 AM in minutes from midnight
        time_in_day = current_time % daily_minutes  # Get time within current day
        time_dependent_rate = self.arrival_rate * (1 + 0.5 * math.exp(-((time_in_day - peak_time)/120)**2))
        
        # Generate inter-arrival time using time-dependent rate
        inter_arrival = random.expovariate(time_dependent_rate)
        self.next_arrival_time = current_time + inter_arrival
        return self.next_arrival_time
    
    def is_finished(self) -> bool:
        return False  # Generate patients continuously until simulation time runs out