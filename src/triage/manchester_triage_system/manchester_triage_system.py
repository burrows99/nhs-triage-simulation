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

# Import telemetry service from the new location
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from services.telemetry_service import TelemetryService


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
                 rules_manager: FuzzyRulesManager = None,
                 telemetry_service: TelemetryService = None):
        """Initialize MTS with dependency injection
        
        Args:
            flowchart_manager: Manages flowchart configurations
            fuzzy_manager: Manages fuzzy system configuration
            rules_manager: Manages fuzzy rules
            telemetry_service: Required telemetry service for logging steps
            
        Raises:
            ValueError: If telemetry_service is None
        """
        # Validate required telemetry service
        if telemetry_service is None:
            raise ValueError("TelemetryService is required for Manchester Triage System initialization")
        
        # Use dependency injection with default implementations
        self._flowchart_manager = flowchart_manager or FlowchartConfigManager()
        self._fuzzy_manager = fuzzy_manager or FuzzySystemConfigManager()
        self._rules_manager = rules_manager or FuzzyRulesManager()
        self._telemetry_service = telemetry_service
        
        # Initialize the triage processor
        self._triage_processor = TriageProcessor(
            self._flowchart_manager,
            self._fuzzy_manager,
            self._rules_manager
        )
        
        # Log system initialization
        self._telemetry_service.add_step(
            step_name="mts_initialization",
            step_type="initialization",
            data={
                "flowcharts_loaded": len(self._flowchart_manager.load_flowcharts()),
                "system_ready": True
            }
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
            patient_id: Optional patient identifier for telemetry tracking
            
        Returns:
            Dict containing triage result with category, wait time, etc.
        """
        # Generate patient ID if not provided
        if patient_id is None:
            raise ValueError("patient_id is required for triage processing")
        
        # Start telemetry session
        self._telemetry_service.start_patient_session(patient_id, flowchart_reason)
        self._telemetry_service.start_step_timer()
        
        # Log input validation
        self._telemetry_service.add_step(
            step_name="input_validation",
            step_type="processing",
            data={
                "flowchart_reason": flowchart_reason,
                "symptoms_count": len(symptoms_input),
                "symptoms": symptoms_input
            }
        )
        
        # Log flowchart lookup
        self._telemetry_service.start_step_timer()
        self._telemetry_service.add_step(
            step_name="flowchart_lookup",
            step_type="processing",
            data={
                "flowchart_reason": flowchart_reason,
                "available_flowcharts": len(self.get_available_flowcharts())
            }
        )
        
        # Start timing for triage processing
        self._telemetry_service.start_step_timer()
        
        # Perform the actual triage
        result = self._triage_processor.process_triage(flowchart_reason, symptoms_input)
        
        # Log triage processing completion
        self._telemetry_service.add_step(
            step_name="triage_processing",
            step_type="processing",
            data={
                "fuzzy_score": result.get('fuzzy_score', 0),
                "triage_category": result.get('triage_category', 'UNKNOWN'),
                "wait_time": result.get('wait_time', 0)
            }
        )
        
        # End patient session
        self._telemetry_service.end_patient_session(result)
        
        return result
    
    def get_available_flowcharts(self) -> List[str]:
        """Get list of available flowcharts
        
        Reference: FMTS paper mentions "around 50 flowcharts" in the system
        """
        return self._triage_processor.get_available_flowcharts()
    
    def get_telemetry_service(self) -> TelemetryService:
        """Get the telemetry service instance
        
        Returns:
            The telemetry service if available, None otherwise
        """
        return self._telemetry_service
    
    def get_symptoms_for_flowchart(self, flowchart_reason: str) -> List[str]:
        """Get symptoms for a specific flowchart
        
        Args:
            flowchart_reason: Flowchart ID (e.g., 'chest_pain')
            
        Returns:
            List of symptoms for the specified flowchart
        """
        return self._triage_processor.get_symptoms_for_flowchart(flowchart_reason)
    
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
    
    # Deprecated methods for backward compatibility
    def setup_mts_flowcharts(self):
        """DEPRECATED: Flowcharts are now managed by FlowchartConfigManager
        
        This method is kept for backward compatibility but does nothing.
        The flowcharts are automatically loaded during initialization.
        """
        import warnings
        warnings.warn(
            "setup_mts_flowcharts() is deprecated. Flowcharts are now managed automatically.",
            DeprecationWarning,
            stacklevel=2
        )
        # Do nothing - flowcharts are managed by the config manager
        pass
    
    def setup_fuzzy_system(self):
        """DEPRECATED: Fuzzy system is now managed by FuzzySystemConfigManager
        
        This method is kept for backward compatibility but does nothing.
        The fuzzy system is automatically configured during initialization.
        """
        import warnings
        warnings.warn(
            "setup_fuzzy_system() is deprecated. Fuzzy system is now managed automatically.",
            DeprecationWarning,
            stacklevel=2
        )
        # Do nothing - fuzzy system is managed by the config manager
        pass
    
    def create_fuzzy_rules(self):
        """DEPRECATED: Fuzzy rules are now managed by FuzzyRulesManager
        
        This method is kept for backward compatibility but does nothing.
        The fuzzy rules are automatically created during initialization.
        """
        import warnings
        warnings.warn(
            "create_fuzzy_rules() is deprecated. Fuzzy rules are now managed automatically.",
            DeprecationWarning,
            stacklevel=2
        )
        # Do nothing - rules are managed by the rules manager
        pass