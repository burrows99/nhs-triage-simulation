from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any, TYPE_CHECKING
import numpy as np
import pandas as pd  # type: ignore
import matplotlib.pyplot as plt  # type: ignore
import seaborn as sns  # type: ignore
from pathlib import Path
from datetime import datetime

try:
    from ..entities.patient import Patient
    from ..enums.resource_type import ResourceType
    from ..enums.priority import TriagePriority
except ImportError:
    from entities.patient import Patient
    from enums.resource_type import ResourceType
    from enums.priority import TriagePriority

if TYPE_CHECKING:
    try:
        from ..entities.hospital import Hospital
    except ImportError:
        from entities.hospital import Hospital


@dataclass
class WaitTimeMetrics:
    """
    Wait time analysis metrics.
    
    Comprehensive statistics for patient wait times across
    different priority levels and resource types.
    """
    mean_wait_time: float
    median_wait_time: float
    std_wait_time: float
    min_wait_time: float
    max_wait_time: float
    percentile_95: float
    percentile_99: float
    sample_size: int
    
    def __post_init__(self) -> None:
        """Validate wait time metrics."""
        if self.sample_size < 0:
            raise ValueError("Sample size cannot be negative")
        if self.mean_wait_time < 0:
            raise ValueError("Mean wait time cannot be negative")
        if self.median_wait_time < 0:
            raise ValueError("Median wait time cannot be negative")


@dataclass
class ResourceUtilizationMetrics:
    """
    Resource utilization analysis metrics.
    
    Tracks resource efficiency and capacity utilization
    for operational optimization.
    """
    mean_utilization: float
    median_utilization: float
    peak_utilization: float
    min_utilization: float
    utilization_variance: float
    time_above_80_percent: float  # Percentage of time above 80% utilization
    time_above_90_percent: float  # Percentage of time above 90% utilization
    sample_size: int
    
    def __post_init__(self) -> None:
        """Validate utilization metrics."""
        if not 0.0 <= self.mean_utilization <= 1.0:
            raise ValueError("Mean utilization must be between 0.0 and 1.0")
        if not 0.0 <= self.peak_utilization <= 1.0:
            raise ValueError("Peak utilization must be between 0.0 and 1.0")
        if self.sample_size < 0:
            raise ValueError("Sample size cannot be negative")


class MetricsService:
    """
    Comprehensive metrics analysis and visualization service.
    
    Provides statistical analysis and visualization capabilities for:
    - Patient wait times by priority and resource type
    - Resource utilization patterns and efficiency
    - System performance trends over time
    - Comparative analysis across different scenarios
    
    Key capabilities:
    - Statistical analysis (mean, median, percentiles)
    - Time series visualization
    - Distribution analysis
    - Performance benchmarking
    - Export capabilities for further analysis
    
    Reference: NHS Performance Indicators and Healthcare Analytics Standards
    """
    
    def __init__(self, output_directory: str = "./metrics_output") -> None:
        """Initialize metrics service."""
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        # Configure plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Data storage
        self.wait_time_data: List[Tuple[float, str, TriagePriority, ResourceType]] = []
        self.utilization_data: List[Tuple[float, ResourceType, float]] = []
        self.system_metrics_data: List[Tuple[float, Dict[str, float]]] = []
    
    def collect_patient_metrics(self, patients: List[Patient]) -> None:
        """
        Collect wait time metrics from discharged patients.
        
        Args:
            patients: List of discharged patients
        """
        for patient in patients:
            if patient.metrics.total_wait_time > 0:
                self.wait_time_data.append((
                    patient.metrics.total_wait_time,
                    patient.patient_id,
                    patient.priority,
                    patient.required_resource
                ))
    
    def collect_hospital_metrics(self, hospital: "Hospital", current_time: float) -> None:
        """
        Collect system-wide metrics from hospital state.
        
        Args:
            hospital: Hospital instance
            current_time: Current simulation time
        """
        # Collect resource utilization
        for resource_type, utilization in hospital.metrics.resource_utilization.items():
            self.utilization_data.append((current_time, resource_type, utilization))
        
        # Collect system metrics
        system_metrics = {
            "system_load": hospital.metrics.current_system_load,
            "patients_in_system": len(hospital.patients_in_system),
            "total_processed": hospital.metrics.total_patients_processed,
            "total_discharged": hospital.metrics.total_patients_discharged,
            "preemptions_executed": hospital.metrics.total_preemptions_executed
        }
        self.system_metrics_data.append((current_time, system_metrics))
    
    def analyze_wait_times(self, priority_filter: Optional[TriagePriority] = None, 
                          resource_filter: Optional[ResourceType] = None) -> WaitTimeMetrics:
        """
        Analyze patient wait times with optional filtering.
        
        Args:
            priority_filter: Filter by specific priority level
            resource_filter: Filter by specific resource type
            
        Returns:
            Wait time analysis metrics
        """
        # Filter data
        filtered_data = self.wait_time_data
        if priority_filter:
            filtered_data = [d for d in filtered_data if d[2] == priority_filter]
        if resource_filter:
            filtered_data = [d for d in filtered_data if d[3] == resource_filter]
        
        if not filtered_data:
            return WaitTimeMetrics(
                mean_wait_time=0.0, median_wait_time=0.0, std_wait_time=0.0,
                min_wait_time=0.0, max_wait_time=0.0, percentile_95=0.0,
                percentile_99=0.0, sample_size=0
            )
        
        wait_times = [d[0] for d in filtered_data]
        
        return WaitTimeMetrics(
            mean_wait_time=float(np.mean(wait_times)),
            median_wait_time=float(np.median(wait_times)),
            std_wait_time=float(np.std(wait_times)),
            min_wait_time=float(np.min(wait_times)),
            max_wait_time=float(np.max(wait_times)),
            percentile_95=float(np.percentile(wait_times, 95)),
            percentile_99=float(np.percentile(wait_times, 99)),
            sample_size=len(wait_times)
        )
    
    def analyze_resource_utilization(self, resource_type: ResourceType) -> ResourceUtilizationMetrics:
        """
        Analyze resource utilization patterns.
        
        Args:
            resource_type: Type of resource to analyze
            
        Returns:
            Resource utilization metrics
        """
        # Filter data for specific resource type
        filtered_data = [d for d in self.utilization_data if d[1] == resource_type]
        
        if not filtered_data:
            return ResourceUtilizationMetrics(
                mean_utilization=0.0, median_utilization=0.0, peak_utilization=0.0,
                min_utilization=0.0, utilization_variance=0.0, time_above_80_percent=0.0,
                time_above_90_percent=0.0, sample_size=0
            )
        
        utilizations = [d[2] for d in filtered_data]
        
        # Calculate time above thresholds
        above_80 = sum(1 for u in utilizations if u > 0.8)
        above_90 = sum(1 for u in utilizations if u > 0.9)
        total_samples = len(utilizations)
        
        return ResourceUtilizationMetrics(
            mean_utilization=float(np.mean(utilizations)),
            median_utilization=float(np.median(utilizations)),
            peak_utilization=float(np.max(utilizations)),
            min_utilization=float(np.min(utilizations)),
            utilization_variance=float(np.var(utilizations)),
            time_above_80_percent=above_80 / total_samples * 100.0,
            time_above_90_percent=above_90 / total_samples * 100.0,
            sample_size=total_samples
        )
    
    def plot_wait_time_distribution(self, save_path: Optional[str] = None) -> None:
        """
        Create wait time distribution plots by priority level.
        
        Args:
            save_path: Optional path to save the plot
        """
        if not self.wait_time_data:
            print("No wait time data available for plotting")
            return
        
        # Prepare data
        df = pd.DataFrame(self.wait_time_data,  # type: ignore
                         columns=['wait_time', 'patient_id', 'priority', 'resource_type'])
        df['priority_name'] = df['priority'].apply(lambda x: x.name)  # type: ignore
        
        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))  # type: ignore
        fig.suptitle('Patient Wait Time Analysis', fontsize=16, fontweight='bold')  # type: ignore
        
        # Distribution by priority
        sns.boxplot(data=df, x='priority_name', y='wait_time', ax=axes[0, 0])  # type: ignore
        axes[0, 0].set_title('Wait Time Distribution by Priority Level')
        axes[0, 0].set_xlabel('Priority Level')
        axes[0, 0].set_ylabel('Wait Time (minutes)')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Distribution by resource type
        df['resource_name'] = df['resource_type'].apply(lambda x: x.name)  # type: ignore
        sns.boxplot(data=df, x='resource_name', y='wait_time', ax=axes[0, 1])  # type: ignore
        axes[0, 1].set_title('Wait Time Distribution by Resource Type')
        axes[0, 1].set_xlabel('Resource Type')
        axes[0, 1].set_ylabel('Wait Time (minutes)')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Histogram of all wait times
        axes[1, 0].hist(df['wait_time'], bins=30, alpha=0.7, edgecolor='black')  # type: ignore
        axes[1, 0].set_title('Overall Wait Time Distribution')
        axes[1, 0].set_xlabel('Wait Time (minutes)')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].axvline(df['wait_time'].mean(), color='red', linestyle='--',  # type: ignore
                          label=f'Mean: {df["wait_time"].mean():.1f} min')  # type: ignore
        axes[1, 0].axvline(df['wait_time'].median(), color='green', linestyle='--',  # type: ignore
                          label=f'Median: {df["wait_time"].median():.1f} min')  # type: ignore
        axes[1, 0].legend()
        
        # Priority vs Resource heatmap
        pivot_data = df.groupby(['priority_name', 'resource_name'])['wait_time'].mean().unstack(fill_value=0)  # type: ignore
        sns.heatmap(pivot_data, annot=True, fmt='.1f', cmap='YlOrRd', ax=axes[1, 1])  # type: ignore
        axes[1, 1].set_title('Average Wait Time by Priority and Resource')
        axes[1, 1].set_xlabel('Resource Type')
        axes[1, 1].set_ylabel('Priority Level')
        
        plt.tight_layout()
        
        # Save plot
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.savefig(self.output_directory / 'wait_time_analysis.png', dpi=300, bbox_inches='tight')
        
        plt.show()
    
    def plot_resource_utilization(self, save_path: Optional[str] = None) -> None:
        """
        Create resource utilization plots over time.
        
        Args:
            save_path: Optional path to save the plot
        """
        if not self.utilization_data:
            print("No utilization data available for plotting")
            return
        
        # Prepare data
        df = pd.DataFrame(self.utilization_data, 
                         columns=['time', 'resource_type', 'utilization'])
        df['resource_name'] = df['resource_type'].apply(lambda x: x.name)
        
        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Resource Utilization Analysis', fontsize=16, fontweight='bold')
        
        # Time series for each resource type
        for i, resource_type in enumerate(ResourceType):
            resource_data = df[df['resource_type'] == resource_type]
            if not resource_data.empty:
                row, col = divmod(i, 2)
                axes[row, col].plot(resource_data['time'], resource_data['utilization'], 
                                   marker='o', markersize=2, linewidth=1)
                axes[row, col].set_title(f'{resource_type.name} Utilization Over Time')
                axes[row, col].set_xlabel('Time (minutes)')
                axes[row, col].set_ylabel('Utilization Rate')
                axes[row, col].set_ylim(0, 1)
                axes[row, col].axhline(y=0.8, color='orange', linestyle='--', alpha=0.7, label='80% threshold')
                axes[row, col].axhline(y=0.9, color='red', linestyle='--', alpha=0.7, label='90% threshold')
                axes[row, col].legend()
                axes[row, col].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.savefig(self.output_directory / 'resource_utilization.png', dpi=300, bbox_inches='tight')
        
        plt.show()
    
    def plot_system_performance(self, save_path: Optional[str] = None) -> None:
        """
        Create system performance overview plots.
        
        Args:
            save_path: Optional path to save the plot
        """
        if not self.system_metrics_data:
            print("No system metrics data available for plotting")
            return
        
        # Prepare data
        times = [d[0] for d in self.system_metrics_data]
        system_loads = [d[1]['system_load'] for d in self.system_metrics_data]
        patients_in_system = [d[1]['patients_in_system'] for d in self.system_metrics_data]
        total_processed = [d[1]['total_processed'] for d in self.system_metrics_data]
        preemptions = [d[1]['preemptions_executed'] for d in self.system_metrics_data]
        
        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Hospital System Performance', fontsize=16, fontweight='bold')
        
        # System load over time
        axes[0, 0].plot(times, system_loads, color='blue', linewidth=2)
        axes[0, 0].set_title('System Load Over Time')
        axes[0, 0].set_xlabel('Time (minutes)')
        axes[0, 0].set_ylabel('System Load')
        axes[0, 0].set_ylim(0, 1)
        axes[0, 0].axhline(y=0.8, color='orange', linestyle='--', alpha=0.7, label='High load threshold')
        axes[0, 0].axhline(y=0.9, color='red', linestyle='--', alpha=0.7, label='Critical load threshold')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Patients in system
        axes[0, 1].plot(times, patients_in_system, color='green', linewidth=2)
        axes[0, 1].set_title('Patients in System Over Time')
        axes[0, 1].set_xlabel('Time (minutes)')
        axes[0, 1].set_ylabel('Number of Patients')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Cumulative patients processed
        axes[1, 0].plot(times, total_processed, color='purple', linewidth=2)
        axes[1, 0].set_title('Cumulative Patients Processed')
        axes[1, 0].set_xlabel('Time (minutes)')
        axes[1, 0].set_ylabel('Total Patients')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Preemptions over time
        axes[1, 1].plot(times, preemptions, color='red', linewidth=2, marker='o', markersize=3)
        axes[1, 1].set_title('Cumulative Preemptions Executed')
        axes[1, 1].set_xlabel('Time (minutes)')
        axes[1, 1].set_ylabel('Number of Preemptions')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        else:
            plt.savefig(self.output_directory / 'system_performance.png', dpi=300, bbox_inches='tight')
        
        plt.show()
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive summary report.
        
        Returns:
            Dictionary containing summary statistics and insights
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "data_summary": {
                "total_patients_analyzed": len(self.wait_time_data),
                "utilization_data_points": len(self.utilization_data),
                "system_metrics_data_points": len(self.system_metrics_data)
            },
            "wait_time_analysis": {},
            "resource_utilization_analysis": {},
            "key_insights": []
        }
        
        # Overall wait time analysis
        overall_wait_metrics = self.analyze_wait_times()
        report["wait_time_analysis"]["overall"] = {
            "mean_minutes": overall_wait_metrics.mean_wait_time,
            "median_minutes": overall_wait_metrics.median_wait_time,
            "95th_percentile_minutes": overall_wait_metrics.percentile_95,
            "sample_size": overall_wait_metrics.sample_size
        }
        
        # Wait time by priority
        for priority in TriagePriority:
            priority_metrics = self.analyze_wait_times(priority_filter=priority)
            if priority_metrics.sample_size > 0:
                report["wait_time_analysis"][priority.name] = {
                    "mean_minutes": priority_metrics.mean_wait_time,
                    "median_minutes": priority_metrics.median_wait_time,
                    "sample_size": priority_metrics.sample_size
                }
        
        # Resource utilization analysis
        for resource_type in ResourceType:
            util_metrics = self.analyze_resource_utilization(resource_type)
            if util_metrics.sample_size > 0:
                report["resource_utilization_analysis"][resource_type.name] = {
                    "mean_utilization": util_metrics.mean_utilization,
                    "peak_utilization": util_metrics.peak_utilization,
                    "time_above_80_percent": util_metrics.time_above_80_percent,
                    "sample_size": util_metrics.sample_size
                }
        
        # Generate insights
        if overall_wait_metrics.sample_size > 0:
            if overall_wait_metrics.mean_wait_time > 60:
                report["key_insights"].append("High average wait times detected (>60 minutes)")
            if overall_wait_metrics.percentile_95 > 120:
                report["key_insights"].append("95th percentile wait time exceeds 2 hours")
        
        return report
    
    def export_data(self, filename: Optional[str] = None) -> str:
        """
        Export collected data to CSV files.
        
        Args:
            filename: Optional base filename for exports
            
        Returns:
            Path to exported files directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = filename or f"hospital_metrics_{timestamp}"
        
        # Export wait time data
        if self.wait_time_data:
            wait_df = pd.DataFrame(self.wait_time_data, 
                                 columns=['wait_time', 'patient_id', 'priority', 'resource_type'])
            wait_df['priority_name'] = wait_df['priority'].apply(lambda x: x.name)
            wait_df['resource_name'] = wait_df['resource_type'].apply(lambda x: x.name)
            wait_df.to_csv(self.output_directory / f"{base_name}_wait_times.csv", index=False)
        
        # Export utilization data
        if self.utilization_data:
            util_df = pd.DataFrame(self.utilization_data, 
                                 columns=['time', 'resource_type', 'utilization'])
            util_df['resource_name'] = util_df['resource_type'].apply(lambda x: x.name)
            util_df.to_csv(self.output_directory / f"{base_name}_utilization.csv", index=False)
        
        # Export system metrics
        if self.system_metrics_data:
            system_data = []
            for time, metrics in self.system_metrics_data:
                row = {'time': time}
                row.update(metrics)
                system_data.append(row)
            system_df = pd.DataFrame(system_data)
            system_df.to_csv(self.output_directory / f"{base_name}_system_metrics.csv", index=False)
        
        return str(self.output_directory)
    
    def clear_data(self) -> None:
        """Clear all collected data."""
        self.wait_time_data.clear()
        self.utilization_data.clear()
        self.system_metrics_data.clear()
    
    def __str__(self) -> str:
        return (f"MetricsService(wait_times={len(self.wait_time_data)}, "
                f"utilization_points={len(self.utilization_data)}, "
                f"system_metrics={len(self.system_metrics_data)})")