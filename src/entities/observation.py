"""Observation Entity

Represents a clinical observation from the observations.csv data.
"""

from datetime import datetime
from typing import Optional, Dict, Any, Union
import logging

logger = logging.getLogger(__name__)

class Observation:
    """Represents a clinical observation or measurement"""
    
    def __init__(self, date: str, patient_id: str, encounter_id: Optional[str],
                 code: str, description: str, value: Optional[str] = None,
                 units: Optional[str] = None, obs_type: Optional[str] = None):
        self.date = self._parse_date(date)
        self.patient_id = patient_id
        self.encounter_id = encounter_id
        self.code = code
        self.description = description
        self.value = value
        self.units = units
        self.obs_type = obs_type or self._infer_type()
    
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
    
    def _infer_type(self) -> str:
        """Infer observation type from description and value"""
        if not self.value:
            return 'text'
        
        # Try to parse as numeric
        try:
            float(self.value)
            return 'numeric'
        except (ValueError, TypeError):
            pass
        
        # Check for common patterns
        desc_lower = self.description.lower()
        if any(word in desc_lower for word in ['blood pressure', 'bp']):
            return 'blood_pressure'
        elif any(word in desc_lower for word in ['temperature', 'temp']):
            return 'temperature'
        elif any(word in desc_lower for word in ['weight', 'mass']):
            return 'weight'
        elif any(word in desc_lower for word in ['height', 'length']):
            return 'height'
        elif any(word in desc_lower for word in ['heart rate', 'pulse']):
            return 'heart_rate'
        else:
            return 'text'
    
    def get_numeric_value(self) -> Optional[float]:
        """Get numeric value if possible"""
        if not self.value:
            return None
        try:
            return float(self.value)
        except (ValueError, TypeError):
            return None
    
    def is_vital_sign(self) -> bool:
        """Check if this is a vital sign"""
        vital_keywords = ['blood pressure', 'heart rate', 'temperature', 'respiratory rate',
                         'oxygen saturation', 'pulse', 'bp', 'hr', 'temp', 'rr', 'spo2']
        desc_lower = self.description.lower()
        return any(keyword in desc_lower for keyword in vital_keywords)
    
    def is_lab_result(self) -> bool:
        """Check if this is a laboratory result"""
        lab_keywords = ['glucose', 'cholesterol', 'hemoglobin', 'hematocrit', 'wbc', 'rbc',
                       'platelet', 'creatinine', 'bun', 'sodium', 'potassium', 'chloride']
        desc_lower = self.description.lower()
        return any(keyword in desc_lower for keyword in lab_keywords)
    
    def is_abnormal(self) -> Optional[bool]:
        """Check if observation is abnormal based on common reference ranges"""
        numeric_value = self.get_numeric_value()
        if numeric_value is None:
            return None
        
        desc_lower = self.description.lower()
        
        # Basic vital sign ranges (simplified)
        if 'heart rate' in desc_lower or 'pulse' in desc_lower:
            return numeric_value < 60 or numeric_value > 100
        elif 'temperature' in desc_lower and 'celsius' in (self.units or '').lower():
            return numeric_value < 36.1 or numeric_value > 37.2
        elif 'temperature' in desc_lower and 'fahrenheit' in (self.units or '').lower():
            return numeric_value < 97.0 or numeric_value > 99.0
        elif 'glucose' in desc_lower:
            return numeric_value < 70 or numeric_value > 140
        
        return None  # Cannot determine without specific reference ranges
    
    def get_observation_category(self) -> str:
        """Get category of observation"""
        if self.is_vital_sign():
            return 'vital_sign'
        elif self.is_lab_result():
            return 'laboratory'
        else:
            return 'clinical'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'date': self.date.isoformat() if self.date else None,
            'patient_id': self.patient_id,
            'encounter_id': self.encounter_id,
            'code': self.code,
            'description': self.description,
            'value': self.value,
            'units': self.units,
            'obs_type': self.obs_type,
            'numeric_value': self.get_numeric_value(),
            'is_vital_sign': self.is_vital_sign(),
            'is_lab_result': self.is_lab_result(),
            'is_abnormal': self.is_abnormal(),
            'category': self.get_observation_category()
        }
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> 'Observation':
        """Create Observation from CSV row"""
        return cls(
            date=row['DATE'],
            patient_id=row['PATIENT'],
            encounter_id=row.get('ENCOUNTER'),
            code=row['CODE'],
            description=row['DESCRIPTION'],
            value=row.get('VALUE'),
            units=row.get('UNITS'),
            obs_type=row.get('TYPE')
        )
    
    def __str__(self) -> str:
        value_str = f": {self.value}" if self.value else ""
        units_str = f" {self.units}" if self.units else ""
        return f"{self.description}{value_str}{units_str}"
    
    def __repr__(self) -> str:
        return f"Observation(code='{self.code}', description='{self.description}', value='{self.value}')"