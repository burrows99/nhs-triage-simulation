"""Base Agent for LLM Triage System

Provides the foundation for AI-powered triage agents that can assess patient symptoms
and provide triage recommendations following NHS guidelines.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import numpy as np


class BaseTriageAgent(ABC):
    """Abstract base class for triage agents"""
    
    def __init__(self, model_name: str = "base_agent"):
        """Initialize the base triage agent
        
        Args:
            model_name: Name identifier for the triage model
        """
        self.model_name = model_name
        self.triage_categories = {
            'RED': {'priority': 1, 'wait_time': 'immediate'},
            'ORANGE': {'priority': 2, 'wait_time': '10 min'},
            'YELLOW': {'priority': 3, 'wait_time': '60 min'},
            'GREEN': {'priority': 4, 'wait_time': '120 min'},
            'BLUE': {'priority': 5, 'wait_time': '240 min'}
        }
        
        # Clinical domains for AI-driven assessment (not rigid flowcharts)
        self.clinical_domains = [
            'cardiovascular', 'respiratory', 'neurological', 'gastrointestinal',
            'musculoskeletal', 'psychiatric', 'pediatric', 'trauma', 'general'
        ]
        
        # Assessment factors for comprehensive evaluation
        self.assessment_factors = [
            'symptom_severity', 'vital_sign_abnormalities', 'pain_assessment',
            'functional_impact', 'risk_factors', 'clinical_deterioration_risk',
            'resource_availability', 'patient_context'
        ]
    
    @abstractmethod
    def triage_patient(self, symptoms: Dict[str, Any], patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform triage assessment on a patient
        
        Args:
            symptoms: Dictionary of patient symptoms and their severity
            patient_data: Additional patient information (age, gender, etc.)
            
        Returns:
            Dictionary containing triage results in the specified format:
            {
                'flowchart_used': str,
                'triage_category': str,
                'wait_time': str,
                'fuzzy_score': float,
                'symptoms_processed': Dict[str, str],
                'numeric_inputs': List[float],
                'priority_score': int
            }
        """
        pass
    
    def _determine_clinical_domain(self, symptoms: Dict[str, Any], patient_data: Dict[str, Any]) -> str:
        """Determine the primary clinical domain for AI-driven assessment
        
        Args:
            symptoms: Patient symptoms dictionary
            patient_data: Additional patient information
            
        Returns:
            Primary clinical domain for assessment context
        """
        # Flexible clinical domain determination based on symptom patterns
        # This provides context for AI assessment without rigid constraints
        
        cardiovascular_indicators = ['chest_pain', 'crushing_sensation', 'palpitations', 'syncope']
        respiratory_indicators = ['breathless', 'breathing_difficulty', 'cough', 'wheeze']
        neurological_indicators = ['headache', 'dizziness', 'confusion', 'weakness', 'seizure']
        gastrointestinal_indicators = ['abdominal_pain', 'nausea', 'vomiting', 'diarrhea']
        trauma_indicators = ['injury', 'fall', 'accident', 'wound', 'fracture']
        
        # Check for pediatric patients
        age = patient_data.get('age', 30)
        if age < 16:
            return 'pediatric'
        
        # Determine primary domain based on symptom presence (not rigid rules)
        domain_scores = {
            'cardiovascular': sum(1 for indicator in cardiovascular_indicators if indicator in symptoms),
            'respiratory': sum(1 for indicator in respiratory_indicators if indicator in symptoms),
            'neurological': sum(1 for indicator in neurological_indicators if indicator in symptoms),
            'gastrointestinal': sum(1 for indicator in gastrointestinal_indicators if indicator in symptoms),
            'trauma': sum(1 for indicator in trauma_indicators if indicator in symptoms)
        }
        
        # Return domain with highest score, or 'general' if no clear pattern
        max_domain = max(domain_scores, key=domain_scores.get) if max(domain_scores.values()) > 0 else 'general'
        return max_domain
    
    def _calculate_priority_score(self, triage_category: str) -> int:
        """Calculate priority score from triage category
        
        Args:
            triage_category: The assigned triage category
            
        Returns:
            Priority score (1-5, lower is higher priority)
        """
        return self.triage_categories.get(triage_category, {}).get('priority', 5)
    
    def _get_wait_time(self, triage_category: str) -> str:
        """Get wait time for triage category
        
        Args:
            triage_category: The assigned triage category
            
        Returns:
            Wait time string
        """
        return self.triage_categories.get(triage_category, {}).get('wait_time', '240 min')