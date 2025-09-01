"""Base Validator for Manchester Triage System

This module provides a base validation class to eliminate code duplication
across validation methods in the MTS system.

Reference: FMTS paper emphasizes systematic validation for objective triage assessment.
"""

from typing import Dict, List, Any
from abc import ABC, abstractmethod


class BaseValidator(ABC):
    """Base class for all MTS validation operations.
    
    Eliminates code duplication by providing common validation patterns
    and standardized result structures.
    """
    
    @staticmethod
    def create_validation_result(include_paper_compliance: bool = False) -> Dict[str, Any]:
        """Create standardized validation result structure.
        
        Args:
            include_paper_compliance: Whether to include paper compliance field
            
        Returns:
            Dictionary with standard validation fields
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        if include_paper_compliance:
            result['paper_compliance'] = True
            
        return result
    
    @staticmethod
    def add_error(result: Dict[str, Any], error: str, 
                  invalidate_paper_compliance: bool = False) -> None:
        """Add error to validation result.
        
        Args:
            result: Validation result dictionary
            error: Error message to add
            invalidate_paper_compliance: Whether this error affects paper compliance
        """
        result['valid'] = False
        result['errors'].append(error)
        
        if invalidate_paper_compliance and 'paper_compliance' in result:
            result['paper_compliance'] = False
    
    @staticmethod
    def add_warning(result: Dict[str, Any], warning: str) -> None:
        """Add warning to validation result.
        
        Args:
            result: Validation result dictionary
            warning: Warning message to add
        """
        result['warnings'].append(warning)
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], 
                               required_fields: List[str],
                               result: Dict[str, Any]) -> None:
        """Validate that all required fields are present.
        
        Args:
            data: Data dictionary to validate
            required_fields: List of required field names
            result: Validation result to update
        """
        for field in required_fields:
            if field not in data:
                BaseValidator.add_error(result, f"Missing required field: {field}")
    
    @staticmethod
    def validate_field_type(data: Dict[str, Any], field: str, 
                          expected_type: type, result: Dict[str, Any]) -> None:
        """Validate field type.
        
        Args:
            data: Data dictionary to validate
            field: Field name to check
            expected_type: Expected Python type
            result: Validation result to update
        """
        if field in data and not isinstance(data[field], expected_type):
            BaseValidator.add_error(
                result, 
                f"Field '{field}' must be of type {expected_type.__name__}, got {type(data[field]).__name__}"
            )
    
    @staticmethod
    def validate_field_values(data: Dict[str, Any], field: str,
                            valid_values: List[Any], result: Dict[str, Any],
                            case_sensitive: bool = True) -> None:
        """Validate field values against allowed list.
        
        Args:
            data: Data dictionary to validate
            field: Field name to check
            valid_values: List of valid values
            result: Validation result to update
            case_sensitive: Whether comparison should be case sensitive
        """
        if field not in data:
            return
            
        value = data[field]
        
        if not case_sensitive and isinstance(value, str):
            value = value.lower()
            valid_values = [str(v).lower() for v in valid_values]
        
        if value not in valid_values:
            BaseValidator.add_error(
                result,
                f"Invalid value '{data[field]}' for field '{field}'. Valid values: {valid_values}"
            )
    
    @staticmethod
    def validate_linguistic_values(symptoms: Dict[str, str], 
                                 result: Dict[str, Any]) -> None:
        """Validate linguistic values for symptoms.
        
        Args:
            symptoms: Dictionary of symptom name to linguistic value
            result: Validation result to update
        """
        valid_linguistic_values = ['none', 'mild', 'moderate', 'severe', 'very_severe']
        
        for symptom, value in symptoms.items():
            if not isinstance(value, str):
                BaseValidator.add_error(
                    result,
                    f"Symptom '{symptom}' value must be string, got {type(value).__name__}"
                )
                continue
                
            if value.lower() not in valid_linguistic_values:
                BaseValidator.add_warning(
                    result,
                    f"Non-standard linguistic value '{value}' for symptom '{symptom}'"
                )
    
    @abstractmethod
    def validate(self, data: Any) -> Dict[str, Any]:
        """Abstract method for specific validation implementation.
        
        Args:
            data: Data to validate
            
        Returns:
            Validation result dictionary
        """
        pass