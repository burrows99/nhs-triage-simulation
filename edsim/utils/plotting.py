# type: ignore
# Matplotlib type annotations are complex and cause linter issues
from typing import Dict, List
import numpy as np
import matplotlib.pyplot as plt
from numpy.typing import NDArray

from ..constants import RESOURCES


def plot_generic_bar(data: Dict[str, float], filepath: str, title: str, ylabel: str, 
                    color: str = 'skyblue', show_values: bool = True) -> None:
    """
    Enhanced bar plot with value labels and customizable colors.
    Uses metrics service for consistent data handling.
    """
    keys = list(data.keys())
    values = [data[k] for k in keys]
    
    plt.figure(figsize=(10, 6))
    bars = plt.bar(keys, values, color=color, edgecolor='black', alpha=0.7)
    
    # Add value labels on bars if requested
    if show_values:
        for bar, value in zip(bars, values):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01,
                    f'{value:.1f}', ha='center', va='bottom', fontweight='bold')
    
    plt.title(title, fontsize=14, fontweight='bold')
    plt.ylabel(ylabel, fontsize=12)
    plt.xlabel('Resources', fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()


def plot_queue_timeline(queue_arr: NDArray[np.float64], filepath: str, title: str,
                       queue_stats: Dict[str, Dict[str, float]] = None) -> None:
    """
    Enhanced queue timeline plot with statistics annotations.
    Integrates with metrics service for comprehensive queue analysis.
    """
    plt.figure(figsize=(12, 8))
    
    if queue_arr.size > 0:
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']  # Professional colors
        
        for r_idx, r in enumerate(RESOURCES):
            color = colors[r_idx % len(colors)]
            queue_data = queue_arr[:, r_idx + 1]
            plt.plot(queue_arr[:, 0], queue_data, label=f'{r.title()}', 
                    color=color, linewidth=2, alpha=0.8)
            
            # Add max queue annotation if stats provided
            if queue_stats and r in queue_stats:
                max_queue = queue_stats[r]['max_queue']
                max_time_idx = np.argmax(queue_data)
                max_time = queue_arr[max_time_idx, 0]
                plt.annotate(f'Max: {max_queue:.0f}', 
                           xy=(max_time, max_queue), 
                           xytext=(10, 10), textcoords='offset points',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor=color, alpha=0.3),
                           arrowprops=dict(arrowstyle='->', color=color))
        
        plt.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)
    else:
        plt.text(0.5, 0.5, 'No queue data available', 
                transform=plt.gca().transAxes, ha='center', va='center',
                fontsize=14, style='italic')
    
    plt.xlabel('Time (minutes)', fontsize=12)
    plt.ylabel('Queue Length (patients)', fontsize=12)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close()


def plot_comparison_bar(results: Dict[str, Dict[str, float]], filepath: str, title: str, ylabel: str) -> None:
    scenarios = list(results.keys())
    x = np.arange(len(RESOURCES))
    width = 0.8 / max(1, len(scenarios))
    plt.figure(figsize=(10, 6))
    for i, sc in enumerate(scenarios):
        vals = [results[sc].get(r, 0.0) for r in RESOURCES]
        plt.bar(x + i * width, vals, width=width, label=sc)
    plt.xticks(x + (len(scenarios) - 1) * width / 2, RESOURCES)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(filepath)
    plt.close()


def plot_queue_comparison(results_queue: Dict[str, NDArray[np.float64]], scenarios: List[str], filepath: str) -> None:
    plt.figure(figsize=(10, 6))
    for r_idx, r in enumerate(RESOURCES):
        for sc in scenarios:
            q_arr = results_queue[sc]
            if q_arr.size == 0:
                continue
            timeline = q_arr[:, r_idx + 1]
            plt.plot(q_arr[:, 0], timeline, label=f"{r}-{sc}")
    plt.xlabel('Time (minutes)')
    plt.ylabel('Total Queue Length')
    plt.title('Queue Timeline Comparison Across Scenarios')
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(filepath)
    plt.close()