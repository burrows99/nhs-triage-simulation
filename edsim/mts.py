#!/usr/bin/env python3
"""
NHS Manchester Triage System (MTS) Implementation

Centralized triage logic for Emergency Department patient routing.
Aligned with NHS Emergency Care Data Set (ECDS) standards and NICE guidelines.

Author: Research Team
Date: December 2024
Version: 1.0
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Union


class MTSTriageSystem:
    """
    Manchester Triage System implementation for NHS Emergency Departments.
    
    Provides standardized triage categorization based on:
    - Clinical presentation (chief complaints)
    - Vital signs assessment
    - Age-based risk stratification
    - Vulnerability factors
    """
    
    # NHS ECDS-ALIGNED CHIEF COMPLAINTS AND MTS TRIAGE MAPPING
    ACUTE_KEYWORDS = {
        'red': [  # Category 1: Immediate (0 minutes)
            'cardiac arrest', 'respiratory arrest', 'major trauma', 'severe shock',
            'unconscious', 'coma', 'severe respiratory distress', 'anaphylaxis',
            'major haemorrhage', 'stroke with severe deficit', 'status epilepticus',
            'severe burns', 'major fracture with vascular compromise'
        ],
        'orange': [  # Category 2: Very Urgent (10 minutes)
            'chest pain', 'difficulty breathing', 'severe abdominal pain', 'head injury',
            'stroke symptoms', 'seizure', 'severe allergic reaction', 'overdose',
            'psychiatric emergency', 'moderate trauma', 'severe pain', 'fever with rash',
            'diabetic emergency', 'acute confusion', 'severe dehydration'
        ],
        'yellow': [  # Category 3: Urgent (60 minutes)
            'moderate pain', 'minor trauma', 'wound requiring sutures', 'fever',
            'vomiting', 'diarrhoea', 'urinary problems', 'rash', 'eye problems',
            'ear problems', 'dental pain', 'back pain', 'joint pain', 'headache',
            'dizziness', 'palpitations', 'anxiety'
        ],
        'green': [  # Category 4: Standard (120 minutes)
            'minor cuts', 'bruises', 'sprains', 'cold symptoms', 'sore throat',
            'minor infections', 'medication queries', 'follow-up care',
            'minor skin conditions', 'constipation'
        ],
        'blue': [  # Category 5: Non-urgent (240 minutes)
            'routine medication', 'health advice', 'minor concerns',
            'administrative queries', 'social issues'
        ]
    }
    
    @staticmethod
    def assign_triage_level(patient_data: Dict[str, Any]) -> str:
        """
        Assign Manchester Triage System (MTS) category based on clinical presentation.
        
        Args:
            patient_data: Dictionary containing patient information with keys:
                - chief_complaint or REASONDESCRIPTION: Primary presenting complaint
                - vital signs: Systolic BP, Heart Rate, Respiratory Rate, etc.
                - age_years: Patient age
                - chronic_count: Number of chronic conditions (optional)
        
        Returns:
            str: Triage level ('red', 'orange', 'yellow', 'green', 'blue')
        """
        # Extract vital signs with safe defaults
        sbp = patient_data.get('Systolic Blood Pressure', patient_data.get('systolic_bp', 120))
        dbp = patient_data.get('Diastolic Blood Pressure', patient_data.get('diastolic_bp', 80))
        hr = patient_data.get('Heart Rate', patient_data.get('heart_rate', 70))
        rr = patient_data.get('Respiratory Rate', patient_data.get('respiratory_rate', 16))
        spo2 = patient_data.get('Oxygen Saturation', patient_data.get('oxygen_saturation', 98))
        temp = patient_data.get('Body Temperature', patient_data.get('temperature', 36.5))
        age = patient_data.get('age_years', patient_data.get('age', 50))
        
        # Get chief complaint
        chief_complaint = str(patient_data.get('chief_complaint', 
                                             patient_data.get('REASONDESCRIPTION', ''))).lower()
        
        # RED: Immediate life-threatening conditions
        if MTSTriageSystem._check_red_criteria(chief_complaint, sbp, hr, rr, spo2, temp, age):
            return 'red'
        
        # ORANGE: Very urgent conditions
        if MTSTriageSystem._check_orange_criteria(chief_complaint, sbp, hr, rr, spo2, temp, age, patient_data):
            return 'orange'
        
        # YELLOW: Urgent conditions
        if MTSTriageSystem._check_yellow_criteria(chief_complaint, sbp, hr, rr, spo2, temp, age, patient_data):
            return 'yellow'
        
        # GREEN: Standard priority
        if MTSTriageSystem._check_green_criteria(chief_complaint):
            return 'green'
        
        # BLUE: Non-urgent (default)
        return 'blue'
    
    @staticmethod
    def _check_red_criteria(chief_complaint: str, sbp: float, hr: float, rr: float, 
                           spo2: float, temp: float, age: float) -> bool:
        """Check for RED (immediate) triage criteria."""
        # Clinical presentation
        for keyword in MTSTriageSystem.ACUTE_KEYWORDS['red']:
            if keyword in chief_complaint:
                return True
        
        # Critical vital signs (if available)
        if all(pd.notna(x) for x in [sbp, spo2, hr, rr, temp]):
            if (sbp < 70 or sbp > 220 or  # Severe hypotension/hypertension
                spo2 < 85 or  # Critical hypoxia
                hr < 40 or hr > 150 or  # Severe bradycardia/tachycardia
                rr < 8 or rr > 35 or  # Respiratory failure
                temp < 32 or temp > 42):  # Severe hypothermia/hyperthermia
                return True
        
        return False
    
    @staticmethod
    def _check_orange_criteria(chief_complaint: str, sbp: float, hr: float, rr: float,
                              spo2: float, temp: float, age: float, patient_data: Dict[str, Any]) -> bool:
        """Check for ORANGE (very urgent) triage criteria."""
        # Clinical presentation
        for keyword in MTSTriageSystem.ACUTE_KEYWORDS['orange']:
            if keyword in chief_complaint:
                return True
        
        # Vulnerable populations with moderate abnormalities
        vulnerable_age = age >= 75 or patient_data.get('chronic_count', 0) >= 3
        if vulnerable_age and all(pd.notna(x) for x in [sbp, hr, temp]):
            if (sbp < 90 or sbp > 180 or  # Moderate BP abnormalities
                hr < 50 or hr > 120 or  # Moderate heart rate abnormalities
                temp < 35 or temp > 39):  # Moderate temperature abnormalities
                return True
        
        return False
    
    @staticmethod
    def _check_yellow_criteria(chief_complaint: str, sbp: float, hr: float, rr: float,
                              spo2: float, temp: float, age: float, patient_data: Dict[str, Any]) -> bool:
        """Check for YELLOW (urgent) triage criteria."""
        # Clinical presentation
        for keyword in MTSTriageSystem.ACUTE_KEYWORDS['yellow']:
            if keyword in chief_complaint:
                return True
        
        # Age-related escalation for elderly patients
        if age >= 75 and patient_data.get('chronic_count', 0) >= 2:
            return True
        
        # Moderate vital sign abnormalities
        if all(pd.notna(x) for x in [sbp, hr, spo2, temp]):
            if (sbp < 100 or sbp > 160 or
                hr < 60 or hr > 100 or
                spo2 < 92 or
                temp < 36 or temp > 38.5):
                return True
        
        return False
    
    @staticmethod
    def _check_green_criteria(chief_complaint: str) -> bool:
        """Check for GREEN (standard) triage criteria."""
        for keyword in MTSTriageSystem.ACUTE_KEYWORDS['green']:
            if keyword in chief_complaint:
                return True
        return False
    
    @staticmethod
    def get_triage_priority(triage_level: str) -> int:
        """Convert triage level to numeric priority for queue management."""
        priority_map = {
            'red': 1,    # Immediate
            'orange': 2, # Very urgent
            'yellow': 3, # Urgent
            'green': 4,  # Standard
            'blue': 5    # Non-urgent
        }
        return priority_map.get(triage_level, 5)
    
    @staticmethod
    def get_target_time(triage_level: str) -> int:
        """Get target time to treatment in minutes based on triage level."""
        target_times = {
            'red': 0,     # Immediate
            'orange': 10, # 10 minutes
            'yellow': 60, # 1 hour
            'green': 120, # 2 hours
            'blue': 240   # 4 hours
        }
        return target_times.get(triage_level, 240)
    
    @staticmethod
    def is_high_acuity(triage_level: str) -> bool:
        """Check if patient requires high acuity care (red/orange)."""
        return triage_level in ['red', 'orange']
    
    @staticmethod
    def requires_immediate_attention(triage_level: str) -> bool:
        """Check if patient requires immediate medical attention."""
        return triage_level == 'red'
    
    @staticmethod
    def get_triage_description(triage_level: str) -> str:
        """Get human-readable description of triage level."""
        descriptions = {
            'red': 'Category 1: Immediate - Life-threatening condition requiring immediate treatment',
            'orange': 'Category 2: Very Urgent - Serious condition requiring treatment within 10 minutes',
            'yellow': 'Category 3: Urgent - Condition requiring treatment within 1 hour',
            'green': 'Category 4: Standard - Condition requiring treatment within 2 hours',
            'blue': 'Category 5: Non-urgent - Condition that can wait up to 4 hours'
        }
        return descriptions.get(triage_level, 'Unknown triage level')


# Convenience function for backward compatibility
def assign_mts_triage(patient_data: Union[Dict[str, Any], pd.Series]) -> str:
    """
    Convenience function to assign MTS triage level.
    
    Args:
        patient_data: Patient data as dictionary or pandas Series
    
    Returns:
        str: Triage level ('red', 'orange', 'yellow', 'green', 'blue')
    """
    if isinstance(patient_data, pd.Series):
        patient_data = patient_data.to_dict()
    
    return MTSTriageSystem.assign_triage_level(patient_data)


# Export main functions for easy import
__all__ = ['MTSTriageSystem', 'assign_mts_triage']