"""Fuzzy Rules Management Package

This module provides imports for all fuzzy rules components that have been
split into separate files following the one-class-per-file principle.

Reference: FMTS paper by Cremeens & Khorasani (2014)
https://www.researchgate.net/publication/286737453_FMTS_A_fuzzy_implementation_of_the_Manchester_triage_system

All components implement the paper's objective triage system requirements.
"""

# Import all fuzzy rules components
from .rule_builder import RuleBuilder
from .default_fuzzy_rules import DefaultFuzzyRules
from .fuzzy_rules_manager import FuzzyRulesManager

# Export all components for backward compatibility
__all__ = [
    'RuleBuilder', 
    'DefaultFuzzyRules',
    'FuzzyRulesManager'
]