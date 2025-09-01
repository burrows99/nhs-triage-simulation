"""Z-mouse and Fuzzy Mark Interface for Knowledge Acquisition

Reference: FMTS paper Section I states "The concept of Z-mouse and fuzzy mark 
is used to provide an easy-to-use visual means for fuzzy data entry in the 
knowledge acquisition component."

This interface allows medical experts to configure the meaning of linguistic 
terms and maintain fuzzy rules as described in the paper.
"""

import pandas as pd
from typing import Dict, List, Any


class ZMouseFuzzyInterface:
    """Z-mouse and Fuzzy Mark Interface for Knowledge Acquisition
    
    Reference: FMTS paper Section I states "The concept of Z-mouse and fuzzy mark 
    is used to provide an easy-to-use visual means for fuzzy data entry in the 
    knowledge acquisition component."
    
    This interface allows medical experts to configure the meaning of linguistic 
    terms and maintain fuzzy rules as described in the paper.
    """
    
    def __init__(self):
        self.linguistic_terms = ['none', 'mild', 'moderate', 'severe', 'very_severe']
        self.fuzzy_marks = {}  # Store fuzzy mark configurations
        self.expert_configurations = {}  # Store expert rule configurations
    
    def create_fuzzy_mark(self, term: str, universe_range: tuple, 
                         membership_points: List[tuple]) -> Dict[str, Any]:
        """Create a fuzzy mark for a linguistic term using Z-mouse concept
        
        Args:
            term: Linguistic term (e.g., 'severe')
            universe_range: (min, max) values for the universe
            membership_points: List of (x, membership_value) points
            
        Reference: Paper Section I - "fuzzy mark" concept for visual fuzzy data entry
        """
        
        fuzzy_mark = {
            'term': term,
            'universe': universe_range,
            'points': membership_points,
            'created_by': 'medical_expert',
            'timestamp': pd.Timestamp.now()
        }
        
        self.fuzzy_marks[term] = fuzzy_mark
        return fuzzy_mark
    
    def z_mouse_input(self, symptom: str, linguistic_value: str, 
                     confidence: float = 1.0) -> Dict[str, Any]:
        """Simulate Z-mouse input for fuzzy data entry
        
        Reference: FMTS paper mentions Z-mouse as "easy-to-use visual means 
        for fuzzy data entry in the knowledge acquisition component"
        
        Args:
            symptom: The symptom being assessed
            linguistic_value: The linguistic assessment (e.g., 'severe')
            confidence: Expert confidence in the assessment (0-1)
        """
        
        z_mouse_data = {
            'symptom': symptom,
            'linguistic_value': linguistic_value,
            'confidence': confidence,
            'fuzzy_membership': self._calculate_fuzzy_membership(linguistic_value, confidence),
            'expert_id': 'medical_expert_001',
            'timestamp': pd.Timestamp.now()
        }
        
        return z_mouse_data
    
    def _calculate_fuzzy_membership(self, linguistic_value: str, confidence: float) -> float:
        """Calculate fuzzy membership based on Z-mouse input"""
        base_values = {
            'none': 0.0,
            'mild': 0.25,
            'moderate': 0.5,
            'severe': 0.75,
            'very_severe': 1.0
        }
        
        base_membership = base_values.get(linguistic_value.lower(), 0.5)
        # Adjust based on expert confidence
        return base_membership * confidence
    
    def configure_linguistic_term(self, term: str, 
                                 membership_function: Dict[str, Any]) -> bool:
        """Allow medical experts to configure linguistic terms
        
        Reference: Paper Section I - medical experts can "configure the meaning 
        of linguistic terms using a fuzzy mouse"
        """
        
        if term not in self.linguistic_terms:
            self.linguistic_terms.append(term)
        
        self.expert_configurations[term] = {
            'membership_function': membership_function,
            'configured_by': 'medical_expert',
            'timestamp': pd.Timestamp.now()
        }
        
        return True
    

    
    def get_linguistic_terms(self) -> List[str]:
        """Get all available linguistic terms"""
        return self.linguistic_terms
    
    def validate_fuzzy_mark(self, fuzzy_mark: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a fuzzy mark configuration
        
        Reference: FMTS paper implies validation of expert inputs
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate required fields
        required_fields = ['term', 'universe', 'points']
        for field in required_fields:
            if field not in fuzzy_mark:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Missing required field: {field}")
        
        # Validate universe range
        if 'universe' in fuzzy_mark:
            universe = fuzzy_mark['universe']
            if not isinstance(universe, tuple) or len(universe) != 2:
                validation_result['valid'] = False
                validation_result['errors'].append("Universe must be a tuple of (min, max)")
            elif universe[0] >= universe[1]:
                validation_result['valid'] = False
                validation_result['errors'].append("Universe min must be less than max")
        
        # Validate membership points
        if 'points' in fuzzy_mark:
            points = fuzzy_mark['points']
            if not isinstance(points, list) or len(points) < 2:
                validation_result['valid'] = False
                validation_result['errors'].append("Points must be a list with at least 2 points")
            else:
                for i, point in enumerate(points):
                    if not isinstance(point, tuple) or len(point) != 2:
                        validation_result['valid'] = False
                        validation_result['errors'].append(f"Point {i} must be a tuple of (x, membership)")
                    elif not (0 <= point[1] <= 1):
                        validation_result['warnings'].append(f"Point {i} membership value {point[1]} outside [0,1] range")
        
        return validation_result