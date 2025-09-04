import random
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
        inter_arrival = random.expovariate(self.arrival_rate)
        self.next_arrival_time = current_time + inter_arrival
        return self.next_arrival_time
    
    def is_finished(self) -> bool:
        return False  # Generate patients continuously until simulation time runs out