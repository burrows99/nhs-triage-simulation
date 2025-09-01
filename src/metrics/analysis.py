import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from .metrics_collector import SimulationMetrics
import json
from datetime import datetime


@dataclass
class StatisticalReport:
    """Comprehensive statistical report for ED simulation"""
    
    # Report metadata
    report_id: str
    generated_at: datetime
    simulation_duration: float
    
    # Descriptive statistics
    patient_flow_stats: Dict[str, Any]
    wait_time_stats: Dict[str, Any]
    service_time_stats: Dict[str, Any]
    resource_utilization_stats: Dict[str, Any]
    
    # Performance analysis
    performance_indicators: Dict[str, float]
    target_compliance: Dict[str, float]
    efficiency_metrics: Dict[str, float]
    
    # Statistical tests
    normality_tests: Dict[str, Dict[str, float]]
    correlation_analysis: Dict[str, float]
    
    # Comparative analysis
    benchmark_comparison: Optional[Dict[str, Any]] = None
    trend_analysis: Optional[Dict[str, Any]] = None
    
    # Recommendations
    recommendations: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for serialization"""
        return {
            'report_metadata': {
                'report_id': self.report_id,
                'generated_at': self.generated_at.isoformat(),
                'simulation_duration': self.simulation_duration
            },
            'descriptive_statistics': {
                'patient_flow': self.patient_flow_stats,
                'wait_times': self.wait_time_stats,
                'service_times': self.service_time_stats,
                'resource_utilization': self.resource_utilization_stats
            },
            'performance_analysis': {
                'performance_indicators': self.performance_indicators,
                'target_compliance': self.target_compliance,
                'efficiency_metrics': self.efficiency_metrics
            },
            'statistical_analysis': {
                'normality_tests': self.normality_tests,
                'correlation_analysis': self.correlation_analysis
            },
            'comparative_analysis': {
                'benchmark_comparison': self.benchmark_comparison,
                'trend_analysis': self.trend_analysis
            },
            'recommendations': self.recommendations or []
        }
        
    def save_to_file(self, filename: str):
        """Save report to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)


class MetricsAnalyzer:
    """Advanced statistical analysis for ED simulation metrics"""
    
    def __init__(self):
        # General Healthcare benchmarks and targets
        self.healthcare_targets = {
            'wait_time_targets': {
                'IMMEDIATE': 0,        # Emergency - immediate escalation
                'VERY_URGENT': 30,     # Serious acute - 30 minutes
                'URGENT': 120,         # Same-day attention - 2 hours
                'STANDARD': 480,       # Routine problems - 8 hours (same day)
                'NON_URGENT': 1440     # Preventive care - 24 hours (next available)
            },
            'performance_targets': {
                'overall_compliance': 95.0,  # 95% of patients seen within target
                'throughput_target': 15.0,   # Patients per hour (lower for general practice)
                'resource_utilization_target': 75.0,  # 75% utilization (more realistic for mixed care)
                'lwbs_rate_target': 2.0,     # <2% LWBS rate (lower for scheduled care)
                'admission_rate_target': 5.0  # 5% admission rate (much lower for general practice)
            },
            'priority_distribution_targets': {
                'IMMEDIATE': (1, 2),      # 1-2% true emergencies
                'VERY_URGENT': (3, 5),    # 3-5% serious acute conditions
                'URGENT': (10, 15),       # 10-15% same-day problems
                'STANDARD': (25, 30),     # 25-30% routine problems
                'NON_URGENT': (50, 60)    # 50-60% preventive/wellness care
            }
        }
        
        # Industry benchmarks
        self.industry_benchmarks = {
            'average_wait_time': 45.0,      # minutes
            'average_los': 180.0,           # minutes
            'resource_efficiency': 75.0,    # percentage
            'patient_satisfaction': 80.0    # percentage
        }
        
    def generate_comprehensive_report(self, metrics: SimulationMetrics, 
                                    report_id: str = None) -> StatisticalReport:
        """Generate comprehensive statistical report"""
        
        if not report_id:
            report_id = f"report_{int(datetime.now().timestamp())}"
            
        # Perform all analyses
        patient_flow_stats = self._analyze_patient_flow(metrics)
        wait_time_stats = self._analyze_wait_times(metrics)
        service_time_stats = self._analyze_service_times(metrics)
        resource_stats = self._analyze_resource_utilization(metrics)
        
        performance_indicators = self._calculate_performance_indicators(metrics)
        target_compliance = self._analyze_target_compliance(metrics)
        efficiency_metrics = self._calculate_efficiency_metrics(metrics)
        
        normality_tests = self._perform_normality_tests(metrics)
        correlation_analysis = self._perform_correlation_analysis(metrics)
        
        recommendations = self._generate_recommendations(metrics, performance_indicators, target_compliance)
        
        return StatisticalReport(
            report_id=report_id,
            generated_at=datetime.now(),
            simulation_duration=metrics.duration,
            patient_flow_stats=patient_flow_stats,
            wait_time_stats=wait_time_stats,
            service_time_stats=service_time_stats,
            resource_utilization_stats=resource_stats,
            performance_indicators=performance_indicators,
            target_compliance=target_compliance,
            efficiency_metrics=efficiency_metrics,
            normality_tests=normality_tests,
            correlation_analysis=correlation_analysis,
            recommendations=recommendations
        )
        
    def _analyze_patient_flow(self, metrics: SimulationMetrics) -> Dict[str, Any]:
        """Analyze patient flow patterns"""
        
        total_patients = metrics.total_arrivals
        
        return {
            'total_arrivals': metrics.total_arrivals,
            'total_departures': metrics.total_departures,
            'total_admissions': metrics.total_admissions,
            'total_discharges': metrics.total_discharges,
            'total_lwbs': metrics.total_lwbs,
            'completion_rate': (metrics.total_departures / metrics.total_arrivals * 100) if metrics.total_arrivals > 0 else 0,
            'admission_rate': (metrics.total_admissions / metrics.total_departures * 100) if metrics.total_departures > 0 else 0,
            'discharge_rate': (metrics.total_discharges / metrics.total_departures * 100) if metrics.total_departures > 0 else 0,
            'lwbs_rate': (metrics.total_lwbs / metrics.total_arrivals * 100) if metrics.total_arrivals > 0 else 0,
            'throughput_per_hour': metrics.throughput_per_hour,
            'priority_distribution': dict(metrics.priority_distribution),
            'priority_percentages': {
                priority: (count / total_patients * 100) if total_patients > 0 else 0
                for priority, count in metrics.priority_distribution.items()
            }
        }
        
    def _analyze_wait_times(self, metrics: SimulationMetrics) -> Dict[str, Any]:
        """Analyze wait time patterns and statistics"""
        
        wait_time_analysis = {}
        
        # Overall wait time statistics
        all_wait_times = []
        for times in metrics.wait_times.values():
            all_wait_times.extend(times)
            
        if all_wait_times:
            wait_time_analysis['overall'] = self._calculate_descriptive_stats(all_wait_times)
            wait_time_analysis['overall']['percentiles'] = {
                'p50': float(np.percentile(all_wait_times, 50)),
                'p75': float(np.percentile(all_wait_times, 75)),
                'p90': float(np.percentile(all_wait_times, 90)),
                'p95': float(np.percentile(all_wait_times, 95)),
                'p99': float(np.percentile(all_wait_times, 99))
            }
            
        # Wait time statistics by priority
        wait_time_analysis['by_priority'] = {}
        for priority, times in metrics.wait_times.items():
            if times:
                wait_time_analysis['by_priority'][priority] = self._calculate_descriptive_stats(times)
                
                # Target compliance for this priority
                target_time = self.healthcare_targets['wait_time_targets'].get(priority, 1440)
                compliant_count = sum(1 for t in times if t <= target_time)
                compliance_rate = (compliant_count / len(times)) * 100
                
                wait_time_analysis['by_priority'][priority]['target_compliance'] = {
                    'target_time': target_time,
                    'compliance_rate': compliance_rate,
                    'breach_count': len(times) - compliant_count,
                    'breach_rate': 100 - compliance_rate
                }
                
        return wait_time_analysis
        
    def _analyze_service_times(self, metrics: SimulationMetrics) -> Dict[str, Any]:
        """Analyze service time patterns"""
        
        service_analysis = {}
        
        # Triage times
        if metrics.triage_times:
            service_analysis['triage'] = self._calculate_descriptive_stats(metrics.triage_times)
            
        # Consultation times
        if metrics.consultation_times:
            service_analysis['consultation'] = self._calculate_descriptive_stats(metrics.consultation_times)
            
        # Total system times
        if metrics.total_system_times:
            service_analysis['total_system'] = self._calculate_descriptive_stats(metrics.total_system_times)
            service_analysis['total_system']['percentiles'] = {
                'p50': float(np.percentile(metrics.total_system_times, 50)),
                'p75': float(np.percentile(metrics.total_system_times, 75)),
                'p90': float(np.percentile(metrics.total_system_times, 90)),
                'p95': float(np.percentile(metrics.total_system_times, 95))
            }
            
        return service_analysis
        
    def _analyze_resource_utilization(self, metrics: SimulationMetrics) -> Dict[str, Any]:
        """Analyze resource utilization patterns"""
        
        resource_analysis = {}
        
        resources = {
            'doctors': metrics.doctor_utilization,
            'nurses': metrics.nurse_utilization,
            'cubicles': metrics.cubicle_utilization,
            'beds': metrics.bed_utilization
        }
        
        for resource_name, utilization_data in resources.items():
            if utilization_data:
                resource_analysis[resource_name] = self._calculate_descriptive_stats(utilization_data)
                
                # Calculate efficiency metrics
                target_utilization = self.healthcare_targets['performance_targets']['resource_utilization_target']
                avg_utilization = np.mean(utilization_data)
                
                resource_analysis[resource_name]['efficiency'] = {
                    'target_utilization': target_utilization,
                    'actual_utilization': avg_utilization,
                    'efficiency_ratio': avg_utilization / target_utilization if target_utilization > 0 else 0,
                    'underutilization': max(0, target_utilization - avg_utilization),
                    'overutilization': max(0, avg_utilization - target_utilization)
                }
                
        return resource_analysis
        
    def _calculate_performance_indicators(self, metrics: SimulationMetrics) -> Dict[str, float]:
        """Calculate key performance indicators"""
        
        indicators = {}
        
        # Throughput indicators
        indicators['throughput_per_hour'] = metrics.throughput_per_hour
        indicators['average_length_of_stay'] = metrics.average_length_of_stay
        
        # Wait time indicators
        all_wait_times = []
        for times in metrics.wait_times.values():
            all_wait_times.extend(times)
            
        if all_wait_times:
            indicators['average_wait_time'] = float(np.mean(all_wait_times))
            indicators['median_wait_time'] = float(np.median(all_wait_times))
            indicators['p95_wait_time'] = float(np.percentile(all_wait_times, 95))
            
        # Resource efficiency
        indicators['resource_efficiency'] = metrics.resource_efficiency
        
        # Patient flow indicators
        if metrics.total_arrivals > 0:
            indicators['completion_rate'] = (metrics.total_departures / metrics.total_arrivals) * 100
            indicators['lwbs_rate'] = (metrics.total_lwbs / metrics.total_arrivals) * 100
            
        if metrics.total_departures > 0:
            indicators['admission_rate'] = (metrics.total_admissions / metrics.total_departures) * 100
            
        # Quality indicators
        if metrics.triage_confidence:
            indicators['average_triage_confidence'] = float(np.mean(metrics.triage_confidence))
            
        return indicators
        
    def _analyze_target_compliance(self, metrics: SimulationMetrics) -> Dict[str, float]:
        """Analyze compliance with General Healthcare targets"""
        
        compliance = {}
        
        # Wait time compliance by priority
        overall_compliant = 0
        overall_total = 0
        
        for priority, times in metrics.wait_times.items():
            if times:
                target_time = self.healthcare_targets['wait_time_targets'].get(priority, 1440)
                compliant_count = sum(1 for t in times if t <= target_time)
                compliance_rate = (compliant_count / len(times)) * 100
                
                compliance[f'{priority}_compliance'] = compliance_rate
                overall_compliant += compliant_count
                overall_total += len(times)
                
        # Overall compliance
        if overall_total > 0:
            compliance['overall_compliance'] = (overall_compliant / overall_total) * 100
            
        # Performance target compliance
        targets = self.healthcare_targets['performance_targets']
        
        if metrics.throughput_per_hour > 0:
            compliance['throughput_compliance'] = min(100, (metrics.throughput_per_hour / targets['throughput_target']) * 100)
            
        if metrics.resource_efficiency > 0:
            compliance['resource_efficiency_compliance'] = min(100, (metrics.resource_efficiency / targets['resource_utilization_target']) * 100)
            
        if metrics.total_arrivals > 0:
            lwbs_rate = (metrics.total_lwbs / metrics.total_arrivals) * 100
            compliance['lwbs_compliance'] = max(0, 100 - (lwbs_rate / targets['lwbs_rate_target']) * 100)
            
        # Priority distribution compliance
        priority_distribution = self._calculate_priority_distribution(metrics)
        for priority, (min_target, max_target) in self.healthcare_targets['priority_distribution_targets'].items():
            actual_percentage = priority_distribution.get(priority, 0)
            if min_target <= actual_percentage <= max_target:
                compliance[f'{priority}_distribution_compliance'] = 100.0
            else:
                # Calculate how far off from target range
                if actual_percentage < min_target:
                    deviation = min_target - actual_percentage
                else:
                    deviation = actual_percentage - max_target
                compliance[f'{priority}_distribution_compliance'] = max(0, 100 - (deviation * 2))  # 2% penalty per 1% deviation
            
        return compliance
    
    def _calculate_priority_distribution(self, metrics: SimulationMetrics) -> Dict[str, float]:
        """Calculate actual priority distribution percentages"""
        total_patients = metrics.total_arrivals
        if total_patients == 0:
            return {}
        
        distribution = {}
        priority_counts = getattr(metrics, 'priority_counts', {})
        
        for priority in ['IMMEDIATE', 'VERY_URGENT', 'URGENT', 'STANDARD', 'NON_URGENT']:
            count = priority_counts.get(priority, 0)
            percentage = (count / total_patients) * 100
            distribution[priority] = percentage
            
        return distribution
        
    def _calculate_efficiency_metrics(self, metrics: SimulationMetrics) -> Dict[str, float]:
        """Calculate efficiency metrics"""
        
        efficiency = {}
        
        # Resource efficiency
        if metrics.doctor_utilization:
            efficiency['doctor_efficiency'] = float(np.mean(metrics.doctor_utilization))
            
        if metrics.nurse_utilization:
            efficiency['nurse_efficiency'] = float(np.mean(metrics.nurse_utilization))
            
        # Time efficiency
        if metrics.triage_times:
            target_triage_time = 5.0  # minutes
            actual_triage_time = np.mean(metrics.triage_times)
            efficiency['triage_efficiency'] = min(100, (target_triage_time / actual_triage_time) * 100)
            
        # Flow efficiency
        if metrics.total_arrivals > 0 and metrics.duration > 0:
            theoretical_max_throughput = 30.0  # patients per hour (theoretical)
            actual_throughput = metrics.throughput_per_hour
            efficiency['flow_efficiency'] = (actual_throughput / theoretical_max_throughput) * 100
            
        # Queue efficiency
        all_queue_lengths = []
        for queue_data in metrics.queue_lengths_over_time.values():
            all_queue_lengths.extend(queue_data)
            
        if all_queue_lengths:
            avg_queue_length = np.mean(all_queue_lengths)
            # Lower queue lengths indicate higher efficiency
            efficiency['queue_efficiency'] = max(0, 100 - (avg_queue_length * 10))
            
        return efficiency
        
    def _perform_normality_tests(self, metrics: SimulationMetrics) -> Dict[str, Dict[str, float]]:
        """Perform normality tests on key metrics"""
        
        normality_results = {}
        
        datasets = {
            'wait_times': [],
            'consultation_times': metrics.consultation_times,
            'triage_times': metrics.triage_times,
            'system_times': metrics.total_system_times
        }
        
        # Combine all wait times
        for times in metrics.wait_times.values():
            datasets['wait_times'].extend(times)
            
        for dataset_name, data in datasets.items():
            if data and len(data) >= 8:  # Minimum sample size for normality tests
                try:
                    # Shapiro-Wilk test
                    shapiro_stat, shapiro_p = stats.shapiro(data)
                    
                    # Kolmogorov-Smirnov test
                    ks_stat, ks_p = stats.kstest(data, 'norm', args=(np.mean(data), np.std(data)))
                    
                    normality_results[dataset_name] = {
                        'shapiro_wilk_statistic': float(shapiro_stat),
                        'shapiro_wilk_p_value': float(shapiro_p),
                        'shapiro_wilk_normal': shapiro_p > 0.05,
                        'ks_statistic': float(ks_stat),
                        'ks_p_value': float(ks_p),
                        'ks_normal': ks_p > 0.05,
                        'sample_size': len(data)
                    }
                except Exception as e:
                    normality_results[dataset_name] = {'error': str(e)}
                    
        return normality_results
        
    def _perform_correlation_analysis(self, metrics: SimulationMetrics) -> Dict[str, float]:
        """Perform correlation analysis between key metrics"""
        
        correlations = {}
        
        # Create dataset for correlation analysis
        data_dict = {}
        
        # Resource utilization data
        if metrics.doctor_utilization:
            data_dict['doctor_utilization'] = metrics.doctor_utilization
            
        if metrics.nurse_utilization:
            data_dict['nurse_utilization'] = metrics.nurse_utilization
            
        # Queue length data
        all_queue_lengths = []
        for queue_data in metrics.queue_lengths_over_time.values():
            all_queue_lengths.extend(queue_data)
            
        if all_queue_lengths:
            # Pad or truncate to match other series
            min_length = min(len(data_dict.get('doctor_utilization', [])), len(all_queue_lengths))
            if min_length > 1:
                data_dict['queue_length'] = all_queue_lengths[:min_length]
                
        # Calculate correlations if we have enough data
        if len(data_dict) >= 2:
            try:
                df = pd.DataFrame(data_dict)
                correlation_matrix = df.corr()
                
                # Extract key correlations
                if 'doctor_utilization' in df.columns and 'nurse_utilization' in df.columns:
                    correlations['doctor_nurse_utilization'] = float(correlation_matrix.loc['doctor_utilization', 'nurse_utilization'])
                    
                if 'doctor_utilization' in df.columns and 'queue_length' in df.columns:
                    correlations['doctor_utilization_queue_length'] = float(correlation_matrix.loc['doctor_utilization', 'queue_length'])
                    
            except Exception as e:
                correlations['error'] = str(e)
                
        return correlations
        
    def _generate_recommendations(self, metrics: SimulationMetrics, 
                                performance_indicators: Dict[str, float],
                                target_compliance: Dict[str, float]) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        
        recommendations = []
        
        # Wait time recommendations
        overall_compliance = target_compliance.get('overall_compliance', 0)
        if overall_compliance < 90:
            recommendations.append(
                f"Wait time compliance is {overall_compliance:.1f}%, below the 95% NHS target. "
                "Consider increasing staffing levels or optimizing patient flow processes."
            )
            
        # Resource utilization recommendations
        resource_efficiency = performance_indicators.get('resource_efficiency', 0)
        if resource_efficiency < 70:
            recommendations.append(
                f"Resource efficiency is {resource_efficiency:.1f}%, indicating underutilization. "
                "Review staffing schedules and consider demand-based resource allocation."
            )
        elif resource_efficiency > 95:
            recommendations.append(
                f"Resource efficiency is {resource_efficiency:.1f}%, indicating potential overutilization. "
                "Consider increasing capacity to prevent staff burnout and maintain quality of care."
            )
            
        # LWBS rate recommendations
        lwbs_rate = performance_indicators.get('lwbs_rate', 0)
        if lwbs_rate > 5:
            recommendations.append(
                f"LWBS rate is {lwbs_rate:.1f}%, above the 5% target. "
                "Focus on reducing wait times and improving patient communication."
            )
            
        # Throughput recommendations
        throughput = performance_indicators.get('throughput_per_hour', 0)
        if throughput < 15:
            recommendations.append(
                f"Throughput is {throughput:.1f} patients/hour, which may be below optimal levels. "
                "Review triage processes and consider parallel processing workflows."
            )
            
        # Priority-specific recommendations
        for priority in ['IMMEDIATE', 'VERY_URGENT']:
            compliance_key = f'{priority}_compliance'
            if compliance_key in target_compliance:
                compliance = target_compliance[compliance_key]
                if compliance < 95:
                    recommendations.append(
                        f"{priority} priority compliance is {compliance:.1f}%. "
                        "Ensure immediate escalation protocols and dedicated fast-track pathways."
                    )
                    
        # Triage confidence recommendations
        triage_confidence = performance_indicators.get('average_triage_confidence', 0)
        if triage_confidence < 0.8:
            recommendations.append(
                f"Average triage confidence is {triage_confidence:.2f}. "
                "Consider additional triage training or decision support tools."
            )
            
        # General recommendations if no specific issues found
        if not recommendations:
            recommendations.append(
                "System performance is within acceptable ranges. "
                "Continue monitoring key metrics and consider incremental improvements."
            )
            
        return recommendations
        
    def _calculate_descriptive_stats(self, data: List[float]) -> Dict[str, float]:
        """Calculate descriptive statistics for a dataset"""
        
        if not data:
            return {'count': 0}
            
        return {
            'count': len(data),
            'mean': float(np.mean(data)),
            'median': float(np.median(data)),
            'std': float(np.std(data)),
            'var': float(np.var(data)),
            'min': float(np.min(data)),
            'max': float(np.max(data)),
            'range': float(np.max(data) - np.min(data)),
            'skewness': float(stats.skew(data)),
            'kurtosis': float(stats.kurtosis(data))
        }
        
    def compare_simulations(self, metrics_list: List[SimulationMetrics], 
                          labels: List[str] = None) -> Dict[str, Any]:
        """Compare multiple simulation runs"""
        
        if not metrics_list:
            return {}
            
        if not labels:
            labels = [f"Simulation {i+1}" for i in range(len(metrics_list))]
            
        comparison = {
            'simulation_count': len(metrics_list),
            'labels': labels,
            'comparative_metrics': {}
        }
        
        # Compare key metrics across simulations
        metrics_to_compare = [
            'throughput_per_hour',
            'average_length_of_stay',
            'resource_efficiency'
        ]
        
        for metric_name in metrics_to_compare:
            values = []
            for metrics in metrics_list:
                if hasattr(metrics, metric_name):
                    values.append(getattr(metrics, metric_name))
                    
            if values:
                comparison['comparative_metrics'][metric_name] = {
                    'values': values,
                    'mean': float(np.mean(values)),
                    'std': float(np.std(values)),
                    'min': float(np.min(values)),
                    'max': float(np.max(values)),
                    'best_simulation': labels[np.argmax(values)] if metric_name != 'average_length_of_stay' else labels[np.argmin(values)]
                }
                
        return comparison
        
    def export_report(self, report: StatisticalReport, filename: str, format: str = 'json'):
        """Export statistical report to file"""
        
        if format.lower() == 'json':
            report.save_to_file(filename)
        elif format.lower() == 'csv':
            # Export key metrics to CSV
            data = []
            
            # Performance indicators
            for metric, value in report.performance_indicators.items():
                data.append({'category': 'performance', 'metric': metric, 'value': value})
                
            # Target compliance
            for metric, value in report.target_compliance.items():
                data.append({'category': 'compliance', 'metric': metric, 'value': value})
                
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")