import random
from typing import Dict, Any, Optional, List
from ..models.entities.patient import Patient
from ..enums.patient_enums import PresentingComplaint, ArrivalMode, AgeGroup


class PatientFactory:
    """Factory for creating realistic patient instances with Manchester Triage System attributes."""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize the patient factory with optional seed for reproducibility."""
        if seed is not None:
            random.seed(seed)
    
    def create_patient(self, entity_id: int, name: Optional[str] = None) -> Patient:
        """Create a patient with randomized realistic attributes."""
        if name is None:
            name = f"Patient_{entity_id}"
        
        # Generate age and corresponding age group
        age_group = random.choice(list(AgeGroup))
        age = random.randint(age_group.min_age, age_group.max_age)
        
        # Generate presenting complaint
        complaint = random.choice(list(PresentingComplaint))
        
        # Generate arrival mode (weighted towards more common modes)
        arrival_mode = random.choices(
            list(ArrivalMode),
            weights=[40, 25, 5, 2, 20, 5, 3],  # Walk-in and ambulance most common
            k=1
        )[0]
        
        # Generate vital signs based on age and complaint severity
        vital_signs = self._generate_vital_signs(age, complaint)
        
        # Generate priority based on complaint and vital signs
        priority = self._determine_priority(complaint, vital_signs, age)
        
        # Generate patient history
        history = self._generate_history(complaint, age_group)
        
        return Patient(
            entity_id=entity_id,
            name=name,
            priority=priority,
            presenting_complaint=complaint.value,
            vital_signs=vital_signs,
            age=age,
            arrival_mode=arrival_mode.value,
            history=history
        )
    
    def create_critical_patient(self, entity_id: int, name: Optional[str] = None) -> Patient:
        """Create a patient with critical/high priority conditions."""
        if name is None:
            name = f"Critical_{entity_id}"
        
        # Critical complaints
        critical_complaints = [
            PresentingComplaint.CARDIAC_ARREST,
            PresentingComplaint.STROKE_SYMPTOMS,
            PresentingComplaint.TRAUMA,
            PresentingComplaint.OVERDOSE,
            PresentingComplaint.SEIZURE
        ]
        
        complaint = random.choice(critical_complaints)
        age = random.randint(25, 75)  # Adults more likely for critical conditions
        
        # Critical patients usually arrive by ambulance
        arrival_mode = random.choices(
            [ArrivalMode.AMBULANCE, ArrivalMode.HELICOPTER, ArrivalMode.POLICE],
            weights=[70, 20, 10],
            k=1
        )[0]
        
        # Generate abnormal vital signs
        vital_signs = self._generate_critical_vital_signs(age)
        
        return Patient(
            entity_id=entity_id,
            name=name,
            priority="Red",  # Always highest priority
            presenting_complaint=complaint.value,
            vital_signs=vital_signs,
            age=age,
            arrival_mode=arrival_mode.value,
            history=f"Critical condition: {complaint.value}"
        )
    
    def _generate_vital_signs(self, age: int, complaint: PresentingComplaint) -> Dict[str, Any]:
        """Generate realistic vital signs based on age and complaint."""
        # Base normal ranges adjusted for age
        if age < 18:
            hr_range = (80, 120)
            bp_systolic = (90, 110)
            bp_diastolic = (50, 70)
            temp_range = (36.5, 37.2)
        elif age < 65:
            hr_range = (60, 100)
            bp_systolic = (110, 140)
            bp_diastolic = (70, 90)
            temp_range = (36.1, 37.2)
        else:
            hr_range = (65, 95)
            bp_systolic = (120, 160)
            bp_diastolic = (70, 95)
            temp_range = (36.0, 37.1)
        
        # Adjust for complaint severity
        if complaint in [PresentingComplaint.FEVER, PresentingComplaint.ALLERGIC_REACTION]:
            temp_range = (37.5, 39.5)
        elif complaint == PresentingComplaint.CHEST_PAIN:
            hr_range = (80, 120)
            bp_systolic = (140, 180)
        
        return {
            "heart_rate": random.randint(*hr_range),
            "blood_pressure": f"{random.randint(*bp_systolic)}/{random.randint(*bp_diastolic)}",
            "temperature": round(random.uniform(*temp_range), 1),
            "respiratory_rate": random.randint(12, 20),
            "oxygen_saturation": random.randint(95, 100)
        }
    
    def _generate_critical_vital_signs(self, age: int) -> Dict[str, Any]:
        """Generate abnormal vital signs for critical patients."""
        return {
            "heart_rate": random.choice([random.randint(30, 50), random.randint(120, 180)]),
            "blood_pressure": random.choice(["80/40", "200/120", "60/30"]),
            "temperature": random.choice([35.0, 40.5, 34.2]),
            "respiratory_rate": random.choice([8, 35, 6]),
            "oxygen_saturation": random.randint(70, 90)
        }
    
    def _determine_priority(self, complaint: PresentingComplaint, vital_signs: Dict[str, Any], age: int) -> str:
        """Determine triage priority based on complaint, vital signs, and age."""
        # Critical conditions always get Red priority
        if complaint in [PresentingComplaint.CARDIAC_ARREST, PresentingComplaint.STROKE_SYMPTOMS]:
            return "Red"
        
        # Check vital signs for abnormalities
        hr = vital_signs["heart_rate"]
        temp = vital_signs["temperature"]
        o2_sat = vital_signs["oxygen_saturation"]
        
        # Red priority conditions
        if hr < 40 or hr > 150 or temp > 39.0 or o2_sat < 90:
            return "Red"
        
        # Orange priority conditions
        if complaint in [PresentingComplaint.CHEST_PAIN, PresentingComplaint.SHORTNESS_OF_BREATH, PresentingComplaint.TRAUMA]:
            return "Orange"
        
        if hr < 50 or hr > 120 or temp > 38.5 or o2_sat < 95:
            return "Orange"
        
        # Yellow priority conditions
        if complaint in [PresentingComplaint.ABDOMINAL_PAIN, PresentingComplaint.HEADACHE, PresentingComplaint.FEVER]:
            return "Yellow"
        
        # Age-based priority adjustment
        if age < 2 or age > 80:
            priorities = ["Orange", "Yellow"]
            return random.choice(priorities)
        
        # Default to Green or Blue for minor conditions
        return random.choice(["Green", "Blue"])
    
    def _generate_history(self, complaint: PresentingComplaint, age_group: AgeGroup) -> str:
        """Generate a brief patient history based on complaint and age."""
        histories = {
            PresentingComplaint.CHEST_PAIN: [
                "History of hypertension",
                "Previous MI 2 years ago",
                "Family history of cardiac disease",
                "No significant cardiac history"
            ],
            PresentingComplaint.SHORTNESS_OF_BREATH: [
                "History of asthma",
                "COPD diagnosis",
                "Recent upper respiratory infection",
                "No respiratory history"
            ],
            PresentingComplaint.TRAUMA: [
                "Motor vehicle accident",
                "Fall from height",
                "Sports injury",
                "Workplace accident"
            ],
            PresentingComplaint.FEVER: [
                "Recent travel",
                "Flu-like symptoms for 3 days",
                "Contact with sick family member",
                "No recent illness"
            ]
        }
        
        complaint_histories = histories.get(complaint, ["No significant medical history"])
        base_history = random.choice(complaint_histories)
        
        # Add age-specific context
        if age_group in [AgeGroup.SENIOR, AgeGroup.ELDERLY]:
            base_history += ". Multiple comorbidities."
        elif age_group in [AgeGroup.INFANT, AgeGroup.TODDLER]:
            base_history += ". Accompanied by parent/guardian."
        
        return base_history
    
    def create_batch(self, count: int, critical_ratio: float = 0.1) -> List[Patient]:
        """Create a batch of patients with a specified ratio of critical cases."""
        patients: List[Patient] = []
        critical_count = int(count * critical_ratio)
        
        # Create critical patients
        for i in range(critical_count):
            patients.append(self.create_critical_patient(i))
        
        # Create regular patients
        for i in range(critical_count, count):
            patients.append(self.create_patient(i))
        
        return patients