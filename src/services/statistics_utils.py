"""Statistics Utilities

Centralized statistical calculations to eliminate duplicate computations across the codebase.
Provides common statistical functions used in NHS metrics, operational metrics, and plotting.
"""

import numpy as np
from typing import List, Dict, Any, Optional


class StatisticsUtils:
    """Centralized statistical calculation utilities.
    
    Eliminates duplicate statistical computations across NHS metrics,
    operational metrics, and plotting services.
    """
    
    @staticmethod
    def calculate_basic_stats(values: List[float]) -> Dict[str, float]:
        """Calculate basic statistical measures for a list of values.
        
        Args:
            values: List of numeric values
            
        Returns:
            Dictionary containing mean, median, std_dev, min, max, 95th percentile
        """
        if not values:
            return {
                'mean': 0.0,
                'median': 0.0,
                'std_dev': 0.0,
                'min': 0.0,
                'max': 0.0,
                '95th_percentile': 0.0,
                'count': 0
            }
        
        return {
            'mean': float(np.mean(values)),
            'median': float(np.median(values)),
            'std_dev': float(np.std(values)),
            'min': float(np.min(values)),
            'max': float(np.max(values)),
            '95th_percentile': float(np.percentile(values, 95)),
            'count': len(values)
        }
    
    @staticmethod
    def calculate_compliance_rate(compliant_count: int, total_count: int) -> float:
        """Calculate compliance rate as percentage.
        
        Args:
            compliant_count: Number of compliant cases
            total_count: Total number of cases
            
        Returns:
            Compliance rate as percentage (0-100)
        """
        return (compliant_count / total_count) * 100.0 if total_count > 0 else 0.0
    
    @staticmethod
    def calculate_admission_rate(admitted_patients: List, total_patients: List) -> float:
        """Calculate admission rate as percentage.
        
        Args:
            admitted_patients: List of admitted patients
            total_patients: List of all patients
            
        Returns:
            Admission rate as percentage (0-100)
        """
        if not total_patients:
            return 0.0
        
        admitted_count = sum(1 for p in total_patients if p.admitted)
        return (admitted_count / len(total_patients)) * 100.0
    
    @staticmethod
    def calculate_4hour_compliance(patients: List) -> Dict[str, Any]:
        """Calculate NHS 4-hour standard compliance metrics.
        
        Args:
            patients: List of patient objects with journey time methods
            
        Returns:
            Dictionary with compliance metrics
        """
        if not patients:
            return {
                'compliant_count': 0,
                'non_compliant_count': 0,
                'compliance_rate_pct': 0.0,
                'total_patients': 0
            }
        
        compliant_count = sum(1 for p in patients if p.meets_4hour_standard())
        total_count = len(patients)
        
        return {
            'compliant_count': compliant_count,
            'non_compliant_count': total_count - compliant_count,
            'compliance_rate_pct': StatisticsUtils.calculate_compliance_rate(compliant_count, total_count),
            'total_patients': total_count
        }
    
    @staticmethod
    def calculate_journey_time_stats(patients: List) -> Dict[str, float]:
        """Calculate journey time statistics for patients.
        
        Args:
            patients: List of patient objects with journey time methods (should already be filtered for completed patients)
            
        Returns:
            Dictionary with journey time statistics
        """
        journey_times = [p.get_total_journey_time() for p in patients]
        return StatisticsUtils.calculate_basic_stats(journey_times)
    
    @staticmethod
    def calculate_assessment_time_stats(patients: List) -> Dict[str, float]:
        """Calculate time-to-assessment statistics for patients.
        
        Args:
            patients: List of patient objects with timing methods (should already be filtered for completed patients)
            
        Returns:
            Dictionary with assessment time statistics
        """
        assessment_times = [p.get_time_to_initial_assessment() for p in patients 
                          if p.get_time_to_initial_assessment() > 0]
        return StatisticsUtils.calculate_basic_stats(assessment_times)
    
    @staticmethod
    def calculate_treatment_time_stats(patients: List) -> Dict[str, float]:
        """Calculate time-to-treatment statistics for patients.
        
        Args:
            patients: List of patient objects with timing methods (should already be filtered for completed patients)
            
        Returns:
            Dictionary with treatment time statistics
        """
        treatment_times = [p.get_time_to_treatment() for p in patients 
                         if p.get_time_to_treatment() > 0]
        return StatisticsUtils.calculate_basic_stats(treatment_times)
    
    @staticmethod
    def calculate_throughput_rate(processed_count: int, time_period_minutes: float) -> float:
        """Calculate throughput rate per hour.
        
        Args:
            processed_count: Number of items processed
            time_period_minutes: Time period in minutes
            
        Returns:
            Throughput rate per hour
        """
        return (processed_count / time_period_minutes) * 60.0 if time_period_minutes > 0 else 0.0
    
    @staticmethod
    def group_patients_by_age(patients: List) -> Dict[str, List]:
        """Group patients by standard NHS age groups.
        
        Args:
            patients: List of patient objects with age attribute
            
        Returns:
            Dictionary with age groups as keys and patient lists as values
        """
        return {
            '0-17': [p for p in patients if p.age < 18],
            '18-64': [p for p in patients if 18 <= p.age < 65],
            '65+': [p for p in patients if p.age >= 65]
        }
    
    @staticmethod
    def calculate_group_performance_stats(patients: List) -> Dict[str, Any]:
        """Calculate comprehensive performance statistics for a group of patients.
        
        Args:
            patients: List of patient objects
            
        Returns:
            Dictionary with comprehensive performance metrics
        """
        if not patients:
            return {
                'count': 0,
                'journey_time_stats': StatisticsUtils.calculate_basic_stats([]),
                'compliance_metrics': StatisticsUtils.calculate_4hour_compliance([]),
                'admission_rate_pct': 0.0
            }
        
        return {
            'count': len(patients),
            'journey_time_stats': StatisticsUtils.calculate_journey_time_stats(patients),
            'compliance_metrics': StatisticsUtils.calculate_4hour_compliance(patients),
            'admission_rate_pct': StatisticsUtils.calculate_admission_rate(patients, patients)
        }