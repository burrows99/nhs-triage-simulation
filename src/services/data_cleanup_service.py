import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime


class DataCleanupService:
    """Service for cleaning and processing patient data from Synthea CSV files."""
    
    def __init__(self):
        self.symptom_mappings = {
            'pain_keywords': ['pain', 'ache', 'discomfort', 'soreness'],
            'cardiac_keywords': ['chest pain', 'angina', 'myocardial infarction', 'heart attack', 'cardiac'],
            'respiratory_keywords': ['asthma', 'copd', 'shortness of breath', 'dyspnea', 'respiratory'],
            'neurological_keywords': ['headache', 'migraine', 'seizure', 'stroke', 'neurological']
        }
    
    def extract_patient_symptoms(self, patient_data: Dict[str, Any]) -> Tuple[List[float], Dict[str, str]]:
        """Extract symptoms and medical history from real patient data."""
        symptoms = {
            'severe_pain': 'none',
            'crushing_sensation': 'none',
            'shortness_of_breath': 'none',
            'chest_pain': 'none',
            'nausea': 'none',
            'headache': 'none',
            'dizziness': 'none'
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
                        symptoms['severe_pain'] = 'severe'
                    elif pain_score >= 4:
                        symptoms['severe_pain'] = 'moderate'
                    else:
                        symptoms['severe_pain'] = 'mild'
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
            if 'chest pain' in description or 'angina' in description:
                symptoms['chest_pain'] = 'moderate'
            elif 'myocardial infarction' in description or 'heart attack' in description:
                symptoms['chest_pain'] = 'severe'
                symptoms['crushing_sensation'] = 'severe'
            
            # Respiratory symptoms
            elif 'asthma' in description or 'copd' in description:
                symptoms['shortness_of_breath'] = 'moderate'
            elif 'respiratory failure' in description or 'pneumonia' in description:
                symptoms['shortness_of_breath'] = 'severe'
            
            # Neurological symptoms
            elif 'headache' in description or 'migraine' in description:
                symptoms['headache'] = 'moderate'
            elif 'stroke' in description or 'seizure' in description:
                symptoms['headache'] = 'severe'
                symptoms['dizziness'] = 'severe'
            
            # Gastrointestinal symptoms
            elif 'nausea' in description or 'vomiting' in description:
                symptoms['nausea'] = 'moderate'
            elif 'appendicitis' in description:
                symptoms['severe_pain'] = 'severe'
                symptoms['nausea'] = 'moderate'
        
        return numeric_inputs, symptoms
    
    def determine_triage_from_real_data(self, patient_data: Dict[str, Any], 
                                      numeric_inputs: List[float], 
                                      symptoms: Dict[str, str]) -> Dict[str, Any]:
        """Determine triage category based on real patient data."""
        categories = ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE']
        wait_times = ['0 min', '10 min', '60 min', '120 min', '240 min']
        priorities = [1, 2, 3, 4, 5]  # RED=1 (highest), BLUE=5 (lowest)
        
        # Start with default GREEN (routine)
        triage_index = 3
        flowchart_used = 'general_assessment'
        
        # Check conditions for higher acuity
        conditions = patient_data.get('conditions', [])
        for condition in conditions:
            description = condition.get('DESCRIPTION', '').lower()
            
            # RED conditions (immediate)
            if any(term in description for term in ['myocardial infarction', 'cardiac arrest', 
                                                   'stroke', 'severe trauma', 'respiratory failure',
                                                   'sepsis', 'anaphylaxis']):
                triage_index = 0
                flowchart_used = 'cardiac_emergency' if 'cardiac' in description or 'myocardial' in description else 'medical_emergency'
                break
            
            # ORANGE conditions (very urgent)
            elif any(term in description for term in ['chest pain', 'angina', 'pneumonia',
                                                     'severe asthma', 'diabetic ketoacidosis',
                                                     'appendicitis', 'fracture']):
                triage_index = min(triage_index, 1)
                if 'chest' in description:
                    flowchart_used = 'chest_pain'
                elif 'asthma' in description:
                    flowchart_used = 'shortness_of_breath'
                elif 'appendicitis' in description:
                    flowchart_used = 'abdominal_pain'
            
            # YELLOW conditions (urgent)
            elif any(term in description for term in ['hypertension', 'moderate asthma',
                                                     'urinary tract infection', 'cellulitis',
                                                     'bronchitis', 'sinusitis']):
                triage_index = min(triage_index, 2)
                if 'hypertension' in description:
                    flowchart_used = 'cardiovascular'
        
        # Check vital signs for escalation
        if len(numeric_inputs) >= 5:
            pain_score, systolic_bp, heart_rate, temperature, resp_rate = numeric_inputs[:5]
            
            # Critical vital signs -> RED
            if (systolic_bp > 200 or systolic_bp < 80 or 
                heart_rate > 150 or heart_rate < 40 or
                temperature > 104 or resp_rate > 30 or resp_rate < 8):
                triage_index = 0
                flowchart_used = 'vital_signs_emergency'
            
            # Concerning vital signs -> ORANGE
            elif (systolic_bp > 180 or systolic_bp < 90 or
                  heart_rate > 120 or heart_rate < 50 or
                  temperature > 102 or resp_rate > 24):
                triage_index = min(triage_index, 1)
                flowchart_used = 'vital_signs_concern'
            
            # Severe pain -> ORANGE
            elif pain_score >= 8:
                triage_index = min(triage_index, 1)
                flowchart_used = 'pain_assessment'
            elif pain_score >= 6:
                triage_index = min(triage_index, 2)
                flowchart_used = 'pain_assessment'
        
        # Check symptoms for escalation
        if symptoms.get('severe_pain') == 'severe' or symptoms.get('crushing_sensation') == 'severe':
            triage_index = min(triage_index, 1)
            flowchart_used = 'chest_pain' if symptoms.get('crushing_sensation') == 'severe' else 'pain_assessment'
        elif symptoms.get('chest_pain') == 'severe':
            triage_index = min(triage_index, 1)
            flowchart_used = 'chest_pain'
        elif symptoms.get('shortness_of_breath') == 'severe':
            triage_index = min(triage_index, 1)
            flowchart_used = 'shortness_of_breath'
        
        # Age-based adjustments
        age = self.calculate_age(patient_data.get('BIRTHDATE', ''))
        if age is not None:
            # Elderly patients get priority bump for certain conditions
            if age >= 75 and triage_index >= 2:
                triage_index = max(0, triage_index - 1)
            # Very young patients also get priority
            elif age <= 2 and triage_index >= 2:
                triage_index = max(0, triage_index - 1)
        
        return {
            'flowchart_used': flowchart_used,
            'triage_category': np.str_(categories[triage_index]),
            'wait_time': np.str_(wait_times[triage_index]),
            'fuzzy_score': 5 - triage_index,  # Higher score for more urgent
            'symptoms_processed': symptoms,
            'numeric_inputs': numeric_inputs,
            'priority_score': np.int64(priorities[triage_index]),
            'patient_conditions': [c.get('DESCRIPTION', '') for c in patient_data.get('conditions', [])],
            'patient_age': age,
            'patient_gender': patient_data.get('GENDER', 'Unknown')
        }
    
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
            categories['pain_level'] = 'severe'
        elif pain_score >= 4:
            categories['pain_level'] = 'moderate'
        elif pain_score > 0:
            categories['pain_level'] = 'mild'
        else:
            categories['pain_level'] = 'none'
        
        # Blood pressure categorization
        if systolic_bp >= 180:
            categories['bp_category'] = 'hypertensive_crisis'
        elif systolic_bp >= 140:
            categories['bp_category'] = 'hypertensive'
        elif systolic_bp >= 120:
            categories['bp_category'] = 'elevated'
        elif systolic_bp >= 90:
            categories['bp_category'] = 'normal'
        else:
            categories['bp_category'] = 'hypotensive'
        
        # Heart rate categorization
        if heart_rate > 100:
            categories['hr_category'] = 'tachycardic'
        elif heart_rate >= 60:
            categories['hr_category'] = 'normal'
        else:
            categories['hr_category'] = 'bradycardic'
        
        # Temperature categorization (assuming Fahrenheit)
        if temperature >= 103:
            categories['temp_category'] = 'high_fever'
        elif temperature >= 100.4:
            categories['temp_category'] = 'fever'
        elif temperature >= 97:
            categories['temp_category'] = 'normal'
        else:
            categories['temp_category'] = 'hypothermic'
        
        # Respiratory rate categorization
        if resp_rate > 20:
            categories['resp_category'] = 'tachypneic'
        elif resp_rate >= 12:
            categories['resp_category'] = 'normal'
        else:
            categories['resp_category'] = 'bradypneic'
        
        return categories
    
    def extract_chief_complaint(self, patient_data: Dict[str, Any]) -> str:
        """Extract the most likely chief complaint from patient data."""
        conditions = patient_data.get('conditions', [])
        
        if not conditions:
            return 'General complaint'
        
        # Sort conditions by start date to get most recent
        recent_conditions = sorted(conditions, 
                                 key=lambda x: x.get('START', ''), 
                                 reverse=True)
        
        if recent_conditions:
            description = recent_conditions[0].get('DESCRIPTION', '')
            
            # Map conditions to common chief complaints
            complaint_mapping = {
                'chest pain': 'Chest pain',
                'angina': 'Chest pain',
                'myocardial infarction': 'Chest pain',
                'shortness of breath': 'Shortness of breath',
                'asthma': 'Shortness of breath',
                'headache': 'Headache',
                'migraine': 'Headache',
                'abdominal pain': 'Abdominal pain',
                'appendicitis': 'Abdominal pain',
                'nausea': 'Nausea and vomiting',
                'vomiting': 'Nausea and vomiting',
                'fever': 'Fever',
                'infection': 'Fever',
                'fracture': 'Injury',
                'trauma': 'Injury'
            }
            
            description_lower = description.lower()
            for key, complaint in complaint_mapping.items():
                if key in description_lower:
                    return complaint
            
            # If no mapping found, return the condition description
            return description
        
        return 'General complaint'
    
    def get_patient_summary(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get a comprehensive summary of patient data for triage."""
        numeric_inputs, symptoms = self.extract_patient_symptoms(patient_data)
        vital_categories = self.normalize_vital_signs(numeric_inputs)
        chief_complaint = self.extract_chief_complaint(patient_data)
        age = self.calculate_age(patient_data.get('BIRTHDATE', ''))
        
        return {
            'patient_id': patient_data.get('Id', 'Unknown'),
            'age': age,
            'gender': patient_data.get('GENDER', 'Unknown'),
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


# Example usage and testing
if __name__ == "__main__":
    # Test the data cleanup service
    cleanup_service = DataCleanupService()
    
    # Sample patient data for testing
    sample_patient = {
        'Id': 'test-patient-123',
        'BIRTHDATE': '1980-05-15',
        'GENDER': 'M',
        'conditions': [
            {'DESCRIPTION': 'Chest pain', 'START': '2024-01-01'},
            {'DESCRIPTION': 'Hypertension', 'START': '2023-01-01'}
        ],
        'observations': [
            {'DESCRIPTION': 'Pain severity - 0-10 verbal numeric rating', 'VALUE': '7'},
            {'DESCRIPTION': 'Systolic blood pressure', 'VALUE': '160'},
            {'DESCRIPTION': 'Heart rate', 'VALUE': '95'}
        ]
    }
    
    # Test extraction methods
    numeric_inputs, symptoms = cleanup_service.extract_patient_symptoms(sample_patient)
    print(f"Numeric inputs: {numeric_inputs}")
    print(f"Symptoms: {symptoms}")
    
    # Test triage determination
    triage_result = cleanup_service.determine_triage_from_real_data(sample_patient, numeric_inputs, symptoms)
    print(f"Triage result: {triage_result}")
    
    # Test patient summary
    summary = cleanup_service.get_patient_summary(sample_patient)
    print(f"Patient summary: {summary}")