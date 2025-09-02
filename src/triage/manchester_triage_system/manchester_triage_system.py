"""Manchester Triage System - Refactored with SOLID Principles

Reference: FMTS paper Section II - "Manchester Triage System is an algorithmic 
standard designed to aid the triage nurse in choosing an appropriate triage 
category using a five-point scale."

This module has been refactored to follow SOLID principles:
- Single Responsibility: Each class has one clear purpose
- Open/Closed: Extensible without modification
- Liskov Substitution: Proper inheritance hierarchies
- Interface Segregation: Focused interfaces
- Dependency Inversion: Depends on abstractions

Paper Quote: "The system consists of around 50 flowcharts with standard 
definitions designed to categorize patients arriving to an emergency room 
based on their level of urgency."
"""

from typing import Dict, List, Any, Optional
from .config import FlowchartConfigManager, FuzzySystemConfigManager
from .rules import FuzzyRulesManager
from .core import TriageProcessor

# Import centralized logger
from src.logger import logger


class ManchesterTriageSystem:
    """Fuzzy Manchester Triage System - SOLID Compliant Implementation
    
    Reference: FMTS paper Section II - "Manchester Triage System is an algorithmic 
    standard designed to aid the triage nurse in choosing an appropriate triage 
    category using a five-point scale."
    
    This class now follows SOLID principles:
    - Single Responsibility: Only coordinates triage operations
    - Open/Closed: Extensible through dependency injection
    - Dependency Inversion: Depends on abstractions, not concretions
    
    Paper Quote: "The system consists of around 50 flowcharts with standard 
    definitions designed to categorize patients arriving to an emergency room 
    based on their level of urgency."
    """
    
    def __init__(self, 
                 flowchart_manager: FlowchartConfigManager = None,
                 fuzzy_manager: FuzzySystemConfigManager = None,
                 rules_manager: FuzzyRulesManager = None):
        """Initialize MTS with dependency injection
        
        Args:
            flowchart_manager: Manages flowchart configurations
            fuzzy_manager: Manages fuzzy system configuration
            rules_manager: Manages fuzzy rules
        """
        # Use dependency injection with default implementations
        self._flowchart_manager = flowchart_manager or FlowchartConfigManager()
        self._fuzzy_manager = fuzzy_manager or FuzzySystemConfigManager()
        self._rules_manager = rules_manager or FuzzyRulesManager()
        
        # Initialize the triage processor
        self._triage_processor = TriageProcessor(
            self._flowchart_manager,
            self._fuzzy_manager,
            self._rules_manager
        )
        
        # Maintain backward compatibility
        self.flowcharts = self._flowchart_manager.load_flowcharts()
        self.fuzzy_rules = self._get_fuzzy_rules_for_compatibility()
    
    def _get_fuzzy_rules_for_compatibility(self) -> List[Any]:
        """Get fuzzy rules for backward compatibility"""
        # Create dummy rules list for compatibility
        # The actual rules are managed internally by the processor
        input_vars = self._fuzzy_manager.create_input_variables()
        output_var = self._fuzzy_manager.create_output_variable()
        return self._rules_manager.create_rules(input_vars, output_var)
    
    def triage_patient(self, flowchart_reason: str, symptoms_input: Dict[str, str], patient_id: str = None) -> Dict[str, Any]:
        """Perform FMTS triage using SOLID-compliant architecture
        
        Reference: FMTS paper describes "decision aid system for the ER nurses 
        to properly categorize patients based on their symptoms"
        
        Args:
            flowchart_reason: One of the 49+ reasons (e.g., 'chest_pain')
            symptoms_input: Dict of symptom_name -> linguistic_value
            patient_id: Optional patient identifier (not used in current implementation)
            
        Returns:
            Dict containing triage result with category, wait time, etc.
        """
        # MOCK DELAY: Adding 5-second delay to test SimPy disruption
        import time
        logger.debug(f"[MOCK DELAY] Starting 5-second delay for triage processing...")
        # time.sleep(5)  # This will block the entire simulation!
        logger.debug(f"[MOCK DELAY] Delay complete, proceeding with triage...")
        
        # Perform the actual triage
        result = self._triage_processor.process_triage(flowchart_reason, symptoms_input)
        
        return result
    
    def get_available_flowcharts(self) -> List[str]:
        """Get list of available flowcharts
        
        Reference: FMTS paper mentions "around 50 flowcharts" in the system
        """
        return self._flowchart_manager.get_available_flowcharts()
    

    
    def get_symptoms_for_flowchart(self, flowchart_reason: str) -> List[str]:
        """Get symptoms for a specific flowchart
        
        Args:
            flowchart_reason: Flowchart ID (e.g., 'chest_pain')
            
        Returns:
            List of symptoms for the specified flowchart
        """
        return self._flowchart_manager.get_symptoms_for_flowchart(flowchart_reason)
    
    def convert_linguistic_to_numeric(self, linguistic_value: str) -> float:
        """Convert linguistic values to numeric representation
        
        Reference: FMTS paper Section II discusses the need to convert imprecise 
        linguistic terms to numeric values for fuzzy processing.
        
        Args:
            linguistic_value: Linguistic term (e.g., 'severe')
            
        Returns:
            Numeric representation of the linguistic value
        """
        converter = self._fuzzy_manager.get_linguistic_converter()
        return converter.convert_to_numeric(linguistic_value)
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for compatibility with simulation framework.
        
        Returns:
            Dict containing system information
        """
        return {
            'system_name': 'Manchester Triage System',
            'type': 'manchester',
            'status': 'active',
            'flowcharts_available': len(self.get_available_flowcharts()),
            'version': '1.0'
        }
    
    def validate_connection(self) -> bool:
        """Validate system connection/readiness.
        
        Returns:
            bool: True if system is ready, False otherwise
        """
        try:
            # Check if core components are initialized
            if (self._triage_processor is not None and 
                self._flowchart_manager is not None and 
                self._fuzzy_manager is not None):
                return True
            return False
        except Exception as e:
            logger.error(f"Manchester Triage System validation failed: {e}")
            return False