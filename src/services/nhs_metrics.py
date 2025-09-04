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
import attr
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from itertools import groupby
from operator import attrgetter

from .base_metrics import BaseMetrics, BaseRecord
from .statistics_utils import StatisticsUtils
from src.logger import logger, log_calculation
from src.models.synthea_models import Patient
# Patient models now come from Synthea data service


@attr.s(auto_attribs=True)
class NHSMetrics(BaseMetrics):
    """NHS A&E Quality Indicators Service
    
    Provides NHS-specific metrics tracking and calculation capabilities.
    """
    
    # Configuration
    reattendance_window_hours: int = 72
    
    # NHS-specific tracking
    patient_history: Dict[str, List[float]] = attr.Factory(lambda: defaultdict(list))
    
    def __attrs_post_init__(self):
        """Initialize NHS Metrics Service after attrs initialization"""
        # Initialize base metrics properly
        super().__init__("NHSMetrics")
        
        # NHS-specific tracking
        self.reattendance_window = self.reattendance_window_hours
        
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
        logger.info(f"🔄 DATA_TRANSFER_START: NHSMetrics.add_patient_arrival() initiated")
        logger.info(f"📊 TRANSFER_SOURCE: Patient object - {str(patient.__dict__)}")
        logger.info(f"📍 TRANSFER_DESTINATION: NHS metrics record storage")
        logger.info(f"🔍 DEBUG: Patient arrival tracking - ID: {patient.Id} | Arrival Time: {arrival_time:.1f}")
        
        # Check for re-attendance
        is_reattendance = self._check_reattendance(patient.Id, arrival_time)
        logger.debug(f"🔍 DEBUG: Re-attendance check result for {patient.Id}: {is_reattendance}")
        
        # Store arrival time and re-attendance status on patient object
        patient.arrival_time = arrival_time
        patient.is_reattendance = is_reattendance
        logger.debug(f"🔍 DEBUG: Set patient.arrival_time = {arrival_time:.1f} for patient {patient.Id}")
        
        logger.info(f"📊 TRANSFER_PAYLOAD: Patient updated - arrival_time={arrival_time}, is_reattendance={is_reattendance}")
        
        # Add patient directly to base metrics (Patient now inherits from BaseRecord)
        self.add_record(patient)
        logger.debug(f"🔍 DEBUG: Added patient to records. Records count now: {len(self.records)}")
        
        if is_reattendance:
            self.counters['reattendance_count'] += 1
            logger.debug(f"🔍 DEBUG: Updated reattendance_count to {self.counters['reattendance_count']}")
        
        # Track arrival time for re-attendance checking
        self.patient_history[patient.Id].append(arrival_time)
        logger.debug(f"🔍 DEBUG: Added arrival time to patient history. History length for {patient.Id}: {len(self.patient_history[patient.Id])}")
        
        logger.info(f"📊 TRANSFER_RESULT: Record stored in metrics - patient_id={patient.Id}, records_count={len(self.records)}")
        logger.info(f"✅ DATA_TRANSFER_SUCCESS: NHS Metrics arrival recorded for patient {patient.Id} at {arrival_time:.2f}min")
        
        # Log patient state for debugging
        logger.info(f"🔍 PATIENT STATE | ID: {patient.Id} | Has arrival_time: {hasattr(patient, 'arrival_time')} | Has departure_time: {hasattr(patient, 'departure_time')}")
        logger.info(f"🔍 PATIENT TIMING | Arrival: {patient.arrival_time if hasattr(patient, 'arrival_time') else 'NOT_SET'} | Departure: {patient.departure_time if hasattr(patient, 'departure_time') else 'NOT_SET'}")
    
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
        logger.info(f"🔄 DEPARTURE_START: Recording departure for patient {patient_id} at {departure_time:.1f}min")
        logger.info(f"📊 DEPARTURE_DETAILS: disposal={disposal}, admitted={admitted}, lwbs={left_without_being_seen}")
        
        patient_record = self.get_record(patient_id)
        if not patient_record:
            logger.error(f"❌ DEPARTURE_ERROR: Patient record not found for ID {patient_id}")
            return
        
        logger.debug(f"🔍 DEBUG: Found patient record for {patient_id}")
        logger.debug(f"🔍 DEBUG: Patient arrival time: {patient_record.arrival_time if hasattr(patient_record, 'arrival_time') else 'NOT_SET'}")
        
        patient_record.departure_time = departure_time
        patient_record.disposal = disposal
        patient_record.admitted = admitted
        patient_record.left_without_being_seen = left_without_being_seen
        
        logger.debug(f"🔍 DEBUG: Updated patient record with departure data")
        
        if admitted:
            self.counters['admissions_count'] += 1
            logger.debug(f"🔍 DEBUG: Updated admissions_count to {self.counters['admissions_count']}")
        
        if left_without_being_seen:
            self.counters['lwbs_count'] += 1
            logger.debug(f"🔍 DEBUG: Updated lwbs_count to {self.counters['lwbs_count']}")
        
        # Complete the record
        self.complete_record(patient_id, departure_time)
        logger.info(f"✅ DEPARTURE_SUCCESS: Patient {patient_id} departure recorded - Total time: {patient_record.get_total_journey_time():.1f}min")
        logger.info(f"📊 COMPLETION_STATUS: Completed patients now: {len([p for p in self.records if p.is_completed_journey()])}")
    
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
    
    @log_calculation("NHS metrics calculation")
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate official NHS A&E Quality Indicators
        
        Returns:
            Dictionary containing all official NHS metrics and performance indicators
        """
        logger.info(f"🔄 METRICS_CALCULATION_START: Beginning NHS metrics calculation")
        logger.info(f"📊 CALCULATION_INPUT: Total records: {len(self.records)}, Active records: {len(self.active_records)}")
        
        completed_patients = [p for p in self.records if p.is_completed_journey()]
        logger.info(f"📊 COMPLETION_ANALYSIS: Found {len(completed_patients)} completed patients out of {len(self.records)} total")
        
        # Log sample of patient completion status for debugging
        for i, patient in enumerate(self.records[:5]):  # Log first 5 patients
            arrival_time = patient.arrival_time if hasattr(patient, 'arrival_time') else 'NONE'
            departure_time = patient.departure_time if hasattr(patient, 'departure_time') else 'NONE'
            logger.debug(f"🔍 PATIENT_DEBUG_{i+1}: ID={patient.Id}, completed={patient.is_completed_journey()}, arrival={arrival_time}, departure={departure_time}")
        
        if not completed_patients:
            logger.warning(f"⚠️ CALCULATION_WARNING: No completed patients to analyze")
            logger.warning(f"⚠️ DIAGNOSTIC: Total records={len(self.records)}, Active records={len(self.active_records)}")
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
        logger.info(f"📊 VALIDATION_RESULT: Using {len(completed_patients)} validated patients for calculations")
        
        # Calculate official NHS metrics using direct scipy/numpy calls
        journey_times = [p.get_total_journey_time() for p in completed_patients]
        assessment_times = [p.get_time_to_initial_assessment() for p in completed_patients if p.get_time_to_initial_assessment() > 0]
        treatment_times = [p.get_time_to_treatment() for p in completed_patients if p.get_time_to_treatment() > 0]
        
        logger.debug(f"🔍 TIME_CALCULATIONS: Journey times count: {len(journey_times)}, Assessment times count: {len(assessment_times)}, Treatment times count: {len(treatment_times)}")
        
        # Log sample journey times for debugging
        if journey_times:
            sample_times = journey_times[:3]
            logger.debug(f"🔍 SAMPLE_JOURNEY_TIMES: {[f'{t:.1f}min' for t in sample_times]}")
        
        # Calculate stats directly using numpy
        journey_time_stats = {
            'mean': np.mean(journey_times) if journey_times else 0,
            'median': np.median(journey_times) if journey_times else 0,
            '95th_percentile': np.percentile(journey_times, 95) if journey_times else 0
        }
        assessment_time_stats = {
            'mean': np.mean(assessment_times) if assessment_times else 0
        }
        treatment_time_stats = {
            'mean': np.mean(treatment_times) if treatment_times else 0
        }
        
        # Calculate 4-hour compliance directly
        compliant_count = sum(1 for p in completed_patients if p.meets_4hour_standard())
        compliance_metrics = {
            'compliance_rate_pct': (compliant_count / len(completed_patients)) * 100 if completed_patients else 0,
            'compliant_count': compliant_count,
            'non_compliant_count': len(completed_patients) - compliant_count
        }
        
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
        
        logger.info(f"✅ METRICS_CALCULATION_SUCCESS: Calculated {len(metrics)} metrics for {len(completed_patients)} patients")
        logger.info(f"📊 KEY_METRICS: 4hr_compliance={metrics['4hour_standard_compliance_pct']:.1f}%, avg_time={metrics['5_total_time_in_ae_avg_minutes']:.1f}min, lwbs_rate={metrics['1_left_before_being_seen_rate_pct']:.1f}%")
        
        return metrics
    
    def _get_triage_distribution(self, patients: List) -> Dict[str, int]:
        """Get distribution of triage categories using Counter"""
        # Initialize all possible triage categories with 0
        distribution = {
            'RED': 0,
            'ORANGE': 0, 
            'YELLOW': 0,
            'GREEN': 0,
            'BLUE': 0
        }
        
        # Count actual categories using Counter
        categories = [p.triage_category for p in patients if p.triage_category]
        if categories:
            counts = Counter(categories)
            for category, count in counts.items():
                if category in distribution:
                    distribution[category] = count
        
        return distribution
    
    def _get_age_group_analysis(self, patients: List) -> Dict[str, Dict]:
        """Analyze performance by age groups using groupby and Counter"""
        def age_group_key(patient):
            age = getattr(patient, 'age', 0)
            if age < 18:
                return '0-17'
            elif age < 65:
                return '18-64'
            else:
                return '65+'
        
        # Group patients by age using itertools.groupby
        sorted_patients = sorted(patients, key=age_group_key)
        age_groups = {k: list(g) for k, g in groupby(sorted_patients, key=age_group_key)}
        
        # Ensure all age groups are represented
        all_groups = {'0-17': [], '18-64': [], '65+': []}
        all_groups.update(age_groups)
        
        analysis = {}
        for group, group_patients in all_groups.items():
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