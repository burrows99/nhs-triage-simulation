"""Flowchart Configuration Source Protocol

This module defines the protocol for flowchart configuration sources, enabling
dependency inversion for different configuration sources in the FMTS system.

Reference: FMTS paper by Cremeens & Khorasani (2014)
https://www.researchgate.net/publication/286737453_FMTS_A_fuzzy_implementation_of_the_Manchester_triage_system

Paper Quote: "The system consists of around 50 flowcharts with standard definitions 
designed to categorize patients arriving to an emergency room based on their level of urgency."

This protocol supports the paper's emphasis on systematic flowchart management
by allowing different flowchart sources to be plugged into the system.
"""

from typing import Dict, List, Any, Protocol


class FlowchartConfigSource(Protocol):
    """Protocol for flowchart configuration sources
    
    Enables dependency inversion - different sources can be used
    (JSON files, databases, APIs, etc.)
    
    Reference: FMTS paper Section II describes the systematic approach to managing
    the ~50 flowcharts that form the core of the Manchester Triage System.
    
    Paper Context: "The system consists of around 50 flowcharts with standard 
    definitions designed to categorize patients arriving to an emergency room 
    based on their level of urgency."
    
    This protocol allows different implementations of flowchart loading to be used,
    supporting the paper's goal of creating a flexible and maintainable triage system.
    """
    
    def load_flowcharts(self) -> Dict[str, Dict[str, Any]]:
        """Load flowchart configurations from source
        
        Returns:
            Dictionary mapping flowchart IDs to their configuration data
            
        Reference: FMTS paper emphasizes the need for systematic management
        of the numerous flowcharts that define triage logic. This method
        provides the interface for loading these critical configurations.
        
        Expected format matches the paper's flowchart structure with:
        - symptoms: List of symptoms to evaluate
        - linguistic_values: Standard linguistic terms (none, mild, moderate, severe, very_severe)
        - category: Medical category for organization
        """
        ...