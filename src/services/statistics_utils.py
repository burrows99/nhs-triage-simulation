"""Statistics Utilities

Centralized statistical calculations delegating to production libraries.
Provides common statistical functions using scipy.stats for reliability.
"""

import numpy as np
from scipy import stats
from typing import List, Dict, Any, Optional
from functools import lru_cache, cached_property
from collections import Counter


class StatisticsUtils:
    """Centralized statistical calculation utilities.
    
    Eliminates duplicate statistical computations across NHS metrics,
    operational metrics, and plotting services.
    All time calculations are centralized here to prevent inconsistencies.
    """
    
    @staticmethod
    def validate_patient_timing(patients: List) -> List:
        """Validate and log timing issues in patient data.
        
        Args:
            patients: List of patient objects with timing data
            
        Returns:
            List of patients with valid timing data (filters out invalid ones)
        """
        from src.logger import logger
        
        # Validate patients using list comprehension with validation function
        def is_valid_patient(patient):
            if not (patient.arrival_time > 0 and patient.departure_time > 0):
                return False
            
            total_time = patient.get_total_journey_time()
            
            if total_time < 0:
                return False
                
            if total_time > 1440:  # 24 hours in minutes
                pass
            
            return True
        
        valid_patients = [p for p in patients if is_valid_patient(p)]
        invalid_count = len(patients) - len(valid_patients)
        
        # Return valid patients without verbose logging
        pass
        
        return valid_patients
    
    @staticmethod
    @lru_cache(maxsize=128)
    def calculate_basic_stats(values: tuple) -> Dict[str, float]:
        """Calculate basic statistics using scipy.stats with caching for performance.
        
        Args:
            values: Tuple of numeric values (tuple for hashability in cache)
            
        Returns:
            Dictionary with basic statistics computed by scipy
        """
        from src.logger import logger
        
        if not values:
            return {
                'count': 0,
                'mean': 0.0,
                'median': 0.0,
                'std_dev': 0.0,
                'min': 0.0,
                'max': 0.0,
                '95th_percentile': 0.0,
                'skewness': 0.0,
                'kurtosis': 0.0
            }
        
        # Filter out invalid values
        valid_values = [v for v in values if v is not None and not np.isnan(v) and v >= 0]
        
        if not valid_values:
            return {
                'count': 0,
                'mean': 0.0,
                'median': 0.0,
                'std_dev': 0.0,
                'min': 0.0,
                'max': 0.0,
                '95th_percentile': 0.0,
                'skewness': 0.0,
                'kurtosis': 0.0
            }
        
        # Delegate to scipy.stats for production-grade statistical calculations
        values_array = np.array(valid_values)
        
        desc_stats = stats.describe(values_array)
        
        result = {
            'count': desc_stats.nobs,
            'mean': desc_stats.mean,
            'median': np.median(values_array),  # scipy doesn't include median in describe
            'std_dev': np.sqrt(desc_stats.variance),
            'min': desc_stats.minmax[0],
            'max': desc_stats.minmax[1],
            '95th_percentile': np.percentile(values_array, 95),
            'skewness': desc_stats.skewness,
            'kurtosis': desc_stats.kurtosis
        }
        
        return result
    
    @staticmethod
    def calculate_basic_stats_from_list(values: List[float]) -> Dict[str, float]:
        """Wrapper for calculate_basic_stats that accepts lists."""
        return StatisticsUtils.calculate_basic_stats(tuple(values))
    
    @staticmethod
    def calculate_compliance_rate(compliant_count: int, total_count: int) -> float:
        """Calculate compliance rate as percentage.
        
        Args:
            compliant_count: Number of compliant cases
            total_count: Total number of cases
            
        Returns:
            Compliance rate as percentage (0-100)
        """
        return (compliant_count / total_count) * 100 if total_count > 0 else 0.0
    
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
        return (len(admitted_patients) / len(total_patients)) * 100
    
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
    
    # Removed wrapper functions - use scipy.stats.describe directly:
    # For journey times: stats.describe([p.get_total_journey_time() for p in patients])
    # For assessment times: stats.describe([p.get_time_to_initial_assessment() for p in patients if p.get_time_to_initial_assessment() > 0])
    # For treatment times: stats.describe([p.get_time_to_treatment() for p in patients if p.get_time_to_treatment() > 0])
    
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
                'journey_time_stats': StatisticsUtils.calculate_basic_stats_from_list([]),
                'compliance_metrics': StatisticsUtils.calculate_4hour_compliance([]),
                'admission_rate_pct': 0.0
            }
        
        return {
            'count': len(patients),
            'journey_time_stats': StatisticsUtils.calculate_journey_time_stats(patients),
            'compliance_metrics': StatisticsUtils.calculate_4hour_compliance(patients),
            'admission_rate_pct': StatisticsUtils.calculate_admission_rate(patients, patients)
        }
    
    @staticmethod
    def calculate_journey_time_stats(patients: List[Any]) -> Dict[str, Any]:
        """Calculate journey time statistics for patients
        
        Args:
            patients: List of patient objects with journey time data
            
        Returns:
            Dictionary with journey time statistics
        """
        if not patients:
            return StatisticsUtils.calculate_basic_stats_from_list([])
        
        # Extract journey times from patients
        journey_times = []
        for patient in patients:
            try:
                if patient.departure_time and patient.arrival_time:
                    journey_time = patient.departure_time - patient.arrival_time
                    journey_times.append(journey_time)
            except AttributeError:
                # Skip patients without required time attributes
                continue
        
        return StatisticsUtils.calculate_basic_stats_from_list(journey_times)