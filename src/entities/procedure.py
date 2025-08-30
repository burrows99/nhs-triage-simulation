"""Procedure Entity

Represents a medical procedure from the procedures.csv data.
"""

from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class Procedure:
    """Represents a medical procedure"""
    
    def __init__(self, date: str, patient_id: str, encounter_id: Optional[str],
                 code: str, description: str, base_cost: Optional[float] = None,
                 reason_code: Optional[str] = None, reason_description: Optional[str] = None):
        self.date = self._parse_date(date)
        self.patient_id = patient_id
        self.encounter_id = encounter_id
        self.code = code
        self.description = description
        self.base_cost = self._parse_float(base_cost)
        self.reason_code = reason_code
        self.reason_description = reason_description
    
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
    
    def is_surgical(self) -> bool:
        """Check if this is a surgical procedure"""
        surgical_keywords = ['surgery', 'surgical', 'operation', 'excision', 'incision',
                           'repair', 'reconstruction', 'transplant', 'implant', 'removal']
        desc_lower = self.description.lower()
        return any(keyword in desc_lower for keyword in surgical_keywords)
    
    def is_diagnostic(self) -> bool:
        """Check if this is a diagnostic procedure"""
        diagnostic_keywords = ['biopsy', 'endoscopy', 'colonoscopy', 'bronchoscopy',
                             'catheterization', 'angiography', 'ultrasound', 'ct', 'mri']
        desc_lower = self.description.lower()
        return any(keyword in desc_lower for keyword in diagnostic_keywords)
    
    def is_therapeutic(self) -> bool:
        """Check if this is a therapeutic procedure"""
        therapeutic_keywords = ['therapy', 'treatment', 'injection', 'infusion',
                              'dialysis', 'chemotherapy', 'radiation']
        desc_lower = self.description.lower()
        return any(keyword in desc_lower for keyword in therapeutic_keywords)
    
    def is_preventive(self) -> bool:
        """Check if this is a preventive procedure"""
        preventive_keywords = ['screening', 'vaccination', 'immunization', 'prophylaxis',
                             'prevention', 'checkup', 'examination']
        desc_lower = self.description.lower()
        return any(keyword in desc_lower for keyword in preventive_keywords)
    
    def get_procedure_category(self) -> str:
        """Get category of procedure"""
        if self.is_surgical():
            return 'surgical'
        elif self.is_diagnostic():
            return 'diagnostic'
        elif self.is_therapeutic():
            return 'therapeutic'
        elif self.is_preventive():
            return 'preventive'
        else:
            return 'other'
    
    def get_cost_category(self) -> str:
        """Categorize procedure by cost"""
        if self.base_cost is None:
            return 'unknown'
        elif self.base_cost < 100:
            return 'low_cost'
        elif self.base_cost < 1000:
            return 'moderate_cost'
        elif self.base_cost < 10000:
            return 'high_cost'
        else:
            return 'very_high_cost'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'date': self.date.isoformat() if self.date else None,
            'patient_id': self.patient_id,
            'encounter_id': self.encounter_id,
            'code': self.code,
            'description': self.description,
            'base_cost': self.base_cost,
            'reason_code': self.reason_code,
            'reason_description': self.reason_description,
            'procedure_category': self.get_procedure_category(),
            'cost_category': self.get_cost_category(),
            'is_surgical': self.is_surgical(),
            'is_diagnostic': self.is_diagnostic(),
            'is_therapeutic': self.is_therapeutic(),
            'is_preventive': self.is_preventive()
        }
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> 'Procedure':
        """Create Procedure from CSV row"""
        return cls(
            date=row['DATE'],
            patient_id=row['PATIENT'],
            encounter_id=row.get('ENCOUNTER'),
            code=row['CODE'],
            description=row['DESCRIPTION'],
            base_cost=row.get('BASE_COST'),
            reason_code=row.get('REASONCODE'),
            reason_description=row.get('REASONDESCRIPTION')
        )
    
    def __str__(self) -> str:
        cost_str = f" (${self.base_cost:.2f})" if self.base_cost else ""
        return f"{self.description} ({self.code}){cost_str}"
    
    def __repr__(self) -> str:
        return f"Procedure(code='{self.code}', description='{self.description}', category='{self.get_procedure_category()}')"