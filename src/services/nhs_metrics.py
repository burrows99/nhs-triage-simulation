"""NHS Metrics Service

Official NHS A&E Quality Indicators tracking service based on NHS Digital/NHS England Standards.

Tracks the 5 official NHS A&E Quality Indicators:
1. Left department before being seen for treatment rate
2. Re-attendance rate
3. Time to initial assessment
4. Time to treatment
5. Total time in A&E

Plus NHS 4-hour standard compliance (95% target)
"""

import numpy as np
import pandas as pd
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta

from .base_metrics import BaseMetrics, BaseRecord
from .statistics_utils import StatisticsUtils
from src.logger import logger
from src.models.synthea_models import Patient
# Patient models now come from Synthea data service


class NHSMetrics(BaseMetrics):
    """NHS A&E Quality Indicators Service
    
    Provides NHS-specific metrics tracking and calculation capabilities.
    """
    
    def __init__(self, reattendance_window_hours: int = 72):
        """Initialize NHS Metrics Service
        
        Args:
            reattendance_window_hours: Time window for re-attendance tracking (default: 72 hours)
        """
        super().__init__("NHSMetrics")
        
        # NHS-specific tracking
        self.reattendance_window = reattendance_window_hours
        self.patient_history: Dict[str, List[float]] = defaultdict(list)
        
        # NHS-specific counters
        self.counters.update({
            'lwbs_count': 0,
            'reattendance_count': 0,
            'admissions_count': 0
        })
    
    def add_patient_arrival(self, patient, arrival_time: float):
        """Record patient arrival using Synthea Patient object
        
        Args:
            patient: Synthea Patient object
            arrival_time: Arrival time in minutes
        """
        # Check for re-attendance
        is_reattendance = self._check_reattendance(patient.Id, arrival_time)
        
        # Store arrival time and re-attendance status on patient object
        patient.arrival_time = arrival_time
        patient.is_reattendance = is_reattendance
        
        # Add patient directly to base metrics (Patient now inherits from BaseRecord)
        self.add_record(patient)
        
        if is_reattendance:
            self.counters['reattendance_count'] += 1
        
        # Track arrival time for re-attendance checking
        self.patient_history[patient.Id].append(arrival_time)
    
    def add_patient_object(self, patient) -> None:
        """Record patient arrival using Patient object
        
        Args:
            patient: Patient object containing all patient data
            
        Returns:
            Patient object for NHS metrics tracking
        """
        # Check for re-attendance
        is_reattendance = self._check_reattendance(patient.Id, patient.arrival_time)
        patient.is_reattendance = is_reattendance
        
        # Add to base metrics
        self.add_record(patient)
        
        if is_reattendance:
            self.counters['reattendance_count'] += 1
        
        # Track arrival time for re-attendance checking
        self.patient_history[patient.Id].append(patient.arrival_time)
        
        return patient
    
    def update_patient_record_from_object(self, patient) -> None:
        """Update Patient record with final data (no-op since we use Patient objects directly)
        
        Args:
            patient: Patient object with complete journey data
        """
        # Since we now use Patient objects directly, this method is a no-op
        # The Patient object is already updated in place
        pass
    
    def record_initial_assessment(self, patient, assessment_time: float):
        """Record start of initial assessment (triage/nursing assessment)"""
        # Store assessment time directly on patient object
        patient.initial_assessment_time = assessment_time
    
    def record_treatment_start(self, patient, treatment_time: float):
        """Record start of treatment (usually doctor consultation)"""
        # Store treatment start time directly on patient object
        patient.treatment_start_time = treatment_time
    
    def record_triage_category(self, patient, category: str):
        """Record Manchester Triage System category"""
        # Store triage category directly on patient object
        patient.triage_category = category
    
    def record_patient_departure(self, patient_id: str, departure_time: float, 
                               disposal: str = "discharged", admitted: bool = False,
                               left_without_being_seen: bool = False):
        """Record patient departure with disposal information
        
        Args:
            patient_id: Patient identifier
            departure_time: Time of departure in minutes
            disposal: Type of discharge (discharged/admitted/transferred)
            admitted: Whether patient was admitted
            left_without_being_seen: Whether patient left before being seen
        """
        patient_record = self.get_record(patient_id)
        if not patient_record:
            return
        
        patient_record.departure_time = departure_time
        patient_record.disposal = disposal
        patient_record.admitted = admitted
        patient_record.left_without_being_seen = left_without_being_seen
        
        if admitted:
            self.counters['admissions_count'] += 1
        
        if left_without_being_seen:
            self.counters['lwbs_count'] += 1
        
        # Complete the record
        self.complete_record(patient_id, departure_time)
    
    def _check_reattendance(self, patient_id: str, arrival_time: float) -> bool:
        """Check if patient is a re-attendance within the specified window"""
        if patient_id not in self.patient_history:
            return False
        
        # Check if any previous attendance was within the time window
        window_start = arrival_time - (self.reattendance_window * 60)  # Convert hours to minutes
        
        for previous_arrival in self.patient_history[patient_id]:
            if previous_arrival >= window_start:
                return True
        
        return False
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate official NHS A&E Quality Indicators
        
        Returns:
            Dictionary containing all official NHS metrics and performance indicators
        """
        completed_patients = [p for p in self.records if p.is_completed_journey()]
        
        if not completed_patients:
            return {
                'error': 'No completed patients to analyze',
                'total_attendances': self.counters['total_records'],
                'active_patients': len(self.active_records)
            }
        
        # Validate patient timing data using centralized validation
        validated_patients = StatisticsUtils.validate_patient_timing(completed_patients)
        
        if not validated_patients:
            return {
                'error': 'No patients with valid timing data to analyze',
                'total_attendances': len(completed_patients),
                'invalid_timing_count': len(completed_patients),
                'active_patients': len(self.active_records)
            }
        
        # Use validated patients for all calculations
        completed_patients = validated_patients
        
        # Calculate official NHS metrics using centralized calculations from StatisticsUtils
        # Ensure all time calculations are centralized and consistent
        journey_time_stats = StatisticsUtils.calculate_journey_time_stats(completed_patients)
        assessment_time_stats = StatisticsUtils.calculate_assessment_time_stats(completed_patients)
        treatment_time_stats = StatisticsUtils.calculate_treatment_time_stats(completed_patients)
        compliance_metrics = StatisticsUtils.calculate_4hour_compliance(completed_patients)
        
        # Validate time calculations to catch negative time errors
        if journey_time_stats['mean'] < 0:
            logger.error(f"❌ NEGATIVE JOURNEY TIME DETECTED: {journey_time_stats['mean']:.2f} minutes")
            logger.error(f"This indicates arrival_time > departure_time for some patients")
            # Log sample of problematic patients for debugging
            for i, patient in enumerate(completed_patients[:3]):
                logger.error(f"Patient {i+1}: arrival={patient.arrival_time:.2f}, departure={patient.departure_time:.2f}, total={patient.get_total_journey_time():.2f}")
        
        metrics = {
            # ATTENDANCE SUMMARY
            'total_attendances': len(completed_patients),
            'active_patients_in_system': len(self.active_records),
            
            # OFFICIAL NHS A&E QUALITY INDICATORS
            '1_left_before_being_seen_rate_pct': StatisticsUtils.calculate_compliance_rate(self.counters['lwbs_count'], len(completed_patients)),
            '2_reattendance_rate_pct': StatisticsUtils.calculate_compliance_rate(self.counters['reattendance_count'], len(completed_patients)),
            '3_time_to_initial_assessment_avg_minutes': assessment_time_stats['mean'],
            '4_time_to_treatment_avg_minutes': treatment_time_stats['mean'],
            '5_total_time_in_ae_avg_minutes': journey_time_stats['mean'],
            
            # NHS 4-HOUR STANDARD
            '4hour_standard_compliance_pct': compliance_metrics['compliance_rate_pct'],
            'attendances_within_4hours': compliance_metrics['compliant_count'],
            'attendances_over_4hours': compliance_metrics['non_compliant_count'],
            '95pct_target_achieved': compliance_metrics['compliance_rate_pct'] >= 95.0,
            '76pct_interim_target_achieved': compliance_metrics['compliance_rate_pct'] >= 76.0,
            
            # ADDITIONAL PERFORMANCE METRICS
            'median_total_time_minutes': journey_time_stats['median'],
            '95th_percentile_time_minutes': journey_time_stats['95th_percentile'],
            'admission_rate_pct': StatisticsUtils.calculate_admission_rate(completed_patients, completed_patients),
            
            # TRIAGE BREAKDOWN
            'triage_category_distribution': self._get_triage_distribution(completed_patients),
            
            # DETAILED BREAKDOWNS
            'age_group_analysis': self._get_age_group_analysis(completed_patients),
            'gender_analysis': self._get_gender_analysis(completed_patients),
            'time_distribution_analysis': self._get_time_distribution_analysis([p.get_total_journey_time() for p in completed_patients]),
        }
        
        # Add base statistics
        metrics.update(self.get_basic_statistics())
        
        return metrics
    
    def _get_triage_distribution(self, patients: List) -> Dict[str, int]:
        """Get distribution of triage categories"""
        # Initialize all possible triage categories with 0
        distribution = {
            'RED': 0,
            'ORANGE': 0, 
            'YELLOW': 0,
            'GREEN': 0,
            'BLUE': 0
        }
        
        # Count actual categories
        categories = [p.triage_category for p in patients if p.triage_category]
        if categories:
            counts = pd.Series(categories).value_counts()
            for category, count in counts.items():
                if category in distribution:
                    distribution[category] = int(count)  # Convert to regular Python int
        
        return distribution
    
    def _get_age_group_analysis(self, patients: List) -> Dict[str, Dict]:
        """Analyze performance by age groups using centralized calculations"""
        age_groups = StatisticsUtils.group_patients_by_age(patients)
        
        analysis = {}
        for group, group_patients in age_groups.items():
            if group_patients:
                group_stats = StatisticsUtils.calculate_group_performance_stats(group_patients)
                analysis[group] = {
                    'count': group_stats['count'],
                    'avg_time_minutes': group_stats['journey_time_stats']['mean'],
                    '4hour_compliance_pct': group_stats['compliance_metrics']['compliance_rate_pct'],
                    'admission_rate_pct': group_stats['admission_rate_pct']
                }
        
        return analysis
    
    def _get_gender_analysis(self, patients: List) -> Dict[str, Dict]:
        """Analyze performance by gender using centralized calculations"""
        genders = defaultdict(list)
        for p in patients:
            genders[p.gender].append(p)
        
        analysis = {}
        for gender, gender_patients in genders.items():
            if gender_patients:
                group_stats = StatisticsUtils.calculate_group_performance_stats(gender_patients)
                analysis[gender] = {
                    'count': group_stats['count'],
                    'avg_time_minutes': group_stats['journey_time_stats']['mean'],
                    '4hour_compliance_pct': group_stats['compliance_metrics']['compliance_rate_pct'],
                    'admission_rate_pct': group_stats['admission_rate_pct']
                }
        
        return analysis
    
    def _get_time_distribution_analysis(self, times: List[float]) -> Dict[str, Any]:
        """Analyze time distribution patterns"""
        if not times:
            return {}
        
        return {
            'min_time_minutes': np.min(times),
            'max_time_minutes': np.max(times),
            'std_dev_minutes': np.std(times),
            'quartiles': {
                '25th_percentile': np.percentile(times, 25),
                '50th_percentile': np.percentile(times, 50),
                '75th_percentile': np.percentile(times, 75)
            },
            'distribution_bins': self._create_time_bins(times)
        }
    
    def _create_time_bins(self, times: List[float]) -> Dict[str, int]:
        """Create time distribution bins for analysis"""
        bins = {
            '0-60min': 0,
            '60-120min': 0,
            '120-240min': 0,
            '240-360min': 0,
            '360+min': 0
        }
        
        for time in times:
            if time <= 60:
                bins['0-60min'] += 1
            elif time <= 120:
                bins['60-120min'] += 1
            elif time <= 240:
                bins['120-240min'] += 1
            elif time <= 360:
                bins['240-360min'] += 1
            else:
                bins['360+min'] += 1
        
        return bins
    
    def print_nhs_dashboard(self) -> Dict:
        """Print comprehensive NHS-style dashboard
        
        Returns:
            Dictionary containing all calculated metrics
        """
        metrics = self.calculate_metrics()
        
        if 'error' in metrics:
            logger.warning(f"⚠️  {metrics['error']}")
            logger.info(f"Total attendances recorded: {metrics.get('total_attendances', 0)}")
            logger.info(f"Active patients in system: {metrics.get('active_patients', 0)}")
            return metrics
        
        logger.info("=" * 70)
        logger.info("OFFICIAL NHS A&E QUALITY INDICATORS DASHBOARD")
        logger.info("Based on NHS Digital/NHS England Standards")
        logger.info("=" * 70)
        
        # Attendance Overview
        logger.info(f"📊 ATTENDANCE SUMMARY:")
        logger.info(f"   Total Attendances: {metrics['total_attendances']:,}")
        logger.info(f"   Active Patients in System: {metrics['active_patients_in_system']:,}")
        
        # Official NHS Quality Indicators
        logger.info(f"🏥 OFFICIAL NHS A&E QUALITY INDICATORS:")
        logger.info(f"   1️⃣  Left Before Being Seen Rate: {metrics['1_left_before_being_seen_rate_pct']:.2f}%")
        logger.info(f"   2️⃣  Re-attendance Rate ({self.reattendance_window}h): {metrics['2_reattendance_rate_pct']:.2f}%")
        logger.info(f"   3️⃣  Time to Initial Assessment: {metrics['3_time_to_initial_assessment_avg_minutes']:.1f} min (avg)")
        logger.info(f"   4️⃣  Time to Treatment: {metrics['4_time_to_treatment_avg_minutes']:.1f} min (avg)")
        logger.info(f"   5️⃣  Total Time in A&E: {metrics['5_total_time_in_ae_avg_minutes']:.1f} min (avg)")
        
        # 4-Hour Standard
        compliance = metrics['4hour_standard_compliance_pct']
        target_95_status = "✅ ACHIEVED" if metrics['95pct_target_achieved'] else "❌ MISSED"
        target_76_status = "✅ MET" if metrics['76pct_interim_target_achieved'] else "❌ MISSED"
        
        logger.info(f"🎯 NHS 4-HOUR STANDARD:")
        logger.info(f"   Compliance Rate: {compliance:.1f}%")
        logger.info(f"   95% Target (Official): {target_95_status}")
        logger.info(f"   76% Interim Target: {target_76_status}")
        logger.info(f"   Within 4 Hours: {metrics['attendances_within_4hours']:,}")
        logger.info(f"   Over 4 Hours: {metrics['attendances_over_4hours']:,}")
        
        # Performance Distribution  
        logger.info(f"📈 PERFORMANCE DISTRIBUTION:")
        logger.info(f"   Median Total Time: {metrics['median_total_time_minutes']:.1f} min")
        logger.info(f"   95th Percentile: {metrics['95th_percentile_time_minutes']:.1f} min")
        
        # Clinical Outcomes
        logger.info(f"🏥 CLINICAL OUTCOMES:")
        logger.info(f"   Admission Rate: {metrics['admission_rate_pct']:.1f}%")
        
        # Triage Distribution
        if metrics['triage_category_distribution']:
            logger.info(f"🚦 TRIAGE CATEGORY DISTRIBUTION:")
            for category, count in sorted(metrics['triage_category_distribution'].items()):
                pct = (count / metrics['total_attendances']) * 100
                logger.info(f"   {category}: {count:,} ({pct:.1f}%)")
        
        # Age Group Analysis
        if metrics['age_group_analysis']:
            logger.info(f"👥 AGE GROUP ANALYSIS:")
            for age_group, data in metrics['age_group_analysis'].items():
                logger.info(f"   {age_group}: {data['count']:,} patients, {data['avg_time_minutes']:.1f} min avg, {data['4hour_compliance_pct']:.1f}% compliant")
        
        return metrics
    
    def _record_to_dict(self, record: BaseRecord) -> Dict[str, Any]:
        """Convert a Patient to dictionary for export using centralized calculations"""
        # Use centralized calculation methods from Patient model
        return {
            'patient_id': record.Id,
            'arrival_time': record.arrival_time,
            'age': record.age,
            'gender': record.gender,
            'triage_category': record.triage_category,
            'initial_assessment_start': record.initial_assessment_time,
            'treatment_start': record.treatment_start_time,
            'departure_time': record.departure_time,
            'total_time_minutes': record.get_total_journey_time(),
            'time_to_assessment_minutes': record.get_time_to_initial_assessment(),
            'time_to_treatment_minutes': record.get_time_to_treatment(),
            'meets_4hour_standard': record.meets_4hour_standard(),
            'is_reattendance': record.is_reattendance,
            'admitted': record.admitted,
            'disposal': record.disposal,
            'presenting_complaint': record.presenting_complaint,
            'left_without_being_seen': record.left_without_being_seen
        }