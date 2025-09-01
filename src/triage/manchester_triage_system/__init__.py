"""FMTS - Complete Implementation of Research Paper
Based on: "FMTS: A fuzzy implementation of the Manchester triage system" (2014)
Authors: Matthew Cremeens, Elham S. Khorasani
University of Illinois at Springfield

Paper Reference: https://www.researchgate.net/publication/286737453_FMTS_A_fuzzy_implementation_of_the_Manchester_triage_system

This package includes all major components described in the FMTS paper:

1. FUZZY MANCHESTER TRIAGE SYSTEM (Section II)
   - Complete 49+ MTS flowcharts as specified in paper
   - Five-point triage scale: RED, ORANGE, YELLOW, GREEN, BLUE
   - Comprehensive fuzzy rules based on actual MTS logic
   - Linguistic variables: none, mild, moderate, severe, very_severe

2. Z-MOUSE AND FUZZY MARK INTERFACE (Section I)
   - Visual means for fuzzy data entry in knowledge acquisition
   - Medical expert configuration of linguistic terms
   - Fuzzy mark creation and management

3. KNOWLEDGE ACQUISITION COMPONENT (Section I)
   - Medical expert session management
   - Dynamic fuzzy rule configuration
   - Linguistic term meaning configuration
   - Expert rule maintenance capabilities

4. DUAL USER INTERFACES (Paper Abstract)
   - Decision aid system for ER nurses (triage function)
   - Knowledge acquisition component for medical experts

Implementation Status: ✅ COMPLETE - All major FMTS paper components implemented
"""

# Import all main classes for easy access
from .manchester_triage_system import ManchesterTriageSystem
from .zmouse_interface import ZMouseFuzzyInterface
from .knowledge_acquisition import KnowledgeAcquisitionSystem

# Package metadata
__version__ = "1.0.0"
__author__ = "Implementation based on Cremeens & Khorasani (2014)"
__email__ = "research@fmts-implementation.org"
__description__ = "Complete FMTS implementation following the research paper"

# Export main classes
__all__ = [
    'ManchesterTriageSystem',
    'ZMouseFuzzyInterface', 
    'KnowledgeAcquisitionSystem'
]

# Convenience function for quick setup
def create_fmts_system():
    """Create a complete FMTS system with all components
    
    Returns:
        ManchesterTriageSystem: Fully configured FMTS system ready for use
    """
    return ManchesterTriageSystem()

# Paper reference information
PAPER_INFO = {
    'title': 'FMTS: A fuzzy implementation of the Manchester triage system',
    'authors': ['Matthew Cremeens', 'Elham S. Khorasani'],
    'year': 2014,
    'institution': 'University of Illinois at Springfield',
    'url': 'https://www.researchgate.net/publication/286737453_FMTS_A_fuzzy_implementation_of_the_Manchester_triage_system'
}

# System capabilities
CAPABILITIES = {
    'flowcharts': '49+ MTS flowcharts implemented',
    'triage_categories': ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE'],
    'linguistic_terms': ['none', 'mild', 'moderate', 'severe', 'very_severe'],
    'interfaces': ['Decision Aid (Nurses)', 'Knowledge Acquisition (Experts)'],
    'features': [
        'Fuzzy inference system',
        'Z-mouse interface',
        'Fuzzy mark creation',
        'Expert rule configuration',
        'Dynamic system updates'
    ]
}