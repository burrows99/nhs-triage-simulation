import numpy as np
from typing import List, Dict, Any, Tuple
from .base_triage import BaseTriage, TriageResult
from ..entities.patient import Patient, Priority


class ManchesterTriage(BaseTriage):
    """Manchester Triage System implementation based on fuzzy MTS research <mcreference link="https://www.researchgate.net/publication/286737453_FMTS_A_fuzzy_implementation_of_the_Manchester_triage_system" index="0">0</mcreference>"""
    
    def __init__(self):
        super().__init__("Manchester Triage System")
        
        # Manchester Triage System discriminators and flowcharts
        self.discriminators = {
            # Immediate (Red) - Life threatening
            'cardiac_arrest': {
                'priority': Priority.IMMEDIATE,
                'keywords': ['cardiac arrest', 'no pulse', 'cpr', 'resuscitation'],
                'vital_thresholds': {'heart_rate': (0, 30)}
            },
            'respiratory_arrest': {
                'priority': Priority.IMMEDIATE,
                'keywords': ['not breathing', 'respiratory arrest', 'apnea'],
                'vital_thresholds': {'respiratory_rate': (0, 5)}
            },
            'unconscious': {
                'priority': Priority.IMMEDIATE,
                'keywords': ['unconscious', 'unresponsive', 'coma', 'gcs'],
                'vital_thresholds': {'consciousness_level': (0, 8)}
            },
            'severe_shock': {
                'priority': Priority.IMMEDIATE,
                'keywords': ['severe shock', 'hypotensive shock'],
                'vital_thresholds': {'systolic_bp': (0, 70)}
            },
            
            # Very Urgent (Orange) - Imminently life threatening
            'chest_pain_cardiac': {
                'priority': Priority.VERY_URGENT,
                'keywords': ['chest pain', 'cardiac', 'heart attack', 'myocardial'],
                'vital_thresholds': {'heart_rate': (120, 200), 'systolic_bp': (160, 250)}
            },
            'severe_breathing_difficulty': {
                'priority': Priority.VERY_URGENT,
                'keywords': ['difficulty breathing', 'dyspnea', 'shortness of breath', 'wheezing'],
                'vital_thresholds': {'respiratory_rate': (25, 40), 'oxygen_saturation': (85, 94)}
            },
            'altered_consciousness': {
                'priority': Priority.VERY_URGENT,
                'keywords': ['confused', 'disoriented', 'altered mental state'],
                'vital_thresholds': {'consciousness_level': (9, 12)}
            },
            'severe_bleeding': {
                'priority': Priority.VERY_URGENT,
                'keywords': ['severe bleeding', 'hemorrhage', 'blood loss'],
                'vital_thresholds': {'systolic_bp': (70, 90)}
            },
            'severe_pain': {
                'priority': Priority.VERY_URGENT,
                'keywords': ['severe pain', 'excruciating'],
                'vital_thresholds': {'pain_score': (8, 10)}
            },
            
            # Urgent (Yellow) - Urgent but not immediately life threatening
            'moderate_pain': {
                'priority': Priority.URGENT,
                'keywords': ['moderate pain', 'significant pain'],
                'vital_thresholds': {'pain_score': (5, 7)}
            },
            'head_injury': {
                'priority': Priority.URGENT,
                'keywords': ['head injury', 'head trauma', 'concussion'],
                'vital_thresholds': {}
            },
            'fever_high': {
                'priority': Priority.URGENT,
                'keywords': ['high fever', 'hyperthermia'],
                'vital_thresholds': {'temperature': (38.5, 42.0)}
            },
            'vomiting_blood': {
                'priority': Priority.URGENT,
                'keywords': ['vomiting blood', 'hematemesis'],
                'vital_thresholds': {}
            },
            
            # Standard (Green) - Less urgent
            'minor_injury': {
                'priority': Priority.STANDARD,
                'keywords': ['minor injury', 'sprain', 'bruise', 'cut'],
                'vital_thresholds': {'pain_score': (2, 4)}
            },
            'mild_symptoms': {
                'priority': Priority.STANDARD,
                'keywords': ['mild', 'slight', 'minor'],
                'vital_thresholds': {}
            },
            'fever_low': {
                'priority': Priority.STANDARD,
                'keywords': ['fever', 'temperature'],
                'vital_thresholds': {'temperature': (37.5, 38.4)}
            },
            
            # Non-urgent (Blue) - Non-urgent
            'chronic_condition': {
                'priority': Priority.NON_URGENT,
                'keywords': ['chronic', 'ongoing', 'routine'],
                'vital_thresholds': {}
            },
            'minor_complaint': {
                'priority': Priority.NON_URGENT,
                'keywords': ['cold', 'cough', 'rash', 'prescription'],
                'vital_thresholds': {'pain_score': (0, 2)}
            }
        }
        
        # Fuzzy linguistic terms for vital signs assessment
        self.vital_fuzzy_ranges = {
            'systolic_bp': {
                'very_low': (0, 90),
                'low': (90, 110),
                'normal': (110, 140),
                'high': (140, 180),
                'very_high': (180, 300)
            },
            'heart_rate': {
                'very_low': (0, 50),
                'low': (50, 60),
                'normal': (60, 100),
                'high': (100, 120),
                'very_high': (120, 200)
            },
            'respiratory_rate': {
                'very_low': (0, 8),
                'low': (8, 12),
                'normal': (12, 20),
                'high': (20, 30),
                'very_high': (30, 60)
            },
            'temperature': {
                'very_low': (30, 35),
                'low': (35, 36.5),
                'normal': (36.5, 37.5),
                'high': (37.5, 39),
                'very_high': (39, 45)
            },
            'oxygen_saturation': {
                'very_low': (0, 85),
                'low': (85, 94),
                'normal': (94, 100),
                'high': (100, 100),
                'very_high': (100, 100)
            },
            'pain_score': {
                'none': (0, 1),
                'mild': (1, 3),
                'moderate': (3, 6),
                'severe': (6, 8),
                'very_severe': (8, 10)
            }
        }
    
    def assess_patients(self, patients: List[Patient]) -> List[TriageResult]:
        """Assess multiple patients using Manchester Triage System"""
        results = []
        
        for patient in patients:
            result = self.assess_single_patient(patient)
            results.append(result)
            self._record_assessment(result)
        
        return results
    
    def assess_single_patient(self, patient: Patient) -> TriageResult:
        """Assess a single patient using Manchester Triage flowcharts"""
        
        # Step 1: Check for immediate life-threatening conditions
        priority, reason, confidence = self._evaluate_discriminators(patient)
        
        # Step 2: Assess vital signs using fuzzy logic
        vital_priority, vital_reason, vital_confidence = self._assess_vital_signs(patient)
        
        # Step 3: Consider age-specific factors
        age_priority, age_reason = self._assess_age_factors(patient)
        
        # Step 4: Combine assessments (take highest priority)
        final_priority = min(priority, vital_priority, age_priority, key=lambda p: p.value)
        
        # Combine reasons
        reasons = [r for r in [reason, vital_reason, age_reason] if r]
        final_reason = "; ".join(reasons) if reasons else "Standard Manchester Triage assessment"
        
        # Calculate confidence (average of non-zero confidences)
        confidences = [c for c in [confidence, vital_confidence] if c > 0]
        final_confidence = sum(confidences) / len(confidences) if confidences else 0.8
        
        # Calculate service time
        service_time = self._calculate_service_time(final_priority, patient)
        
        return TriageResult(
            patient=patient,
            priority=final_priority,
            reason=final_reason,
            service_time=service_time,
            confidence_score=final_confidence
        )
    
    def _evaluate_discriminators(self, patient: Patient) -> Tuple[Priority, str, float]:
        """Evaluate patient against Manchester Triage discriminators"""
        highest_priority = Priority.NON_URGENT
        matched_discriminators = []
        confidence = 0.0
        
        # Check chief complaint against discriminators
        if patient.chief_complaint:
            complaint_lower = patient.chief_complaint.lower()
            
            for disc_name, disc_info in self.discriminators.items():
                # Check keyword matching
                keyword_match = any(keyword in complaint_lower for keyword in disc_info['keywords'])
                
                # Check vital sign thresholds
                vital_match = self._check_vital_thresholds(patient, disc_info['vital_thresholds'])
                
                if keyword_match or vital_match:
                    disc_priority = disc_info['priority']
                    if disc_priority.value < highest_priority.value:
                        highest_priority = disc_priority
                    
                    match_strength = 0.8 if keyword_match else 0.6
                    if vital_match:
                        match_strength += 0.2
                    
                    matched_discriminators.append((disc_name, match_strength))
                    confidence = max(confidence, match_strength)
        
        # Create reason string
        if matched_discriminators:
            disc_names = [name.replace('_', ' ').title() for name, _ in matched_discriminators]
            reason = f"Manchester discriminator(s): {', '.join(disc_names)}"
        else:
            reason = ""
        
        return highest_priority, reason, confidence
    
    def _check_vital_thresholds(self, patient: Patient, thresholds: Dict[str, Tuple[float, float]]) -> bool:
        """Check if patient's vital signs meet discriminator thresholds"""
        if not thresholds:
            return False
        
        for vital_name, (min_val, max_val) in thresholds.items():
            vital_value = patient.get_current_vital_sign(vital_name)
            if vital_value is not None:
                if min_val <= vital_value <= max_val:
                    return True
        
        return False
    
    def _assess_vital_signs(self, patient: Patient) -> Tuple[Priority, str, float]:
        """Assess vital signs using fuzzy logic approach"""
        priority = Priority.NON_URGENT
        abnormal_vitals = []
        confidence = 0.0
        
        for vital_name, ranges in self.vital_fuzzy_ranges.items():
            vital_value = patient.get_current_vital_sign(vital_name)
            if vital_value is not None:
                category, severity = self._categorize_vital_sign(vital_name, vital_value, ranges)
                
                if category in ['very_low', 'very_high']:
                    priority = min(priority, Priority.IMMEDIATE, key=lambda p: p.value)
                    abnormal_vitals.append(f"Critical {vital_name}: {vital_value}")
                    confidence = max(confidence, 0.9)
                elif category in ['low', 'high']:
                    priority = min(priority, Priority.VERY_URGENT, key=lambda p: p.value)
                    abnormal_vitals.append(f"Abnormal {vital_name}: {vital_value}")
                    confidence = max(confidence, 0.7)
                elif category == 'severe' and vital_name == 'pain_score':
                    priority = min(priority, Priority.VERY_URGENT, key=lambda p: p.value)
                    abnormal_vitals.append(f"Severe pain: {vital_value}/10")
                    confidence = max(confidence, 0.8)
                elif category == 'moderate' and vital_name == 'pain_score':
                    priority = min(priority, Priority.URGENT, key=lambda p: p.value)
                    abnormal_vitals.append(f"Moderate pain: {vital_value}/10")
                    confidence = max(confidence, 0.6)
        
        reason = "; ".join(abnormal_vitals) if abnormal_vitals else ""
        return priority, reason, confidence
    
    def _categorize_vital_sign(self, vital_name: str, value: float, ranges: Dict[str, Tuple[float, float]]) -> Tuple[str, float]:
        """Categorize vital sign value using fuzzy ranges"""
        for category, (min_val, max_val) in ranges.items():
            if min_val <= value <= max_val:
                # Calculate severity within range (0.0 to 1.0)
                if category in ['very_low', 'very_high']:
                    severity = 1.0
                elif category in ['low', 'high']:
                    severity = 0.7
                else:
                    severity = 0.3
                return category, severity
        
        # If no range matches, assume normal
        return 'normal', 0.0
    
    def _assess_age_factors(self, patient: Patient) -> Tuple[Priority, str]:
        """Assess age-related priority factors"""
        if patient.age is None:
            return Priority.NON_URGENT, ""
        
        # Pediatric considerations (Manchester Triage specific rules)
        if patient.age < 1:  # Infants
            return Priority.URGENT, "Infant (<1 year)"
        elif patient.age < 5:  # Young children
            return Priority.STANDARD, "Young child (<5 years)"
        elif patient.age > 80:  # Elderly
            return Priority.STANDARD, "Elderly patient (>80 years)"
        
        return Priority.NON_URGENT, ""
    
    def _calculate_service_time(self, priority: Priority, patient: Patient) -> float:
        """Calculate expected service/consultation time based on priority and patient complexity"""
        base_service_time = self.get_target_service_time(priority)
        
        # Adjust based on complexity factors
        complexity_multiplier = 1.0
        
        # Age adjustments (more complex cases take longer)
        if patient.age is not None:
            if patient.age < 2:  # Infants require more careful handling
                complexity_multiplier += 0.4
            elif patient.age < 16:  # Pediatric cases
                complexity_multiplier += 0.2
            elif patient.age > 75:  # Elderly may have multiple issues
                complexity_multiplier += 0.3
        
        # Chief complaint complexity
        if patient.chief_complaint:
            complex_complaints = ['chest pain', 'difficulty breathing', 'head injury', 'abdominal pain']
            if any(term in patient.chief_complaint.lower() for term in complex_complaints):
                complexity_multiplier += 0.4  # Complex diagnoses take longer
        
        # Medical history complexity
        if patient.medical_history:
            complexity_multiplier += 0.2  # Existing conditions complicate care
        
        # Pain level affects examination time
        pain_score = patient.get_current_vital_sign('pain_score')
        if pain_score is not None and pain_score >= 7:
            complexity_multiplier += 0.2  # High pain requires more attention
        
        # Add some randomness to simulate real-world variability
        randomness = np.random.uniform(0.8, 1.2)
        
        return base_service_time * complexity_multiplier * randomness