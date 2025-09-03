"""FMTS Paper References Utility

Centralized repository for all FMTS paper references to eliminate duplication
across the Manchester Triage System implementation.

Reference: FMTS: A fuzzy implementation of the Manchester triage system
Authors: Matthew Cremeens, Elham S. Khorasani
Year: 2014
Institution: University of Illinois at Springfield
URL: https://www.researchgate.net/publication/286737453_FMTS_A_fuzzy_implementation_of_the_Manchester_triage_system
"""

from typing import Dict, Any


class FMTSPaperReferences:
    """Centralized FMTS paper references and citations.
    
    Eliminates duplication of paper quotes and references across the codebase.
    """
    
    # Paper Information
    PAPER_TITLE = "FMTS: A fuzzy implementation of the Manchester triage system"
    AUTHORS = ["Matthew Cremeens", "Elham S. Khorasani"]
    YEAR = 2014
    INSTITUTION = "University of Illinois at Springfield"
    URL = "https://www.researchgate.net/publication/286737453_FMTS_A_fuzzy_implementation_of_the_Manchester_triage_system"
    
    # Core System Definitions
    MTS_DEFINITION = (
        "Manchester Triage System is an algorithmic standard designed to aid the triage nurse "
        "in choosing an appropriate triage category using a five-point scale."
    )
    
    FLOWCHART_COUNT = (
        "The system consists of around 50 flowcharts with standard definitions designed to "
        "categorize patients arriving to an emergency room based on their level of urgency."
    )
    
    OBJECTIVE_TRIAGE_NEED = (
        "Hence, an objective triage system is needed that can correctly model the meaning of "
        "imprecise terms in the MTS and assign an appropriate waiting time to patients."
    )
    
    # Problem Statement
    SUBJECTIVE_ASSESSMENT_PROBLEM = (
        "The evaluation is typically performed by a triage nurse who collects patient information "
        "and relies on her memory of guidelines and subjective assessment to assign an urgency level to patients."
    )
    
    NURSE_DISAGREEMENT_PROBLEM = (
        "this might result in two nurses coming to different conclusions about the urgency of a "
        "patient's condition even if the same flowcharts are being used."
    )
    
    IMPRECISE_TERMS_PROBLEM = (
        "MTS flowcharts are full of imprecise linguistic terms such as very low PEFR, exhaustion, "
        "significant respiratory history, urgent, etc."
    )
    
    # Solution Approach
    DECISION_AID_SYSTEM = (
        "decision aid system for the ER nurses to properly categorize patients based on their symptoms"
    )
    
    FUZZY_SYSTEM_DESCRIPTION = (
        "The paper develops a Fuzzy Manchester Triage System (FMTS). FMTS is a dynamic fuzzy "
        "inference system which implements the flowcharts designed by the Manchester Triage Group."
    )
    
    # User Interfaces
    DUAL_INTERFACES = (
        "FMTS provides two user interfaces: one is a decision aid system for the ER nurses to "
        "properly categorize patients based on their symptoms"
    )
    
    KNOWLEDGE_ACQUISITION = (
        "knowledge acquisition component for medical experts to configure the system and maintain "
        "the fuzzy rules"
    )
    
    # Z-Mouse Interface
    ZMOUSE_CONCEPT = (
        "The concept of Z-mouse and fuzzy mark are introduced as easy-to-use visual means for "
        "fuzzy data entry in knowledge acquisition"
    )
    
    # Triage Categories and Wait Times
    WAIT_TIME_QUESTION = (
        "What does the categorization of a patient mean for her waiting time to be treated?"
    )
    
    CRISP_OUTPUT_NEED = (
        "A crisp output is needed if we want to distinguish precisely between these two types of patients."
    )
    
    # Clinical Scenarios
    CLINICAL_SCENARIO_EXAMPLE = (
        "If two children are in triage for shortness of breath and one has what would be considered "
        "very low oxygenation (SaO2) and the other has acute onset after injury, which should be seen first?"
    )
    
    # System Validation
    SYSTEMATIC_VALIDATION_NEED = (
        "systematic validation to ensure the objective nature of the triage system"
    )
    
    # Removed unused get_paper_info method
    
    @classmethod
    def get_reference_comment(cls, section: str, quote: str) -> str:
        """Generate standardized reference comment.
        
        Args:
            section: Paper section (e.g., "Section II")
            quote: Quote from the paper
            
        Returns:
            Formatted reference comment
        """
        return f"Reference: FMTS paper {section} - \"{quote}\""
    
    @classmethod
    def get_context_comment(cls, context: str) -> str:
        """Generate standardized paper context comment.
        
        Args:
            context: Context explanation
            
        Returns:
            Formatted context comment
        """
        return f"Paper Context: {context}"
    
    # Removed unused get_bibtex_citation method