import random
from typing import List, Optional
from faker import Faker
from ..entities.patient.patient import Patient
from ..entities.patient.symptoms import Symptoms
from ..enums.priority import Priority

class PatientFactory:
    """Factory service for generating realistic patient data using Faker"""
    
    def __init__(self) -> None:
        self.fake: Faker = Faker()
        
        # Predefined symptom categories for realistic generation
        self.critical_symptoms = [
            "cardiac arrest", "severe bleeding", "unconscious", "not breathing",
            "severe trauma", "anaphylaxis", "severe burns", "stroke symptoms"
        ]
        
        self.very_urgent_symptoms = [
            "chest pain", "difficulty breathing", "severe pain", "high fever",
            "sepsis", "severe headache", "seizure", "severe vomiting"
        ]
        
        self.urgent_symptoms = [
            "moderate pain", "abdominal pain", "fever", "headache",
            "nausea", "dizziness", "rash", "cough"
        ]
        
        self.standard_symptoms = [
            "mild pain", "minor cut", "bruise", "cold symptoms",
            "sore throat", "minor burn", "sprain"
        ]
        
        self.non_urgent_symptoms = [
            "minor headache", "mild rash", "minor scrape", "fatigue",
            "mild nausea", "minor ache"
        ]
        
        # Medical history keywords
        self.medical_conditions = [
            "diabetes", "hypertension", "heart disease", "asthma", "arthritis",
            "cancer history", "surgery history", "chronic pain", "allergies",
            "depression", "anxiety", "migraine", "kidney disease"
        ]
    
    def generate_symptoms_by_priority(self, target_priority: Priority) -> List[str]:
        """Generate symptoms that would likely result in the target priority"""
        if target_priority == Priority.RED:
            return random.sample(self.critical_symptoms, random.randint(1, 2))
        elif target_priority == Priority.ORANGE:
            return random.sample(self.very_urgent_symptoms, random.randint(1, 3))
        elif target_priority == Priority.YELLOW:
            return random.sample(self.urgent_symptoms, random.randint(1, 2))
        elif target_priority == Priority.GREEN:
            return random.sample(self.standard_symptoms, random.randint(1, 2))
        else:  # BLUE
            return random.sample(self.non_urgent_symptoms, random.randint(1, 2))
    
    def generate_random_symptoms(self) -> List[str]:
        """Generate random symptoms from any category"""
        all_symptoms = (
            self.critical_symptoms + self.very_urgent_symptoms + 
            self.urgent_symptoms + self.standard_symptoms + self.non_urgent_symptoms
        )
        return random.sample(all_symptoms, random.randint(1, 3))
    
    def generate_medical_history(self) -> str:
        """Generate realistic medical history"""
        if random.choice([True, False]):  # 50% chance of having medical history
            conditions = random.sample(self.medical_conditions, random.randint(1, 3))
            return f"Patient has history of {', '.join(conditions)}. "
        return "No significant medical history."
    
    def create_patient(self, target_priority: Optional[Priority] = None) -> Patient:
        """Create a single patient with optional target priority"""
        # Generate basic patient info
        name: str = self.fake.name()
        
        # Generate symptoms based on target priority or random
        if target_priority:
            symptom_list: List[str] = self.generate_symptoms_by_priority(target_priority)
        else:
            symptom_list = self.generate_random_symptoms()
        
        symptoms: Symptoms = Symptoms(symptoms=symptom_list)
        
        # Generate medical history
        history: str = self.generate_medical_history()
        
        return Patient(
            id=random.randint(1000, 9999),
            name=name,
            symptoms=symptoms,
            history=history
        )
    
    def create_patients(self, count: int, target_priority: Optional[Priority] = None) -> List[Patient]:
        """Create multiple patients"""
        return [self.create_patient(target_priority) for _ in range(count)]
    
    def create_emergency_patient(self) -> Patient:
        """Create a patient with critical symptoms (RED priority)"""
        return self.create_patient(Priority.RED)
    
    def create_urgent_patient(self) -> Patient:
        """Create a patient with very urgent symptoms (ORANGE priority)"""
        return self.create_patient(Priority.ORANGE)
    
    def create_standard_patient(self) -> Patient:
        """Create a patient with standard symptoms (GREEN priority)"""
        return self.create_patient(Priority.GREEN)
    
    def create_mixed_priority_patients(self, count: int) -> List[Patient]:
        """Create patients with mixed priority levels"""
        patients: List[Patient] = []
        priorities: List[Priority] = [Priority.RED, Priority.ORANGE, Priority.YELLOW, Priority.GREEN, Priority.BLUE]
        
        for _ in range(count):
            priority: Priority = random.choice(priorities)
            patients.append(self.create_patient(priority))
        
        return patients
    
    def create_batch_by_priority(self, red: int = 0, orange: int = 0, yellow: int = 0, 
                                green: int = 0, blue: int = 0) -> List[Patient]:
        """Create a specific batch of patients by priority counts"""
        patients: List[Patient] = []
        
        patients.extend(self.create_patients(red, Priority.RED))
        patients.extend(self.create_patients(orange, Priority.ORANGE))
        patients.extend(self.create_patients(yellow, Priority.YELLOW))
        patients.extend(self.create_patients(green, Priority.GREEN))
        patients.extend(self.create_patients(blue, Priority.BLUE))
        
        # Shuffle to randomize order
        random.shuffle(patients)
        return patients