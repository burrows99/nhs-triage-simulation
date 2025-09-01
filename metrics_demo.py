#!/usr/bin/env python3
"""
Comprehensive Metrics Demonstration for ED Simulation

This script demonstrates the complete metrics tracking and visualization system
for the Emergency Department simulation, including:
- Real-time metrics collection during simulation
- Statistical analysis and reporting
- Dissertation-quality matplotlib visualizations
- Performance benchmarking against NHS targets
"""

import os
import sys
import numpy as np
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.simulation_engine import SimulationEngine
from src.metrics.metrics_collector import MetricsCollector
from src.metrics.visualization import MetricsVisualizer, PlotConfig
from src.metrics.analysis import MetricsAnalyzer
from src.config.simulation_parameters import SimulationParameters


def run_comprehensive_metrics_demo():
    """Run comprehensive metrics demonstration"""
    
    print("\n" + "="*80)
    print("NHS EMERGENCY DEPARTMENT METRICS DEMONSTRATION")
    print("="*80)
    print("Comprehensive metrics tracking and analysis system")
    print("Based on authentic Manchester Triage System (FMTS)")
    print("="*80)
    
    # Create output directory for plots
    output_dir = "metrics_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Configure visualization settings
    plot_config = PlotConfig(
        save_plots=True,
        output_dir=output_dir,
        file_format="png",
        dpi=300
    )
    
    # Initialize components
    visualizer = MetricsVisualizer(plot_config)
    analyzer = MetricsAnalyzer()
    
    # Run multiple simulation scenarios for comparison
    scenarios = [
        {
            'name': 'Normal Operations',
            'duration': 120,  # 2 hours
            'arrival_rate': 0.3,
            'num_doctors': 4,
            'num_nurses': 2
        },
        {
            'name': 'High Demand',
            'duration': 120,
            'arrival_rate': 0.5,
            'num_doctors': 4,
            'num_nurses': 2
        },
        {
            'name': 'Optimized Staffing',
            'duration': 120,
            'arrival_rate': 0.4,
            'num_doctors': 6,
            'num_nurses': 3
        }
    ]
    
    simulation_results = []
    
    for i, scenario in enumerate(scenarios):
        print(f"\n{'='*60}")
        print(f"RUNNING SCENARIO {i+1}: {scenario['name'].upper()}")
        print(f"{'='*60}")
        print(f"Duration: {scenario['duration']} minutes")
        print(f"Arrival Rate: {scenario['arrival_rate']} patients/minute")
        print(f"Staffing: {scenario['num_doctors']} doctors, {scenario['num_nurses']} nurses")
        print(f"{'='*60}")
        
        # Configure simulation parameters
        params = SimulationParameters(
            duration=scenario['duration'],
            arrival_rate=scenario['arrival_rate'],
            num_doctors=scenario['num_doctors'],
            num_triage_nurses=scenario['num_nurses'],
            random_seed=42 + i  # Different seed for each scenario
        )
        
        # Create simulation engine with metrics
        engine = SimulationEngine(params)
        
        # Run simulation
        print("Starting simulation...")
        results = engine.run_simulation()
        
        # Get comprehensive metrics
        metrics = engine.ed.get_comprehensive_metrics()
        metrics_summary = engine.ed.get_metrics_summary()
        
        print(f"\nSimulation completed successfully!")
        print(f"Total patients processed: {metrics.total_arrivals}")
        print(f"Throughput: {metrics.throughput_per_hour:.1f} patients/hour")
        print(f"Average system time: {metrics.average_length_of_stay:.1f} minutes")
        
        # Store results for comparison
        simulation_results.append({
            'scenario': scenario['name'],
            'metrics': metrics,
            'summary': metrics_summary,
            'params': params
        })
        
        # Generate comprehensive visualizations for this scenario
        print(f"\nGenerating visualizations for {scenario['name']}...")
        
        # Update output directory for this scenario
        scenario_dir = os.path.join(output_dir, scenario['name'].lower().replace(' ', '_'))
        os.makedirs(scenario_dir, exist_ok=True)
        plot_config.output_dir = scenario_dir
        visualizer.config = plot_config
        
        # Create comprehensive dashboard
        saved_plots = visualizer.create_comprehensive_dashboard(
            metrics, 
            title=f"ED Simulation Dashboard - {scenario['name']}"
        )
        
        print(f"Visualizations saved to: {scenario_dir}")
        for plot_type, filename in saved_plots.items():
            print(f"  - {plot_type}: {filename}")
        
        # Create executive summary
        executive_plot = visualizer.create_executive_summary_plot(metrics)
        print(f"  - Executive Summary: {executive_plot}")
        
        # Generate statistical analysis report
        print(f"\nGenerating statistical analysis report...")
        report = analyzer.generate_comprehensive_report(
            metrics, 
            report_id=f"{scenario['name'].lower().replace(' ', '_')}_{int(datetime.now().timestamp())}"
        )
        
        # Save report
        report_filename = os.path.join(scenario_dir, "statistical_report.json")
        report.save_to_file(report_filename)
        print(f"Statistical report saved to: {report_filename}")
        
        # Print key findings
        print(f"\n{'='*40}")
        print(f"KEY FINDINGS - {scenario['name'].upper()}")
        print(f"{'='*40}")
        
        print(f"Performance Indicators:")
        for metric, value in report.performance_indicators.items():
            print(f"  - {metric.replace('_', ' ').title()}: {value:.2f}")
            
        print(f"\nNHS Target Compliance:")
        for metric, value in report.target_compliance.items():
            print(f"  - {metric.replace('_', ' ').title()}: {value:.1f}%")
            
        print(f"\nRecommendations:")
        for i, recommendation in enumerate(report.recommendations, 1):
            print(f"  {i}. {recommendation}")
    
    # Comparative analysis across scenarios
    print(f"\n{'='*80}")
    print("COMPARATIVE ANALYSIS ACROSS SCENARIOS")
    print(f"{'='*80}")
    
    # Extract metrics for comparison
    metrics_list = [result['metrics'] for result in simulation_results]
    scenario_names = [result['scenario'] for result in simulation_results]
    
    # Perform comparative analysis
    comparison = analyzer.compare_simulations(metrics_list, scenario_names)
    
    print(f"\nComparative Metrics:")
    for metric_name, metric_data in comparison['comparative_metrics'].items():
        print(f"\n{metric_name.replace('_', ' ').title()}:")
        for i, (scenario, value) in enumerate(zip(scenario_names, metric_data['values'])):
            print(f"  {scenario}: {value:.2f}")
        print(f"  Best Performance: {metric_data['best_simulation']}")
        print(f"  Mean: {metric_data['mean']:.2f} ± {metric_data['std']:.2f}")
    
    # Create comparative visualizations
    print(f"\nGenerating comparative visualizations...")
    
    # Comparative throughput analysis
    import matplotlib.pyplot as plt
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Scenario Comparison Dashboard', fontsize=16, fontweight='bold')
    
    # Throughput comparison
    throughputs = [result['metrics'].throughput_per_hour for result in simulation_results]
    colors = ['#4ECDC4', '#FF6B6B', '#45B7D1']
    
    bars1 = ax1.bar(scenario_names, throughputs, color=colors)
    ax1.set_ylabel('Patients/Hour')
    ax1.set_title('Throughput Comparison')
    ax1.tick_params(axis='x', rotation=45)
    
    # Add value labels
    for bar, value in zip(bars1, throughputs):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{value:.1f}', ha='center', va='bottom')
    
    # Resource efficiency comparison
    efficiencies = [result['metrics'].resource_efficiency for result in simulation_results]
    bars2 = ax2.bar(scenario_names, efficiencies, color=colors)
    ax2.set_ylabel('Efficiency (%)')
    ax2.set_title('Resource Efficiency Comparison')
    ax2.tick_params(axis='x', rotation=45)
    
    for bar, value in zip(bars2, efficiencies):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{value:.1f}%', ha='center', va='bottom')
    
    # Average wait time comparison
    avg_wait_times = []
    for result in simulation_results:
        all_waits = []
        for times in result['metrics'].wait_times.values():
            all_waits.extend(times)
        avg_wait_times.append(np.mean(all_waits) if all_waits else 0)
    
    bars3 = ax3.bar(scenario_names, avg_wait_times, color=colors)
    ax3.set_ylabel('Minutes')
    ax3.set_title('Average Wait Time Comparison')
    ax3.tick_params(axis='x', rotation=45)
    
    for bar, value in zip(bars3, avg_wait_times):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{value:.1f}', ha='center', va='bottom')
    
    # System load comparison
    system_loads = [len(result['metrics'].total_system_times) for result in simulation_results]
    bars4 = ax4.bar(scenario_names, system_loads, color=colors)
    ax4.set_ylabel('Patients Completed')
    ax4.set_title('System Load Comparison')
    ax4.tick_params(axis='x', rotation=45)
    
    for bar, value in zip(bars4, system_loads):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{value}', ha='center', va='bottom')
    
    plt.tight_layout()
    comparison_plot = os.path.join(output_dir, "scenario_comparison.png")
    plt.savefig(comparison_plot, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"Comparative analysis saved to: {comparison_plot}")
    
    # Generate final summary report
    print(f"\n{'='*80}")
    print("FINAL SUMMARY AND RECOMMENDATIONS")
    print(f"{'='*80}")
    
    # Find best performing scenario
    best_throughput_idx = np.argmax(throughputs)
    best_efficiency_idx = np.argmax(efficiencies)
    best_wait_time_idx = np.argmin(avg_wait_times)
    
    print(f"\nBest Performance by Metric:")
    print(f"  - Highest Throughput: {scenario_names[best_throughput_idx]} ({throughputs[best_throughput_idx]:.1f} patients/hour)")
    print(f"  - Highest Efficiency: {scenario_names[best_efficiency_idx]} ({efficiencies[best_efficiency_idx]:.1f}%)")
    print(f"  - Lowest Wait Time: {scenario_names[best_wait_time_idx]} ({avg_wait_times[best_wait_time_idx]:.1f} minutes)")
    
    print(f"\nOverall Recommendations:")
    print(f"  1. The '{scenario_names[best_efficiency_idx]}' scenario shows the best overall performance")
    print(f"  2. Increasing staffing levels significantly improves patient outcomes")
    print(f"  3. Resource utilization should be monitored to prevent overutilization")
    print(f"  4. Wait time targets are achievable with proper resource allocation")
    
    print(f"\n{'='*80}")
    print("METRICS DEMONSTRATION COMPLETE")
    print(f"{'='*80}")
    print(f"All outputs saved to: {output_dir}")
    print(f"Generated {len(simulation_results)} scenario analyses")
    print(f"Created comprehensive visualizations and statistical reports")
    print(f"Demonstrated NHS target compliance analysis")
    print(f"{'='*80}")


if __name__ == "__main__":
    # Add matplotlib backend configuration
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend for server environments
    
    try:
        run_comprehensive_metrics_demo()
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()