"""Flowchart Configuration Manager

This module manages flowchart configurations with SOLID principles, providing
validation, access, and organization capabilities for the FMTS system.

Reference: FMTS paper by Cremeens & Khorasani (2014)
https://www.researchgate.net/publication/286737453_FMTS_A_fuzzy_implementation_of_the_Manchester_triage_system

Paper Quote: "For a triage nurse with 50 flowcharts in her hand, trying to correctly 
prioritize a patient is a clumsy process."

This manager addresses the paper's concern by providing systematic flowchart management
that eliminates the clumsiness of manual flowchart handling.
"""

import pandas as pd
from typing import Dict, List, Any
from .default_flowchart_config import DefaultFlowchartConfig


class FlowchartConfigManager:
    """Manages flowchart configurations with SOLID principles
    
    Single Responsibility: Only manages flowchart configurations
    Open/Closed: Can be extended with new configuration sources
    
    Reference: FMTS paper emphasizes the need for systematic management of the
    numerous flowcharts that define the Manchester Triage System.
    
    Paper Context: "The evaluation is typically performed by a triage nurse who 
    collects patient information and relies on her memory of guidelines and 
    subjective assessment to assign an urgency level to patients."
    
    This manager eliminates reliance on memory by providing systematic access
    to all flowchart configurations, supporting the paper's goal of objective
    triage assessment.
    """
    
    def __init__(self):
        """Initialize with default flowchart configuration"""
        self._config_source = DefaultFlowchartConfig()
        self._flowcharts_df = None
        self._flowcharts_dict = None
    
    def load_flowcharts(self) -> pd.DataFrame:
        """Load flowcharts into pandas DataFrame for efficient access
        
        Reference: FMTS paper Section II describes the systematic approach needed
        to manage the ~50 flowcharts that form the core of the triage system.
        
        Paper Quote: "The system consists of around 50 flowcharts with standard 
        definitions designed to categorize patients arriving to an emergency room 
        based on their level of urgency."
        
        This method provides efficient access to all flowcharts, eliminating the
        "clumsy process" mentioned in the paper.
        
        Returns:
            pandas DataFrame containing all flowchart configurations
        """
        if self._flowcharts_df is None:
            if hasattr(self._config_source, 'get_all_flowcharts'):
                flowcharts_data = self._config_source.get_all_flowcharts()
            else:
                flowcharts_data = self._config_source.load_flowcharts()
            
            self._flowcharts_dict = flowcharts_data
            
            # Convert to DataFrame for pandas operations as per paper's systematic approach
            flowchart_records = [
                {
                    'flowchart_id': flowchart_id,
                    'symptoms': config['symptoms'],
                    'linguistic_values': config['linguistic_values'],
                    'category': config.get('category', 'general'),
                    'paper_reference': config.get('paper_reference', 'FMTS paper implementation')
                }
                for flowchart_id, config in flowcharts_data.items()
            ]
            
            self._flowcharts_df = pd.DataFrame(flowchart_records)
        
        return self._flowcharts_df
    
    def get_flowchart(self, flowchart_id: str) -> Dict[str, Any]:
        """Get specific flowchart configuration
        
        Reference: FMTS paper emphasizes the need for quick access to specific
        flowcharts during triage assessment.
        
        Paper Context: Addresses the paper's concern about nurses having to
        manually search through "50 flowcharts in her hand" by providing
        direct programmatic access.
        
        Args:
            flowchart_id: Unique identifier for the flowchart
            
        Returns:
            Dictionary containing flowchart configuration or None if not found
        """
        if self._flowcharts_dict is None:
            self.load_flowcharts()
        
        return self._flowcharts_dict.get(flowchart_id)
    
    def get_flowcharts_by_category(self, category: str) -> Dict[str, Dict[str, Any]]:
        """Get flowcharts filtered by category
        
        Reference: FMTS paper's systematic approach to organizing medical presentations
        by category (respiratory, cardiovascular, neurological, etc.).
        
        This method supports the paper's organized approach to triage by allowing
        category-based flowchart access.
        
        Args:
            category: Medical category (e.g., 'respiratory', 'cardiovascular')
            
        Returns:
            Dictionary of flowcharts in the specified category
        """
        if self._flowcharts_dict is None:
            self.load_flowcharts()
        
        return {
            flowchart_id: config
            for flowchart_id, config in self._flowcharts_dict.items()
            if config.get('category') == category
        }
    
    def get_available_flowcharts(self) -> List[str]:
        """Get list of available flowchart IDs
        
        Reference: FMTS paper mentions the comprehensive nature of the system
        with "around 50 flowcharts" available for triage assessment.
        
        This method provides the complete list supporting the paper's goal
        of comprehensive triage coverage.
        
        Returns:
            List of all available flowchart identifiers
        """
        df = self.load_flowcharts()
        return df['flowchart_id'].tolist()
    
    def get_symptoms_for_flowchart(self, flowchart_id: str) -> List[str]:
        """Get symptoms for a specific flowchart
        
        Reference: FMTS paper emphasizes the importance of systematic symptom
        evaluation as part of the objective triage process.
        
        Paper Context: Supports the paper's goal of eliminating subjective
        assessment by providing structured access to symptom lists.
        
        Args:
            flowchart_id: Unique identifier for the flowchart
            
        Returns:
            List of symptoms associated with the flowchart
        """
        flowchart = self.get_flowchart(flowchart_id)
        return flowchart['symptoms'] if flowchart else []
    
    def validate_flowchart(self, flowchart_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate flowchart configuration
        
        Reference: FMTS paper emphasizes the importance of systematic validation
        to ensure the objective nature of the triage system.
        
        Paper Context: "Hence, an objective triage system is needed that can correctly 
        model the meaning of imprecise terms in the MTS and assign an appropriate 
        waiting time to patients."
        
        Validation ensures flowcharts meet the paper's requirements for objective
        triage assessment.
        
        Args:
            flowchart_config: Flowchart configuration to validate
            
        Returns:
            Dictionary containing validation results with errors and warnings
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'paper_compliance': True
        }
        
        # Check required fields as per paper's systematic approach
        required_fields = ['symptoms', 'linguistic_values']
        for field in required_fields:
            if field not in flowchart_config:
                validation_result['valid'] = False
                validation_result['paper_compliance'] = False
                validation_result['errors'].append(
                    f"Missing required field: {field}. FMTS paper requires systematic symptom definition."
                )
        
        # Validate symptoms
        if 'symptoms' in flowchart_config:
            symptoms = flowchart_config['symptoms']
            if not isinstance(symptoms, list) or len(symptoms) == 0:
                validation_result['valid'] = False
                validation_result['paper_compliance'] = False
                validation_result['errors'].append(
                    "Symptoms must be a non-empty list. Paper requires systematic symptom evaluation."
                )
            elif len(symptoms) > 5:
                validation_result['warnings'].append(
                    f"More than 5 symptoms ({len(symptoms)}) may affect fuzzy processing efficiency. "
                    f"Consider grouping related symptoms for better FMTS performance."
                )
        
        # Validate linguistic values against paper's standard terms
        if 'linguistic_values' in flowchart_config:
            linguistic_values = flowchart_config['linguistic_values']
            expected_values = ['none', 'mild', 'moderate', 'severe', 'very_severe']
            if linguistic_values != expected_values:
                validation_result['paper_compliance'] = False
                validation_result['warnings'].append(
                    f"Non-standard linguistic values detected. FMTS paper uses: {expected_values}. "
                    f"Current values: {linguistic_values}"
                )
        
        # Check for paper reference
        if 'paper_reference' not in flowchart_config:
            validation_result['warnings'].append(
                "Missing paper reference. Consider adding reference to FMTS paper implementation."
            )
        
        return validation_result
    
    def get_flowchart_statistics(self) -> Dict[str, Any]:
        """Get statistics about the flowchart collection
        
        Reference: FMTS paper mentions "around 50 flowcharts" - this method
        provides statistics to verify compliance with paper requirements.
        
        Returns:
            Dictionary containing comprehensive flowchart statistics
        """
        df = self.load_flowcharts()
        
        # Category distribution
        category_counts = df['category'].value_counts().to_dict()
        
        # Symptom analysis
        all_symptoms = []
        for symptoms_list in df['symptoms']:
            all_symptoms.extend(symptoms_list)
        
        unique_symptoms = len(set(all_symptoms))
        avg_symptoms_per_flowchart = len(all_symptoms) / len(df)
        
        return {
            'total_flowcharts': len(df),
            'paper_target': '~50 flowcharts',
            'paper_compliance': len(df) >= 45,  # Allow some flexibility around "around 50"
            'categories': category_counts,
            'unique_categories': len(category_counts),
            'symptom_analysis': {
                'total_symptoms': len(all_symptoms),
                'unique_symptoms': unique_symptoms,
                'avg_symptoms_per_flowchart': round(avg_symptoms_per_flowchart, 2)
            },
            'paper_reference': {
                'title': 'FMTS: A fuzzy implementation of the Manchester triage system',
                'authors': ['Matthew Cremeens', 'Elham S. Khorasani'],
                'year': 2014,
                'url': 'https://www.researchgate.net/publication/286737453_FMTS_A_fuzzy_implementation_of_the_Manchester_triage_system'
            }
        }
    
    def get_paper_compliance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive paper compliance report
        
        Reference: FMTS paper by Cremeens & Khorasani (2014)
        
        Returns:
            Detailed report on how well the flowcharts implement the paper's requirements
        """
        stats = self.get_flowchart_statistics()
        df = self.load_flowcharts()
        
        # Analyze paper compliance
        compliance_issues = []
        if stats['total_flowcharts'] < 45:
            compliance_issues.append(
                f"Flowchart count ({stats['total_flowcharts']}) below paper's ~50 target"
            )
        
        # Check linguistic values compliance
        non_compliant_flowcharts = 0
        for _, row in df.iterrows():
            expected_values = ['none', 'mild', 'moderate', 'severe', 'very_severe']
            if row['linguistic_values'] != expected_values:
                non_compliant_flowcharts += 1
        
        if non_compliant_flowcharts > 0:
            compliance_issues.append(
                f"{non_compliant_flowcharts} flowcharts use non-standard linguistic values"
            )
        
        return {
            'paper_reference': stats['paper_reference'],
            'compliance_summary': {
                'overall_compliance': len(compliance_issues) == 0,
                'flowchart_count_compliance': stats['paper_compliance'],
                'linguistic_values_compliance': non_compliant_flowcharts == 0,
                'systematic_organization': len(stats['categories']) >= 5
            },
            'detailed_statistics': stats,
            'compliance_issues': compliance_issues,
            'recommendations': self._generate_compliance_recommendations(stats, compliance_issues)
        }
    
    def _generate_compliance_recommendations(self, stats: Dict[str, Any], issues: List[str]) -> List[str]:
        """Generate recommendations for improving paper compliance
        
        Args:
            stats: Flowchart statistics
            issues: List of compliance issues
            
        Returns:
            List of recommendations for better FMTS paper compliance
        """
        recommendations = []
        
        if stats['total_flowcharts'] < 45:
            recommendations.append(
                "Add more flowcharts to reach the paper's target of ~50 flowcharts "
                "for comprehensive emergency department coverage."
            )
        
        if len(stats['categories']) < 5:
            recommendations.append(
                "Expand flowchart categories to cover more medical specialties "
                "as implied by the paper's comprehensive approach."
            )
        
        if stats['symptom_analysis']['avg_symptoms_per_flowchart'] < 3:
            recommendations.append(
                "Consider adding more symptoms per flowchart to improve "
                "the granularity of triage assessment as per paper's detailed approach."
            )
        
        if not issues:
            recommendations.append(
                "Flowchart collection demonstrates good compliance with FMTS paper requirements. "
                "Continue monitoring for consistency with paper's systematic triage goals."
            )
        
        return recommendations