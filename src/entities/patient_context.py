"""Patient Context Entity

Provides comprehensive patient context by aggregating all related medical data.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import csv
import os
import logging

from .medical_condition import MedicalCondition
from .medication import Medication
from .allergy import Allergy
from .encounter import Encounter
from .observation import Observation
from .procedure import Procedure
from .immunization import Immunization

logger = logging.getLogger(__name__)

class PatientContext:
    """Comprehensive patient context aggregating all medical data"""
    
    def __init__(self, patient_id: str):
        self.patient_id = patient_id
        
        # Medical data collections
        self.conditions: List[MedicalCondition] = []
        self.medications: List[Medication] = []
        self.allergies: List[Allergy] = []
        self.encounters: List[Encounter] = []
        self.observations: List[Observation] = []
        self.procedures: List[Procedure] = []
        self.immunizations: List[Immunization] = []
        
        # Load all data
        self._load_all_data()
    
    def _load_csv_data(self, entity_class, patient_field: str = 'PATIENT'):
        """Load data from CSV file for this patient using BaseEntity auto-path"""
        try:
            return entity_class.load_from_csv(patient_id=self.patient_id, patient_field=patient_field)
        except Exception as e:
            logger.error(f"Error loading {entity_class.__name__} data: {e}")
            return []
    
    def _load_all_data(self):
        """Load all medical data for this patient"""
        self.conditions = self._load_csv_data(MedicalCondition)
        self.medications = self._load_csv_data(Medication)
        self.allergies = self._load_csv_data(Allergy)
        self.encounters = self._load_csv_data(Encounter)
        self.observations = self._load_csv_data(Observation)
        self.procedures = self._load_csv_data(Procedure)
        self.immunizations = self._load_csv_data(Immunization)
    
    def get_active_conditions(self) -> List[MedicalCondition]:
        """Get currently active medical conditions"""
        return [c for c in self.conditions if c.is_active]
    
    def get_chronic_conditions(self) -> List[MedicalCondition]:
        """Get chronic medical conditions"""
        return [c for c in self.conditions if c.is_chronic()]
    
    def get_active_medications(self) -> List[Medication]:
        """Get currently active medications"""
        return [m for m in self.medications if m.is_active]
    
    def get_long_term_medications(self) -> List[Medication]:
        """Get long-term medications"""
        return [m for m in self.medications if m.is_long_term()]
    
    def get_active_allergies(self) -> List[Allergy]:
        """Get currently active allergies"""
        return [a for a in self.allergies if a.is_active]
    
    def get_drug_allergies(self) -> List[Allergy]:
        """Get drug allergies"""
        return [a for a in self.allergies if a.is_drug_allergy() and a.is_active]
    
    def get_severe_allergies(self) -> List[Allergy]:
        """Get severe allergies"""
        return [a for a in self.allergies if a.get_severity_category() == 'severe' and a.is_active]
    
    def get_recent_encounters(self, days: int = 30) -> List[Encounter]:
        """Get recent encounters within specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return [e for e in self.encounters if e.start and e.start >= cutoff_date]
    
    def get_emergency_encounters(self) -> List[Encounter]:
        """Get emergency encounters"""
        return [e for e in self.encounters if e.is_emergency()]
    
    def get_recent_observations(self, days: int = 30) -> List[Observation]:
        """Get recent observations within specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return [o for o in self.observations if o.date and o.date >= cutoff_date]
    
    def get_vital_signs(self, days: int = 7) -> List[Observation]:
        """Get recent vital signs"""
        recent_obs = self.get_recent_observations(days)
        return [o for o in recent_obs if o.is_vital_sign()]
    
    def get_lab_results(self, days: int = 30) -> List[Observation]:
        """Get recent lab results"""
        recent_obs = self.get_recent_observations(days)
        return [o for o in recent_obs if o.is_lab_result()]
    
    def get_recent_procedures(self, days: int = 90) -> List[Procedure]:
        """Get recent procedures within specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return [p for p in self.procedures if p.date and p.date >= cutoff_date]
    
    def get_surgical_procedures(self) -> List[Procedure]:
        """Get surgical procedures"""
        return [p for p in self.procedures if p.is_surgical()]
    
    def get_recent_immunizations(self, days: int = 365) -> List[Immunization]:
        """Get recent immunizations within specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return [i for i in self.immunizations if i.date and i.date >= cutoff_date]
    
    def get_vaccination_status(self) -> Dict[str, Any]:
        """Get vaccination status summary"""
        recent_vaccines = self.get_recent_immunizations(365)
        vaccine_types = {}
        
        for vaccine in recent_vaccines:
            vaccine_type = vaccine.get_vaccine_type()
            if vaccine_type not in vaccine_types:
                vaccine_types[vaccine_type] = []
            vaccine_types[vaccine_type].append(vaccine)
        
        return {
            'total_recent_vaccines': len(recent_vaccines),
            'vaccine_types': vaccine_types,
            'has_recent_flu_vaccine': 'influenza' in vaccine_types,
            'has_recent_covid_vaccine': 'covid-19' in vaccine_types
        }
    
    def get_risk_factors(self) -> Dict[str, Any]:
        """Identify patient risk factors"""
        risk_factors = {
            'chronic_conditions': len(self.get_chronic_conditions()),
            'active_medications': len(self.get_active_medications()),
            'drug_allergies': len(self.get_drug_allergies()),
            'severe_allergies': len(self.get_severe_allergies()),
            'recent_emergency_visits': len([e for e in self.get_recent_encounters(90) if e.is_emergency()]),
            'recent_hospitalizations': len([e for e in self.get_recent_encounters(90) if e.is_inpatient()]),
            'surgical_history': len(self.get_surgical_procedures())
        }
        
        # Calculate overall risk score (simplified)
        risk_score = (
            risk_factors['chronic_conditions'] * 2 +
            risk_factors['active_medications'] +
            risk_factors['severe_allergies'] * 3 +
            risk_factors['recent_emergency_visits'] * 2 +
            risk_factors['recent_hospitalizations'] * 3
        )
        
        risk_factors['overall_risk_score'] = risk_score
        risk_factors['risk_level'] = self._categorize_risk(risk_score)
        
        return risk_factors
    
    def _categorize_risk(self, score: int) -> str:
        """Categorize risk level based on score"""
        if score >= 15:
            return 'high'
        elif score >= 8:
            return 'moderate'
        elif score >= 3:
            return 'low'
        else:
            return 'minimal'
    
    def get_clinical_summary(self) -> Dict[str, Any]:
        """Get comprehensive clinical summary"""
        return {
            'patient_id': self.patient_id,
            'active_conditions': [c.to_dict() for c in self.get_active_conditions()],
            'chronic_conditions': [c.to_dict() for c in self.get_chronic_conditions()],
            'active_medications': [m.to_dict() for m in self.get_active_medications()],
            'active_allergies': [a.to_dict() for a in self.get_active_allergies()],
            'recent_encounters': [e.to_dict() for e in self.get_recent_encounters()],
            'recent_vital_signs': [o.to_dict() for o in self.get_vital_signs()],
            'recent_lab_results': [o.to_dict() for o in self.get_lab_results()],
            'recent_procedures': [p.to_dict() for p in self.get_recent_procedures()],
            'vaccination_status': self.get_vaccination_status(),
            'risk_factors': self.get_risk_factors(),
            'summary_stats': {
                'total_conditions': len(self.conditions),
                'total_medications': len(self.medications),
                'total_allergies': len(self.allergies),
                'total_encounters': len(self.encounters),
                'total_observations': len(self.observations),
                'total_procedures': len(self.procedures),
                'total_immunizations': len(self.immunizations)
            }
        }
    
    def get_triage_relevant_info(self) -> Dict[str, Any]:
        """Get information most relevant for triage decisions"""
        return {
            'patient_id': self.patient_id,
            'active_conditions': [{
                'description': c.description,
                'code': c.code,
                'is_chronic': c.is_chronic()
            } for c in self.get_active_conditions()],
            'active_medications': [{
                'description': m.description,
                'code': m.code
            } for m in self.get_active_medications()],
            'drug_allergies': [{
                'description': a.description,
                'severity': a.get_severity_category()
            } for a in self.get_drug_allergies()],
            'recent_vital_signs': [{
                'description': o.description,
                'value': o.value,
                'units': o.units,
                'date': o.date.isoformat() if o.date else None
            } for o in self.get_vital_signs()],
            'recent_emergency_visits': len([e for e in self.get_recent_encounters(30) if e.is_emergency()]),
            'risk_level': self.get_risk_factors()['risk_level']
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return self.get_clinical_summary()
    
    def __str__(self) -> str:
        risk_level = self.get_risk_factors()['risk_level']
        active_conditions = len(self.get_active_conditions())
        active_meds = len(self.get_active_medications())
        return f"PatientContext(id={self.patient_id}, risk={risk_level}, conditions={active_conditions}, medications={active_meds})"
    
    def __repr__(self) -> str:
        return f"PatientContext(patient_id='{self.patient_id}')"