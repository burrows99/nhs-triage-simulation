"""Triage Result Builder

This module builds triage result objects following SOLID principles.

Reference: FMTS paper Section II - "What does the categorization of a patient mean 
for her waiting time to be treated? If two children are in triage for shortness of 
breath and one has what would be considered very low oxygenation (SaO2) and the 
other has acute onset after injury, which should be seen first?"

Paper Context: "A crisp output is needed if we want to distinguish precisely 
between these two types of patients."

This builder addresses the paper's requirement by creating structured triage 
results with clear categorization and precise wait time assignments.

Single Responsibility: Only builds result objects
"""

from typing import Dict, Any
from ..config import TriageCategoryMapper


class TriageResultBuilder:
    """Builds triage result objects
    
    Single Responsibility: Only builds result objects
    """
    
    def __init__(self, category_mapper: TriageCategoryMapper):
        self._category_mapper = category_mapper
    
    def build_result(self, 
                    flowchart_reason: str,
                    fuzzy_score: float,
                    symptom_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build complete triage result"""
        
        # Map fuzzy score to category and wait time
        category_info = self._category_mapper.map_score_to_category(fuzzy_score)
        
        return {
            'flowchart_used': flowchart_reason,
            'triage_category': category_info['category'],
            'wait_time': category_info['wait_time'],
            'fuzzy_score': float(fuzzy_score),
            'symptoms_processed': symptom_data['processed_symptoms'],
            'numeric_inputs': symptom_data['numeric_values'],
            'priority_score': category_info['priority_score']
        }