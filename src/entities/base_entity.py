"""Base Entity Class

Provides common functionality for all medical entities including date parsing,
CSV operations, and data conversion methods.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging
import csv
import os

logger = logging.getLogger(__name__)

class BaseEntity(ABC):
    """Abstract base class for all medical entities
    
    Provides common functionality for:
    - Date parsing and handling
    - CSV data loading and conversion
    - Data validation and serialization
    - Common utility methods
    """
    
    def __init__(self):
        """Initialize base entity"""
        self.created_at = datetime.now()
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object with multiple format support
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            Parsed datetime object or None if parsing fails
        """
        if not date_str or date_str.strip() == '' or date_str.lower() in ['none', 'null']:
            return None
        
        # Common date formats to try
        date_formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y',
            '%d/%m/%Y'
        ]
        
        # Try ISO format first
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            pass
        
        # Try other common formats
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def _parse_float(self, value) -> Optional[float]:
        """Parse float value safely with validation
        
        Args:
            value: Value to parse as float
            
        Returns:
            Parsed float or None if invalid
        """
        if value is None or value == '' or str(value).lower() in ['none', 'null', 'nan']:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _parse_int(self, value) -> Optional[int]:
        """Parse integer value safely with validation
        
        Args:
            value: Value to parse as integer
            
        Returns:
            Parsed integer or None if invalid
        """
        if value is None or value == '' or str(value).lower() in ['none', 'null']:
            return None
        try:
            return int(float(value))  # Handle cases like "5.0"
        except (ValueError, TypeError):
            return None
    
    def _parse_boolean(self, value) -> Optional[bool]:
        """Parse boolean value from various string representations
        
        Args:
            value: Value to parse as boolean
            
        Returns:
            Parsed boolean or None if invalid
        """
        if value is None or value == '':
            return None
        
        if isinstance(value, bool):
            return value
        
        str_value = str(value).lower().strip()
        if str_value in ['true', '1', 'yes', 'y', 'on']:
            return True
        elif str_value in ['false', '0', 'no', 'n', 'off']:
            return False
        else:
            return None
    
    def _safe_get(self, data: Dict[str, Any], key: str, default=None):
        """Safely get value from dictionary with case-insensitive key matching
        
        Args:
            data: Dictionary to search
            key: Key to find (case-insensitive)
            default: Default value if key not found
            
        Returns:
            Value from dictionary or default
        """
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
    
    def _validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Validate that required fields are present in data
        
        Args:
            data: Data dictionary to validate
            required_fields: List of required field names
            
        Returns:
            True if all required fields present, False otherwise
        """
        missing_fields = []
        for field in required_fields:
            if not self._safe_get(data, field):
                missing_fields.append(field)
        
        if missing_fields:
            logger.warning(f"Missing required fields: {missing_fields}")
            return False
        
        return True
    
    @classmethod
    def get_csv_file_path(cls) -> str:
        """Generate CSV file path based on class name
        
        Returns:
            Path to CSV file for this entity type
        """
        # Convert class name to CSV filename
        # MedicalCondition -> medical_condition -> conditions.csv
        # Medication -> medication -> medications.csv
        class_name = cls.__name__
        
        # Handle special cases
        if class_name == 'MedicalCondition':
            csv_name = 'conditions.csv'
        elif class_name == 'Patient':
            csv_name = 'patients.csv'
        else:
            # Convert CamelCase to snake_case and add 's' for plural
            import re
            snake_case = re.sub('([A-Z])', r'_\1', class_name).lower().lstrip('_')
            csv_name = f"{snake_case}s.csv"
        
        return os.path.join('output', 'csv', csv_name)
    
    @classmethod
    def load_from_csv(cls, patient_id: str = None, 
                     patient_field: str = 'PATIENT') -> List['BaseEntity']:
        """Load entities from CSV file using auto-generated path
        
        Args:
            patient_id: Optional patient ID to filter by
            patient_field: Name of patient ID field in CSV
            
        Returns:
            List of entity instances
        """
        csv_file_path = cls.get_csv_file_path()
        
        if not os.path.exists(csv_file_path):
            logger.warning(f"CSV file not found: {csv_file_path}")
            return []
        
        entities = []
        try:
            with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Filter by patient ID if specified
                    if patient_id and row.get(patient_field) != patient_id:
                        continue
                    
                    try:
                        entity = cls.from_csv_row(row)
                        if entity:
                            entities.append(entity)
                    except Exception as e:
                        logger.error(f"Error creating {cls.__name__} from row: {e}")
        except Exception as e:
            logger.error(f"Error reading CSV file {csv_file_path}: {e}")
        
        return entities
    
    @classmethod
    @abstractmethod
    def from_csv_row(cls, row: Dict[str, str]) -> Optional['BaseEntity']:
        """Create entity instance from CSV row
        
        Args:
            row: Dictionary containing CSV row data
            
        Returns:
            Entity instance or None if creation fails
        """
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary for serialization
        
        Returns:
            Dictionary representation of entity
        """
        pass
    
    def to_json_serializable(self) -> Dict[str, Any]:
        """Convert entity to JSON-serializable dictionary
        
        Returns:
            JSON-serializable dictionary
        """
        data = self.to_dict()
        
        # Convert datetime objects to ISO strings
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        
        return data
    
    def get_age_from_birthdate(self, birthdate: datetime, reference_date: datetime = None) -> Optional[int]:
        """Calculate age from birthdate
        
        Args:
            birthdate: Birth date
            reference_date: Reference date (defaults to now)
            
        Returns:
            Age in years or None if calculation fails
        """
        if not birthdate:
            return None
        
        if not reference_date:
            reference_date = datetime.now()
        
        try:
            age = reference_date.year - birthdate.year
            # Adjust if birthday hasn't occurred this year
            if reference_date.month < birthdate.month or \
               (reference_date.month == birthdate.month and reference_date.day < birthdate.day):
                age -= 1
            return max(0, age)
        except Exception as e:
            logger.warning(f"Error calculating age: {e}")
            return None
    
    def days_between_dates(self, start_date: datetime, end_date: datetime = None) -> Optional[int]:
        """Calculate days between two dates
        
        Args:
            start_date: Start date
            end_date: End date (defaults to now)
            
        Returns:
            Number of days or None if calculation fails
        """
        if not start_date:
            return None
        
        if not end_date:
            end_date = datetime.now()
        
        try:
            return (end_date - start_date).days
        except Exception as e:
            logger.warning(f"Error calculating days between dates: {e}")
            return None
    
    def __str__(self) -> str:
        """String representation of entity"""
        return f"{self.__class__.__name__}()"
    
    def __repr__(self) -> str:
        """Detailed representation of entity"""
        return f"{self.__class__.__name__}(created_at={self.created_at})"