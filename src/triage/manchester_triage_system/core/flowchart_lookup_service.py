"""Flowchart Lookup Service

This module provides flowchart lookup operations following SOLID principles.

Reference: FMTS paper Section II - "The system consists of around 50 flowcharts with 
standard definitions designed to categorize patients arriving to an emergency room 
based on their level of urgency."

Paper Context: "For a triage nurse with 50 flowcharts in her hand, trying to 
correctly prioritize a patient is a clumsy process."

This service addresses the paper's concern by providing systematic flowchart 
management that eliminates the need for manual flowchart navigation.

Single Responsibility: Only handles flowchart lookup logic
"""

from typing import Dict, List, Any, Optional
from ..config import FlowchartConfigManager


class FlowchartLookupService:
    """Service for flowchart lookup operations
    
    Single Responsibility: Only handles flowchart lookup logic
    """
    
    def __init__(self, flowchart_manager: FlowchartConfigManager):
        self._flowchart_manager = flowchart_manager
    
    def find_flowchart(self, flowchart_reason: str) -> Optional[Dict[str, Any]]:
        """Find flowchart configuration by reason"""
        return self._flowchart_manager.get_flowchart(flowchart_reason)
    
    def get_default_flowchart(self) -> Dict[str, Any]:
        """Get default flowchart when requested one is not found"""
        # Default to chest_pain as per original implementation
        return self._flowchart_manager.get_flowchart('chest_pain')
    
    def get_flowchart_symptoms(self, flowchart_reason: str) -> List[str]:
        """Get symptoms for a specific flowchart"""
        return self._flowchart_manager.get_symptoms_for_flowchart(flowchart_reason)