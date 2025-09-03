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
        completed_patients = [p for p in self.records if hasattr(p, 'departure_time') and p.departure_time > 0]
        
        if not completed_patients:
            return {
                'error': 'No completed patients to analyze',
                'total_attendances': self.counters['total_records'],
                'active_patients': len(self.active_records)
            }
        
        # Calculate official NHS metrics
        total_times = [p.departure_time - p.arrival_time for p in completed_patients if hasattr(p, 'arrival_time')]
        initial_assessment_times = [p.initial_assessment_start - p.arrival_time for p in completed_patients 
                                  if hasattr(p, 'initial_assessment_start') and hasattr(p, 'arrival_time') and p.initial_assessment_start > 0]
        treatment_times = [p.treatment_start - p.arrival_time for p in completed_patients 
                          if hasattr(p, 'treatment_start') and hasattr(p, 'arrival_time') and p.treatment_start > 0]
        
        four_hour_compliant = sum(1 for p in completed_patients if hasattr(p, 'arrival_time') and hasattr(p, 'departure_time') and (p.departure_time - p.arrival_time) <= 240)
        
        metrics = {
            # ATTENDANCE SUMMARY
            'total_attendances': len(completed_patients),
            'active_patients_in_system': len(self.active_records),
            
            # OFFICIAL NHS A&E QUALITY INDICATORS
            '1_left_before_being_seen_rate_pct': (self.counters['lwbs_count'] / len(completed_patients)) * 100 if completed_patients else 0,
            '2_reattendance_rate_pct': (self.counters['reattendance_count'] / len(completed_patients)) * 100 if completed_patients else 0,
            '3_time_to_initial_assessment_avg_minutes': np.mean(initial_assessment_times) if initial_assessment_times else 0,
            '4_time_to_treatment_avg_minutes': np.mean(treatment_times) if treatment_times else 0,
            '5_total_time_in_ae_avg_minutes': np.mean(total_times) if total_times else 0,
            
            # NHS 4-HOUR STANDARD
            '4hour_standard_compliance_pct': (four_hour_compliant / len(completed_patients)) * 100 if completed_patients else 0,
            'attendances_within_4hours': four_hour_compliant,
            'attendances_over_4hours': len(completed_patients) - four_hour_compliant,
            '95pct_target_achieved': (four_hour_compliant / len(completed_patients)) >= 0.95 if completed_patients else False,
            '76pct_interim_target_achieved': (four_hour_compliant / len(completed_patients)) >= 0.76 if completed_patients else False,
            
            # ADDITIONAL PERFORMANCE METRICS
            'median_total_time_minutes': np.median(total_times) if total_times else 0,
            '95th_percentile_time_minutes': np.percentile(total_times, 95) if total_times else 0,
            'admission_rate_pct': (self.counters['admissions_count'] / len(completed_patients)) * 100 if completed_patients else 0,
            
            # TRIAGE BREAKDOWN
            'triage_category_distribution': self._get_triage_distribution(completed_patients),
            
            # DETAILED BREAKDOWNS
            'age_group_analysis': self._get_age_group_analysis(completed_patients),
            'gender_analysis': self._get_gender_analysis(completed_patients),
            'time_distribution_analysis': self._get_time_distribution_analysis(total_times),
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
        """Analyze performance by age groups"""
        age_groups = {
            '0-17': [p for p in patients if p.age < 18],
            '18-64': [p for p in patients if 18 <= p.age < 65],
            '65+': [p for p in patients if p.age >= 65]
        }
        
        analysis = {}
        for group, group_patients in age_groups.items():
            if group_patients:
                times = [p.departure_time - p.arrival_time for p in group_patients if hasattr(p, 'arrival_time') and hasattr(p, 'departure_time')]
                compliant = sum(1 for p in group_patients if hasattr(p, 'arrival_time') and hasattr(p, 'departure_time') and (p.departure_time - p.arrival_time) <= 240)
                analysis[group] = {
                    'count': len(group_patients),
                    'avg_time_minutes': np.mean(times),
                    '4hour_compliance_pct': (compliant / len(group_patients)) * 100,
                    'admission_rate_pct': (sum(1 for p in group_patients if p.admitted) / len(group_patients)) * 100
                }
        
        return analysis
    
    def _get_gender_analysis(self, patients: List) -> Dict[str, Dict]:
        """Analyze performance by gender"""
        genders = defaultdict(list)
        for p in patients:
            genders[p.gender].append(p)
        
        analysis = {}
        for gender, gender_patients in genders.items():
            if gender_patients:
                times = [p.departure_time - p.arrival_time for p in gender_patients if hasattr(p, 'arrival_time') and hasattr(p, 'departure_time')]
                compliant = sum(1 for p in gender_patients if hasattr(p, 'arrival_time') and hasattr(p, 'departure_time') and (p.departure_time - p.arrival_time) <= 240)
                analysis[gender] = {
                    'count': len(gender_patients),
                    'avg_time_minutes': np.mean(times),
                    '4hour_compliance_pct': (compliant / len(gender_patients)) * 100,
                    'admission_rate_pct': (sum(1 for p in gender_patients if p.admitted) / len(gender_patients)) * 100
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
        """Convert a Patient to dictionary for export"""
        if not hasattr(record, 'Id'):
            return super()._record_to_dict(record)
        
        return {
            'patient_id': record.Id,
            'arrival_time': record.arrival_time,
            'age': record.age,
            'gender': record.gender,
            'triage_category': record.triage_category,
            'initial_assessment_start': record.initial_assessment_start,
            'treatment_start': record.treatment_start,
            'departure_time': record.departure_time,
            'total_time_minutes': record.departure_time - record.arrival_time if hasattr(record, 'arrival_time') and hasattr(record, 'departure_time') else 0,
            'time_to_assessment_minutes': record.initial_assessment_start - record.arrival_time if hasattr(record, 'initial_assessment_start') and hasattr(record, 'arrival_time') and record.initial_assessment_start > 0 else 0,
            'time_to_treatment_minutes': record.treatment_start - record.arrival_time if hasattr(record, 'treatment_start') and hasattr(record, 'arrival_time') and record.treatment_start > 0 else 0,
            'meets_4hour_standard': (record.departure_time - record.arrival_time) <= 240 if hasattr(record, 'arrival_time') and hasattr(record, 'departure_time') else False,
            'is_reattendance': getattr(record, 'is_reattendance', False),
            'admitted': record.admitted,
            'disposal': record.disposal,
            'presenting_complaint': record.presenting_complaint,
            'left_without_being_seen': record.left_without_being_seen
        }