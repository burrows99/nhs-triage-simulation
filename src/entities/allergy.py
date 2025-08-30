"""Allergy Entity

Represents an allergy from the allergies.csv data.
"""

from datetime import datetime
from typing import Optional, Dict, Any
import logging
from .base_entity import BaseEntity

logger = logging.getLogger(__name__)

class Allergy(BaseEntity):
    """Represents a patient allergy"""
    
    def __init__(self, start: str, stop: Optional[str], patient_id: str, 
                 encounter_id: Optional[str], code: str, description: str):
        super().__init__()
        self.start = self._parse_date(start)
        self.stop = self._parse_date(stop) if stop else None
        self.patient_id = patient_id
        self.encounter_id = encounter_id
        self.code = code
        self.description = description
        self.is_active = self.stop is None
    
    def get_severity_category(self) -> str:
        """Categorize allergy severity based on description"""
        desc_lower = self.description.lower()
        if any(word in desc_lower for word in ['severe', 'anaphylaxis', 'life-threatening']):
            return 'severe'
        elif any(word in desc_lower for word in ['moderate', 'significant']):
            return 'moderate'
        else:
            return 'mild'
    
    def is_drug_allergy(self) -> bool:
        """Check if this is a drug/medication allergy"""
        desc_lower = self.description.lower()
        drug_keywords = ['drug', 'medication', 'antibiotic', 'penicillin', 'aspirin', 
                        'ibuprofen', 'codeine', 'morphine', 'sulfa']
        return any(keyword in desc_lower for keyword in drug_keywords)
    
    def is_food_allergy(self) -> bool:
        """Check if this is a food allergy"""
        desc_lower = self.description.lower()
        food_keywords = ['food', 'peanut', 'shellfish', 'dairy', 'milk', 'egg', 
                        'wheat', 'soy', 'tree nut', 'fish']
        return any(keyword in desc_lower for keyword in food_keywords)
    
    def is_environmental_allergy(self) -> bool:
        """Check if this is an environmental allergy"""
        desc_lower = self.description.lower()
        env_keywords = ['pollen', 'dust', 'mold', 'pet', 'dander', 'latex', 
                       'bee', 'wasp', 'insect', 'environmental']
        return any(keyword in desc_lower for keyword in env_keywords)
    
    def get_allergy_type(self) -> str:
        """Get the type of allergy"""
        if self.is_drug_allergy():
            return 'drug'
        elif self.is_food_allergy():
            return 'food'
        elif self.is_environmental_allergy():
            return 'environmental'
        else:
            return 'other'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'start': self.start.isoformat() if self.start else None,
            'stop': self.stop.isoformat() if self.stop else None,
            'patient_id': self.patient_id,
            'encounter_id': self.encounter_id,
            'code': self.code,
            'description': self.description,
            'is_active': self.is_active,
            'severity_category': self.get_severity_category(),
            'allergy_type': self.get_allergy_type(),
            'is_drug_allergy': self.is_drug_allergy(),
            'is_food_allergy': self.is_food_allergy(),
            'is_environmental_allergy': self.is_environmental_allergy()
        }
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> Optional['Allergy']:
        """Create Allergy from CSV row"""
        required_fields = ['START', 'PATIENT', 'CODE', 'DESCRIPTION']
        missing_fields = [field for field in required_fields if not row.get(field)]
        
        if missing_fields:
            logger.warning(f"Missing required fields for Allergy: {missing_fields}")
            return None
        
        return cls(
            start=row.get('START'),
            stop=row.get('STOP'),
            patient_id=row.get('PATIENT'),
            encounter_id=row.get('ENCOUNTER'),
            code=row.get('CODE'),
            description=row.get('DESCRIPTION')
        )
    
    def __str__(self) -> str:
        status = "Active" if self.is_active else "Resolved"
        return f"{self.description} ({self.code}) - {status} [{self.get_severity_category()}]"
    
    def __repr__(self) -> str:
        return f"Allergy(code='{self.code}', description='{self.description}', type='{self.get_allergy_type()}')"