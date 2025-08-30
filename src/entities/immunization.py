"""Immunization Entity

Represents an immunization from the immunizations.csv data.
"""

from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class Immunization:
    """Represents a vaccination or immunization"""
    
    def __init__(self, date: str, patient_id: str, encounter_id: Optional[str],
                 code: str, description: str, base_cost: Optional[float] = None):
        self.date = self._parse_date(date)
        self.patient_id = patient_id
        self.encounter_id = encounter_id
        self.code = code
        self.description = description
        self.base_cost = self._parse_float(base_cost)
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str or date_str.strip() == '':
            return None
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            try:
                return datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                logger.warning(f"Could not parse date: {date_str}")
                return None
    
    def _parse_float(self, value) -> Optional[float]:
        """Parse float value safely"""
        if value is None or value == '' or value == 'None':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def is_childhood_vaccine(self) -> bool:
        """Check if this is a childhood vaccine"""
        childhood_vaccines = ['dtap', 'polio', 'mmr', 'varicella', 'hib', 'pcv', 'rotavirus',
                            'hepatitis b', 'hepatitis a', 'meningococcal']
        desc_lower = self.description.lower()
        return any(vaccine in desc_lower for vaccine in childhood_vaccines)
    
    def is_adult_vaccine(self) -> bool:
        """Check if this is an adult vaccine"""
        adult_vaccines = ['tdap', 'tetanus', 'shingles', 'pneumococcal', 'hpv',
                         'meningococcal', 'hepatitis a', 'hepatitis b']
        desc_lower = self.description.lower()
        return any(vaccine in desc_lower for vaccine in adult_vaccines)
    
    def is_seasonal_vaccine(self) -> bool:
        """Check if this is a seasonal vaccine"""
        seasonal_vaccines = ['influenza', 'flu', 'covid', 'coronavirus']
        desc_lower = self.description.lower()
        return any(vaccine in desc_lower for vaccine in seasonal_vaccines)
    
    def is_travel_vaccine(self) -> bool:
        """Check if this is a travel-related vaccine"""
        travel_vaccines = ['yellow fever', 'typhoid', 'japanese encephalitis',
                          'rabies', 'cholera', 'meningitis']
        desc_lower = self.description.lower()
        return any(vaccine in desc_lower for vaccine in travel_vaccines)
    
    def get_vaccine_category(self) -> str:
        """Get category of vaccine"""
        if self.is_childhood_vaccine():
            return 'childhood'
        elif self.is_adult_vaccine():
            return 'adult'
        elif self.is_seasonal_vaccine():
            return 'seasonal'
        elif self.is_travel_vaccine():
            return 'travel'
        else:
            return 'other'
    
    def get_vaccine_type(self) -> str:
        """Get specific vaccine type from description"""
        desc_lower = self.description.lower()
        
        # Common vaccine mappings
        if 'influenza' in desc_lower or 'flu' in desc_lower:
            return 'influenza'
        elif 'covid' in desc_lower or 'coronavirus' in desc_lower:
            return 'covid-19'
        elif 'dtap' in desc_lower:
            return 'dtap'
        elif 'mmr' in desc_lower:
            return 'mmr'
        elif 'varicella' in desc_lower or 'chickenpox' in desc_lower:
            return 'varicella'
        elif 'hepatitis b' in desc_lower:
            return 'hepatitis_b'
        elif 'hepatitis a' in desc_lower:
            return 'hepatitis_a'
        elif 'pneumococcal' in desc_lower:
            return 'pneumococcal'
        elif 'shingles' in desc_lower or 'zoster' in desc_lower:
            return 'shingles'
        elif 'hpv' in desc_lower:
            return 'hpv'
        else:
            return 'other'
    
    def days_since_vaccination(self) -> Optional[int]:
        """Get days since vaccination"""
        if not self.date:
            return None
        return (datetime.now() - self.date).days
    
    def is_recent(self, days: int = 30) -> bool:
        """Check if vaccination was recent"""
        days_since = self.days_since_vaccination()
        return days_since is not None and days_since <= days
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'date': self.date.isoformat() if self.date else None,
            'patient_id': self.patient_id,
            'encounter_id': self.encounter_id,
            'code': self.code,
            'description': self.description,
            'base_cost': self.base_cost,
            'vaccine_category': self.get_vaccine_category(),
            'vaccine_type': self.get_vaccine_type(),
            'days_since_vaccination': self.days_since_vaccination(),
            'is_recent': self.is_recent(),
            'is_childhood_vaccine': self.is_childhood_vaccine(),
            'is_adult_vaccine': self.is_adult_vaccine(),
            'is_seasonal_vaccine': self.is_seasonal_vaccine(),
            'is_travel_vaccine': self.is_travel_vaccine()
        }
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> 'Immunization':
        """Create Immunization from CSV row"""
        return cls(
            date=row['DATE'],
            patient_id=row['PATIENT'],
            encounter_id=row.get('ENCOUNTER'),
            code=row['CODE'],
            description=row['DESCRIPTION'],
            base_cost=row.get('BASE_COST')
        )
    
    def __str__(self) -> str:
        date_str = self.date.strftime('%Y-%m-%d') if self.date else 'Unknown date'
        return f"{self.description} ({self.code}) - {date_str}"
    
    def __repr__(self) -> str:
        return f"Immunization(code='{self.code}', type='{self.get_vaccine_type()}', category='{self.get_vaccine_category()}')"