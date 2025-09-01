"""Metrics Service for Manchester Triage System

This module provides comprehensive metrics analysis capabilities for triage operations,
including statistical analysis, resource utilization tracking, and visualization data preparation.
"""

import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import Counter
import statistics

# Import metrics enums
from ..enum.metrics import (
    TriageCategory, MetricType, StatisticType, TimeInterval,
    ResourceType, PerformanceIndicator, FlowchartReason,
    ReportType, VisualizationType, AlertLevel, DataQuality
)


@dataclass
class PatientMetrics:
    """Represents metrics for a single patient"""
    patient_id: str
    arrival_time: datetime
    encounter_start_time: datetime
    wait_time_minutes: float
    triage_category: TriageCategory
    flowchart_reason: FlowchartReason
    processing_duration_ms: float


@dataclass
class SystemMetrics:
    """Represents overall system performance metrics"""
    total_patients: int
    avg_wait_time: float
    median_wait_time: float
    mode_wait_time: Optional[float]
    min_wait_time: float
    max_wait_time: float
    std_wait_time: float
    total_processing_time_ms: float
    avg_processing_time_ms: float
    resource_utilization: float
    peak_arrival_hour: int
    triage_category_distribution: Dict[TriageCategory, int]
    flowchart_usage: Dict[FlowchartReason, int]


class MetricsService:
    """Service for analyzing triage system metrics and generating insights
    
    This service processes telemetry data to provide comprehensive analytics including:
    - Statistical analysis of wait times
    - Resource utilization metrics
    - Patient arrival patterns
    - Histogram data for visualization
    """
    
    def __init__(self):
        """Initialize the metrics service"""
        self._patient_metrics: List[PatientMetrics] = []
        self._system_start_time: Optional[datetime] = None
        self._system_end_time: Optional[datetime] = None
    
    def load_telemetry_data(self, telemetry_file_path: str) -> None:
        """Load telemetry data from JSON file and extract patient metrics
        
        Args:
            telemetry_file_path: Path to the telemetry JSON file
        """
        with open(telemetry_file_path, 'r', encoding='utf-8') as f:
            telemetry_data = json.load(f)
        
        self._extract_patient_metrics(telemetry_data)
    
    def add_telemetry_data(self, telemetry_data: Dict[str, Any]) -> None:
        """Add telemetry data directly from a telemetry service
        
        Args:
            telemetry_data: Telemetry data dictionary
        """
        self._extract_patient_metrics(telemetry_data)
    
    def _extract_patient_metrics(self, telemetry_data: Dict[str, Any]) -> None:
        """Extract patient metrics from telemetry data
        
        Args:
            telemetry_data: Raw telemetry data
        """
        steps = telemetry_data.get('telemetry_steps', [])
        
        # Group steps by patient
        patient_sessions = {}
        for step in steps:
            patient_id = step.get('patient_id')
            if patient_id:
                if patient_id not in patient_sessions:
                    patient_sessions[patient_id] = []
                patient_sessions[patient_id].append(step)
        
        # Process each patient session
        for patient_id, patient_steps in patient_sessions.items():
            metrics = self._calculate_patient_metrics(patient_id, patient_steps)
            if metrics:
                self._patient_metrics.append(metrics)
        
        # Update system time bounds
        if steps:
            session_start = datetime.fromisoformat(telemetry_data['metadata']['session_start_time'])
            if self._system_start_time is None or session_start < self._system_start_time:
                self._system_start_time = session_start
            
            last_step_time = datetime.fromisoformat(steps[-1]['timestamp'])
            if self._system_end_time is None or last_step_time > self._system_end_time:
                self._system_end_time = last_step_time
    
    def _calculate_patient_metrics(self, patient_id: str, steps: List[Dict[str, Any]]) -> Optional[PatientMetrics]:
        """Calculate metrics for a single patient
        
        Args:
            patient_id: Patient identifier
            steps: List of telemetry steps for this patient
            
        Returns:
            PatientMetrics object or None if insufficient data
        """
        # Find session start and end
        session_start = None
        session_end = None
        triage_result = None
        flowchart_reason = None
        total_duration = 0
        
        for step in steps:
            step_time = datetime.fromisoformat(step['timestamp'])
            
            if step['step_name'] == 'patient_session_start':
                session_start = step_time
                flowchart_reason = step['data'].get('flowchart_reason')
            elif step['step_name'] == 'patient_session_end':
                session_end = step_time
                triage_result = step['data'].get('triage_result', {})
            
            if step.get('duration_ms'):
                total_duration += step['duration_ms']
        
        if not all([session_start, session_end, triage_result, flowchart_reason]):
            return None
        
        # Calculate wait time (assuming encounter starts immediately after triage)
        wait_time_raw = triage_result.get('wait_time', 0)
        if isinstance(wait_time_raw, str):
            # Extract numeric value from strings like '60 min'
            import re
            match = re.search(r'(\d+(?:\.\d+)?)', str(wait_time_raw))
            wait_time_minutes = float(match.group(1)) if match else 0.0
        else:
            wait_time_minutes = float(wait_time_raw)
        encounter_start_time = session_end + timedelta(minutes=wait_time_minutes)
        
        # Convert string values to enums
        try:
            triage_category = TriageCategory(triage_result.get('triage_category', 'UNKNOWN'))
        except ValueError:
            triage_category = TriageCategory.UNKNOWN
        
        try:
            flowchart_reason_enum = FlowchartReason(flowchart_reason)
        except ValueError:
            flowchart_reason_enum = FlowchartReason.OTHER
        
        return PatientMetrics(
            patient_id=patient_id,
            arrival_time=session_start,
            encounter_start_time=encounter_start_time,
            wait_time_minutes=wait_time_minutes,
            triage_category=triage_category,
            flowchart_reason=flowchart_reason_enum,
            processing_duration_ms=total_duration
        )
    
    def calculate_wait_time_statistics(self) -> Dict[str, float]:
        """Calculate statistical measures for wait times
        
        Returns:
            Dictionary containing mean, median, mode, min, max, and std deviation
        """
        if not self._patient_metrics:
            return {}
        
        wait_times = [p.wait_time_minutes for p in self._patient_metrics]
        
        # Calculate mode (most common wait time)
        mode_wait_time = None
        try:
            mode_wait_time = statistics.mode(wait_times)
        except statistics.StatisticsError:
            # No unique mode, use most frequent rounded value
            rounded_times = [round(wt) for wt in wait_times]
            if rounded_times:
                mode_wait_time = statistics.mode(rounded_times)
        
        return {
            'mean': np.mean(wait_times),
            'median': np.median(wait_times),
            'mode': mode_wait_time,
            'min': np.min(wait_times),
            'max': np.max(wait_times),
            'std': np.std(wait_times),
            'count': len(wait_times)
        }
    
    def calculate_resource_utilization(self) -> Dict[str, float]:
        """Calculate resource utilization metrics
        
        Returns:
            Dictionary containing utilization percentages and throughput metrics
        """
        if not self._patient_metrics or not self._system_start_time or not self._system_end_time:
            return {}
        
        total_system_time = (self._system_end_time - self._system_start_time).total_seconds()
        total_processing_time = sum(p.processing_duration_ms for p in self._patient_metrics) / 1000
        
        # Calculate utilization (assuming single resource/server)
        utilization = (total_processing_time / total_system_time) * 100 if total_system_time > 0 else 0
        
        # Calculate throughput
        patients_per_hour = len(self._patient_metrics) / (total_system_time / 3600) if total_system_time > 0 else 0
        
        return {
            'utilization_percentage': min(utilization, 100),  # Cap at 100%
            'total_system_time_seconds': total_system_time,
            'total_processing_time_seconds': total_processing_time,
            'patients_per_hour': patients_per_hour,
            'avg_processing_time_seconds': total_processing_time / len(self._patient_metrics) if self._patient_metrics else 0
        }
    
    def generate_arrival_curve_data(self, interval: TimeInterval = TimeInterval.HOUR) -> Dict[str, List]:
        """Generate patient arrival curve data
        
        Args:
            interval: Time interval for grouping arrivals (default: 1 hour)
            
        Returns:
            Dictionary with time intervals and arrival/encounter counts
        """
        if not self._patient_metrics:
            return {'time_intervals': [], 'arrivals': [], 'encounters': []}
        
        # Create time intervals
        start_time = min(p.arrival_time for p in self._patient_metrics)
        end_time = max(p.encounter_start_time for p in self._patient_metrics)
        
        intervals = []
        current_time = start_time
        while current_time <= end_time:
            intervals.append(current_time)
            current_time += timedelta(minutes=interval.minutes)
        
        # Count arrivals and encounters per interval
        arrival_counts = [0] * len(intervals)
        encounter_counts = [0] * len(intervals)
        
        for patient in self._patient_metrics:
            # Find arrival interval
            for i, interval_start in enumerate(intervals[:-1]):
                interval_end = intervals[i + 1]
                if interval_start <= patient.arrival_time < interval_end:
                    arrival_counts[i] += 1
                    break
            
            # Find encounter interval
            for i, interval_start in enumerate(intervals[:-1]):
                interval_end = intervals[i + 1]
                if interval_start <= patient.encounter_start_time < interval_end:
                    encounter_counts[i] += 1
                    break
        
        return {
            'time_intervals': [t.isoformat() for t in intervals[:-1]],
            'arrivals': arrival_counts[:-1],
            'encounters': encounter_counts[:-1]
        }
    
    def generate_wait_time_histogram_data(self, bins: int = 20) -> Dict[str, Any]:
        """Generate histogram data for wait times with arrival and encounter times
        
        Args:
            bins: Number of histogram bins
            
        Returns:
            Dictionary containing histogram data and patient timing information
        """
        if not self._patient_metrics:
            return {}
        
        wait_times = [p.wait_time_minutes for p in self._patient_metrics]
        
        # Create histogram
        hist_counts, bin_edges = np.histogram(wait_times, bins=bins)
        
        # Prepare patient timing data
        patient_data = []
        for patient in self._patient_metrics:
            patient_data.append({
                'patient_id': patient.patient_id,
                'arrival_time': patient.arrival_time.isoformat(),
                'encounter_start_time': patient.encounter_start_time.isoformat(),
                'wait_time_minutes': patient.wait_time_minutes,
                'triage_category': patient.triage_category.value,
                'flowchart_reason': patient.flowchart_reason.value
            })
        
        return {
            'histogram': {
                'counts': hist_counts.tolist(),
                'bin_edges': bin_edges.tolist(),
                'bin_centers': [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(bin_edges)-1)]
            },
            'patient_data': patient_data,
            'statistics': self.calculate_wait_time_statistics()
        }
    
    def generate_system_metrics(self) -> SystemMetrics:
        """Generate comprehensive system metrics
        
        Returns:
            SystemMetrics object with all calculated metrics
        """
        if not self._patient_metrics:
            return SystemMetrics(
                total_patients=0, avg_wait_time=0, median_wait_time=0, mode_wait_time=None,
                min_wait_time=0, max_wait_time=0, std_wait_time=0, total_processing_time_ms=0,
                avg_processing_time_ms=0, resource_utilization=0, peak_arrival_hour=0,
                triage_category_distribution={}, flowchart_usage={}
            )
        
        wait_stats = self.calculate_wait_time_statistics()
        resource_stats = self.calculate_resource_utilization()
        
        # Calculate peak arrival hour
        arrival_hours = [p.arrival_time.hour for p in self._patient_metrics]
        peak_hour = Counter(arrival_hours).most_common(1)[0][0] if arrival_hours else 0
        
        # Calculate distributions
        triage_dist = Counter(p.triage_category for p in self._patient_metrics)
        flowchart_dist = Counter(p.flowchart_reason for p in self._patient_metrics)
        
        return SystemMetrics(
            total_patients=len(self._patient_metrics),
            avg_wait_time=wait_stats.get('mean', 0),
            median_wait_time=wait_stats.get('median', 0),
            mode_wait_time=wait_stats.get('mode'),
            min_wait_time=wait_stats.get('min', 0),
            max_wait_time=wait_stats.get('max', 0),
            std_wait_time=wait_stats.get('std', 0),
            total_processing_time_ms=sum(p.processing_duration_ms for p in self._patient_metrics),
            avg_processing_time_ms=np.mean([p.processing_duration_ms for p in self._patient_metrics]),
            resource_utilization=resource_stats.get('utilization_percentage', 0),
            peak_arrival_hour=peak_hour,
            triage_category_distribution=triage_dist,
            flowchart_usage=flowchart_dist
        )
    
    def export_metrics_report(self, output_path: str, filename: str = None) -> str:
        """Export comprehensive metrics report to JSON file
        
        Args:
            output_path: Directory path for the report
            filename: Optional filename (defaults to timestamp-based name)
            
        Returns:
            Full path to the created report file
        """
        import os
        
        # Create output directory if it doesn't exist
        os.makedirs(output_path, exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_report_{timestamp}.json"
        
        if not filename.endswith('.json'):
            filename += '.json'
        
        full_path = os.path.join(output_path, filename)
        
        # Generate comprehensive report
        system_metrics = self.generate_system_metrics()
        wait_time_histogram = self.generate_wait_time_histogram_data()
        arrival_curve = self.generate_arrival_curve_data()
        resource_utilization = self.calculate_resource_utilization()
        
        report = {
            'metadata': {
                'report_timestamp': datetime.now().isoformat(),
                'analysis_period': {
                    'start': self._system_start_time.isoformat() if self._system_start_time else None,
                    'end': self._system_end_time.isoformat() if self._system_end_time else None
                },
                'total_patients_analyzed': len(self._patient_metrics)
            },
            'system_metrics': {
                'total_patients': system_metrics.total_patients,
                'wait_time_statistics': {
                    'mean_minutes': system_metrics.avg_wait_time,
                    'median_minutes': system_metrics.median_wait_time,
                    'mode_minutes': system_metrics.mode_wait_time,
                    'min_minutes': system_metrics.min_wait_time,
                    'max_minutes': system_metrics.max_wait_time,
                    'std_deviation_minutes': system_metrics.std_wait_time
                },
                'resource_utilization': resource_utilization,
                'peak_arrival_hour': system_metrics.peak_arrival_hour,
                'triage_category_distribution': {k.value: v for k, v in system_metrics.triage_category_distribution.items()},
                'flowchart_usage': {k.value: v for k, v in system_metrics.flowchart_usage.items()}
            },
            'wait_time_histogram': wait_time_histogram,
            'arrival_curve': arrival_curve
        }
        
        # Write report to file
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return full_path
    
    def update_from_telemetry_service(self, telemetry_service) -> None:
        """Update metrics with data from a telemetry service instance
        
        Args:
            telemetry_service: TelemetryService instance to extract data from
        """
        telemetry_data = {
            'metadata': {
                'session_start_time': telemetry_service._session_start_time.isoformat(),
                'total_steps': len(telemetry_service._steps)
            },
            'telemetry_steps': telemetry_service.get_telemetry_data()
        }
        
        # Clear previous metrics and add updated data
        self.clear_data()
        self.add_telemetry_data(telemetry_data)
    
    def get_metrics_summary(self) -> dict:
        """Get current metrics summary
        
        Returns:
            Dictionary containing current system metrics
        """
        system_metrics = self.generate_system_metrics()
        
        return {
            'total_patients': system_metrics.total_patients,
            'avg_wait_time': system_metrics.avg_wait_time,
            'median_wait_time': system_metrics.median_wait_time,
            'resource_utilization': system_metrics.resource_utilization,
            'peak_arrival_hour': system_metrics.peak_arrival_hour,
            'triage_distribution': {k.value: v for k, v in system_metrics.triage_category_distribution.items()},
            'flowchart_usage': {k.value: v for k, v in system_metrics.flowchart_usage.items()}
        }
    
    def clear_data(self) -> None:
        """Clear all collected metrics data"""
        self._patient_metrics.clear()
        self._system_start_time = None
        self._system_end_time = None