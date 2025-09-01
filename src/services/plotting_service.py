"""Plotting Service for Manchester Triage System

This module provides comprehensive plotting and visualization capabilities
for triage system metrics and analysis.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import os
from pathlib import Path

# Import metrics enums
from ..enum.metrics import (
    TriageCategory, VisualizationType, TimeInterval
)


class PlottingService:
    """Service for generating plots and visualizations from metrics data
    
    This service creates various types of plots including:
    - Wait time histograms and distributions
    - Patient arrival curves
    - Triage category distributions
    - Resource utilization charts
    - Performance trend analysis
    """
    
    def __init__(self, output_dir: str = "output/manchester_triage_system/plots"):
        """Initialize the plotting service
        
        Args:
            output_dir: Directory to save generated plots
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set plotting style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Color schemes for different plot types
        self.triage_colors = {
            TriageCategory.RED: '#FF0000',
            TriageCategory.ORANGE: '#FF8C00',
            TriageCategory.YELLOW: '#FFD700',
            TriageCategory.GREEN: '#32CD32',
            TriageCategory.BLUE: '#1E90FF',
            TriageCategory.UNKNOWN: '#808080'
        }
    
    def plot_wait_time_histogram(self, wait_time_data: Dict[str, Any], 
                                filename: str = None, show: bool = False) -> str:
        """Generate wait time histogram
        
        Args:
            wait_time_data: Dictionary containing histogram data from metrics service
            filename: Optional filename for saving the plot
            show: Whether to display the plot
            
        Returns:
            Path to the saved plot file
        """
        if not wait_time_data or 'histogram' not in wait_time_data:
            raise ValueError("Invalid wait time data provided")
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Main histogram
        hist_data = wait_time_data['histogram']
        bin_centers = hist_data['bin_centers']
        counts = hist_data['counts']
        
        ax1.bar(bin_centers, counts, width=np.diff(hist_data['bin_edges'])[0] * 0.8,
                alpha=0.7, color='skyblue', edgecolor='navy')
        ax1.set_xlabel('Wait Time (minutes)')
        ax1.set_ylabel('Number of Patients')
        ax1.set_title('Patient Wait Time Distribution')
        ax1.grid(True, alpha=0.3)
        
        # Add statistics text
        stats = wait_time_data.get('statistics', {})
        if stats:
            stats_text = f"Mean: {stats.get('mean', 0):.1f} min\n"
            stats_text += f"Median: {stats.get('median', 0):.1f} min\n"
            stats_text += f"Std Dev: {stats.get('std', 0):.1f} min"
            ax1.text(0.75, 0.95, stats_text, transform=ax1.transAxes, 
                    verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat'))
        
        # Timeline plot showing patient arrivals and encounter starts
        patient_data = wait_time_data.get('patient_data', [])
        if patient_data:
            arrival_times = [datetime.fromisoformat(p['arrival_time']) for p in patient_data]
            encounter_times = [datetime.fromisoformat(p['encounter_start_time']) for p in patient_data]
            
            ax2.scatter(arrival_times, [1] * len(arrival_times), 
                       alpha=0.6, label='Patient Arrivals', color='green', s=30)
            ax2.scatter(encounter_times, [2] * len(encounter_times), 
                       alpha=0.6, label='Encounter Starts', color='red', s=30)
            
            ax2.set_xlabel('Time')
            ax2.set_ylabel('Event Type')
            ax2.set_title('Patient Flow Timeline')
            ax2.set_yticks([1, 2])
            ax2.set_yticklabels(['Arrivals', 'Encounters'])
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # Format x-axis for time
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
            ax2.xaxis.set_major_locator(mdates.HourLocator(interval=1))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        # Save plot
        if filename is None:
            filename = f"wait_time_histogram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()
        
        return str(filepath)
    
    def plot_arrival_curves(self, arrival_data: Dict[str, List], 
                           filename: str = None, show: bool = False) -> str:
        """Generate patient arrival and encounter curves
        
        Args:
            arrival_data: Dictionary containing time intervals, arrivals, and encounters
            filename: Optional filename for saving the plot
            show: Whether to display the plot
            
        Returns:
            Path to the saved plot file
        """
        if not arrival_data or 'time_intervals' not in arrival_data:
            raise ValueError("Invalid arrival data provided")
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        time_intervals = [datetime.fromisoformat(t) for t in arrival_data['time_intervals']]
        arrivals = arrival_data['arrivals']
        encounters = arrival_data['encounters']
        
        # Plot curves
        ax.plot(time_intervals, arrivals, marker='o', linewidth=2, 
                label='Patient Arrivals', color='blue', markersize=4)
        ax.plot(time_intervals, encounters, marker='s', linewidth=2, 
                label='Encounter Starts', color='red', markersize=4)
        
        # Fill areas under curves
        ax.fill_between(time_intervals, arrivals, alpha=0.3, color='blue')
        ax.fill_between(time_intervals, encounters, alpha=0.3, color='red')
        
        ax.set_xlabel('Time')
        ax.set_ylabel('Number of Patients')
        ax.set_title('Patient Arrival and Encounter Curves')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        # Add peak indicators
        if arrivals:
            peak_arrival_idx = np.argmax(arrivals)
            peak_time = time_intervals[peak_arrival_idx]
            peak_value = arrivals[peak_arrival_idx]
            ax.annotate(f'Peak Arrivals\n{peak_value} patients', 
                       xy=(peak_time, peak_value), xytext=(10, 10),
                       textcoords='offset points', 
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                       arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
        
        plt.tight_layout()
        
        # Save plot
        if filename is None:
            filename = f"arrival_curves_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()
        
        return str(filepath)
    
    def plot_triage_distribution(self, triage_distribution: Dict[str, int], 
                                filename: str = None, show: bool = False) -> str:
        """Generate triage category distribution plots
        
        Args:
            triage_distribution: Dictionary mapping triage categories to counts
            filename: Optional filename for saving the plot
            show: Whether to display the plot
            
        Returns:
            Path to the saved plot file
        """
        if not triage_distribution:
            raise ValueError("Empty triage distribution data")
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        categories = list(triage_distribution.keys())
        counts = list(triage_distribution.values())
        total_patients = sum(counts)
        percentages = [count/total_patients * 100 for count in counts]
        
        # Get colors for categories
        colors = []
        for cat in categories:
            try:
                triage_cat = TriageCategory(cat)
                colors.append(self.triage_colors.get(triage_cat, '#808080'))
            except ValueError:
                colors.append('#808080')
        
        # Bar chart
        bars = ax1.bar(categories, counts, color=colors, alpha=0.8, edgecolor='black')
        ax1.set_xlabel('Triage Category')
        ax1.set_ylabel('Number of Patients')
        ax1.set_title('Triage Category Distribution')
        ax1.grid(True, alpha=0.3)
        
        # Add count labels on bars
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{count}', ha='center', va='bottom', fontweight='bold')
        
        # Pie chart
        wedges, texts, autotexts = ax2.pie(counts, labels=categories, colors=colors,
                                          autopct='%1.1f%%', startangle=90,
                                          explode=[0.05 if cat == 'RED' else 0 for cat in categories])
        ax2.set_title('Triage Category Proportions')
        
        # Enhance pie chart text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        plt.tight_layout()
        
        # Save plot
        if filename is None:
            filename = f"triage_distribution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()
        
        return str(filepath)
    
    def plot_resource_utilization(self, resource_data: Dict[str, float], 
                                 filename: str = None, show: bool = False) -> str:
        """Generate resource utilization visualization
        
        Args:
            resource_data: Dictionary containing resource utilization metrics
            filename: Optional filename for saving the plot
            show: Whether to display the plot
            
        Returns:
            Path to the saved plot file
        """
        if not resource_data:
            raise ValueError("Empty resource utilization data")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Utilization gauge
        utilization = resource_data.get('utilization_percentage', 0)
        
        # Create gauge chart
        theta = np.linspace(0, np.pi, 100)
        r = np.ones_like(theta)
        
        ax1.plot(theta, r, 'k-', linewidth=8)
        
        # Color segments based on utilization level
        util_theta = np.pi * (utilization / 100)
        util_range = np.linspace(0, util_theta, int(utilization))
        
        if utilization < 50:
            color = 'green'
        elif utilization < 80:
            color = 'orange'
        else:
            color = 'red'
        
        ax1.fill_between(util_range, 0, 1, color=color, alpha=0.7)
        ax1.set_xlim(0, np.pi)
        ax1.set_ylim(0, 1.2)
        ax1.set_title(f'Resource Utilization: {utilization:.1f}%', fontsize=14, fontweight='bold')
        ax1.text(np.pi/2, 0.5, f'{utilization:.1f}%', ha='center', va='center', 
                fontsize=20, fontweight='bold')
        ax1.set_xticks([])
        ax1.set_yticks([])
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)
        ax1.spines['bottom'].set_visible(False)
        ax1.spines['left'].set_visible(False)
        
        # Throughput metrics
        patients_per_hour = resource_data.get('patients_per_hour', 0)
        avg_processing_time = resource_data.get('avg_processing_time_seconds', 0)
        
        metrics = ['Patients/Hour', 'Avg Processing\nTime (sec)']
        values = [patients_per_hour, avg_processing_time]
        
        bars = ax2.bar(metrics, values, color=['skyblue', 'lightcoral'], alpha=0.8)
        ax2.set_title('Throughput Metrics')
        ax2.set_ylabel('Value')
        
        # Add value labels
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                    f'{value:.1f}', ha='center', va='bottom', fontweight='bold')
        
        # System time breakdown
        total_time = resource_data.get('total_system_time_seconds', 0)
        processing_time = resource_data.get('total_processing_time_seconds', 0)
        idle_time = total_time - processing_time
        
        if total_time > 0:
            sizes = [processing_time, idle_time]
            labels = ['Processing Time', 'Idle Time']
            colors_pie = ['lightgreen', 'lightgray']
            
            ax3.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90)
            ax3.set_title('System Time Breakdown')
        
        # Performance indicators
        indicators = ['Utilization', 'Efficiency', 'Throughput']
        # Calculate efficiency and throughput scores (0-100)
        efficiency = min(100, (patients_per_hour / 100) * 100) if patients_per_hour else 0
        throughput_score = min(100, patients_per_hour * 2) if patients_per_hour else 0
        
        scores = [utilization, efficiency, throughput_score]
        colors_bar = ['red' if s < 50 else 'orange' if s < 80 else 'green' for s in scores]
        
        bars = ax4.barh(indicators, scores, color=colors_bar, alpha=0.8)
        ax4.set_xlim(0, 100)
        ax4.set_xlabel('Score (0-100)')
        ax4.set_title('Performance Indicators')
        
        # Add score labels
        for bar, score in zip(bars, scores):
            width = bar.get_width()
            ax4.text(width + 1, bar.get_y() + bar.get_height()/2.,
                    f'{score:.1f}', ha='left', va='center', fontweight='bold')
        
        plt.tight_layout()
        
        # Save plot
        if filename is None:
            filename = f"resource_utilization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()
        
        return str(filepath)
    
    def plot_flowchart_usage(self, flowchart_usage: Dict[str, int], 
                            filename: str = None, show: bool = False) -> str:
        """Generate flowchart usage analysis plot
        
        Args:
            flowchart_usage: Dictionary mapping flowchart reasons to usage counts
            filename: Optional filename for saving the plot
            show: Whether to display the plot
            
        Returns:
            Path to the saved plot file
        """
        if not flowchart_usage:
            raise ValueError("Empty flowchart usage data")
        
        # Sort by usage count
        sorted_usage = sorted(flowchart_usage.items(), key=lambda x: x[1], reverse=True)
        reasons = [item[0] for item in sorted_usage]
        counts = [item[1] for item in sorted_usage]
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12))
        
        # Horizontal bar chart for all flowcharts
        y_pos = np.arange(len(reasons))
        bars = ax1.barh(y_pos, counts, alpha=0.8, color='steelblue')
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels([reason.replace('_', ' ').title() for reason in reasons])
        ax1.set_xlabel('Number of Cases')
        ax1.set_title('Flowchart Usage Distribution')
        ax1.grid(True, alpha=0.3, axis='x')
        
        # Add count labels
        for bar, count in zip(bars, counts):
            width = bar.get_width()
            ax1.text(width + max(counts)*0.01, bar.get_y() + bar.get_height()/2.,
                    f'{count}', ha='left', va='center', fontweight='bold')
        
        # Top 10 flowcharts pie chart
        top_10 = sorted_usage[:10]
        if len(sorted_usage) > 10:
            others_count = sum(count for _, count in sorted_usage[10:])
            top_10.append(('Others', others_count))
        
        top_reasons = [item[0] for item in top_10]
        top_counts = [item[1] for item in top_10]
        
        # Generate colors
        colors = plt.cm.Set3(np.linspace(0, 1, len(top_reasons)))
        
        wedges, texts, autotexts = ax2.pie(top_counts, labels=[r.replace('_', ' ').title() for r in top_reasons], 
                                          colors=colors, autopct='%1.1f%%', startangle=90)
        ax2.set_title('Top Flowchart Reasons (Proportional View)')
        
        # Enhance pie chart text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(8)
        
        plt.tight_layout()
        
        # Save plot
        if filename is None:
            filename = f"flowchart_usage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()
        
        return str(filepath)
    
    def create_dashboard(self, metrics_data: Dict[str, Any], 
                        filename: str = None, show: bool = False) -> str:
        """Create a comprehensive dashboard with multiple visualizations
        
        Args:
            metrics_data: Complete metrics data from metrics service
            filename: Optional filename for saving the plot
            show: Whether to display the plot
            
        Returns:
            Path to the saved plot file
        """
        fig = plt.figure(figsize=(20, 16))
        
        # Create grid layout
        gs = fig.add_gridspec(4, 4, hspace=0.3, wspace=0.3)
        
        # 1. Wait time histogram (top left, spans 2 columns)
        ax1 = fig.add_subplot(gs[0, :2])
        if 'wait_time_histogram' in metrics_data:
            hist_data = metrics_data['wait_time_histogram']['histogram']
            bin_centers = hist_data['bin_centers']
            counts = hist_data['counts']
            ax1.bar(bin_centers, counts, alpha=0.7, color='skyblue')
            ax1.set_title('Wait Time Distribution')
            ax1.set_xlabel('Wait Time (minutes)')
            ax1.set_ylabel('Patients')
        
        # 2. Triage distribution pie (top right, spans 2 columns)
        ax2 = fig.add_subplot(gs[0, 2:])
        if 'triage_category_distribution' in metrics_data['system_metrics']:
            triage_dist = metrics_data['system_metrics']['triage_category_distribution']
            categories = list(triage_dist.keys())
            counts = list(triage_dist.values())
            colors = [self.triage_colors.get(TriageCategory(cat), '#808080') for cat in categories]
            ax2.pie(counts, labels=categories, colors=colors, autopct='%1.1f%%')
            ax2.set_title('Triage Category Distribution')
        
        # 3. Arrival curves (second row, spans all columns)
        ax3 = fig.add_subplot(gs[1, :])
        if 'arrival_curve' in metrics_data:
            arrival_data = metrics_data['arrival_curve']
            time_intervals = [datetime.fromisoformat(t) for t in arrival_data['time_intervals']]
            arrivals = arrival_data['arrivals']
            encounters = arrival_data['encounters']
            ax3.plot(time_intervals, arrivals, 'b-o', label='Arrivals', markersize=3)
            ax3.plot(time_intervals, encounters, 'r-s', label='Encounters', markersize=3)
            ax3.set_title('Patient Flow Over Time')
            ax3.set_xlabel('Time')
            ax3.set_ylabel('Number of Patients')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
        
        # 4. Resource utilization gauge (third row, left)
        ax4 = fig.add_subplot(gs[2, :2])
        if 'resource_utilization' in metrics_data['system_metrics']:
            utilization = metrics_data['system_metrics']['resource_utilization']['utilization_percentage']
            
            # Simple gauge representation
            theta = np.linspace(0, np.pi, 100)
            r = np.ones_like(theta)
            ax4.plot(theta, r, 'k-', linewidth=6)
            
            util_theta = np.pi * (utilization / 100)
            util_range = np.linspace(0, util_theta, max(1, int(utilization)))
            color = 'green' if utilization < 50 else 'orange' if utilization < 80 else 'red'
            ax4.fill_between(util_range, 0, 1, color=color, alpha=0.7)
            
            ax4.set_title(f'Resource Utilization: {utilization:.1f}%')
            ax4.text(np.pi/2, 0.5, f'{utilization:.1f}%', ha='center', va='center', 
                    fontsize=16, fontweight='bold')
            ax4.set_xlim(0, np.pi)
            ax4.set_ylim(0, 1.2)
            ax4.axis('off')
        
        # 5. Key metrics summary (third row, right)
        ax5 = fig.add_subplot(gs[2, 2:])
        ax5.axis('off')
        
        # Create metrics summary text
        summary_text = "📊 KEY METRICS SUMMARY\n\n"
        if 'system_metrics' in metrics_data:
            sm = metrics_data['system_metrics']
            summary_text += f"Total Patients: {sm.get('total_patients', 0)}\n"
            summary_text += f"Avg Wait Time: {sm['wait_time_statistics'].get('mean_minutes', 0):.1f} min\n"
            summary_text += f"Median Wait Time: {sm['wait_time_statistics'].get('median_minutes', 0):.1f} min\n"
            summary_text += f"Peak Hour: {sm.get('peak_arrival_hour', 0)}:00\n"
            
            if 'resource_utilization' in sm:
                ru = sm['resource_utilization']
                summary_text += f"Patients/Hour: {ru.get('patients_per_hour', 0):.1f}\n"
                summary_text += f"Utilization: {ru.get('utilization_percentage', 0):.1f}%"
        
        ax5.text(0.1, 0.9, summary_text, transform=ax5.transAxes, fontsize=12,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        # 6. Top flowchart usage (bottom row)
        ax6 = fig.add_subplot(gs[3, :])
        if 'flowchart_usage' in metrics_data['system_metrics']:
            flowchart_usage = metrics_data['system_metrics']['flowchart_usage']
            sorted_usage = sorted(flowchart_usage.items(), key=lambda x: x[1], reverse=True)[:8]
            reasons = [item[0].replace('_', ' ').title() for item in sorted_usage]
            counts = [item[1] for item in sorted_usage]
            
            bars = ax6.bar(reasons, counts, alpha=0.8, color='lightcoral')
            ax6.set_title('Top Flowchart Usage')
            ax6.set_xlabel('Flowchart Reason')
            ax6.set_ylabel('Number of Cases')
            ax6.tick_params(axis='x', rotation=45)
            
            # Add count labels
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                ax6.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                        f'{count}', ha='center', va='bottom', fontsize=8)
        
        # Add main title
        fig.suptitle('Manchester Triage System - Analytics Dashboard', 
                    fontsize=20, fontweight='bold', y=0.98)
        
        # Save plot
        if filename is None:
            filename = f"dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        filepath = self.output_dir / filename
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        
        if show:
            plt.show()
        else:
            plt.close()
        
        return str(filepath)
    
    def get_available_plot_types(self) -> List[str]:
        """Get list of available plot types
        
        Returns:
            List of available plotting methods
        """
        return [
            'wait_time_histogram',
            'arrival_curves', 
            'triage_distribution',
            'resource_utilization',
            'flowchart_usage',
            'dashboard'
        ]
    
    def clear_output_directory(self) -> None:
        """Clear all files in the output directory"""
        for file in self.output_dir.glob('*.png'):
            file.unlink()