from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import numpy as np
from .models import Patient
from .constants import TRIAGE_LEVELS, TRIAGE_WEIGHTS, MRI_NEED_PROB, ULTRASOUND_NEED_PROB
from .mts import MTSTriageSystem


@dataclass
class PatientConfiguration:
    """
    Configuration class that manages all patient-related constants and probabilities.
    Follows Single Responsibility Principle by centralizing patient configuration.
    """
    triage_levels: List[str] = field(default_factory=lambda: TRIAGE_LEVELS.copy())
    triage_weights: List[float] = field(default_factory=lambda: TRIAGE_WEIGHTS.copy())
    mri_need_probability: float = MRI_NEED_PROB
    ultrasound_need_probability: float = ULTRASOUND_NEED_PROB
    
    def __post_init__(self):
        # Validate configuration on initialization
        self.validate_configuration()
    
    def validate_configuration(self) -> bool:
        """
        Validates that the configuration is consistent and valid.
        """
        if len(self.triage_levels) != len(self.triage_weights):
            raise ValueError("Triage levels and weights must have the same length")
        
        if not np.isclose(sum(self.triage_weights), 1.0):
            raise ValueError("Triage weights must sum to 1.0")
        
        if not (0 <= self.mri_need_probability <= 1):
            raise ValueError("MRI need probability must be between 0 and 1")
        
        if not (0 <= self.ultrasound_need_probability <= 1):
            raise ValueError("Ultrasound need probability must be between 0 and 1")
        
        return True


class PatientAttributeGenerator:
    """
    Handles random attribute generation for patients.
    Follows Single Responsibility Principle by focusing only on attribute generation.
    """
    
    def __init__(self, config: PatientConfiguration):
        self.config = config
        self.config.validate_configuration()
    
    def generate_triage_level(self, patient_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates triage level using MTS logic if patient data is provided,
        otherwise falls back to random choice based on configured weights.
        
        Args:
            patient_data: Optional patient clinical data for MTS triage assignment
        
        Returns:
            str: Triage level ('red', 'orange', 'yellow', 'green', 'blue')
        """
        if patient_data:
            # Use centralized MTS triage logic
            return MTSTriageSystem.assign_triage_level(patient_data)
        else:
            # Fallback to random choice for simulation purposes
            return np.random.choice(self.config.triage_levels, p=self.config.triage_weights)
    
    def needs_mri(self, triage_level: str) -> bool:
        """
        Determines if a patient needs MRI based on triage level and probability.
        Currently only red triage patients can need MRI.
        """
        if triage_level == 'red':
            return np.random.random() < self.config.mri_need_probability
        return False
    
    def needs_ultrasound(self, triage_level: Optional[str] = None) -> bool:
        """
        Determines if a patient needs ultrasound.
        Currently independent of triage level.
        """
        return np.random.random() < self.config.ultrasound_need_probability
    
    def generate_all_attributes(self) -> Dict[str, Any]:
        """
        Generates all patient attributes in one call.
        Returns a dictionary with all generated attributes.
        """
        triage = self.generate_triage_level()
        return {
            'triage': triage,
            'needs_mri': self.needs_mri(triage),
            'needs_ultrasound': self.needs_ultrasound(triage)
        }


class PatientFactory:
    """
    Factory class for creating Patient objects.
    Follows Factory Pattern and Single Responsibility Principle.
    """
    
    def __init__(self, config: Optional[PatientConfiguration] = None):
        if config is None:
            config = PatientConfiguration()
        self.attribute_generator = PatientAttributeGenerator(config)
        self._next_patient_id = 0
    
    def create_patient(self, patient_id: Optional[int] = None, patient_data: Optional[Dict[str, Any]] = None) -> Patient:
        """
        Creates a new patient with randomly generated attributes.
        
        Args:
            patient_id: Optional patient ID
            patient_data: Optional clinical data for MTS-based triage assignment
        """
        if patient_id is None:
            patient_id = self._next_patient_id
            self._next_patient_id += 1
        
        triage = self.attribute_generator.generate_triage_level(patient_data)
        
        return Patient(
            pid=patient_id,
            triage=triage,
            needs_mri=self.attribute_generator.needs_mri(triage),
            needs_ultrasound=self.attribute_generator.needs_ultrasound()
        )
    
    def create_patient_with_attributes(self, patient_id: int, **kwargs: Any) -> Patient:
        """
        Creates a patient with specific attributes (useful for testing).
        """
        # Generate defaults first
        attributes = self.attribute_generator.generate_all_attributes()
        
        # Override with provided attributes
        attributes.update(kwargs)
        
        return Patient(
            pid=patient_id,
            triage=attributes.get('triage', 'green'),  # Default triage if not provided
            needs_mri=attributes.get('needs_mri', False),
            needs_ultrasound=attributes.get('needs_ultrasound', False)
        )
    
    def reset_patient_id_counter(self):
        """
        Resets the internal patient ID counter (useful for testing).
        """
        self._next_patient_id = 0