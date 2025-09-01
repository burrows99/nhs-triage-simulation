"""Flowchart Configuration Package

This module provides imports for all flowchart configuration components that have been
split into separate files following the one-class-per-file principle.

Reference: FMTS paper by Cremeens & Khorasani (2014)
https://www.researchgate.net/publication/286737453_FMTS_A_fuzzy_implementation_of_the_Manchester_triage_system

All components implement the paper's systematic flowchart management requirements.
"""

# Import all flowchart configuration components
from .flowchart_config_source import FlowchartConfigSource
from .default_flowchart_config import DefaultFlowchartConfig
from .flowchart_config_manager import FlowchartConfigManager

# Export all components for backward compatibility
__all__ = [
    'FlowchartConfigSource',
    'DefaultFlowchartConfig',
    'FlowchartConfigManager'
]