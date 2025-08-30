#!/usr/bin/env python3
"""
Comprehensive Test Script for All Three Triage Systems

This script tests and compares:
1. Manchester Triage System (Fuzzy Logic)
2. Single LLM-based Triage System
3. Multi-Agent LLM-based Triage System

Each system runs a simulation and generates plots for comparison.
"""

import simpy
import logging
import time
from src.config.config_manager import configure_logging, get_simulation_config
from src.entities.emergency_department import EmergencyDepartment
from src.triage_systems.manchester_triage import ManchesterTriage
from src.triage_systems.single_LLM_based_triage import SingleLLMBasedTriage
from src.triage_systems.multi_LLM_based_triage import MultiLLMBasedTriage
from src.visualization.plots import EDVisualizer
from src.visualization.telemetry_plots import TelemetryVisualizer
from src.utils.telemetry import get_telemetry_collector
import pandas as pd
import matplotlib.pyplot as plt
import os

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)

def run_triage_system_simulation(triage_system, system_name):
    """Run simulation for a specific triage system"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Starting {system_name} Simulation")
    logger.info(f"{'='*60}")
    
    start_time = time.time()
    
    # Initialize simulation environment
    env = simpy.Environment()
    
    # Initialize emergency department with triage system
    ed = EmergencyDepartment(env, triage_system)
    
    # Start patient generation process
    env.process(ed.patient_generator())
    
    # Run the simulation
    sim_config = get_simulation_config()
    logger.info(f"Running {system_name} simulation for {sim_config['duration']} minutes")
    env.run(until=sim_config['duration'])
    
    # Get metrics summary
    metrics_summary = ed.metrics.get_summary_stats()
    
    # Calculate simulation time
    simulation_time = time.time() - start_time
    
    # Print results
    print(f"\n{'='*60}")
    print(f"{system_name} Simulation Results")
    print(f"{'='*60}")
    print(f"Simulation Duration: {sim_config['duration']} minutes")
    print(f"Real Time Taken: {simulation_time:.2f} seconds")
    print(f"Total patients: {metrics_summary['total_patients']}")
    print(f"Admission rate: {metrics_summary['admitted_rate']:.2f}")
    print(f"Average wait for triage: {metrics_summary['avg_wait_for_triage']:.2f} minutes")
    print(f"Average wait for consultation: {metrics_summary['avg_wait_for_consult']:.2f} minutes")
    print(f"Average total time in system: {metrics_summary['avg_total_time']:.2f} minutes")
    
    # Print wait times by priority
    print("\nAverage wait times by priority (1-5):")
    for priority, wait_time in metrics_summary['avg_wait_by_priority'].items():
        print(f"  Priority {priority}: {wait_time:.2f} minutes")
    
    # Create visualizations
    try:
        logger.info(f"Generating visualizations for {system_name}...")
        visualizer = EDVisualizer(ed.metrics, triage_system)
        visualizer.create_wait_time_plots()
        visualizer.create_priority_distribution_plot()
        visualizer.verify_poisson_arrivals()
        logger.info(f"{system_name} visualizations completed successfully!")
    except Exception as e:
        logger.error(f"Error during {system_name} visualization: {e}")
        logger.exception("Full traceback:")
    
    return ed.metrics, metrics_summary, simulation_time

def create_comparison_plots(results):
    """Create comparison plots across all triage systems"""
    logger.info("Creating comparison plots...")
    
    # Extract data for comparison
    system_names = []
    total_patients = []
    avg_wait_triage = []
    avg_wait_consult = []
    avg_total_time = []
    admission_rates = []
    simulation_times = []
    
    for system_name, (metrics, summary, sim_time) in results.items():
        system_names.append(system_name)
        total_patients.append(summary['total_patients'])
        avg_wait_triage.append(summary['avg_wait_for_triage'])
        avg_wait_consult.append(summary['avg_wait_for_consult'])
        avg_total_time.append(summary['avg_total_time'])
        admission_rates.append(summary['admitted_rate'])
        simulation_times.append(sim_time)
    
    # Create comparison plots
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Triage Systems Comparison', fontsize=16, fontweight='bold')
    
    # Plot 1: Total Patients
    axes[0, 0].bar(system_names, total_patients, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[0, 0].set_title('Total Patients Processed')
    axes[0, 0].set_ylabel('Number of Patients')
    axes[0, 0].tick_params(axis='x', rotation=45)
    
    # Plot 2: Average Wait Times
    x = range(len(system_names))
    width = 0.35
    axes[0, 1].bar([i - width/2 for i in x], avg_wait_triage, width, label='Triage Wait', color='#1f77b4')
    axes[0, 1].bar([i + width/2 for i in x], avg_wait_consult, width, label='Consult Wait', color='#ff7f0e')
    axes[0, 1].set_title('Average Wait Times')
    axes[0, 1].set_ylabel('Wait Time (minutes)')
    axes[0, 1].set_xticks(x)
    axes[0, 1].set_xticklabels(system_names, rotation=45)
    axes[0, 1].legend()
    
    # Plot 3: Total Time in System
    axes[0, 2].bar(system_names, avg_total_time, color=['#2ca02c', '#d62728', '#9467bd'])
    axes[0, 2].set_title('Average Total Time in System')
    axes[0, 2].set_ylabel('Time (minutes)')
    axes[0, 2].tick_params(axis='x', rotation=45)
    
    # Plot 4: Admission Rates
    axes[1, 0].bar(system_names, admission_rates, color=['#8c564b', '#e377c2', '#7f7f7f'])
    axes[1, 0].set_title('Admission Rates')
    axes[1, 0].set_ylabel('Admission Rate')
    axes[1, 0].tick_params(axis='x', rotation=45)
    
    # Plot 5: Simulation Performance
    axes[1, 1].bar(system_names, simulation_times, color=['#bcbd22', '#17becf', '#ff9896'])
    axes[1, 1].set_title('Simulation Runtime')
    axes[1, 1].set_ylabel('Time (seconds)')
    axes[1, 1].tick_params(axis='x', rotation=45)
    
    # Plot 6: Priority Distribution Comparison (if data available)
    try:
        priority_data = {}
        for system_name, (metrics, summary, _) in results.items():
            df = metrics.get_dataframe()
            if not df.empty and 'priority' in df.columns:
                priority_counts = df['priority'].value_counts().sort_index()
                priority_data[system_name] = priority_counts
        
        if priority_data:
            priorities = [1, 2, 3, 4, 5]
            x = range(len(priorities))
            width = 0.25
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
            
            for i, (system_name, counts) in enumerate(priority_data.items()):
                values = [counts.get(p, 0) for p in priorities]
                axes[1, 2].bar([j + i*width for j in x], values, width, 
                              label=system_name, color=colors[i % len(colors)])
            
            axes[1, 2].set_title('Priority Distribution Comparison')
            axes[1, 2].set_ylabel('Number of Patients')
            axes[1, 2].set_xlabel('Priority Level')
            axes[1, 2].set_xticks([i + width for i in x])
            axes[1, 2].set_xticklabels(priorities)
            axes[1, 2].legend()
        else:
            axes[1, 2].text(0.5, 0.5, 'No priority data available', 
                           ha='center', va='center', transform=axes[1, 2].transAxes)
            axes[1, 2].set_title('Priority Distribution Comparison')
    except Exception as e:
        logger.warning(f"Could not create priority distribution comparison: {e}")
        axes[1, 2].text(0.5, 0.5, 'Priority comparison unavailable', 
                        ha='center', va='center', transform=axes[1, 2].transAxes)
        axes[1, 2].set_title('Priority Distribution Comparison')
    
    plt.tight_layout()
    
    # Save comparison plot
    comparison_dir = 'output/comparison'
    os.makedirs(comparison_dir, exist_ok=True)
    plt.savefig(f'{comparison_dir}/triage_systems_comparison.png', dpi=300, bbox_inches='tight')
    logger.info(f"Comparison plot saved to {comparison_dir}/triage_systems_comparison.png")
    
    plt.show()

def create_summary_report(results):
    """Create a summary report of all triage systems"""
    logger.info("Creating summary report...")
    
    report_lines = []
    report_lines.append("NHS TRIAGE SYSTEMS COMPARISON REPORT")
    report_lines.append("=" * 50)
    report_lines.append("")
    
    for system_name, (metrics, summary, sim_time) in results.items():
        report_lines.append(f"{system_name.upper()}:")
        report_lines.append("-" * len(system_name))
        report_lines.append(f"  Total Patients: {summary['total_patients']}")
        report_lines.append(f"  Admission Rate: {summary['admitted_rate']:.2f}")
        report_lines.append(f"  Avg Triage Wait: {summary['avg_wait_for_triage']:.2f} min")
        report_lines.append(f"  Avg Consult Wait: {summary['avg_wait_for_consult']:.2f} min")
        report_lines.append(f"  Avg Total Time: {summary['avg_total_time']:.2f} min")
        report_lines.append(f"  Simulation Time: {sim_time:.2f} sec")
        report_lines.append("")
    
    report_lines.append("SYSTEM COMPARISON:")
    report_lines.append("-" * 18)
    
    # Find best performing system for each metric
    best_throughput = max(results.items(), key=lambda x: x[1][1]['total_patients'])
    best_triage_wait = min(results.items(), key=lambda x: x[1][1]['avg_wait_for_triage'])
    best_consult_wait = min(results.items(), key=lambda x: x[1][1]['avg_wait_for_consult'])
    best_total_time = min(results.items(), key=lambda x: x[1][1]['avg_total_time'])
    fastest_sim = min(results.items(), key=lambda x: x[1][2])
    
    report_lines.append(f"  Best Throughput: {best_throughput[0]} ({best_throughput[1][1]['total_patients']} patients)")
    report_lines.append(f"  Shortest Triage Wait: {best_triage_wait[0]} ({best_triage_wait[1][1]['avg_wait_for_triage']:.2f} min)")
    report_lines.append(f"  Shortest Consult Wait: {best_consult_wait[0]} ({best_consult_wait[1][1]['avg_wait_for_consult']:.2f} min)")
    report_lines.append(f"  Shortest Total Time: {best_total_time[0]} ({best_total_time[1][1]['avg_total_time']:.2f} min)")
    report_lines.append(f"  Fastest Simulation: {fastest_sim[0]} ({fastest_sim[1][2]:.2f} sec)")
    
    # Save report
    report_dir = 'output/comparison'
    os.makedirs(report_dir, exist_ok=True)
    with open(f'{report_dir}/triage_systems_report.txt', 'w') as f:
        f.write('\n'.join(report_lines))
    
    # Print report
    print('\n'.join(report_lines))
    logger.info(f"Summary report saved to {report_dir}/triage_systems_report.txt")

def main():
    """Main function to test all triage systems"""
    print("NHS TRIAGE SYSTEMS COMPREHENSIVE TEST")
    print("=" * 50)
    print("Testing three triage systems:")
    print("1. Manchester Triage System (Fuzzy Logic)")
    print("2. Single LLM-based Triage System")
    print("3. Multi-Agent LLM-based Triage System")
    print("\nNote: LLM systems require Ollama service to be running.")
    print("=" * 50)
    
    results = {}
    
    # Test 1: Manchester Triage System
    try:
        manchester_system = ManchesterTriage()
        results["Manchester Triage"] = run_triage_system_simulation(
            manchester_system, "Manchester Triage System"
        )
    except Exception as e:
        logger.error(f"Manchester Triage System failed: {e}")
        logger.exception("Full traceback:")
    
    # Test 2: Single LLM-based Triage System
    try:
        single_llm_system = SingleLLMBasedTriage()
        results["Single LLM"] = run_triage_system_simulation(
            single_llm_system, "Single LLM-based Triage System"
        )
    except Exception as e:
        logger.error(f"Single LLM Triage System failed: {e}")
        logger.exception("Full traceback:")
        print("\nNote: Single LLM system requires Ollama service. Skipping...")
    
    # Test 3: Multi-Agent LLM-based Triage System
    try:
        multi_llm_system = MultiLLMBasedTriage()
        results["Multi-Agent LLM"] = run_triage_system_simulation(
            multi_llm_system, "Multi-Agent LLM-based Triage System"
        )
    except Exception as e:
        logger.error(f"Multi-Agent LLM Triage System failed: {e}")
        logger.exception("Full traceback:")
        print("\nNote: Multi-Agent LLM system requires Ollama service. Skipping...")
    
    # Create comparison visualizations and report
    if len(results) > 1:
        create_comparison_plots(results)
        create_summary_report(results)
    elif len(results) == 1:
        print("\nOnly one system completed successfully. Comparison not possible.")
        create_summary_report(results)
    else:
        print("\nNo systems completed successfully. Please check the logs.")
    
    # Generate telemetry visualizations
    print("\n" + "=" * 50)
    print("GENERATING TELEMETRY VISUALIZATIONS")
    print("=" * 50)
    
    try:
        telemetry_collector = get_telemetry_collector()
        if telemetry_collector.completed_sessions:
            print(f"Processing telemetry data for {len(telemetry_collector.completed_sessions)} sessions...")
            
            telemetry_visualizer = TelemetryVisualizer(telemetry_collector)
            generated_files = telemetry_visualizer.create_all_visualizations('output')
            
            print(f"Generated {len(generated_files['plots'])} telemetry plots")
            print(f"Generated {len(generated_files['reports'])} telemetry reports")
            print("Telemetry visualizations saved to output/telemetry/")
            
            # Print summary of telemetry findings
            stats = telemetry_collector.get_summary_stats()
            print("\nTelemetry Summary:")
            for system_name, system_stats in stats.get('systems', {}).items():
                print(f"  {system_name}:")
                print(f"    - Average processing time: {system_stats['avg_duration_ms']:.1f} ms")
                print(f"    - Success rate: {system_stats['success_rate']:.1%}")
                print(f"    - Sessions processed: {system_stats['count']}")
        else:
            print("No telemetry data collected during simulation.")
            
    except Exception as e:
        logger.error(f"Error generating telemetry visualizations: {e}")
        logger.exception("Full traceback:")
        print(f"Failed to generate telemetry visualizations: {e}")
    
    print("\n" + "=" * 50)
    print("COMPREHENSIVE TEST COMPLETED")
    print("=" * 50)
    print(f"Systems tested: {len(results)}")
    print("Check the output directories for detailed results and plots.")
    if len(results) > 1:
        print("Comparison plots and report available in output/comparison/")
    print("Telemetry analysis available in output/telemetry/")
    print("\nTelemetry Features:")
    print("  - Decision step timelines for each patient")
    print("  - System performance comparisons")
    print("  - Decision step analysis across all systems")
    print("  - Detailed telemetry reports with error analysis")

if __name__ == "__main__":
    main()