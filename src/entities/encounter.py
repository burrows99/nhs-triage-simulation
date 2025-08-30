"""Encounter Entity

Represents a healthcare encounter from the encounters.csv data.
"""

from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class Encounter:
    """Represents a healthcare encounter/visit"""
    
    def __init__(self, encounter_id: str, start: str, stop: Optional[str], 
                 patient_id: str, provider_id: Optional[str], payer_id: Optional[str],
                 encounter_class: str, code: str, description: str,
                 base_encounter_cost: Optional[float] = None,
                 total_claim_cost: Optional[float] = None,
                 payer_coverage: Optional[float] = None,
                 reason_code: Optional[str] = None,
                 reason_description: Optional[str] = None):
        self.encounter_id = encounter_id
        self.start = self._parse_date(start)
        self.stop = self._parse_date(stop) if stop else None
        self.patient_id = patient_id
        self.provider_id = provider_id
        self.payer_id = payer_id
        self.encounter_class = encounter_class
        self.code = code
        self.description = description
        self.base_encounter_cost = self._parse_float(base_encounter_cost)
        self.total_claim_cost = self._parse_float(total_claim_cost)
        self.payer_coverage = self._parse_float(payer_coverage)
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
    
    def get_duration_hours(self) -> Optional[float]:
        """Get duration of encounter in hours"""
        if not self.start or not self.stop:
            return None
        return (self.stop - self.start).total_seconds() / 3600
    
    def get_out_of_pocket_cost(self) -> Optional[float]:
        """Calculate out-of-pocket cost"""
        if self.total_claim_cost is None:
            return None
        if self.payer_coverage is None:
            return self.total_claim_cost
        return max(0, self.total_claim_cost - self.payer_coverage)
    
    def is_emergency(self) -> bool:
        """Check if this is an emergency encounter"""
        return self.encounter_class.lower() in ['emergency', 'emergent', 'urgent']
    
    def is_inpatient(self) -> bool:
        """Check if this is an inpatient encounter"""
        return self.encounter_class.lower() in ['inpatient', 'inpatient encounter']
    
    def is_outpatient(self) -> bool:
        """Check if this is an outpatient encounter"""
        return self.encounter_class.lower() in ['outpatient', 'ambulatory', 'office visit']
    
    def get_encounter_type(self) -> str:
        """Get standardized encounter type"""
        if self.is_emergency():
            return 'emergency'
        elif self.is_inpatient():
            return 'inpatient'
        elif self.is_outpatient():
            return 'outpatient'
        else:
            return 'other'
    
    def is_completed(self) -> bool:
        """Check if encounter is completed"""
        return self.stop is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'encounter_id': self.encounter_id,
            'start': self.start.isoformat() if self.start else None,
            'stop': self.stop.isoformat() if self.stop else None,
            'patient_id': self.patient_id,
            'provider_id': self.provider_id,
            'payer_id': self.payer_id,
            'encounter_class': self.encounter_class,
            'code': self.code,
            'description': self.description,
            'base_encounter_cost': self.base_encounter_cost,
            'total_claim_cost': self.total_claim_cost,
            'payer_coverage': self.payer_coverage,
            'reason_code': self.reason_code,
            'reason_description': self.reason_description,
            'duration_hours': self.get_duration_hours(),
            'out_of_pocket_cost': self.get_out_of_pocket_cost(),
            'encounter_type': self.get_encounter_type(),
            'is_completed': self.is_completed()
        }
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, str]) -> 'Encounter':
        """Create Encounter from CSV row"""
        return cls(
            encounter_id=row['Id'],
            start=row['START'],
            stop=row.get('STOP'),
            patient_id=row['PATIENT'],
            provider_id=row.get('PROVIDER'),
            payer_id=row.get('PAYER'),
            encounter_class=row['ENCOUNTERCLASS'],
            code=row['CODE'],
            description=row['DESCRIPTION'],
            base_encounter_cost=row.get('BASE_ENCOUNTER_COST'),
            total_claim_cost=row.get('TOTAL_CLAIM_COST'),
            payer_coverage=row.get('PAYER_COVERAGE'),
            reason_code=row.get('REASONCODE'),
            reason_description=row.get('REASONDESCRIPTION')
        )
    
    def __str__(self) -> str:
        status = "Completed" if self.is_completed() else "Ongoing"
        return f"{self.description} ({self.encounter_class}) - {status}"
    
    def __repr__(self) -> str:
        return f"Encounter(id='{self.encounter_id}', type='{self.get_encounter_type()}', description='{self.description}')"