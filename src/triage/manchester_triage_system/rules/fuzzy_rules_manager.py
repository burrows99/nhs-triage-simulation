"""Fuzzy Rules Manager

This module manages fuzzy rules with SOLID principles, providing validation,
statistics, and caching capabilities for the FMTS system.

Reference: FMTS paper by Cremeens & Khorasani (2014)
https://www.researchgate.net/publication/286737453_FMTS_A_fuzzy_implementation_of_the_Manchester_triage_system

Paper Quote: "FMTS is a dynamic fuzzy inference system which implements the flowcharts 
designed by the Manchester Triage Group."

This manager supports the paper's emphasis on dynamic systems by providing flexible
rule management with validation and performance optimization.
"""

from skfuzzy import control as ctrl
from typing import List, Dict, Any
from .default_fuzzy_rules import DefaultFuzzyRules
from src.triage.triage_constants import FuzzyCategories


class FuzzyRulesManager:
    """Manages fuzzy rules with SOLID principles
    
    Single Responsibility: Only manages fuzzy rules
    Open/Closed: Can be extended with new rule sources
    
    Reference: FMTS paper describes the need for systematic rule management
    to handle the ~50 flowcharts and various triage scenarios.
    
    Paper Quote: "The system consists of around 50 flowcharts with standard 
    definitions designed to categorize patients arriving to an emergency room 
    based on their level of urgency."
    
    This manager ensures all rules are properly validated and organized
    to support the paper's objective triage system.
    """
    
    def __init__(self):
        """Initialize with default fuzzy rules"""
        self._rule_source = DefaultFuzzyRules()
        self._cached_rules = None
    
    def create_rules(self, input_vars: List[ctrl.Antecedent], output_var: ctrl.Consequent) -> List[ctrl.Rule]:
        """Create fuzzy rules for the system
        
        Reference: FMTS paper Section II describes the need for comprehensive fuzzy rules
        that can handle all scenarios in the ~50 MTS flowcharts.
        
        Paper Quote: "Hence, an objective triage system is needed that can correctly model 
        the meaning of imprecise terms in the MTS and assign an appropriate waiting time to patients."
        
        This method creates the objective rule set that addresses the paper's core goal.
        
        Args:
            input_vars: List of fuzzy input variables (symptoms)
            output_var: Fuzzy output variable (triage category)
            
        Returns:
            List of fuzzy rules implementing the FMTS logic
        """
        if self._cached_rules is None:
            self._cached_rules = self._rule_source.get_rules(input_vars, output_var)
            
        return self._cached_rules
    
    def validate_rules(self, rules: List[ctrl.Rule]) -> Dict[str, Any]:
        """Validate fuzzy rules
        
        Reference: FMTS paper emphasizes the importance of systematic validation
        to ensure the objective nature of the triage system.
        
        Paper Context: The paper addresses the problem where "two nurses coming to 
        different conclusions about the urgency of a patient's condition even if the 
        same flowcharts are being used." Validation ensures consistency.
        
        Args:
            rules: List of fuzzy rules to validate
            
        Returns:
            Dictionary containing validation results with errors, warnings, and coverage analysis
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'rule_count': len(rules),
            'categories_covered': set(),
            'paper_compliance': True
        }
        
        # Check if we have rules
        if not rules:
            validation_result['valid'] = False
            validation_result['paper_compliance'] = False
            validation_result['errors'].append("No rules provided - FMTS paper requires comprehensive rule set")
            return validation_result
        
        # Analyze rule coverage for five-point scale as per paper
        # Reference: Paper describes five-point triage scale implementation
        expected_categories = FuzzyCategories.get_category_set()
        
        for rule in rules:
            try:
                # Extract consequent category from rule
                consequent_label = str(rule.consequent).split('[')[1].split(']')[0]
                validation_result['categories_covered'].add(consequent_label)
            except (IndexError, AttributeError):
                validation_result['warnings'].append("Could not parse rule consequent")
        
        # Check coverage against paper's five-point scale
        missing_categories = expected_categories - validation_result['categories_covered']
        if missing_categories:
            validation_result['paper_compliance'] = False
            validation_result['warnings'].append(
                f"Missing rules for FMTS categories: {missing_categories}. "
                f"Paper requires complete five-point scale coverage."
            )
        
        # Check rule count against paper's comprehensive approach
        # Reference: Paper mentions ~50 flowcharts requiring comprehensive rule coverage
        if len(rules) < 5:
            validation_result['warnings'].append(
                "Very few rules - may not provide comprehensive coverage for FMTS paper's "
                "~50 flowcharts and complex triage scenarios"
            )
        elif len(rules) > 25:
            validation_result['warnings'].append(
                "Many rules - may cause performance issues. Consider rule optimization "
                "while maintaining FMTS paper compliance."
            )
        
        # Validate paper compliance
        if validation_result['categories_covered'] == expected_categories:
            validation_result['paper_compliance'] = True
        
        return validation_result
    
    def get_rule_statistics(self, rules: List[ctrl.Rule]) -> Dict[str, Any]:
        """Get statistics about the rule set
        
        Reference: FMTS paper emphasizes the systematic nature of the triage system.
        Statistics help ensure the implementation meets the paper's requirements.
        
        Args:
            rules: List of fuzzy rules to analyze
            
        Returns:
            Dictionary containing rule statistics and paper compliance metrics
        """
        stats = {
            'total_rules': len(rules),
            'categories': {},
            'complexity_score': 0,
            'paper_compliance_score': 0,
            'coverage_analysis': {}
        }
        
        # Count rules per category
        expected_categories = FuzzyCategories.get_all_categories()
        for category in expected_categories:
            stats['categories'][category] = 0
        
        for rule in rules:
            try:
                consequent_label = str(rule.consequent).split('[')[1].split(']')[0]
                if consequent_label in stats['categories']:
                    stats['categories'][consequent_label] += 1
            except (IndexError, AttributeError):
                continue
        
        # Calculate complexity (rough estimate based on rule count and distribution)
        stats['complexity_score'] = len(rules) * 1.5
        
        # Calculate paper compliance score
        # Reference: Paper requires comprehensive coverage of all triage categories
        covered_categories = sum(1 for count in stats['categories'].values() if count > 0)
        stats['paper_compliance_score'] = (covered_categories / len(expected_categories)) * 100
        
        # Coverage analysis
        stats['coverage_analysis'] = {
            'categories_covered': covered_categories,
            'total_categories': len(expected_categories),
            'coverage_percentage': stats['paper_compliance_score'],
            'missing_categories': [cat for cat, count in stats['categories'].items() if count == 0]
        }
        
        return stats
    
    def clear_cache(self):
        """Clear the rules cache to force regeneration
        
        Reference: FMTS paper emphasizes dynamic system capabilities.
        Cache clearing supports dynamic rule updates as mentioned in the paper.
        """
        self._cached_rules = None
    
    def get_paper_compliance_report(self, rules: List[ctrl.Rule]) -> Dict[str, Any]:
        """Generate a comprehensive paper compliance report
        
        Reference: FMTS paper by Cremeens & Khorasani (2014)
        
        Returns:
            Detailed report on how well the rules implement the paper's requirements
        """
        validation = self.validate_rules(rules)
        statistics = self.get_rule_statistics(rules)
        
        return {
            'paper_reference': {
                'title': 'FMTS: A fuzzy implementation of the Manchester triage system',
                'authors': ['Matthew Cremeens', 'Elham S. Khorasani'],
                'year': 2014,
                'url': 'https://www.researchgate.net/publication/286737453_FMTS_A_fuzzy_implementation_of_the_Manchester_triage_system'
            },
            'compliance_summary': {
                'overall_compliance': validation['paper_compliance'],
                'five_point_scale_coverage': statistics['coverage_analysis']['coverage_percentage'],
                'rule_comprehensiveness': 'Adequate' if len(rules) >= 8 else 'Insufficient',
                'objective_system_implementation': validation['valid']
            },
            'paper_requirements_met': {
                'five_point_triage_scale': len(validation['categories_covered']) == 5,
                'objective_categorization': validation['valid'],
                'comprehensive_rule_coverage': len(rules) >= 8,
                'dynamic_system_support': True  # Supported by manager architecture
            },
            'detailed_analysis': {
                'validation_results': validation,
                'statistical_analysis': statistics
            },
            'recommendations': self._generate_compliance_recommendations(validation, statistics)
        }
    
    def _generate_compliance_recommendations(self, validation: Dict[str, Any], statistics: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving paper compliance
        
        Args:
            validation: Validation results
            statistics: Statistical analysis
            
        Returns:
            List of recommendations for better FMTS paper compliance
        """
        recommendations = []
        
        if not validation['paper_compliance']:
            recommendations.append(
                "Implement missing triage categories to achieve full five-point scale "
                "coverage as required by the FMTS paper."
            )
        
        if statistics['coverage_analysis']['coverage_percentage'] < 100:
            missing = statistics['coverage_analysis']['missing_categories']
            recommendations.append(
                f"Add rules for missing categories: {missing} to meet paper's "
                f"comprehensive triage system requirements."
            )
        
        if len(validation['categories_covered']) < 5:
            recommendations.append(
                "Ensure all five triage categories (RED, ORANGE, YELLOW, GREEN, BLUE) "
                "are covered as specified in the FMTS paper."
            )
        
        if statistics['total_rules'] < 8:
            recommendations.append(
                "Consider adding more rules to handle the complexity described in the "
                "paper's ~50 flowcharts and various triage scenarios."
            )
        
        if not recommendations:
            recommendations.append(
                "Rule set demonstrates good compliance with FMTS paper requirements. "
                "Continue monitoring for consistency with paper's objective triage goals."
            )
        
        return recommendations