"""Plotting Service for Metrics Visualization

This service provides comprehensive plotting capabilities for all types of metrics,
including NHS metrics, operational metrics, and custom visualizations.

Single Responsibility: Only handles data visualization and plotting
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import os

# Import centralized logger
from src.logger import logger


class PlottingService:
    """Centralized plotting service for all metrics visualization."""
    
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
        
        # Registry for metric services
        self.metric_services: Dict[str, Any] = {}
        
        logger.info("Plotting service initialized")
    
    def register_metric_service(self, name: str, service: Any) -> None:
        """Register a metric service for plotting
        
        Args:
            name: Name identifier for the service
            service: Metric service instance
        """
        self.metric_services[name] = service
        logger.info(f"Registered metric service: {name}")
    
    def unregister_metric_service(self, name: str) -> None:
        """Unregister a metric service
        
        Args:
            name: Name of service to unregister
        """
        if name in self.metric_services:
            del self.metric_services[name]
            logger.info(f"Unregistered metric service: {name}")
    
    def get_metric_service(self, name: str) -> Optional[Any]:
        """Get a registered metric service
        
        Args:
            name: Name of service to retrieve
            
        Returns:
            Metric service instance or None
        """
        return self.metric_services.get(name)
    
    def create_compliance_chart(self, compliance_data: Dict[str, float], 
                              title: str = "NHS 4-Hour A&E Standard Compliance",
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
        
        # Check if this is an error case (no completed patients)
        if 'error' in compliance_data:
            # Create an informative chart for the error case
            ax.text(0.5, 0.6, 'NHS 4-Hour A&E Standard Compliance', 
                   ha='center', va='center', fontsize=16, fontweight='bold', transform=ax.transAxes)
            ax.text(0.5, 0.5, f"Status: {compliance_data['error']}", 
                   ha='center', va='center', fontsize=14, color='red', transform=ax.transAxes)
            ax.text(0.5, 0.4, f"Total Attendances: {compliance_data.get('total_attendances', 0)}", 
                   ha='center', va='center', fontsize=12, transform=ax.transAxes)
            ax.text(0.5, 0.35, f"Active Patients: {compliance_data.get('active_patients', 0)}", 
                   ha='center', va='center', fontsize=12, transform=ax.transAxes)
            ax.text(0.5, 0.25, 'Patients are still in the system and have not completed their journey', 
                   ha='center', va='center', fontsize=10, style='italic', transform=ax.transAxes)
            ax.text(0.5, 0.2, 'Charts will be generated once patients complete their A&E journey', 
                   ha='center', va='center', fontsize=10, style='italic', transform=ax.transAxes)
            
            # Remove axes for clean look
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['left'].set_visible(False)
        else:
            # Extract compliance rate for normal case
            compliance_rate = compliance_data.get('4hour_standard_compliance_pct', 0)
            total_patients = compliance_data.get('total_attendances', 0)
            within_4hrs = compliance_data.get('attendances_within_4hours', 0)
            over_4hrs = compliance_data.get('attendances_over_4hours', 0)
            
            # Create gauge-style chart
            angles = np.linspace(0, np.pi, 100)
            values = np.ones_like(angles) * compliance_rate / 100
            
            # Plot compliance arc
            ax.fill_between(angles, 0, values, alpha=0.7, color=self.colors['nhs_green'] if compliance_rate >= 95 else self.colors['nhs_red'])
            ax.fill_between(angles, values, 1, alpha=0.3, color='lightgray')
            
            # Add target lines
            target_95 = np.ones_like(angles) * 0.95
            target_76 = np.ones_like(angles) * 0.76
            ax.plot(angles, target_95, '--', color=self.colors['nhs_blue'], linewidth=2, label='95% NHS Target (Official)')
            ax.plot(angles, target_76, '--', color=self.colors['warning'], linewidth=2, label='76% Interim Target')
            
            # Formatting
            ax.set_ylim(0, 1)
            ax.set_xlim(0, np.pi)
            detailed_title = f"{title}\n{compliance_rate:.1f}% of patients seen within 4 hours\n({within_4hrs}/{total_patients} patients)"
            ax.set_title(detailed_title, fontsize=14, fontweight='bold')
            ax.legend(loc='upper right')
            ax.grid(True, alpha=0.3)
            
            # Remove x-axis labels for cleaner look
            ax.set_xticks([])
            ax.set_ylabel('Compliance Rate (% of patients within 240 minutes)', fontsize=10)
            
            # Add explanatory text
            ax.text(np.pi/2, -0.15, 'Total Time = Arrival to Departure from A&E\nIncludes: Triage + Doctor Assessment + Diagnostics + Disposition', 
                    ha='center', va='top', fontsize=9, style='italic', transform=ax.transData)
        
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def create_utilization_chart(self, utilization_data: Dict[str, Dict[str, float]],
                               title: str = "Resource Utilization Analysis",
                               save_path: Optional[str] = None) -> plt.Figure:
        """Create a resource utilization chart.
        
        Args:
            utilization_data: Dictionary with utilization metrics per resource
            title: Chart title
            save_path: Optional path to save the chart
            
        Returns:
            Matplotlib figure object
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Extract data for plotting
        resources = list(utilization_data.keys())
        avg_utilizations = [utilization_data[r].get('average_utilization_pct', 0) for r in resources]
        peak_utilizations = [utilization_data[r].get('peak_utilization_pct', 0) for r in resources]
        
        # Bar chart for average vs peak utilization
        x = np.arange(len(resources))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, avg_utilizations, width, label='Average Utilization', 
                        color=self.colors['primary'], alpha=0.8)
        bars2 = ax1.bar(x + width/2, peak_utilizations, width, label='Peak Utilization', 
                        color=self.colors['warning'], alpha=0.8)
        
        ax1.set_xlabel('Resources')
        ax1.set_ylabel('Utilization (%)')
        ax1.set_title('Average vs Peak Utilization')
        ax1.set_xticks(x)
        ax1.set_xticklabels(resources)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for bar in bars1:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.1f}%', ha='center', va='bottom')
        
        for bar in bars2:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.1f}%', ha='center', va='bottom')
        
        # Pie chart for resource distribution
        if avg_utilizations:
            ax2.pie(avg_utilizations, labels=resources, autopct='%1.1f%%',
                   colors=[self.colors['primary'], self.colors['secondary'], self.colors['success']][:len(resources)])
            ax2.set_title('Utilization Distribution')
        
        plt.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def create_queue_analysis_chart(self, queue_data: Dict[str, Dict[str, float]],
                                  title: str = "Queue Performance Analysis",
                                  save_path: Optional[str] = None) -> plt.Figure:
        """Create a queue performance analysis chart.
        
        Args:
            queue_data: Dictionary with queue metrics per resource
            title: Chart title
            save_path: Optional path to save the chart
            
        Returns:
            Matplotlib figure object
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        resources = list(queue_data.keys())
        
        if not resources:
            ax1.text(0.5, 0.5, 'No queue data available', ha='center', va='center')
            return fig
        
        # Average queue lengths
        avg_queues = [queue_data[r].get('average_queue_length', 0) for r in resources]
        ax1.bar(resources, avg_queues, color=self.colors['info'], alpha=0.8)
        ax1.set_title('Average Queue Length')
        ax1.set_ylabel('Queue Length')
        ax1.grid(True, alpha=0.3)
        
        # Peak queue lengths (convert strings to numbers and handle NaN)
        peak_queues = []
        for r in resources:
            peak_val = queue_data[r].get('peak_queue_length', 0)
            # Convert string to number if needed
            if isinstance(peak_val, str):
                try:
                    peak_val = float(peak_val)
                except (ValueError, TypeError):
                    peak_val = 0
            # Handle NaN values
            if pd.isna(peak_val) or np.isnan(peak_val) if isinstance(peak_val, (int, float)) else False:
                peak_val = 0
            peak_queues.append(peak_val)
        ax2.bar(resources, peak_queues, color=self.colors['warning'], alpha=0.8)
        ax2.set_title('Peak Queue Length')
        ax2.set_ylabel('Queue Length')
        ax2.grid(True, alpha=0.3)
        
        # Time with queue percentage
        time_with_queue = [queue_data[r].get('time_with_queue', 0) for r in resources]
        ax3.bar(resources, time_with_queue, color=self.colors['secondary'], alpha=0.8)
        ax3.set_title('Time with Queue (%)')
        ax3.set_ylabel('Percentage of Time')
        ax3.grid(True, alpha=0.3)
        
        # Queue length distribution (if we have std dev data)
        if all('queue_length_std_dev' in queue_data[r] for r in resources):
            std_devs = [queue_data[r]['queue_length_std_dev'] for r in resources]
            ax4.bar(resources, std_devs, color=self.colors['success'], alpha=0.8)
            ax4.set_title('Queue Length Variability (Std Dev)')
            ax4.set_ylabel('Standard Deviation')
            ax4.grid(True, alpha=0.3)
        else:
            ax4.text(0.5, 0.5, 'No variability data available', ha='center', va='center')
        
        plt.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def create_combined_dashboard(self, nhs_metrics: Optional[Dict] = None,
                                operation_metrics: Optional[Dict] = None,
                                title: str = "Hospital Performance Dashboard",
                                save_path: Optional[str] = None) -> plt.Figure:
        """Create a combined dashboard with both NHS and operational metrics.
        
        Args:
            nhs_metrics: NHS metrics data
            operation_metrics: Operational metrics data
            title: Dashboard title
            save_path: Optional path to save the dashboard
            
        Returns:
            Matplotlib figure object
        """
        fig = plt.figure(figsize=(20, 16))
        
        # Create a grid layout
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # NHS Compliance (top left)
        if nhs_metrics:
            ax1 = fig.add_subplot(gs[0, 0])
            if 'error' in nhs_metrics:
                # Handle error case
                ax1.text(0.5, 0.6, 'NHS 4-Hour Standard', ha='center', va='center', fontsize=12, fontweight='bold', transform=ax1.transAxes)
                ax1.text(0.5, 0.4, f"{nhs_metrics['error']}", ha='center', va='center', fontsize=10, color='red', transform=ax1.transAxes)
                ax1.text(0.5, 0.2, f"Active: {nhs_metrics.get('active_patients', 0)}", ha='center', va='center', fontsize=10, transform=ax1.transAxes)
                ax1.set_xlim(0, 1)
                ax1.set_ylim(0, 1)
                ax1.set_xticks([])
                ax1.set_yticks([])
                for spine in ax1.spines.values():
                    spine.set_visible(False)
            else:
                compliance_rate = nhs_metrics.get('4hour_standard_compliance_pct', 0)
                ax1.pie([compliance_rate, 100-compliance_rate], 
                       labels=['Within 4hrs', 'Over 4hrs'],
                       colors=[self.colors['nhs_green'], self.colors['nhs_red']],
                       autopct='%1.1f%%')
                ax1.set_title(f'NHS 4-Hour Standard\n{compliance_rate:.1f}% Compliance')
        
        # Resource Utilization (top middle)
        if operation_metrics and 'utilization' in operation_metrics:
            ax2 = fig.add_subplot(gs[0, 1])
            util_data = operation_metrics['utilization']
            resources = list(util_data.keys())
            utilizations = [util_data[r].get('average_utilization_pct', 0) for r in resources]
            
            bars = ax2.bar(resources, utilizations, 
                          color=[self.colors['primary'], self.colors['secondary'], self.colors['success']][:len(resources)])
            ax2.set_title('Average Resource Utilization')
            ax2.set_ylabel('Utilization (%)')
            ax2.grid(True, alpha=0.3)
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                        f'{height:.1f}%', ha='center', va='bottom')
        
        # Queue Performance (top right)
        if operation_metrics and 'queues' in operation_metrics:
            ax3 = fig.add_subplot(gs[0, 2])
            queue_data = operation_metrics['queues']
            resources = list(queue_data.keys())
            avg_queues = [queue_data[r].get('average_queue_length', 0) for r in resources]
            
            ax3.bar(resources, avg_queues, color=self.colors['info'])
            ax3.set_title('Average Queue Lengths')
            ax3.set_ylabel('Queue Length')
            ax3.grid(True, alpha=0.3)
        
        # NHS Triage Distribution (middle left)
        if nhs_metrics and 'triage_category_distribution' in nhs_metrics and 'error' not in nhs_metrics:
            ax4 = fig.add_subplot(gs[1, 0])
            triage_dist = nhs_metrics['triage_category_distribution']
            if triage_dist:
                categories = list(triage_dist.keys())
                counts = list(triage_dist.values())
                ax4.pie(counts, labels=categories, autopct='%1.1f%%')
                ax4.set_title('Triage Category Distribution')
        
        # Wait Times (middle center)
        if operation_metrics and 'wait_times' in operation_metrics:
            ax5 = fig.add_subplot(gs[1, 1])
            wait_data = operation_metrics['wait_times']
            resources = list(wait_data.keys())
            avg_waits = [wait_data[r].get('average_wait_time_minutes', 0) for r in resources]
            
            ax5.bar(resources, avg_waits, color=self.colors['warning'])
            ax5.set_title('Average Wait Times')
            ax5.set_ylabel('Wait Time (minutes)')
            ax5.grid(True, alpha=0.3)
        
        # System Performance Summary (bottom span)
        ax6 = fig.add_subplot(gs[2, :])
        
        # Create summary text
        summary_text = "System Performance Summary\n\n"
        
        if nhs_metrics:
            summary_text += f"NHS Metrics:\n"
            if 'error' in nhs_metrics:
                summary_text += f"• Status: {nhs_metrics['error']}\n"
                summary_text += f"• Total Attendances: {nhs_metrics.get('total_attendances', 0)}\n"
                summary_text += f"• Active Patients: {nhs_metrics.get('active_patients', 0)}\n"
            else:
                summary_text += f"• Total Patients: {nhs_metrics.get('total_attendances', 0)}\n"
                summary_text += f"• 4-Hour Compliance: {nhs_metrics.get('4hour_standard_compliance_pct', 0):.1f}%\n"
                summary_text += f"• Average Time in A&E: {nhs_metrics.get('5_total_time_in_ae_avg_minutes', 0):.1f} minutes\n"
                summary_text += f"• Admission Rate: {nhs_metrics.get('admission_rate_pct', 0):.1f}%\n"
            summary_text += "\n"
        
        if operation_metrics:
            summary_text += f"Operational Metrics:\n"
            if 'system_performance' in operation_metrics:
                sys_perf = operation_metrics['system_performance']
                summary_text += f"• Simulation Duration: {sys_perf.get('simulation_duration_minutes', 0):.1f} minutes\n"
                summary_text += f"• Total Snapshots: {sys_perf.get('total_snapshots', 0)}\n"
                summary_text += f"• Processing Rate: {sys_perf.get('processing_rate_per_hour', 0):.1f} patients/hour\n"
        
        ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes, 
                fontsize=12, verticalalignment='top', fontfamily='monospace')
        ax6.set_xlim(0, 1)
        ax6.set_ylim(0, 1)
        ax6.axis('off')
        
        plt.suptitle(title, fontsize=20, fontweight='bold')
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def generate_all_charts(self, output_dir: str = "./output/plots") -> Dict[str, str]:
        """Generate all available charts for registered metric services.
        
        Args:
            output_dir: Directory to save charts
            
        Returns:
            Dictionary mapping chart names to file paths
        """
        os.makedirs(output_dir, exist_ok=True)
        generated_charts = {}
        
        # Generate NHS charts if NHS metrics service is registered
        nhs_service = self.get_metric_service('nhs')
        if nhs_service:
            try:
                nhs_metrics = nhs_service.calculate_metrics()
                
                # Compliance chart
                compliance_path = os.path.join(output_dir, 'nhs_compliance.png')
                self.create_compliance_chart(nhs_metrics, save_path=compliance_path)
                generated_charts['nhs_compliance'] = compliance_path
                
                # Triage distribution
                if 'triage_category_distribution' in nhs_metrics:
                    triage_path = os.path.join(output_dir, 'triage_distribution.png')
                    self.create_triage_distribution_chart(nhs_metrics['triage_category_distribution'], save_path=triage_path)
                    generated_charts['triage_distribution'] = triage_path
                
                logger.info("Generated NHS charts")
            except Exception as e:
                logger.error(f"Error generating NHS charts: {e}")
        
        # Generate operational charts if operation metrics service is registered
        op_service = self.get_metric_service('operations')
        if op_service:
            try:
                op_metrics = op_service.calculate_metrics()
                
                # Utilization chart
                if 'utilization' in op_metrics:
                    util_path = os.path.join(output_dir, 'resource_utilization.png')
                    self.create_utilization_chart(op_metrics['utilization'], save_path=util_path)
                    generated_charts['resource_utilization'] = util_path
                
                # Queue analysis
                if 'queues' in op_metrics:
                    queue_path = os.path.join(output_dir, 'queue_analysis.png')
                    self.create_queue_analysis_chart(op_metrics['queues'], save_path=queue_path)
                    generated_charts['queue_analysis'] = queue_path
                
                logger.info("Generated operational charts")
            except Exception as e:
                logger.error(f"Error generating operational charts: {e}")
        
        # Generate combined dashboard if both services are available
        if nhs_service and op_service:
            try:
                nhs_metrics = nhs_service.calculate_metrics()
                op_metrics = op_service.calculate_metrics()
                
                dashboard_path = os.path.join(output_dir, 'combined_dashboard.png')
                self.create_combined_dashboard(nhs_metrics, op_metrics, save_path=dashboard_path)
                generated_charts['combined_dashboard'] = dashboard_path
                
                logger.info("Generated combined dashboard")
            except Exception as e:
                logger.error(f"Error generating combined dashboard: {e}")
        
        return generated_charts
    
    def create_triage_distribution_chart(self, triage_data: Dict[str, int],
                                       title: str = "Manchester Triage System (MTS) Category Distribution",
                                       save_path: Optional[str] = None) -> plt.Figure:
        """Create a triage category distribution pie chart.
        
        Args:
            triage_data: Dictionary with triage category counts
            title: Chart title
            save_path: Optional path to save the chart
            
        Returns:
            Matplotlib figure object
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        categories = list(triage_data.keys())
        counts = list(triage_data.values())
        total_patients = sum(counts)
        
        # NHS triage colors
        triage_colors = {
            'RED': '#DA020E',
            'ORANGE': '#FF8C00',
            'YELLOW': '#FFD700',
            'GREEN': '#009639',
            'BLUE': '#005EB8'
        }
        
        # Triage category descriptions
        triage_descriptions = {
            'RED': 'Immediate (Life-threatening)',
            'ORANGE': 'Very Urgent (10 min max wait)',
            'YELLOW': 'Urgent (60 min max wait)',
            'GREEN': 'Standard (120 min max wait)',
            'BLUE': 'Non-urgent (240 min max wait)'
        }
        
        colors = [triage_colors.get(cat, self.colors['primary']) for cat in categories]
        
        # Create pie chart
        wedges, texts, autotexts = ax1.pie(counts, labels=categories, colors=colors, 
                                         autopct='%1.1f%%', startangle=90)
        
        # Enhance text
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax1.set_title(f"{title}\nTotal Patients: {total_patients}", fontsize=14, fontweight='bold')
        
        # Create legend table with detailed descriptions
        ax2.axis('off')
        legend_data = []
        for cat in ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE']:
            if cat in triage_data:
                count = triage_data[cat]
                pct = (count / total_patients) * 100 if total_patients > 0 else 0
                legend_data.append([
                    cat,
                    triage_descriptions.get(cat, ''),
                    f"{count} ({pct:.1f}%)"
                ])
        
        if legend_data:
            table = ax2.table(cellText=legend_data, 
                            colLabels=['Category', 'Clinical Priority & Max Wait Time', 'Count (%)'],
                            cellLoc='left', loc='center', colWidths=[0.15, 0.6, 0.25])
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1.2, 2)
            
            # Color code the category column
            for i, cat_data in enumerate(legend_data):
                cat = cat_data[0]
                if cat in triage_colors:
                    table[(i+1, 0)].set_facecolor(triage_colors[cat])
                    table[(i+1, 0)].set_text_props(weight='bold', color='white')
        
        ax2.set_title('MTS Category Definitions\n(Based on Clinical Urgency)', fontsize=12, fontweight='bold')
        
        plt.suptitle('Patient Distribution by Manchester Triage System Categories', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def create_time_distribution_chart(self, time_data: List[float],
                                     title: str = "Total Patient Journey Time Distribution",
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
        
        # Calculate statistics
        mean_time = np.mean(time_data)
        median_time = np.median(time_data)
        percentile_95 = np.percentile(time_data, 95)
        total_patients = len(time_data)
        within_4hrs = sum(1 for t in time_data if t <= 240)
        
        # Create histogram
        n, bins, patches = ax.hist(time_data, bins=20, alpha=0.7, color=self.colors['primary'], 
                                 edgecolor='black', label=f'Patient Distribution (n={total_patients})')
        
        # Add 4-hour line
        ax.axvline(x=240, color=self.colors['nhs_red'], linestyle='--', linewidth=3, 
                  label=f'NHS 4-Hour Standard (240 min)\n{within_4hrs}/{total_patients} patients within target')
        
        # Add statistics lines
        ax.axvline(x=mean_time, color=self.colors['warning'], linestyle='-', linewidth=2, 
                  label=f'Mean Total Time: {mean_time:.1f} min')
        ax.axvline(x=median_time, color=self.colors['success'], linestyle='-', linewidth=2, 
                  label=f'Median Total Time: {median_time:.1f} min')
        ax.axvline(x=percentile_95, color=self.colors['info'], linestyle=':', linewidth=2, 
                  label=f'95th Percentile: {percentile_95:.1f} min')
        
        # Enhanced labeling
        ax.set_xlabel('Total Time in A&E (minutes)\nFrom Arrival to Departure', fontsize=12, fontweight='bold')
        ax.set_ylabel('Number of Patients', fontsize=12, fontweight='bold')
        
        detailed_title = f"{title}\nComplete Patient Journey: Arrival → Triage → Doctor → Diagnostics → Disposition → Departure"
        ax.set_title(detailed_title, fontsize=14, fontweight='bold')
        
        # Position legend outside plot area
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # Add explanatory text box
        textstr = 'Total Time Components:\n• Wait time for triage\n• Triage assessment (nurse)\n• Wait time for doctor\n• Doctor assessment\n• Diagnostics (if required)\n• Disposition (discharge/admit)'
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
        ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=9,
                verticalalignment='top', bbox=props)
        
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def create_age_group_analysis_chart(self, age_data: Dict[str, Dict[str, float]],
                                      title: str = "Patient Demographics & Performance Analysis by Age Group",
                                      save_path: Optional[str] = None) -> plt.Figure:
        """Create age group analysis bar chart.
        
        Args:
            age_data: Dictionary with age group data
            title: Chart title
            save_path: Optional path to save the chart
            
        Returns:
            Matplotlib figure object
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
        
        age_groups = list(age_data.keys())
        patient_counts = [age_data[group]['count'] for group in age_groups]
        avg_times = [age_data[group]['avg_time_minutes'] for group in age_groups]
        compliance_rates = [age_data[group]['4hour_compliance_pct'] for group in age_groups]
        
        total_patients = sum(patient_counts)
        
        # Patient counts by age group
        bars1 = ax1.bar(age_groups, patient_counts, color=self.colors['primary'], alpha=0.7)
        ax1.set_title('Patient Volume Distribution\nby Age Demographics', fontweight='bold', fontsize=12)
        ax1.set_ylabel('Number of Patients', fontweight='bold')
        ax1.set_xlabel('Age Groups', fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Add value labels on bars with percentages
        for i, bar in enumerate(bars1):
            height = bar.get_height()
            pct = (height / total_patients) * 100 if total_patients > 0 else 0
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{int(height)}\n({pct:.1f}%)', ha='center', va='bottom', fontweight='bold')
        
        # Average times and compliance by age group
        ax2_twin = ax2.twinx()
        
        bars2 = ax2.bar(age_groups, avg_times, color=self.colors['secondary'], alpha=0.7, 
                        label='Average Total Time in A&E')
        line = ax2_twin.plot(age_groups, compliance_rates, color=self.colors['nhs_green'], 
                           marker='o', linewidth=3, markersize=10, label='4-Hour Compliance Rate',
                           markerfacecolor='white', markeredgewidth=2)
        
        ax2.set_title('Performance Metrics by Age Group\nTotal Time vs NHS 4-Hour Compliance', 
                     fontweight='bold', fontsize=12)
        ax2.set_ylabel('Average Total Time (minutes)\nArrival to Departure', 
                      color=self.colors['secondary'], fontweight='bold')
        ax2.set_xlabel('Age Groups', fontweight='bold')
        ax2_twin.set_ylabel('NHS 4-Hour Compliance Rate (%)\n% Patients Seen Within 240 Minutes', 
                           color=self.colors['nhs_green'], fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Add target lines
        ax2_twin.axhline(y=95, color=self.colors['nhs_red'], linestyle='--', alpha=0.8, 
                        linewidth=2, label='95% NHS Target (Official)')
        ax2_twin.axhline(y=76, color=self.colors['warning'], linestyle=':', alpha=0.8, 
                        linewidth=2, label='76% Interim Target')
        
        # Add value labels on bars and line points
        for i, bar in enumerate(bars2):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{height:.1f}\nmin', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        for i, (x, y) in enumerate(zip(range(len(age_groups)), compliance_rates)):
            ax2_twin.text(x, y + 2, f'{y:.1f}%', ha='center', va='bottom', 
                         fontsize=9, fontweight='bold', color=self.colors['nhs_green'])
        
        # Combine legends
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_twin.get_legend_handles_labels()
        ax2_twin.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=10)
        
        plt.suptitle(f'{title}\nTotal Patients: {total_patients}', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_path:
            self._save_figure(fig, save_path)
        
        return fig
    
    def create_performance_dashboard(self, metrics_data: Dict[str, Any],
                                   title: str = "NHS A&E Quality Indicators Performance Dashboard",
                                   save_path: Optional[str] = None) -> plt.Figure:
        """Create a comprehensive performance dashboard.
        
        Args:
            metrics_data: Complete NHS metrics data
            title: Dashboard title
            save_path: Optional path to save the dashboard
            
        Returns:
            Matplotlib figure object
        """
        fig = plt.figure(figsize=(24, 16))
        gs = fig.add_gridspec(4, 4, hspace=0.4, wspace=0.3)
        
        # 1. Compliance gauge (top left)
        ax1 = fig.add_subplot(gs[0, 0])
        compliance_rate = metrics_data.get('4hour_standard_compliance_pct', 0)
        total_patients = metrics_data.get('total_attendances', 0)
        within_4hrs = metrics_data.get('attendances_within_4hours', 0)
        self._create_gauge(ax1, compliance_rate, 
                          f"NHS 4-Hour Standard\n{within_4hrs}/{total_patients} patients\nwithin 240 minutes", 
                          "%")
        
        # 2. Key NHS Quality Indicators (top middle-right)
        ax2 = fig.add_subplot(gs[0, 1:3])
        key_metrics = {
            '1️⃣ LWBS Rate (%)': f"{metrics_data.get('1_left_before_being_seen_rate_pct', 0):.1f}%",
            '2️⃣ Re-attendance Rate (%)': f"{metrics_data.get('2_reattendance_rate_pct', 0):.1f}%",
            '3️⃣ Time to Assessment (min)': f"{metrics_data.get('3_time_to_initial_assessment_avg_minutes', 0):.1f}",
            '4️⃣ Time to Treatment (min)': f"{metrics_data.get('4_time_to_treatment_avg_minutes', 0):.1f}",
            '5️⃣ Total Time in A&E (min)': f"{metrics_data.get('5_total_time_in_ae_avg_minutes', 0):.1f}",
            'Admission Rate (%)': f"{metrics_data.get('admission_rate_pct', 0):.1f}%"
        }
        self._create_metrics_table(ax2, key_metrics, "Official NHS A&E Quality Indicators")
        
        # 3. Triage distribution (top right)
        ax3 = fig.add_subplot(gs[0, 3])
        if 'triage_category_distribution' in metrics_data:
            triage_data = metrics_data['triage_category_distribution']
            categories = list(triage_data.keys())
            counts = list(triage_data.values())
            colors = ['#DA020E', '#FF8C00', '#FFD700', '#009639', '#005EB8']
            ax3.pie(counts, labels=categories, autopct='%1.1f%%', colors=colors[:len(categories)])
            ax3.set_title('Manchester Triage System\nCategory Distribution', fontweight='bold')
        
        # 4. Performance targets comparison (second row)
        ax4 = fig.add_subplot(gs[1, :])
        targets = ['4-Hour Standard', 'Time to Assessment', 'Time to Treatment', 'LWBS Rate', 'Re-attendance']
        actual_values = [
            compliance_rate,
            metrics_data.get('3_time_to_initial_assessment_avg_minutes', 0),
            metrics_data.get('4_time_to_treatment_avg_minutes', 0),
            metrics_data.get('1_left_before_being_seen_rate_pct', 0),
            metrics_data.get('2_reattendance_rate_pct', 0)
        ]
        target_values = [95, 15, 60, 5, 5]  # NHS targets
        
        x_pos = np.arange(len(targets))
        bars1 = ax4.bar(x_pos - 0.2, actual_values, 0.4, label='Actual Performance', 
                        color=self.colors['primary'], alpha=0.8)
        bars2 = ax4.bar(x_pos + 0.2, target_values, 0.4, label='NHS Targets', 
                        color=self.colors['nhs_red'], alpha=0.6)
        
        ax4.set_xlabel('NHS Quality Indicators', fontweight='bold')
        ax4.set_ylabel('Performance Values', fontweight='bold')
        ax4.set_title('Actual Performance vs NHS Targets\n(Lower is better for Time metrics and Rates)', fontweight='bold')
        ax4.set_xticks(x_pos)
        ax4.set_xticklabels(targets, rotation=45, ha='right')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # Add value labels
        for bar, val in zip(bars1, actual_values):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{val:.1f}', ha='center', va='bottom', fontweight='bold')
        
        # 5. Time distribution histogram (third row)
        ax5 = fig.add_subplot(gs[2, :])
        if 'patient_times' in metrics_data:
            times = metrics_data['patient_times']
            mean_time = np.mean(times)
            median_time = np.median(times)
            
            ax5.hist(times, bins=25, alpha=0.7, color=self.colors['primary'], 
                    label=f'Patient Distribution (n={len(times)})')
            ax5.axvline(x=240, color=self.colors['nhs_red'], linestyle='--', linewidth=3,
                       label=f'NHS 4-Hour Standard (240 min)')
            ax5.axvline(x=mean_time, color=self.colors['warning'], linestyle='-', linewidth=2,
                       label=f'Mean: {mean_time:.1f} min')
            ax5.axvline(x=median_time, color=self.colors['success'], linestyle='-', linewidth=2,
                       label=f'Median: {median_time:.1f} min')
            
            ax5.set_xlabel('Total Time in A&E (minutes) - Arrival to Departure', fontweight='bold')
            ax5.set_ylabel('Number of Patients', fontweight='bold')
            ax5.set_title('Patient Journey Time Distribution\nComplete A&E Experience: Triage → Assessment → Treatment → Disposition', 
                         fontweight='bold')
            ax5.legend()
            ax5.grid(True, alpha=0.3)
        
        # 6. Age group performance analysis (bottom row)
        ax6 = fig.add_subplot(gs[3, :])
        if 'age_group_analysis' in metrics_data:
            age_data = metrics_data['age_group_analysis']
            age_groups = list(age_data.keys())
            counts = [age_data[group]['count'] for group in age_groups]
            avg_times = [age_data[group]['avg_time_minutes'] for group in age_groups]
            compliance_rates = [age_data[group]['4hour_compliance_pct'] for group in age_groups]
            
            # Create dual y-axis
            ax6_twin = ax6.twinx()
            
            bars = ax6.bar(age_groups, counts, color=self.colors['secondary'], alpha=0.7, 
                          label='Patient Count')
            line1 = ax6_twin.plot(age_groups, avg_times, color=self.colors['warning'], 
                                 marker='s', linewidth=3, markersize=8, label='Avg Time (min)')
            line2 = ax6_twin.plot(age_groups, compliance_rates, color=self.colors['nhs_green'], 
                                 marker='o', linewidth=3, markersize=8, label='4-Hour Compliance (%)')
            
            ax6.set_xlabel('Age Groups', fontweight='bold')
            ax6.set_ylabel('Number of Patients', fontweight='bold')
            ax6_twin.set_ylabel('Time (minutes) / Compliance (%)', fontweight='bold')
            ax6.set_title('Demographics & Performance Analysis by Age Group\nPatient Volume, Average Journey Time, and NHS Compliance', 
                         fontweight='bold')
            
            # Add target line
            ax6_twin.axhline(y=95, color=self.colors['nhs_red'], linestyle='--', alpha=0.7, 
                            label='95% NHS Target')
            
            # Combine legends
            lines1, labels1 = ax6.get_legend_handles_labels()
            lines2, labels2 = ax6_twin.get_legend_handles_labels()
            ax6_twin.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
            ax6.grid(True, alpha=0.3)
        
        # Add comprehensive title with key statistics
        total_attendances = metrics_data.get('total_attendances', 0)
        compliance_pct = metrics_data.get('4hour_standard_compliance_pct', 0)
        avg_time = metrics_data.get('5_total_time_in_ae_avg_minutes', 0)
        
        comprehensive_title = f"{title}\nTotal Attendances: {total_attendances} | 4-Hour Compliance: {compliance_pct:.1f}% | Average Journey Time: {avg_time:.1f} minutes"
        plt.suptitle(comprehensive_title, fontsize=18, fontweight='bold')
        
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
    
    def _create_metrics_table(self, ax, metrics: Dict[str, str], table_title: str = "Key Metrics"):
        """Create a metrics table with detailed formatting."""
        ax.axis('tight')
        ax.axis('off')
        
        # Convert metrics to table data
        table_data = [[key, value] for key, value in metrics.items()]
        
        # Create table
        table = ax.table(cellText=table_data, 
                        colLabels=['NHS Quality Indicator', 'Current Performance'],
                        cellLoc='left', loc='center', colWidths=[0.7, 0.3])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 2)
        
        # Style the table
        for i in range(len(metrics) + 1):
            for j in range(2):
                cell = table[(i, j)]
                if i == 0:  # Header
                    cell.set_facecolor(self.colors['nhs_blue'])
                    cell.set_text_props(weight='bold', color='white', fontsize=11)
                else:
                    # Alternate row colors
                    cell.set_facecolor('#f0f0f0' if i % 2 == 0 else 'white')
                    if j == 0:  # Metric name column
                        cell.set_text_props(weight='bold', fontsize=9)
                    else:  # Value column
                        cell.set_text_props(fontsize=10, ha='center')
        
        # Add title
        ax.set_title(table_title, fontsize=12, fontweight='bold', pad=20)
    
    def _save_figure(self, fig: plt.Figure, save_path: str):
        """Save figure to specified path."""
        # Ensure directory exists
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save with high DPI
        fig.savefig(save_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')