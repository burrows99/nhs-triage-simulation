"""Triage Validator

This module validates triage inputs and results following SOLID principles.

Single Responsibility: Only handles validation
"""

from typing import Dict, Any
from src.triage.triage_constants import TriageCategories
from .base_validator import BaseValidator
from ..paper_references import FMTSPaperReferences, reference_section_ii, paper_context


class TriageValidator(BaseValidator):
    """Validates triage inputs and results
    
    Single Responsibility: Only handles validation
    
    Reference: FMTS paper Section II - addresses systematic validation needs
    Paper Context: Eliminates subjective interpretation through consistent validation
    """
    
    @staticmethod
    def validate_inputs(flowchart_reason: str, symptoms_input: Dict[str, str]) -> Dict[str, Any]:
        """Validate triage inputs.
        
        Reference: FMTS paper emphasizes systematic input validation
        """
        result = BaseValidator.create_validation_result()
        
        # Validate flowchart reason
        if not flowchart_reason or not isinstance(flowchart_reason, str):
            BaseValidator.add_error(result, "Invalid flowchart reason")
        
        # Validate symptoms input structure
        BaseValidator.validate_field_type(
            {'symptoms': symptoms_input}, 'symptoms', dict, result
        )
        
        if isinstance(symptoms_input, dict):
            if len(symptoms_input) == 0:
                BaseValidator.add_warning(result, "No symptoms provided")
            else:
                # Validate linguistic values
                BaseValidator.validate_linguistic_values(symptoms_input, result)
        
        return result
    
    @staticmethod
    def validate_result(result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate triage result.
        
        Reference: FMTS paper requires systematic result validation
        """
        validation_result = BaseValidator.create_validation_result()
        
        # Check required fields
        required_fields = ['flowchart_used', 'triage_category', 'wait_time', 'fuzzy_score']
        BaseValidator.validate_required_fields(result, required_fields, validation_result)
        
        # Validate triage category
        if 'triage_category' in result:
            valid_categories = TriageCategories.get_all_categories()
            BaseValidator.validate_field_values(
                result, 'triage_category', valid_categories, validation_result
            )
        
        return validation_result
    
    def validate(self, data: Any) -> Dict[str, Any]:
        """Implementation of abstract validate method.
        
        Args:
            data: Triage data to validate (can be inputs or results)
            
        Returns:
            Validation result dictionary
        """
        if isinstance(data, dict) and 'triage_category' in data:
            return self.validate_result(data)
        else:
            # Assume it's input validation - this is a simplified approach
            return BaseValidator.create_validation_result()