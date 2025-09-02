import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from src.triage.triage_constants import (
    TriageFlowcharts, SymptomKeys, LinguisticValues, TriageCategories,
    MedicalConditions, VitalSignCategories, FlowchartNames, CommonStrings, SymptomNames
)


class DataCleanupService:
    """Service for cleaning and processing patient data from Synthea CSV files."""
    
    def __init__(self):
        self.symptom_mappings = {
            'pain_keywords': CommonStrings.PAIN_KEYWORDS,
            'cardiac_keywords': MedicalConditions.get_cardiac_conditions() + [CommonStrings.CARDIAC_KEYWORD],
            'respiratory_keywords': MedicalConditions.get_respiratory_conditions() + [CommonStrings.RESPIRATORY_KEYWORD],
            'neurological_keywords': MedicalConditions.get_neurological_conditions() + [CommonStrings.NEUROLOGICAL_KEYWORD]
        }
    
    def convert_wait_time_to_minutes(self, wait_time_str: str, random_service) -> float:
        """Convert MTS wait time string to numeric minutes with random variation.
        
        Args:
            wait_time_str: MTS wait time string (e.g., 'immediate', '10 min', etc.)
            random_service: RandomService instance for generating variations
            
        Returns:
            Wait time in minutes with appropriate random variation
            
        Raises:
            ValueError: If wait_time_str format is not recognized
        """
        if not wait_time_str:
            raise ValueError("Wait time string cannot be empty or None")
        
        wait_time_str = wait_time_str.lower().strip()
        
        if wait_time_str == "immediate":
            return random_service.get_wait_time_variation('immediate')
        elif "10 min" in wait_time_str:
            return random_service.get_wait_time_variation('10_min')
        elif "60 min" in wait_time_str:
            return random_service.get_wait_time_variation('60_min')
        elif "120 min" in wait_time_str:
            return random_service.get_wait_time_variation('120_min')
        elif "240 min" in wait_time_str:
            return random_service.get_wait_time_variation('240_min')
        else:
            raise ValueError(f"Unknown wait time format: '{wait_time_str}'. Expected: 'immediate', '10 min', '60 min', '120 min', or '240 min'")
    
    def extract_patient_symptoms(self, patient_data: Dict[str, Any]) -> Tuple[List[float], Dict[str, str]]:
        """Extract symptoms and medical history from real patient data."""
        symptoms = {
            SymptomKeys.PAIN_LEVEL: LinguisticValues.NONE,
            SymptomKeys.CRUSHING_SENSATION: LinguisticValues.NONE,
            SymptomKeys.BREATHING_DIFFICULTY: LinguisticValues.NONE,
            SymptomNames.CHEST_PAIN: LinguisticValues.NONE,
            SymptomNames.NAUSEA: LinguisticValues.NONE,
            SymptomNames.HEADACHE: LinguisticValues.NONE,
            SymptomNames.DIZZINESS: LinguisticValues.NONE
        }
        
        numeric_inputs = [0.0] * 5  # Default values: [pain_score, systolic_bp, heart_rate, temperature, resp_rate]
        
        # Extract from observations
        observations = patient_data.get('observations', [])
        for obs in observations:
            description = obs.get('DESCRIPTION', '').lower()
            value = obs.get('VALUE', '')
            
            # Map observations to symptoms and numeric inputs
            if 'pain' in description and 'severity' in description:
                try:
                    pain_score = float(value)
                    numeric_inputs[0] = pain_score
                    if pain_score >= 7:
                        symptoms[SymptomKeys.PAIN_LEVEL] = LinguisticValues.SEVERE
                    elif pain_score >= 4:
                        symptoms[SymptomKeys.PAIN_LEVEL] = LinguisticValues.MODERATE
                    else:
                        symptoms[SymptomKeys.PAIN_LEVEL] = LinguisticValues.MILD
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
            
            # Cardiac symptoms
            if MedicalConditions.CHEST_PAIN in description or MedicalConditions.ANGINA in description:
                symptoms[SymptomNames.CHEST_PAIN] = LinguisticValues.MODERATE
            elif MedicalConditions.MYOCARDIAL_INFARCTION in description or MedicalConditions.HEART_ATTACK in description:
                symptoms[SymptomNames.CHEST_PAIN] = LinguisticValues.SEVERE
                symptoms[SymptomKeys.CRUSHING_SENSATION] = LinguisticValues.SEVERE
            
            # Respiratory symptoms
            elif MedicalConditions.ASTHMA in description or MedicalConditions.COPD in description:
                symptoms[SymptomKeys.BREATHING_DIFFICULTY] = LinguisticValues.MODERATE
            elif MedicalConditions.RESPIRATORY_FAILURE in description or MedicalConditions.PNEUMONIA in description:
                symptoms[SymptomKeys.BREATHING_DIFFICULTY] = LinguisticValues.SEVERE
            
            # Neurological symptoms
            elif MedicalConditions.HEADACHE in description or MedicalConditions.MIGRAINE in description:
                symptoms[SymptomNames.HEADACHE] = LinguisticValues.MODERATE
            elif MedicalConditions.STROKE in description or MedicalConditions.SEIZURE in description:
                symptoms[SymptomNames.HEADACHE] = LinguisticValues.SEVERE
                symptoms[SymptomNames.DIZZINESS] = LinguisticValues.SEVERE
            
            # Gastrointestinal symptoms
            elif MedicalConditions.NAUSEA in description or MedicalConditions.VOMITING in description:
                symptoms[SymptomNames.NAUSEA] = LinguisticValues.MODERATE
            elif MedicalConditions.APPENDICITIS in description:
                symptoms[SymptomKeys.PAIN_LEVEL] = LinguisticValues.SEVERE
                symptoms[SymptomNames.NAUSEA] = LinguisticValues.MODERATE
        
        return numeric_inputs, symptoms
    
    def calculate_age(self, birth_date: str) -> Optional[int]:
        """Calculate age from birth date string."""
        if not birth_date:
            return None
        try:
            birth_year = int(birth_date.split('-')[0])
            return 2024 - birth_year
        except (ValueError, IndexError):
            return None
    
    def normalize_vital_signs(self, numeric_inputs: List[float]) -> Dict[str, str]:
        """Normalize vital signs to clinical categories."""
        if len(numeric_inputs) < 5:
            return {}
        
        pain_score, systolic_bp, heart_rate, temperature, resp_rate = numeric_inputs[:5]
        
        categories = {}
        
        # Pain categorization
        if pain_score >= 8:
            categories['pain_level'] = LinguisticValues.SEVERE
        elif pain_score >= 4:
            categories['pain_level'] = LinguisticValues.MODERATE
        elif pain_score > 0:
            categories['pain_level'] = LinguisticValues.MILD
        else:
            categories['pain_level'] = LinguisticValues.NONE
        
        # Blood pressure categorization
        if systolic_bp >= 180:
            categories['bp_category'] = VitalSignCategories.BP_HYPERTENSIVE_CRISIS
        elif systolic_bp >= 140:
            categories['bp_category'] = VitalSignCategories.BP_HYPERTENSIVE
        elif systolic_bp >= 120:
            categories['bp_category'] = VitalSignCategories.BP_ELEVATED
        elif systolic_bp >= 90:
            categories['bp_category'] = VitalSignCategories.BP_NORMAL
        else:
            categories['bp_category'] = VitalSignCategories.BP_HYPOTENSIVE
        
        # Heart rate categorization
        if heart_rate > 100:
            categories['hr_category'] = VitalSignCategories.HR_TACHYCARDIC
        elif heart_rate >= 60:
            categories['hr_category'] = VitalSignCategories.HR_NORMAL
        else:
            categories['hr_category'] = VitalSignCategories.HR_BRADYCARDIC
        
        # Temperature categorization (assuming Fahrenheit)
        if temperature >= 103:
            categories['temp_category'] = VitalSignCategories.TEMP_HIGH_FEVER
        elif temperature >= 100.4:
            categories['temp_category'] = VitalSignCategories.TEMP_FEVER
        elif temperature >= 97:
            categories['temp_category'] = VitalSignCategories.TEMP_NORMAL
        else:
            categories['temp_category'] = VitalSignCategories.TEMP_HYPOTHERMIC
        
        # Respiratory rate categorization
        if resp_rate > 20:
            categories['resp_category'] = VitalSignCategories.RESP_TACHYPNEIC
        elif resp_rate >= 12:
            categories['resp_category'] = VitalSignCategories.RESP_NORMAL
        else:
            categories['resp_category'] = VitalSignCategories.RESP_BRADYPNEIC
        
        return categories
    
    def extract_chief_complaint(self, patient_data: Dict[str, Any]) -> str:
        """Extract the most likely chief complaint from patient data."""
        conditions = patient_data.get('conditions', [])
        
        if not conditions:
            return CommonStrings.GENERAL_COMPLAINT
        
        # Sort conditions by start date to get most recent
        recent_conditions = sorted(conditions, 
                                 key=lambda x: x.get('START', ''), 
                                 reverse=True)
        
        if recent_conditions:
            description = recent_conditions[0].get('DESCRIPTION', '')
            
            # Map conditions to common chief complaints using centralized constants
            complaint_mapping = FlowchartNames.get_condition_to_flowchart_mapping()
            # Add additional mappings
            complaint_mapping.update({
                MedicalConditions.STROKE: CommonStrings.NEUROLOGICAL_TERM,
                MedicalConditions.DIZZINESS: CommonStrings.NEUROLOGICAL_TERM,
                CommonStrings.SHORTNESS_OF_BREATH_TERM: FlowchartNames.SHORTNESS_OF_BREATH_DISPLAY,
                CommonStrings.FEVER_TERM: CommonStrings.FEVER_DISPLAY,
                CommonStrings.INFECTION_TERM: CommonStrings.FEVER_DISPLAY,
                MedicalConditions.FRACTURE: FlowchartNames.INJURY_DISPLAY,
                CommonStrings.TRAUMA_TERM: FlowchartNames.INJURY_DISPLAY
            })
            
            description_lower = description.lower()
            for key, complaint in complaint_mapping.items():
                if key in description_lower:
                    return complaint
            
            # If no mapping found, return the condition description
            return description
        
        return CommonStrings.GENERAL_COMPLAINT
    
    def get_patient_summary(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get a comprehensive summary of patient data for triage."""
        numeric_inputs, symptoms = self.extract_patient_symptoms(patient_data)
        vital_categories = self.normalize_vital_signs(numeric_inputs)
        chief_complaint = self.extract_chief_complaint(patient_data)
        age = self.calculate_age(patient_data.get('BIRTHDATE', ''))
        
        summary = {
            'patient_id': patient_data.get('Id', CommonStrings.UNKNOWN),
            'age': age,
            'gender': patient_data.get('GENDER', CommonStrings.UNKNOWN),
            'chief_complaint': chief_complaint,
            'symptoms': symptoms,
            'vital_signs': {
                'numeric_values': numeric_inputs,
                'categories': vital_categories
            },
            'conditions': [c.get('DESCRIPTION', '') for c in patient_data.get('conditions', [])],
            'condition_count': len(patient_data.get('conditions', [])),
            'observation_count': len(patient_data.get('observations', []))
        }
        
        return summary