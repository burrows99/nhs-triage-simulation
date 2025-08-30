"""Telemetry visualization for triage decision-making processes

This module provides visualization capabilities for telemetry data collected
during triage decision-making processes across all triage systems.
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
try:
    import seaborn as sns
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
from src.utils.telemetry import TelemetryCollector, PatientTelemetry, DecisionStepType
from src.config.config_manager import get_output_paths, create_output_directories
import logging
import os

logger = logging.getLogger(__name__)

class TelemetryVisualizer:
    """Visualizer for triage telemetry data"""
    
    def __init__(self, telemetry_collector: TelemetryCollector):
        self.telemetry_collector = telemetry_collector
        self.completed_sessions = telemetry_collector.completed_sessions
        
        # Set up plotting style
        plt.style.use('default')
        if HAS_SEABORN:
            sns.set_palette("husl")
        
    def create_decision_timeline_plot(self, patient_id: int, output_dir: str) -> Optional[str]:
        """Create a timeline plot showing decision steps for a specific patient"""
        patient_sessions = [s for s in self.completed_sessions if s.patient_id == patient_id]
        
        if not patient_sessions:
            logger.warning(f"No telemetry data found for patient {patient_id}")
            return None
            
        fig, axes = plt.subplots(len(patient_sessions), 1, figsize=(15, 6 * len(patient_sessions)))
        if len(patient_sessions) == 1:
            axes = [axes]
            
        for idx, session in enumerate(patient_sessions):
            ax = axes[idx]
            
            # Extract step data
            steps = session.decision_steps
            step_names = [f"{step.step_type.value}\n({step.duration_ms:.1f}ms)" for step in steps]
            step_times = [(step.timestamp - session.start_timestamp) * 1000 for step in steps]  # Convert to ms
            step_durations = [step.duration_ms for step in steps]
            step_success = [step.success for step in steps]
            
            # Create timeline
            colors = ['green' if success else 'red' for success in step_success]
            bars = ax.barh(range(len(steps)), step_durations, left=step_times, color=colors, alpha=0.7)
            
            # Customize plot
            ax.set_yticks(range(len(steps)))
            ax.set_yticklabels(step_names, fontsize=10)
            ax.set_xlabel('Time (milliseconds from start)', fontsize=12)
            ax.set_title(f'Decision Timeline - {session.triage_system}\nPatient {patient_id} (Priority: {session.final_priority})', 
                        fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            # Add duration labels on bars
            for i, (bar, duration) in enumerate(zip(bars, step_durations)):
                if duration > 50:  # Only label bars that are wide enough
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_y() + bar.get_height()/2, 
                           f'{duration:.1f}ms', ha='center', va='center', fontsize=9, fontweight='bold')
        
        plt.tight_layout()
        
        # Save plot
        filename = f'patient_{patient_id}_decision_timeline.png'
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Decision timeline plot saved: {filepath}")
        return filepath
    
    def create_system_performance_comparison(self, output_dir: str) -> Optional[str]:
        """Create comparison plots of system performance metrics"""
        if not self.completed_sessions:
            logger.warning("No telemetry data available for system comparison")
            return None
            
        # Group sessions by system
        system_data = {}
        for session in self.completed_sessions:
            system_name = session.triage_system
            if system_name not in system_data:
                system_data[system_name] = {
                    'total_durations': [],
                    'step_counts': [],
                    'error_counts': [],
                    'success_rates': [],
                    'llm_inference_times': []
                }
            
            system_data[system_name]['total_durations'].append(session.total_duration_ms)
            system_data[system_name]['step_counts'].append(len(session.decision_steps))
            system_data[system_name]['error_counts'].append(session.error_count)
            system_data[system_name]['success_rates'].append(1.0 if session.success else 0.0)
            
            # Extract LLM inference times
            llm_times = [step.duration_ms for step in session.decision_steps 
                        if step.step_type == DecisionStepType.LLM_INFERENCE]
            system_data[system_name]['llm_inference_times'].extend(llm_times)
        
        # Create subplots
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Triage System Performance Comparison', fontsize=16, fontweight='bold')
        
        systems = list(system_data.keys())
        if HAS_SEABORN:
            colors = sns.color_palette("husl", len(systems))
        else:
            colors = plt.cm.tab10(np.linspace(0, 1, len(systems)))
        
        # 1. Total Duration Comparison
        ax = axes[0, 0]
        duration_data = [system_data[sys]['total_durations'] for sys in systems]
        bp = ax.boxplot(duration_data, labels=systems, patch_artist=True)
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
        ax.set_title('Total Processing Time Distribution')
        ax.set_ylabel('Duration (ms)')
        ax.tick_params(axis='x', rotation=45)
        
        # 2. Step Count Comparison
        ax = axes[0, 1]
        step_data = [system_data[sys]['step_counts'] for sys in systems]
        bp = ax.boxplot(step_data, labels=systems, patch_artist=True)
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
        ax.set_title('Decision Steps Count')
        ax.set_ylabel('Number of Steps')
        ax.tick_params(axis='x', rotation=45)
        
        # 3. Success Rate Comparison
        ax = axes[0, 2]
        success_rates = [np.mean(system_data[sys]['success_rates']) * 100 for sys in systems]
        bars = ax.bar(systems, success_rates, color=colors)
        ax.set_title('Success Rate Comparison')
        ax.set_ylabel('Success Rate (%)')
        ax.set_ylim(0, 105)
        ax.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar, rate in zip(bars, success_rates):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                   f'{rate:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # 4. Error Count Comparison
        ax = axes[1, 0]
        error_data = [system_data[sys]['error_counts'] for sys in systems]
        bp = ax.boxplot(error_data, labels=systems, patch_artist=True)
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
        ax.set_title('Error Count Distribution')
        ax.set_ylabel('Number of Errors')
        ax.tick_params(axis='x', rotation=45)
        
        # 5. LLM Inference Time Comparison (for LLM-based systems)
        ax = axes[1, 1]
        llm_systems = [sys for sys in systems if 'LLM' in sys]
        if llm_systems:
            llm_data = [system_data[sys]['llm_inference_times'] for sys in llm_systems]
            bp = ax.boxplot(llm_data, labels=llm_systems, patch_artist=True)
            llm_colors = colors[:len(llm_systems)]
            for patch, color in zip(bp['boxes'], llm_colors):
                patch.set_facecolor(color)
        ax.set_title('LLM Inference Time Distribution')
        ax.set_ylabel('Inference Time (ms)')
        ax.tick_params(axis='x', rotation=45)
        
        # 6. Average Processing Time by System
        ax = axes[1, 2]
        avg_durations = [np.mean(system_data[sys]['total_durations']) for sys in systems]
        bars = ax.bar(systems, avg_durations, color=colors)
        ax.set_title('Average Processing Time')
        ax.set_ylabel('Average Duration (ms)')
        ax.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar, duration in zip(bars, avg_durations):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(avg_durations) * 0.01, 
                   f'{duration:.0f}ms', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        # Save plot
        filename = 'system_performance_comparison.png'
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"System performance comparison plot saved: {filepath}")
        return filepath
    
    def create_decision_step_analysis(self, output_dir: str) -> Optional[str]:
        """Create analysis of decision steps across all systems"""
        if not self.completed_sessions:
            logger.warning("No telemetry data available for step analysis")
            return None
            
        # Collect step data
        step_data = []
        for session in self.completed_sessions:
            for step in session.decision_steps:
                step_data.append({
                    'system': session.triage_system,
                    'step_type': step.step_type.value,
                    'duration_ms': step.duration_ms,
                    'success': step.success,
                    'patient_id': session.patient_id
                })
        
        if not step_data:
            logger.warning("No step data available for analysis")
            return None
            
        df = pd.DataFrame(step_data)
        
        # Create subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Decision Step Analysis Across All Systems', fontsize=16, fontweight='bold')
        
        # 1. Step Duration by Type
        ax = axes[0, 0]
        step_types = df['step_type'].unique()
        step_durations = [df[df['step_type'] == step_type]['duration_ms'].values for step_type in step_types]
        bp = ax.boxplot(step_durations, labels=step_types, patch_artist=True)
        if HAS_SEABORN:
            colors = sns.color_palette("husl", len(step_types))
        else:
            colors = plt.cm.tab10(np.linspace(0, 1, len(step_types)))
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
        ax.set_title('Step Duration by Type')
        ax.set_ylabel('Duration (ms)')
        ax.tick_params(axis='x', rotation=45)
        
        # 2. Step Success Rate by Type
        ax = axes[0, 1]
        success_rates = df.groupby('step_type')['success'].mean() * 100
        bars = ax.bar(success_rates.index, success_rates.values, color=colors)
        ax.set_title('Step Success Rate by Type')
        ax.set_ylabel('Success Rate (%)')
        ax.set_ylim(0, 105)
        ax.tick_params(axis='x', rotation=45)
        
        # Add value labels
        for bar, rate in zip(bars, success_rates.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                   f'{rate:.1f}%', ha='center', va='bottom', fontweight='bold')
        
        # 3. Step Count by System
        ax = axes[1, 0]
        step_counts = df.groupby(['system', 'step_type']).size().unstack(fill_value=0)
        step_counts.plot(kind='bar', stacked=True, ax=ax, colormap='tab10')
        ax.set_title('Step Count by System and Type')
        ax.set_ylabel('Number of Steps')
        ax.tick_params(axis='x', rotation=45)
        ax.legend(title='Step Type', bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # 4. Average Step Duration by System
        ax = axes[1, 1]
        avg_durations = df.groupby('system')['duration_ms'].mean()
        if HAS_SEABORN:
            step_colors = sns.color_palette("husl", len(avg_durations))
        else:
            step_colors = plt.cm.tab10(np.linspace(0, 1, len(avg_durations)))
        bars = ax.bar(avg_durations.index, avg_durations.values, color=step_colors)
        ax.set_title('Average Step Duration by System')
        ax.set_ylabel('Average Duration (ms)')
        ax.tick_params(axis='x', rotation=45)
        
        # Add value labels
        for bar, duration in zip(bars, avg_durations.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(avg_durations.values) * 0.01, 
                   f'{duration:.0f}ms', ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        # Save plot
        filename = 'decision_step_analysis.png'
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Decision step analysis plot saved: {filepath}")
        return filepath
    
    def generate_telemetry_report(self, output_dir: str) -> str:
        """Generate a comprehensive telemetry report"""
        report_lines = []
        report_lines.append("# Triage System Telemetry Report")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        if not self.completed_sessions:
            report_lines.append("No telemetry data available.")
        else:
            # Summary statistics
            stats = self.telemetry_collector.get_summary_stats()
            report_lines.append("## Summary Statistics")
            report_lines.append(f"- Total Sessions: {stats['total_sessions']}")
            report_lines.append(f"- Average Duration: {stats['avg_duration_ms']:.1f} ms")
            report_lines.append(f"- Total Errors: {stats['total_errors']}")
            report_lines.append("")
            
            # System-specific statistics
            report_lines.append("## System Performance")
            for system_name, system_stats in stats['systems'].items():
                report_lines.append(f"### {system_name}")
                report_lines.append(f"- Sessions: {system_stats['count']}")
                report_lines.append(f"- Average Duration: {system_stats['avg_duration_ms']:.1f} ms")
                report_lines.append(f"- Success Rate: {system_stats['success_rate']:.1%}")
                report_lines.append(f"- Total Errors: {system_stats['total_errors']}")
                report_lines.append("")
            
            # Patient-specific details
            report_lines.append("## Patient Details")
            for session in self.completed_sessions:
                report_lines.append(f"### Patient {session.patient_id} - {session.triage_system}")
                report_lines.append(f"- Final Priority: {session.final_priority}")
                report_lines.append(f"- Total Duration: {session.total_duration_ms:.1f} ms")
                report_lines.append(f"- Decision Steps: {len(session.decision_steps)}")
                report_lines.append(f"- Success: {'Yes' if session.success else 'No'}")
                report_lines.append(f"- Errors: {session.error_count}")
                
                # Step details
                report_lines.append("  **Decision Steps:**")
                for i, step in enumerate(session.decision_steps, 1):
                    status = "✓" if step.success else "✗"
                    report_lines.append(f"  {i}. {status} {step.step_type.value} ({step.duration_ms:.1f}ms)")
                    if step.error_message:
                        report_lines.append(f"     Error: {step.error_message}")
                
                report_lines.append("")
        
        # Save report
        report_content = "\n".join(report_lines)
        report_path = os.path.join(output_dir, 'telemetry_report.md')
        
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        logger.info(f"Telemetry report saved: {report_path}")
        return report_path
    
    def create_all_visualizations(self, base_output_dir: str) -> Dict[str, List[str]]:
        """Create all telemetry visualizations and reports in system-specific directories"""
        generated_files = {
            'plots': [],
            'reports': []
        }
        
        try:
            # Group sessions by system
            system_sessions = {}
            for session in self.completed_sessions:
                system_name = session.triage_system
                if system_name not in system_sessions:
                    system_sessions[system_name] = []
                system_sessions[system_name].append(session)
            
            # Generate system-specific telemetry
            for system_name, sessions in system_sessions.items():
                # Create system-specific telemetry directory
                system_dir = os.path.join(base_output_dir, system_name, 'telemetry')
                os.makedirs(system_dir, exist_ok=True)
                
                # Create a temporary visualizer for this system only
                system_collector = TelemetryCollector()
                system_collector.completed_sessions = sessions
                system_visualizer = TelemetryVisualizer(system_collector)
                
                # Generate patient timeline plots for this system
                patient_ids = list(set(session.patient_id for session in sessions))
                for patient_id in patient_ids[:3]:  # Limit to first 3 patients per system
                    timeline_plot = system_visualizer.create_decision_timeline_plot(patient_id, system_dir)
                    if timeline_plot:
                        generated_files['plots'].append(timeline_plot)
                
                # Generate system-specific telemetry report
                report_path = system_visualizer.generate_telemetry_report(system_dir)
                generated_files['reports'].append(report_path)
                
                # Export system-specific raw telemetry data
                json_path = os.path.join(system_dir, f'{system_name.lower().replace(" ", "_").replace("-", "_")}_telemetry_data.json')
                system_collector.export_telemetry_json(json_path)
                generated_files['reports'].append(json_path)
                
                logger.info(f"Generated telemetry for {system_name}: {len(sessions)} sessions")
            
            # Generate comparison plots in the comparison directory (if multiple systems)
            if len(system_sessions) > 1:
                comparison_dir = os.path.join(base_output_dir, 'comparison')
                os.makedirs(comparison_dir, exist_ok=True)
                
                # Generate system performance comparison
                perf_plot = self.create_system_performance_comparison(comparison_dir)
                if perf_plot:
                    generated_files['plots'].append(perf_plot)
                
                # Generate decision step analysis
                step_plot = self.create_decision_step_analysis(comparison_dir)
                if step_plot:
                    generated_files['plots'].append(step_plot)
                
                # Generate overall telemetry report
                overall_report_path = self.generate_telemetry_report(comparison_dir)
                generated_files['reports'].append(overall_report_path)
                
                # Export complete telemetry data
                json_path = os.path.join(comparison_dir, 'complete_telemetry_data.json')
                self.telemetry_collector.export_telemetry_json(json_path)
                generated_files['reports'].append(json_path)
            
            logger.info(f"Generated {len(generated_files['plots'])} plots and {len(generated_files['reports'])} reports")
            
        except Exception as e:
            logger.error(f"Error creating telemetry visualizations: {e}")
            logger.exception("Full traceback:")
        
        return generated_files