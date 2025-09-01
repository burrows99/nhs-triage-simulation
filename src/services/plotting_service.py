"""Plotting Service for NHS Metrics Visualization

This service provides comprehensive plotting capabilities for NHS metrics,
including various chart types and customization options.

Single Responsibility: Only handles data visualization and plotting
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import os


class PlottingService:
    """Centralized plotting service for NHS metrics visualization."""
    
    def __init__(self, style: str = 'seaborn-v0_8', figsize: Tuple[int, int] = (12, 8)):
        """Initialize plotting service with style and default figure size.
        
        Args:
            style: Matplotlib style to use
            figsize: Default figure size (width, height)
        """
        plt.style.use(style)
        sns.set_palette("husl")
        self.default_figsize = figsize
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72', 
            'success': '#F18F01',
            'warning': '#C73E1D',
            'info': '#6A994E',
            'nhs_blue': '#005EB8',
            'nhs_green': '#009639',
            'nhs_red': '#DA020E'
        }
    
    def create_compliance_chart(self, compliance_data: Dict[str, float], 
                              title: str = "NHS 4-Hour Standard Compliance",
                              save_path: Optional[str] = None) -> plt.Figure:
        """Create a compliance rate chart.
        
        Args:
            compliance_data: Dictionary with compliance metrics
            title: Chart title
            save_path: Optional path to save the chart
            
        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.default_figsize)
        
        # Extract compliance rate
        compliance_rate = compliance_data.get('4hour_standard_compliance_pct', 0)
        
        # Create gauge-style chart
        angles = np.linspace(0, np.pi, 100)
        values = np.ones_like(angles) * compliance_rate / 100
        
        # Plot compliance arc
        ax.fill_between(angles, 0, values, alpha=0.7, color=self.colors['nhs_green'] if compliance_rate >= 95 else self.colors['nhs_red'])
        ax.fill_between(angles, values, 1, alpha=0.3, color='lightgray')
        
        # Add target lines
        target_95 = np.ones_like(angles) * 0.95
        target_76 = np.ones_like(angles) * 0.76
        ax.plot(angles, target_95, '--', color=self.colors['nhs_blue'], linewidth=2, label='95% Target')
        ax.plot(angles, target_76, '--', color=self.colors['warning'], linewidth=2, label='76% Interim Target')
        
        # Formatting
        ax.set_ylim(0, 1)
        ax.set_xlim(0, np.pi)
        ax.set_title(f"{title}\n{compliance_rate:.1f}%", fontsize=16, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Remove x-axis labels for cleaner look
        ax.set_xticks([])
        ax.set_ylabel('Compliance Rate')
        
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def create_triage_distribution_chart(self, triage_data: Dict[str, int],
                                       title: str = "Triage Category Distribution",
                                       save_path: Optional[str] = None) -> plt.Figure:
        """Create a triage category distribution pie chart.
        
        Args:
            triage_data: Dictionary with triage category counts
            title: Chart title
            save_path: Optional path to save the chart
            
        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.default_figsize)
        
        categories = list(triage_data.keys())
        counts = list(triage_data.values())
        
        # NHS triage colors
        triage_colors = {
            'RED': '#DA020E',
            'ORANGE': '#FF8C00',
            'YELLOW': '#FFD700',
            'GREEN': '#009639',
            'BLUE': '#005EB8'
        }
        
        colors = [triage_colors.get(cat, self.colors['primary']) for cat in categories]
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(counts, labels=categories, colors=colors, 
                                         autopct='%1.1f%%', startangle=90)
        
        # Enhance text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title(title, fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def create_time_distribution_chart(self, time_data: List[float],
                                     title: str = "Patient Time Distribution",
                                     save_path: Optional[str] = None) -> plt.Figure:
        """Create a histogram of patient times.
        
        Args:
            time_data: List of patient times in minutes
            title: Chart title
            save_path: Optional path to save the chart
            
        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=self.default_figsize)
        
        # Create histogram
        n, bins, patches = ax.hist(time_data, bins=20, alpha=0.7, color=self.colors['primary'], edgecolor='black')
        
        # Add 4-hour line
        ax.axvline(x=240, color=self.colors['nhs_red'], linestyle='--', linewidth=2, label='4-Hour Standard')
        
        # Add statistics
        mean_time = np.mean(time_data)
        median_time = np.median(time_data)
        ax.axvline(x=mean_time, color=self.colors['warning'], linestyle='-', linewidth=2, label=f'Mean: {mean_time:.1f} min')
        ax.axvline(x=median_time, color=self.colors['success'], linestyle='-', linewidth=2, label=f'Median: {median_time:.1f} min')
        
        ax.set_xlabel('Time in A&E (minutes)')
        ax.set_ylabel('Number of Patients')
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def create_age_group_analysis_chart(self, age_data: Dict[str, Dict[str, float]],
                                      title: str = "Age Group Analysis",
                                      save_path: Optional[str] = None) -> plt.Figure:
        """Create age group analysis bar chart.
        
        Args:
            age_data: Dictionary with age group data
            title: Chart title
            save_path: Optional path to save the chart
            
        Returns:
            Matplotlib figure object
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        age_groups = list(age_data.keys())
        patient_counts = [age_data[group]['count'] for group in age_groups]
        avg_times = [age_data[group]['avg_time'] for group in age_groups]
        compliance_rates = [age_data[group]['compliance_pct'] for group in age_groups]
        
        # Patient counts by age group
        bars1 = ax1.bar(age_groups, patient_counts, color=self.colors['primary'], alpha=0.7)
        ax1.set_title('Patient Count by Age Group', fontweight='bold')
        ax1.set_ylabel('Number of Patients')
        ax1.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom')
        
        # Average times and compliance by age group
        ax2_twin = ax2.twinx()
        
        bars2 = ax2.bar(age_groups, avg_times, color=self.colors['secondary'], alpha=0.7, label='Avg Time')
        line = ax2_twin.plot(age_groups, compliance_rates, color=self.colors['nhs_green'], 
                           marker='o', linewidth=3, markersize=8, label='Compliance %')
        
        ax2.set_title('Average Time & Compliance by Age Group', fontweight='bold')
        ax2.set_ylabel('Average Time (minutes)', color=self.colors['secondary'])
        ax2_twin.set_ylabel('Compliance Rate (%)', color=self.colors['nhs_green'])
        ax2.grid(True, alpha=0.3)
        
        # Add 95% compliance line
        ax2_twin.axhline(y=95, color=self.colors['nhs_red'], linestyle='--', alpha=0.7, label='95% Target')
        
        # Combine legends
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_twin.get_legend_handles_labels()
        ax2_twin.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        
        plt.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def create_performance_dashboard(self, metrics_data: Dict[str, Any],
                                   title: str = "NHS A&E Performance Dashboard",
                                   save_path: Optional[str] = None) -> plt.Figure:
        """Create a comprehensive performance dashboard.
        
        Args:
            metrics_data: Complete NHS metrics data
            title: Dashboard title
            save_path: Optional path to save the dashboard
            
        Returns:
            Matplotlib figure object
        """
        fig = plt.figure(figsize=(20, 12))
        gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)
        
        # 1. Compliance gauge (top left)
        ax1 = fig.add_subplot(gs[0, 0])
        compliance_rate = metrics_data.get('4hour_standard_compliance_pct', 0)
        self._create_gauge(ax1, compliance_rate, "4-Hour Compliance", "%")
        
        # 2. Key metrics (top middle-right)
        ax2 = fig.add_subplot(gs[0, 1:3])
        key_metrics = {
            'Total Patients': metrics_data.get('total_attendances', 0),
            'Avg Time (min)': metrics_data.get('avg_total_time_minutes', 0),
            'Admission Rate (%)': metrics_data.get('admission_rate_pct', 0),
            'LWBS Rate (%)': metrics_data.get('left_before_seen_rate_pct', 0)
        }
        self._create_metrics_table(ax2, key_metrics)
        
        # 3. Triage distribution (top right)
        ax3 = fig.add_subplot(gs[0, 3])
        if 'triage_distribution' in metrics_data:
            triage_data = metrics_data['triage_distribution']
            categories = list(triage_data.keys())
            counts = list(triage_data.values())
            ax3.pie(counts, labels=categories, autopct='%1.1f%%')
            ax3.set_title('Triage Distribution')
        
        # 4. Time distribution histogram (middle)
        ax4 = fig.add_subplot(gs[1, :])
        if 'patient_times' in metrics_data:
            times = metrics_data['patient_times']
            ax4.hist(times, bins=20, alpha=0.7, color=self.colors['primary'])
            ax4.axvline(x=240, color=self.colors['nhs_red'], linestyle='--', label='4-Hour Standard')
            ax4.set_xlabel('Time in A&E (minutes)')
            ax4.set_ylabel('Number of Patients')
            ax4.set_title('Patient Time Distribution')
            ax4.legend()
        
        # 5. Age group analysis (bottom)
        ax5 = fig.add_subplot(gs[2, :])
        if 'age_groups' in metrics_data:
            age_data = metrics_data['age_groups']
            age_groups = list(age_data.keys())
            counts = [age_data[group]['count'] for group in age_groups]
            ax5.bar(age_groups, counts, color=self.colors['secondary'], alpha=0.7)
            ax5.set_title('Patient Count by Age Group')
            ax5.set_ylabel('Number of Patients')
        
        plt.suptitle(title, fontsize=20, fontweight='bold')
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def _create_gauge(self, ax, value: float, title: str, unit: str = ""):
        """Create a gauge chart for a single metric."""
        # Create semicircle gauge
        theta = np.linspace(0, np.pi, 100)
        r = np.ones_like(theta)
        
        # Background
        ax.fill_between(theta, 0, r, alpha=0.3, color='lightgray')
        
        # Value fill
        value_normalized = min(value / 100, 1.0)
        value_theta = theta[theta <= np.pi * value_normalized]
        value_r = r[:len(value_theta)]
        
        color = self.colors['nhs_green'] if value >= 95 else self.colors['nhs_red']
        ax.fill_between(value_theta, 0, value_r, alpha=0.8, color=color)
        
        # Center text
        ax.text(np.pi/2, 0.5, f"{value:.1f}{unit}", ha='center', va='center', 
               fontsize=14, fontweight='bold')
        ax.text(np.pi/2, 0.2, title, ha='center', va='center', fontsize=10)
        
        ax.set_xlim(0, np.pi)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
    
    def _create_metrics_table(self, ax, metrics: Dict[str, float]):
        """Create a metrics table."""
        ax.axis('tight')
        ax.axis('off')
        
        table_data = [[key, f"{value:.1f}"] for key, value in metrics.items()]
        table = ax.table(cellText=table_data, colLabels=['Metric', 'Value'],
                        cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1.2, 1.5)
        
        # Style the table
        for i in range(len(metrics) + 1):
            for j in range(2):
                cell = table[(i, j)]
                if i == 0:  # Header
                    cell.set_facecolor(self.colors['nhs_blue'])
                    cell.set_text_props(weight='bold', color='white')
                else:
                    cell.set_facecolor('lightgray' if i % 2 == 0 else 'white')
    
    def _save_figure(self, fig: plt.Figure, save_path: str):
        """Save figure to specified path."""
        # Ensure directory exists
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save with high DPI
        fig.savefig(save_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
    
    def close_all_figures(self):
        """Close all matplotlib figures to free memory."""
        plt.close('all')
    
    def set_style(self, style: str):
        """Change matplotlib style."""
        plt.style.use(style)
    
    def get_available_styles(self) -> List[str]:
        """Get list of available matplotlib styles."""
        return plt.style.available