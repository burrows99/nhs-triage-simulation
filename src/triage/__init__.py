"""Simplified triage system module for emergency department simulation

This module provides triage systems:
1. BaseTriage - Abstract base class for all triage systems
2. ManchesterTriage - NHS Manchester Triage System with fuzzy logic

Each system accepts arrays of patients and assigns priorities with reasons and service times.
AI triage system to be implemented later.
"""

from .base_triage import BaseTriage, TriageResult
from .manchester_triage import ManchesterTriage

__all__ = [
    'BaseTriage',
    'TriageResult',
    'ManchesterTriage'
]