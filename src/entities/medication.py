"""Medication Entity

Represents a medication from the medications.csv data.
"""

from datetime import datetime
from typing import Optional, Dict, Any
import logging
from .base_entity import BaseEntity

logger = logging.getLogger(__name__)

class Medication(BaseEntity):
    """Represents a medication prescription or administration"""
    
    def __init__(self, start: str, stop: Optional[str], patient_id: str, 
                 payer_id: Optional[str], encounter_id: Optional[str], 
                 code: str, description: str, base_cost: Optional[float] = None,
                 payer_coverage: Optional[float] = None, dispenses: Optional[int] = None,
                 total_cost: Optional[float] = None, reason_code: Optional[str] = None,
                 reason_description: Optional[str] = None):
        super().__init__()
        self.start = self._parse_date(start)
        self.stop = self._parse_date(stop) if stop else None
        self.patient_id = patient_id
        self.payer_id = payer_id
        self.encounter_id = encounter_id
        self.code = code
        self.description = description
        self.base_cost = self._parse_float(base_cost)
        self.payer_coverage = self._parse_float(payer_coverage)
        self.dispenses = self._parse_int(dispenses)
        self.total_cost = self._parse_float(total_cost)
        self.reason_code = reason_code
        self.reason_description = reason_description
        self.is_active = self.stop is None
    

    
    def get_duration_days(self) -> Optional[int]:
        """Get duration of medication in days"""
        return self.days_between_dates(self.start, self.stop)
    
    def get_out_of_pocket_cost(self) -> Optional[float]:
        """Calculate out-of-pocket cost"""
        if self.total_cost is None:
            return None
        if self.payer_coverage is None:
            return self.total_cost
        return max(0, self.total_cost - self.payer_coverage)
    
    def is_long_term(self) -> bool:
        """Check if medication is long-term (>30 days)"""
        duration = self.get_duration_days()
        return duration is not None and duration > 30
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'start': self.start.isoformat() if self.start else None,
            'stop': self.stop.isoformat() if self.stop else None,
            'patient_id': self.patient_id,
            'payer_id': self.payer_id,
            'encounter_id': self.encounter_id,
            'code': self.code,
            'description': self.description,
            'base_cost': self.base_cost,
            'payer_coverage': self.payer_coverage,
            'dispenses': self.dispenses,
            'total_cost': self.total_cost,
            'reason_code': self.reason_code,
            'reason_description': self.reason_description,
            'is_active': self.is_active,
            'duration_days': self.get_duration_days(),
            'out_of_pocket_cost': self.get_out_of_pocket_cost(),
            'is_long_term': self.is_long_term()
        }
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> Optional['Medication']:
        """Create Medication from CSV row"""
        # Use static validation methods from MedicalCondition (or create similar ones)
        required_fields = ['START', 'PATIENT', 'CODE', 'DESCRIPTION']
        missing_fields = []
        for field in required_fields:
            if not row.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            logger.warning(f"Missing required fields for Medication: {missing_fields}")
            return None
        
        return cls(
            start=row.get('START'),
            stop=row.get('STOP'),
            patient_id=row.get('PATIENT'),
            payer_id=row.get('PAYER'),
            encounter_id=row.get('ENCOUNTER'),
            code=row.get('CODE'),
            description=row.get('DESCRIPTION'),
            base_cost=row.get('BASE_COST'),
            payer_coverage=row.get('PAYER_COVERAGE'),
            dispenses=row.get('DISPENSES'),
            total_cost=row.get('TOTALCOST'),
            reason_code=row.get('REASONCODE'),
            reason_description=row.get('REASONDESCRIPTION')
        )
    
    def __str__(self) -> str:
        status = "Active" if self.is_active else "Completed"
        return f"{self.description} ({self.code}) - {status}"
    
    def __repr__(self) -> str:
        return f"Medication(code='{self.code}', description='{self.description}', active={self.is_active})"