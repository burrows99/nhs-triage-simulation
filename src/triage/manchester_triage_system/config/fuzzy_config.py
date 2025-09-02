"""Fuzzy System Configuration Management

This module handles the configuration of fuzzy logic components,
separating fuzzy system setup from the core triage logic.

Follows SOLID principles:
- Single Responsibility: Only manages fuzzy system configuration
- Open/Closed: Extensible for different fuzzy system types
- Dependency Inversion: Uses abstractions for configuration
"""

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
from typing import Dict, List, Any, Protocol
from src.triage.triage_constants import (
    TriageCategories, LinguisticValues, FuzzyCategories, WaitTimeDisplays
)


class LinguisticValueConverter:
    """Handles conversion between linguistic and numeric values
    
    Single Responsibility: Only handles linguistic-numeric conversion
    """
    
    def __init__(self, mapping: Dict[str, float] = None):
        self._mapping = mapping or self._get_default_mapping()
    
    def _get_default_mapping(self) -> Dict[str, float]:
        """Get default linguistic to numeric mapping
        
        Reference: FMTS paper Section II - objective numeric mapping
        for imprecise linguistic terms
        """
        return LinguisticValues.get_numeric_mapping()
    
    def convert_to_numeric(self, linguistic_value: str) -> float:
        """Convert linguistic value to numeric representation"""
        return self._mapping.get(linguistic_value.lower(), 0.0)
    
    def convert_to_linguistic(self, numeric_value: float) -> str:
        """Convert numeric value to closest linguistic representation"""
        # Find closest linguistic value
        min_diff = float('inf')
        closest_term = 'none'
        
        for term, value in self._mapping.items():
            diff = abs(numeric_value - value)
            if diff < min_diff:
                min_diff = diff
                closest_term = term
        
        return closest_term
    
    def get_mapping(self) -> Dict[str, float]:
        """Get the current linguistic-numeric mapping"""
        return self._mapping.copy()
    
    def update_mapping(self, new_mapping: Dict[str, float]) -> None:
        """Update the linguistic-numeric mapping"""
        self._mapping.update(new_mapping)


class TriageCategoryMapper:
    """Handles mapping between fuzzy scores and triage categories
    
    Single Responsibility: Only handles triage category mapping
    """
    
    def __init__(self):
        self._categories = np.array(TriageCategories.get_all_categories())
        self._wait_times = np.array(WaitTimeDisplays.get_wait_time_displays())
        self._priority_scores = np.array([1, 2, 3, 4, 5])
    
    def map_score_to_category(self, fuzzy_score: float) -> Dict[str, Any]:
        """Map fuzzy score to triage category and wait time
        
        Reference: FMTS paper - "What does the categorization of a patient 
        mean for her waiting time to be treated?"
        """
        # Use numpy's automatic rounding and indexing
        category_index = int(np.round(fuzzy_score)) - 1
        category_index = np.clip(category_index, 0, 4)  # Ensure valid index
        
        return {
            'category': self._categories[category_index],
            'wait_time': self._wait_times[category_index],
            'priority_score': self._priority_scores[category_index],
            'category_index': category_index
        }
    
    def get_categories(self) -> List[str]:
        """Get available triage categories"""
        return self._categories.tolist()
    
    def get_wait_times(self) -> List[str]:
        """Get wait times for each category"""
        return self._wait_times.tolist()


class DefaultFuzzyConfig:
    """Default fuzzy system configuration based on FMTS paper
    
    Reference: FMTS paper describes fuzzy system implementation
    """
    
    @staticmethod
    def get_input_variables_config() -> Dict[str, Any]:
        """Get input variables configuration
        
        Reference: FMTS paper - 5 symptoms input variables
        """
        return {
            'num_symptoms': 5,
            'universe_range': (0, 11),
            'universe_step': 1,
            'variable_names': ['symptom1', 'symptom2', 'symptom3', 'symptom4', 'symptom5']
        }
    
    @staticmethod
    def get_output_variables_config() -> Dict[str, Any]:
        """Get output variables configuration
        
        Reference: FMTS paper - triage category output (1-5 scale)
        """
        return {
            'universe_range': (1, 6),
            'universe_step': 1,
            'variable_name': 'triage_category'
        }
    
    @staticmethod
    def get_linguistic_terms() -> List[str]:
        """Get linguistic terms
        
        Reference: FMTS paper - imprecise linguistic terms
        """
        return LinguisticValues.get_severity_levels()
    
    @staticmethod
    def get_membership_functions_config() -> Dict[str, Any]:
        """Get membership functions configuration
        
        Reference: FMTS paper - triangular membership functions
        """
        return {
            'input_function_type': 'auto',  # Use scikit-fuzzy's automf
            'output_functions': FuzzyCategories.get_membership_functions()
        }


class FuzzyVariableFactory:
    """Factory for creating fuzzy variables
    
    Single Responsibility: Only creates fuzzy variables
    Open/Closed: Can be extended for new variable types
    """
    
    @staticmethod
    def create_input_variables(config: Dict[str, Any], linguistic_terms: List[str]) -> List[ctrl.Antecedent]:
        """Create input variables (antecedents) for fuzzy system"""
        universe = np.arange(
            config['universe_range'][0],
            config['universe_range'][1],
            config['universe_step']
        )
        
        variables = []
        for var_name in config['variable_names']:
            variable = ctrl.Antecedent(universe, var_name)
            variable.automf(names=linguistic_terms)
            variables.append(variable)
        
        return variables
    
    @staticmethod
    def create_output_variable(config: Dict[str, Any], membership_config: Dict[str, Any]) -> ctrl.Consequent:
        """Create output variable (consequent) for fuzzy system"""
        universe = np.arange(
            config['universe_range'][0],
            config['universe_range'][1],
            config['universe_step']
        )
        
        variable = ctrl.Consequent(universe, config['variable_name'])
        
        # Create membership functions for output categories
        for category, points in membership_config['output_functions'].items():
            variable[category] = fuzz.trimf(variable.universe, points)
        
        return variable


class FuzzySystemConfigManager:
    """Manages fuzzy system configuration with SOLID principles
    
    Single Responsibility: Manages fuzzy system configuration
    Open/Closed: Can be extended with new configuration sources
    """
    
    def __init__(self):
        """Initialize with default fuzzy configuration"""
        self._config_source = DefaultFuzzyConfig()
        self._linguistic_converter = None
        self._category_mapper = None
        self._input_variables = None
        self._output_variable = None
    
    def get_linguistic_converter(self) -> LinguisticValueConverter:
        """Get linguistic value converter"""
        if self._linguistic_converter is None:
            self._linguistic_converter = LinguisticValueConverter()
        return self._linguistic_converter
    
    def get_category_mapper(self) -> TriageCategoryMapper:
        """Get triage category mapper"""
        if self._category_mapper is None:
            self._category_mapper = TriageCategoryMapper()
        return self._category_mapper
    
    def create_input_variables(self) -> List[ctrl.Antecedent]:
        """Create fuzzy input variables"""
        if self._input_variables is None:
            input_config = self._config_source.get_input_variables_config()
            linguistic_terms = self._config_source.get_linguistic_terms()
            self._input_variables = FuzzyVariableFactory.create_input_variables(
                input_config, linguistic_terms
            )
        return self._input_variables
    
    def create_output_variable(self) -> ctrl.Consequent:
        """Create fuzzy output variable"""
        if self._output_variable is None:
            output_config = self._config_source.get_output_variables_config()
            membership_config = self._config_source.get_membership_functions_config()
            self._output_variable = FuzzyVariableFactory.create_output_variable(
                output_config, membership_config
            )
        return self._output_variable
    
    def get_linguistic_terms(self) -> List[str]:
        """Get linguistic terms"""
        return self._config_source.get_linguistic_terms()
    
    def validate_fuzzy_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate fuzzy system configuration"""
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate input variables config
        if 'input_variables' in config:
            input_config = config['input_variables']
            if 'num_symptoms' not in input_config:
                validation_result['errors'].append("Missing num_symptoms in input config")
            elif input_config['num_symptoms'] != 5:
                validation_result['warnings'].append("FMTS paper specifies 5 input symptoms")
        
        # Validate linguistic terms
        if 'linguistic_terms' in config:
            terms = config['linguistic_terms']
            expected_terms = LinguisticValues.get_severity_levels()
            if terms != expected_terms:
                validation_result['warnings'].append("Non-standard linguistic terms detected")
        
        # Validate output categories
        if 'output_functions' in config:
            functions = config['output_functions']
            expected_categories = FuzzyCategories.get_all_categories()
            missing_categories = set(expected_categories) - set(functions.keys())
            if missing_categories:
                validation_result['errors'].append(f"Missing output categories: {missing_categories}")
        
        if validation_result['errors']:
            validation_result['valid'] = False
        
        return validation_result