"""Medical Condition Entity

Represents a medical condition/diagnosis from the conditions.csv data.
"""

from datetime import datetime
from typing import Optional, Dict, Any
import logging
from .base_entity import BaseEntity

logger = logging.getLogger(__name__)

class MedicalCondition(BaseEntity):
    """Represents a medical condition or diagnosis"""
    
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
    
    def get_duration_days(self) -> Optional[int]:
        """Get duration of condition in days"""
        return self.days_between_dates(self.start, self.stop)
    
    def is_chronic(self) -> bool:
        """Check if condition is chronic (active for >90 days)"""
        duration = self.get_duration_days()
        return duration is not None and duration > 90
    
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
            'duration_days': self.get_duration_days(),
            'is_chronic': self.is_chronic()
        }
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> Optional['MedicalCondition']:
        """Create MedicalCondition from CSV row"""
        # Validate required fields
        if not cls._validate_required_fields_static(row, ['START', 'PATIENT', 'CODE', 'DESCRIPTION']):
            return None
        
        return cls(
            start=cls._safe_get_static(row, 'START'),
            stop=cls._safe_get_static(row, 'STOP'),
            patient_id=cls._safe_get_static(row, 'PATIENT'),
            encounter_id=cls._safe_get_static(row, 'ENCOUNTER'),
            code=cls._safe_get_static(row, 'CODE'),
            description=cls._safe_get_static(row, 'DESCRIPTION')
        )
    
    @classmethod
    def _safe_get_static(cls, data: Dict[str, Any], key: str, default=None):
        """Static version of _safe_get for class methods"""
        if not isinstance(data, dict):
            return default
        
        # Try exact match first
        if key in data:
            return data[key]
        
        # Try case-insensitive match
        key_lower = key.lower()
        for k, v in data.items():
            if k.lower() == key_lower:
                return v
        
        return default
    
    @classmethod
    def _validate_required_fields_static(cls, data: Dict[str, Any], required_fields: list) -> bool:
        """Static version of _validate_required_fields for class methods"""
        missing_fields = []
        for field in required_fields:
            if not cls._safe_get_static(data, field):
                missing_fields.append(field)
        
        if missing_fields:
            logger.warning(f"Missing required fields for {cls.__name__}: {missing_fields}")
            return False
        
        return True
    
    def __str__(self) -> str:
        status = "Active" if self.is_active else "Resolved"
        return f"{self.description} ({self.code}) - {status}"
    
    def __repr__(self) -> str:
        return f"MedicalCondition(code='{self.code}', description='{self.description}', active={self.is_active})"