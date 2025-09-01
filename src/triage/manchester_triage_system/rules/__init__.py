"""Fuzzy Rules Management Package

This package contains fuzzy rules management modules that follow SOLID principles
and implement one class per file for better maintainability.

Reference: FMTS paper by Cremeens & Khorasani (2014)
https://www.researchgate.net/publication/286737453_FMTS_A_fuzzy_implementation_of_the_Manchester_triage_system

All components implement the paper's objective triage system requirements:
- Single responsibility for rule creation and management
- Open/closed principle for extensible rule sources  
- Dependency inversion with configurable rule sources
"""

# Import from individual files (one class per file)
from .rule_builder import RuleBuilder
from .default_fuzzy_rules import DefaultFuzzyRules
from .fuzzy_rules_manager import FuzzyRulesManager

__all__ = [
    'RuleBuilder',
    'DefaultFuzzyRules', 
    'FuzzyRulesManager'
]