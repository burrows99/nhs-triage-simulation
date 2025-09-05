import os
from typing import List, Dict, Any
import matplotlib.pyplot as plt  # type: ignore
from ..models.simulation.snapshot import Snapshot
from ..utils.constants import TRIAGE_PRIORITIES


class PlottingService:
    """Service for plotting hospital simulation data and saving to output directory."""
    
    def __init__(self, snapshots: List[Snapshot], output_dir: str = "output"):
        self.snapshots = snapshots
        self.output_dir = output_dir
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _collect_queue_data(self) -> Dict[str, Dict[str, List[int]]]:
        """Collect queue length data from snapshots."""
        data = {}  # type: ignore
        for snap in self.snapshots:
            for _, reslist in snap.resources_state.items():
                for res in reslist:
                    if res.name not in data:
                        data[res.name] = {p: [] for p in TRIAGE_PRIORITIES}  # type: ignore
                    for p in TRIAGE_PRIORITIES:
                        data[res.name][p].append(len(res.queues[p]))  # type: ignore
        return data  # type: ignore
    
    def _calculate_running_average(self, values: List[int]) -> List[float]:
        """Calculate running average for a list of values."""
        running_avg = []  # type: ignore
        cumsum = 0  # type: ignore
        for i, value in enumerate(values):  # type: ignore
            cumsum += value  # type: ignore
            running_avg.append(cumsum / (i + 1))  # type: ignore
        return running_avg  # type: ignore
    
    def _setup_queue_plot_axes(self, ax: Any, res_name: str, queues: Dict[str, List[int]]) -> None:
        """Setup axes for queue length plots with current and average lines."""
        for priority, lengths in queues.items():  # type: ignore
            time_steps = range(1, len(lengths)+1)  # type: ignore
            
            # Plot instantaneous queue lengths
            ax.plot(time_steps, lengths, label=f"{priority} (Current)", alpha=0.7)  # type: ignore
            
            # Calculate and plot running average
            running_avg = self._calculate_running_average(lengths)
            ax.plot(time_steps, running_avg, label=f"{priority} (Avg)", linestyle='--', linewidth=2)  # type: ignore
        
        ax.set_title(f"Queue lengths over time: {res_name} (Current vs Running Average)")  # type: ignore
        ax.set_ylabel("Number of Patients")  # type: ignore
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')  # type: ignore
        ax.grid(True, alpha=0.3)  # type: ignore
    
    def _save_plot(self, filename: str, message: str) -> None:
        """Save current plot to output directory."""
        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')  # type: ignore
        plt.close()  # type: ignore
        print(f"{message}: {output_path}")
    
    def plot_queue_lengths(self) -> None:
        """Plot queue lengths over time for each resource with running averages."""
        data = self._collect_queue_data()
        
        fig, axes = plt.subplots(len(data), 1, figsize=(12, 5 * len(data)), sharex=True)  # type: ignore
        if len(data) == 1:  # type: ignore
            axes = [axes]  # type: ignore
        
        for ax, (res_name, queues) in zip(axes, data.items()):  # type: ignore
            self._setup_queue_plot_axes(ax, res_name, queues)
        
        plt.xlabel("Simulation Step")  # type: ignore
        plt.tight_layout()  # type: ignore
        self._save_plot("queue_lengths_with_averages.png", "Queue lengths with running averages plot saved to")
    
    def _collect_patient_timing_data(self):  # type: ignore
        """Collect patient timing data from snapshots."""
        timing_data = {  # type: ignore
            'wait_times': [],
            'service_times': [],
            'actual_service_times': [],
            'length_of_stay': []
        }
        
        for snap in self.snapshots:  # type: ignore
            # Collect data from all resources
            for _, reslist in snap.resources_state.items():  # type: ignore
                for res in reslist:  # type: ignore
                    # Current patient data
                    if res.current_patient:  # type: ignore
                        patient = res.current_patient  # type: ignore
                        if patient.wait_time is not None:  # type: ignore
                            timing_data['wait_times'].append(float(patient.wait_time))  # type: ignore
                        if patient.service_time is not None:  # type: ignore
                            timing_data['service_times'].append(float(patient.service_time))  # type: ignore
                        if patient.actual_service_time is not None:  # type: ignore
                            timing_data['actual_service_times'].append(float(patient.actual_service_time))  # type: ignore
                        if patient.length_of_stay is not None:  # type: ignore
                            timing_data['length_of_stay'].append(float(patient.length_of_stay))  # type: ignore
                    
                    # Queue patients data
                    for priority_queue in res.queues.values():  # type: ignore
                        for patient in priority_queue:  # type: ignore
                            if patient.wait_time is not None:  # type: ignore
                                timing_data['wait_times'].append(float(patient.wait_time))  # type: ignore
                            if patient.service_time is not None:  # type: ignore
                                timing_data['service_times'].append(float(patient.service_time))  # type: ignore
                            if patient.actual_service_time is not None:  # type: ignore
                                timing_data['actual_service_times'].append(float(patient.actual_service_time))  # type: ignore
                            if patient.length_of_stay is not None:  # type: ignore
                                timing_data['length_of_stay'].append(float(patient.length_of_stay))  # type: ignore
        
        return timing_data  # type: ignore
    
    def plot_patient_timing_metrics(self) -> None:
        """Plot patient timing metrics with running averages."""
        timing_data = self._collect_patient_timing_data()  # type: ignore
        
        # Create subplots for different metrics
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))  # type: ignore
        axes = axes.flatten()  # type: ignore
        
        metrics = [
            ('wait_times', 'Wait Time (minutes)', 'Patient Wait Times'),
            ('service_times', 'Service Time (minutes)', 'Patient Service Times'),
            ('actual_service_times', 'Actual Service Time (minutes)', 'Patient Actual Service Times'),
            ('length_of_stay', 'Length of Stay (minutes)', 'Patient Length of Stay')
        ]
        
        for i, (metric_key, ylabel, title) in enumerate(metrics):  # type: ignore
            ax = axes[i]  # type: ignore
            data = timing_data[metric_key]  # type: ignore
            
            if data:  # type: ignore
                time_steps = range(1, len(data) + 1)  # type: ignore
                
                # Plot individual values
                ax.plot(time_steps, data, 'o-', alpha=0.6, markersize=3, label='Individual Values')  # type: ignore
                
                # Calculate and plot running average
                running_avg = self._calculate_running_average([int(x) for x in data])  # type: ignore
                ax.plot(time_steps, running_avg, '--', linewidth=2, color='red', label='Running Average')  # type: ignore
                
                ax.set_title(title)  # type: ignore
                ax.set_xlabel('Patient Index')  # type: ignore
                ax.set_ylabel(ylabel)  # type: ignore
                ax.legend()  # type: ignore
                ax.grid(True, alpha=0.3)  # type: ignore
            else:
                ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)  # type: ignore
                ax.set_title(title)  # type: ignore
        
        plt.tight_layout()  # type: ignore
        self._save_plot("patient_timing_metrics.png", "Patient timing metrics plot saved to")
    
    def plot_timing_distributions(self) -> None:
        """Plot histograms of timing distributions."""
        timing_data = self._collect_patient_timing_data()  # type: ignore
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))  # type: ignore
        axes = axes.flatten()  # type: ignore
        
        metrics = [
            ('wait_times', 'Wait Time (minutes)', 'Wait Time Distribution'),
            ('service_times', 'Service Time (minutes)', 'Service Time Distribution'),
            ('actual_service_times', 'Actual Service Time (minutes)', 'Actual Service Time Distribution'),
            ('length_of_stay', 'Length of Stay (minutes)', 'Length of Stay Distribution')
        ]
        
        for i, (metric_key, xlabel, title) in enumerate(metrics):  # type: ignore
            ax = axes[i]  # type: ignore
            data = timing_data[metric_key]  # type: ignore
            
            if data:  # type: ignore
                ax.hist(data, bins=20, alpha=0.7, edgecolor='black')  # type: ignore
                ax.set_title(f"{title} (n={len(data)})")  # type: ignore
                ax.set_xlabel(xlabel)  # type: ignore
                ax.set_ylabel('Frequency')  # type: ignore
                ax.grid(True, alpha=0.3)  # type: ignore
                
                # Add statistics text
                if data:
                    mean_val = sum(data) / len(data)  # type: ignore
                    ax.axvline(mean_val, color='red', linestyle='--', label=f'Mean: {mean_val:.1f}')  # type: ignore
                    ax.legend()  # type: ignore
            else:
                ax.text(0.5, 0.5, 'No data available', ha='center', va='center', transform=ax.transAxes)  # type: ignore
                ax.set_title(title)  # type: ignore
        
        plt.tight_layout()  # type: ignore
        self._save_plot("timing_distributions.png", "Timing distributions plot saved to")
    
    def generate_all_plots(self) -> None:
        """Generate and save all available plots."""
        print("Generating all simulation plots...")
        self.plot_queue_lengths()
        self.plot_patient_timing_metrics()
        self.plot_timing_distributions()
        print(f"All plots saved to: {self.output_dir}")