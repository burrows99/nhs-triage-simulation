"""Core Triage Processing Package

This package contains the core triage processing logic with SOLID principles:
- Single responsibility for each processing component
- Dependency inversion with injected services
- Open/closed principle for extensible processing strategies
"""

from .triage_processor import (
    TriageProcessor,
    FlowchartLookupService,
    SymptomProcessor,
    FuzzyInferenceEngine,
    TriageResultBuilder,
    TriageValidator
)

__all__ = [
    'TriageProcessor',
    'FlowchartLookupService',
    'SymptomProcessor',
    'FuzzyInferenceEngine',
    'TriageResultBuilder',
    'TriageValidator'
]