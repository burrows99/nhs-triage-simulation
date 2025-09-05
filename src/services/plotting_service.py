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
        self._save_plot("queue_lengths_with_averages.png", "Queue lengths with running averages plot saved to")# type: ignore
    
    def generate_all_plots(self) -> None:
        """Generate and save all available plots."""
        print("Generating all simulation plots...")
        self.plot_queue_lengths()
        print(f"All plots saved to: {self.output_dir}")