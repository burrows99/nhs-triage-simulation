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
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
from .plotting_service import PlottingService

# Import centralized logger
from src.logger import logger


@dataclass
class PatientRecord:
    """Official NHS patient record for A&E Quality Indicators tracking"""
    patient_id: str
    arrival_time: float
    age: int = 30
    gender: str = "Unknown"
    triage_category: str = ""
    
    # Official NHS timestamps for quality indicators
    initial_assessment_start: float = 0  # Time to initial assessment
    treatment_start: float = 0           # Time to treatment  
    departure_time: float = 0            # Total time in A&E
    
    # Status flags for NHS indicators
    left_without_being_seen: bool = False
    is_reattendance: bool = False
    admitted: bool = False
    
    # Additional clinical data
    presenting_complaint: str = ""
    disposal: str = ""  # discharged/admitted/transferred
    
    def total_time_in_ae(self) -> float:
        """Total time in A&E (minutes) - Official NHS Quality Indicator"""
        if self.departure_time == 0:
            return 0
        return self.departure_time - self.arrival_time
    
    def time_to_initial_assessment(self) -> float:
        """Time to initial assessment (minutes) - Official NHS Quality Indicator"""
        if self.initial_assessment_start == 0:
            return 0
        return self.initial_assessment_start - self.arrival_time
    
    def time_to_treatment(self) -> float:
        """Time to treatment (minutes) - Official NHS Quality Indicator"""
        if self.treatment_start == 0:
            return 0
        return self.treatment_start - self.arrival_time
    
    def meets_4hour_standard(self) -> bool:
        """Meets NHS 4-hour standard (95% target)"""
        return self.total_time_in_ae() <= 240


class NHSMetricsService:
    """
    Official NHS A&E Quality Indicators Service
    
    Provides a clean interface for tracking and calculating NHS A&E Quality Indicators
    from patient data. Can be integrated into any hospital simulation or real system.
    """
    
    def __init__(self, reattendance_window_hours: int = 72):
        """
        Initialize NHS Metrics Service
        
        Args:
            reattendance_window_hours: Time window for re-attendance tracking (default: 72 hours)
        """
        # Patient data storage
        self.patients: List[PatientRecord] = []
        self.active_patients: Dict[str, PatientRecord] = {}
        
        # Re-attendance tracking
        self.reattendance_window = reattendance_window_hours
        self.patient_history: Dict[str, List[float]] = defaultdict(list)
        
        # Real-time counters
        self.total_attendances = 0
        self.lwbs_count = 0
        self.reattendance_count = 0
        self.admissions_count = 0
        
        # Initialize plotting service
        self.plotting_service = PlottingService()
    
    def add_patient_arrival(self, patient_id: str, arrival_time: float, 
                           age: int = 30, gender: str = "Unknown", 
                           presenting_complaint: str = "") -> PatientRecord:
        """
        Record patient arrival and return patient record
        
        Args:
            patient_id: Unique patient identifier
            arrival_time: Arrival time in minutes from simulation start
            age: Patient age
            gender: Patient gender
            presenting_complaint: Chief complaint or reason for visit
            
        Returns:
            PatientRecord object for tracking patient journey
        """
        # Check for re-attendance
        is_reattendance = self._check_reattendance(patient_id, arrival_time)
        
        patient = PatientRecord(
            patient_id=patient_id,
            arrival_time=arrival_time,
            age=age,
            gender=gender,
            is_reattendance=is_reattendance,
            presenting_complaint=presenting_complaint
        )
        
        # Store patient
        self.active_patients[patient_id] = patient
        self.total_attendances += 1
        
        if is_reattendance:
            self.reattendance_count += 1
        
        # Track arrival time for re-attendance checking
        self.patient_history[patient_id].append(arrival_time)
        
        return patient
    
    def record_initial_assessment(self, patient_id: str, assessment_time: float):
        """Record start of initial assessment (triage/nursing assessment)"""
        if patient_id in self.active_patients:
            self.active_patients[patient_id].initial_assessment_start = assessment_time
    
    def record_treatment_start(self, patient_id: str, treatment_time: float):
        """Record start of treatment (usually doctor consultation)"""
        if patient_id in self.active_patients:
            self.active_patients[patient_id].treatment_start = treatment_time
    
    def record_triage_category(self, patient_id: str, category: str):
        """Record Manchester Triage System category"""
        if patient_id in self.active_patients:
            self.active_patients[patient_id].triage_category = category
    
    def record_patient_departure(self, patient_id: str, departure_time: float, 
                               disposal: str = "discharged", admitted: bool = False,
                               left_without_being_seen: bool = False):
        """
        Record patient departure with disposal information
        
        Args:
            patient_id: Patient identifier
            departure_time: Time of departure in minutes
            disposal: Type of discharge (discharged/admitted/transferred)
            admitted: Whether patient was admitted
            left_without_being_seen: Whether patient left before being seen
        """
        if patient_id not in self.active_patients:
            return
        
        patient = self.active_patients[patient_id]
        patient.departure_time = departure_time
        patient.disposal = disposal
        patient.admitted = admitted
        patient.left_without_being_seen = left_without_being_seen
        
        if admitted:
            self.admissions_count += 1
        
        if left_without_being_seen:
            self.lwbs_count += 1
        
        # Move to completed patients
        self.patients.append(patient)
        del self.active_patients[patient_id]
    
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
    
    def calculate_nhs_metrics(self) -> Dict:
        """
        Calculate official NHS A&E Quality Indicators
        
        Returns:
            Dictionary containing all official NHS metrics and performance indicators
        """
        completed_patients = [p for p in self.patients if p.departure_time > 0]
        
        if not completed_patients:
            return {
                'error': 'No completed patients to analyze',
                'total_attendances': self.total_attendances,
                'active_patients': len(self.active_patients)
            }
        
        # Calculate official NHS metrics
        total_times = [p.total_time_in_ae() for p in completed_patients]
        initial_assessment_times = [p.time_to_initial_assessment() for p in completed_patients 
                                  if p.initial_assessment_start > 0]
        treatment_times = [p.time_to_treatment() for p in completed_patients 
                          if p.treatment_start > 0]
        
        four_hour_compliant = sum(1 for p in completed_patients if p.meets_4hour_standard())
        
        metrics = {
            # ATTENDANCE SUMMARY
            'total_attendances': len(completed_patients),
            'active_patients_in_system': len(self.active_patients),
            
            # OFFICIAL NHS A&E QUALITY INDICATORS
            '1_left_before_being_seen_rate_pct': (self.lwbs_count / len(completed_patients)) * 100 if completed_patients else 0,
            '2_reattendance_rate_pct': (self.reattendance_count / len(completed_patients)) * 100 if completed_patients else 0,
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
            'admission_rate_pct': (self.admissions_count / len(completed_patients)) * 100 if completed_patients else 0,
            
            # TRIAGE BREAKDOWN
            'triage_category_distribution': self._get_triage_distribution(completed_patients),
            
            # DETAILED BREAKDOWNS
            'age_group_analysis': self._get_age_group_analysis(completed_patients),
            'gender_analysis': self._get_gender_analysis(completed_patients),
            'time_distribution_analysis': self._get_time_distribution_analysis(total_times),
        }
        
        return metrics
    
    def _get_triage_distribution(self, patients: List[PatientRecord]) -> Dict[str, int]:
        """Get distribution of triage categories"""
        categories = [p.triage_category for p in patients if p.triage_category]
        return dict(pd.Series(categories).value_counts()) if categories else {}
    
    def _get_age_group_analysis(self, patients: List[PatientRecord]) -> Dict[str, Dict]:
        """Analyze performance by age groups"""
        age_groups = {
            '0-17': [p for p in patients if p.age < 18],
            '18-64': [p for p in patients if 18 <= p.age < 65],
            '65+': [p for p in patients if p.age >= 65]
        }
        
        analysis = {}
        for group, group_patients in age_groups.items():
            if group_patients:
                times = [p.total_time_in_ae() for p in group_patients]
                compliant = sum(1 for p in group_patients if p.meets_4hour_standard())
                analysis[group] = {
                    'count': len(group_patients),
                    'avg_time_minutes': np.mean(times),
                    '4hour_compliance_pct': (compliant / len(group_patients)) * 100,
                    'admission_rate_pct': (sum(1 for p in group_patients if p.admitted) / len(group_patients)) * 100
                }
        
        return analysis
    
    def _get_gender_analysis(self, patients: List[PatientRecord]) -> Dict[str, Dict]:
        """Analyze performance by gender"""
        genders = defaultdict(list)
        for p in patients:
            genders[p.gender].append(p)
        
        analysis = {}
        for gender, gender_patients in genders.items():
            if gender_patients:
                times = [p.total_time_in_ae() for p in gender_patients]
                compliant = sum(1 for p in gender_patients if p.meets_4hour_standard())
                analysis[gender] = {
                    'count': len(gender_patients),
                    'avg_time_minutes': np.mean(times),
                    '4hour_compliance_pct': (compliant / len(gender_patients)) * 100,
                    'admission_rate_pct': (sum(1 for p in gender_patients if p.admitted) / len(gender_patients)) * 100
                }
        
        return analysis
    
    def _get_time_distribution_analysis(self, times: List[float]) -> Dict[str, float]:
        """Analyze time distribution statistics"""
        if not times:
            return {}
        
        return {
            'min_time_minutes': np.min(times),
            'max_time_minutes': np.max(times),
            'std_dev_minutes': np.std(times),
            '25th_percentile_minutes': np.percentile(times, 25),
            '75th_percentile_minutes': np.percentile(times, 75),
            '90th_percentile_minutes': np.percentile(times, 90),
            '99th_percentile_minutes': np.percentile(times, 99)
        }
    
    def print_nhs_dashboard(self) -> Dict:
        """
        Print comprehensive NHS-style dashboard
        
        Returns:
            Dictionary containing all calculated metrics
        """
        metrics = self.calculate_nhs_metrics()
        
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
    
    def export_data(self, json_filepath: str = None, csv_filepath: str = None):
        """
        Export NHS metrics and patient data
        
        Args:
            json_filepath: Path to export metrics as JSON
            csv_filepath: Path to export patient data as CSV
        """
        if json_filepath:
            metrics = self.calculate_nhs_metrics()
            with open(json_filepath, 'w') as f:
                json.dump(metrics, f, indent=2, default=str)
            logger.info(f"NHS metrics exported to {json_filepath}")
        
        if csv_filepath:
            if not self.patients:
                logger.info("No patient data to export")
                return
            
            data = []
            for p in self.patients:
                data.append({
                    'patient_id': p.patient_id,
                    'arrival_time': p.arrival_time,
                    'age': p.age,
                    'gender': p.gender,
                    'triage_category': p.triage_category,
                    'initial_assessment_start': p.initial_assessment_start,
                    'treatment_start': p.treatment_start,
                    'departure_time': p.departure_time,
                    'total_time_minutes': p.total_time_in_ae(),
                    'time_to_assessment_minutes': p.time_to_initial_assessment(),
                    'time_to_treatment_minutes': p.time_to_treatment(),
                    'meets_4hour_standard': p.meets_4hour_standard(),
                    'is_reattendance': p.is_reattendance,
                    'admitted': p.admitted,
                    'disposal': p.disposal,
                    'presenting_complaint': p.presenting_complaint,
                    'left_without_being_seen': p.left_without_being_seen
                })
            
            df = pd.DataFrame(data)
            df.to_csv(csv_filepath, index=False)
            logger.info(f"Patient data exported to {csv_filepath}")
    
    def plot_compliance_chart(self, save_path: Optional[str] = None):
        """Generate NHS 4-hour compliance chart.
        
        Args:
            save_path: Optional path to save the chart
        """
        metrics = self.calculate_nhs_metrics()
        return self.plotting_service.create_compliance_chart(metrics, save_path=save_path)
    
    def plot_triage_distribution(self, save_path: Optional[str] = None):
        """Generate triage category distribution chart.
        
        Args:
            save_path: Optional path to save the chart
        """
        # Get triage distribution data
        triage_counts = defaultdict(int)
        for patient in self.patients:
            if patient.triage_category:
                triage_counts[patient.triage_category] += 1
        
        return self.plotting_service.create_triage_distribution_chart(
            dict(triage_counts), save_path=save_path)
    
    def plot_time_distribution(self, save_path: Optional[str] = None):
        """Generate patient time distribution histogram.
        
        Args:
            save_path: Optional path to save the chart
        """
        times = [p.total_time_in_ae() for p in self.patients if p.total_time_in_ae() > 0]
        return self.plotting_service.create_time_distribution_chart(times, save_path=save_path)
    
    def plot_age_group_analysis(self, save_path: Optional[str] = None):
        """Generate age group analysis chart.
        
        Args:
            save_path: Optional path to save the chart
        """
        # Calculate age group data
        age_groups = {
            '0-17': {'patients': [], 'count': 0, 'avg_time_minutes': 0, '4hour_compliance_pct': 0},
            '18-64': {'patients': [], 'count': 0, 'avg_time_minutes': 0, '4hour_compliance_pct': 0},
            '65+': {'patients': [], 'count': 0, 'avg_time_minutes': 0, '4hour_compliance_pct': 0}
        }
        
        for patient in self.patients:
            if patient.age < 18:
                group = '0-17'
            elif patient.age < 65:
                group = '18-64'
            else:
                group = '65+'
            
            age_groups[group]['patients'].append(patient)
            age_groups[group]['count'] += 1
        
        # Calculate averages and compliance
        for group_data in age_groups.values():
            if group_data['count'] > 0:
                times = [p.total_time_in_ae() for p in group_data['patients']]
                group_data['avg_time_minutes'] = np.mean(times)
                compliant = sum(1 for p in group_data['patients'] if p.meets_4hour_standard())
                group_data['4hour_compliance_pct'] = (compliant / group_data['count']) * 100
        
        # Remove empty groups and format for plotting
        plot_data = {group: data for group, data in age_groups.items() if data['count'] > 0}
        
        return self.plotting_service.create_age_group_analysis_chart(plot_data, save_path=save_path)
    
    def plot_performance_dashboard(self, save_path: Optional[str] = None):
        """Generate comprehensive NHS performance dashboard.
        
        Args:
            save_path: Optional path to save the dashboard
        """
        metrics = self.calculate_nhs_metrics()
        
        # Prepare dashboard data
        dashboard_data = metrics.copy()
        
        # Add triage distribution
        triage_counts = defaultdict(int)
        for patient in self.patients:
            if patient.triage_category:
                triage_counts[patient.triage_category] += 1
        dashboard_data['triage_distribution'] = dict(triage_counts)
        
        # Add patient times
        dashboard_data['patient_times'] = [p.total_time_in_ae() for p in self.patients if p.total_time_in_ae() > 0]
        
        # Add age group data
        age_groups = {
            '0-17': {'patients': [], 'count': 0},
            '18-64': {'patients': [], 'count': 0},
            '65+': {'patients': [], 'count': 0}
        }
        
        for patient in self.patients:
            if patient.age < 18:
                group = '0-17'
            elif patient.age < 65:
                group = '18-64'
            else:
                group = '65+'
            
            age_groups[group]['patients'].append(patient)
            age_groups[group]['count'] += 1
        
        dashboard_data['age_groups'] = {group: data for group, data in age_groups.items() if data['count'] > 0}
        
        return self.plotting_service.create_performance_dashboard(dashboard_data, save_path=save_path)
    
    def generate_all_plots(self, output_dir: str = "./output/nhs_metrics/plots"):
        """Generate all available NHS metrics plots.
        
        Args:
            output_dir: Directory to save all plots
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        plots_generated = []
        
        try:
            # Generate individual plots
            self.plot_compliance_chart(f"{output_dir}/compliance_chart.png")
            plots_generated.append("compliance_chart.png")
            
            self.plot_triage_distribution(f"{output_dir}/triage_distribution.png")
            plots_generated.append("triage_distribution.png")
            
            self.plot_time_distribution(f"{output_dir}/time_distribution.png")
            plots_generated.append("time_distribution.png")
            
            if len(self.patients) > 0:  # Only if we have patient data
                self.plot_age_group_analysis(f"{output_dir}/age_group_analysis.png")
                plots_generated.append("age_group_analysis.png")
            
            # Generate comprehensive dashboard
            self.plot_performance_dashboard(f"{output_dir}/performance_dashboard.png")
            plots_generated.append("performance_dashboard.png")
            
            logger.info(f"Generated {len(plots_generated)} NHS metrics plots in {output_dir}:")
            for plot in plots_generated:
                logger.info(f"  - {plot}")
                
        except Exception as e:
            logger.error(f"Error generating plots: {e}")
        
        return plots_generated
    
    def close_plots(self):
        """Close all matplotlib figures to free memory."""
        self.plotting_service.close_all_figures()
    
    def reset(self):
        """Reset all metrics and patient data"""
        self.patients.clear()
        self.active_patients.clear()
        self.patient_history.clear()
        self.total_attendances = 0
        self.lwbs_count = 0
        self.reattendance_count = 0
        self.admissions_count = 0
    
    def get_patient_count(self) -> Dict[str, int]:
        """Get current patient counts"""
        return {
            'completed_patients': len(self.patients),
            'active_patients': len(self.active_patients),
            'total_attendances': self.total_attendances
        }