#!/usr/bin/env python3
"""
Main simulation runner for NHS Emergency Department Triage Simulator

Based on SimPy discrete event simulation and research methodology from:
"Patient Flow Optimization in an Emergency Department Using SimPy-Based 
Simulation Modeling and Analysis: A Case Study"
"""

import argparse
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from src.core.simulation_engine import SimulationEngine
from src.config.simulation_parameters import SimulationParameters


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description='NHS Emergency Department Triage Simulator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.main                           # Run with default parameters
  python -m src.main --scenario high_demand    # Run high demand scenario
  python -m src.main --config config.json     # Run with custom config file
  python -m src.main --duration 480 --rate 0.8 # Run 8 hours with 0.8 patients/min
  python -m src.main --triage adaptive         # Use adaptive triage system
        """
    )
    
    # Configuration options
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration JSON file'
    )
    
    parser.add_argument(
        '--scenario', '-s',
        choices=['low_demand', 'high_demand', 'crisis', 'optimization_test'],
        help='Predefined scenario to run'
    )
    
    # Simulation parameters
    parser.add_argument(
        '--duration', '-d',
        type=float,
        help='Simulation duration in minutes (default: 1440 = 24 hours)'
    )
    
    parser.add_argument(
        '--rate', '-r',
        type=float,
        help='Patient arrival rate (patients per minute)'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        help='Random seed for reproducibility'
    )
    
    # Resource configuration
    parser.add_argument(
        '--doctors',
        type=int,
        help='Number of doctors'
    )
    
    parser.add_argument(
        '--nurses',
        type=int,
        help='Number of triage nurses'
    )
    
    parser.add_argument(
        '--cubicles',
        type=int,
        help='Number of consultation cubicles'
    )
    
    # Triage system options
    parser.add_argument(
        '--triage',
        choices=['manchester'],
        default='manchester',
        help='Triage system type (AI triage to be implemented later)'
    )
    
    # Output options
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output directory for results and plots'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress output except errors'
    )
    
    # Analysis options
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Generate detailed analysis and plots'
    )
    
    parser.add_argument(
        '--compare',
        nargs='+',
        help='Compare multiple scenarios or configurations'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run comprehensive analysis: all scenarios, comparisons, and generate complete reports'
    )
    
    return parser


def load_configuration(args: argparse.Namespace) -> SimulationParameters:
    """Load simulation configuration from arguments"""
    
    # Start with default parameters
    if args.config:
        # Load from file
        config_path = Path(args.config)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {args.config}")
        params = SimulationParameters.load_from_file(str(config_path))
    elif args.scenario:
        # Load predefined scenario
        scenarios = SimulationParameters().get_scenario_configs()
        if args.scenario not in scenarios:
            raise ValueError(f"Unknown scenario: {args.scenario}")
        params = scenarios[args.scenario]
    else:
        # Use default parameters
        params = SimulationParameters()
    
    # Override with command line arguments
    if args.duration is not None:
        params.duration = args.duration
    
    if args.rate is not None:
        params.arrival_rate = args.rate
    
    if args.seed is not None:
        params.random_seed = args.seed
    
    if args.doctors is not None:
        params.num_doctors = args.doctors
    
    if args.nurses is not None:
        params.num_triage_nurses = args.nurses
    
    if args.cubicles is not None:
        params.num_cubicles = args.cubicles
    
    if args.triage is not None:
        params.triage_system_type = args.triage
    
    # Removed calculator parameter as we only use Manchester triage
    
    if args.verbose:
        params.enable_detailed_logging = True
        params.log_patient_journeys = True
    
    if args.quiet:
        params.enable_detailed_logging = False
        params.log_patient_journeys = False
    
    return params


def run_single_simulation(params: SimulationParameters, 
                         output_dir: Optional[str] = None,
                         quiet: bool = False) -> Dict[str, Any]:
    """Run a single simulation with given parameters"""
    
    if not quiet:
        print(f"\n{'='*60}")
        print("NHS EMERGENCY DEPARTMENT TRIAGE SIMULATOR")
        print(f"{'='*60}")
        print(f"Configuration:")
        print(f"  Duration: {params.duration:.0f} minutes ({params.duration/60:.1f} hours)")
        print(f"  Arrival Rate: {params.arrival_rate:.2f} patients/minute")
        print(f"  Resources: {params.num_doctors} doctors, {params.num_cubicles} cubicles, {params.num_triage_nurses} nurses")
        print(f"  Triage System: {params.triage_system_type}")
        print(f"  Random Seed: {params.random_seed}")
        print(f"{'='*60}")
    
    # Validate parameters
    if not params.validate():
        raise ValueError("Invalid simulation parameters")
    
    # Create and run simulation
    engine = SimulationEngine(params)
    results = engine.run_simulation()
    
    # Print summary
    if not quiet:
        engine.print_summary()
    
    # Save results if output directory specified
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save configuration
        params.save_to_file(str(output_path / 'config.json'))
        
        # Save results
        import json
        with open(output_path / 'results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        if not quiet:
            print(f"\nResults saved to: {output_path}")
    
    return results


def run_comparison(scenarios: list, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """Run comparison of multiple scenarios"""
    
    print(f"\n{'='*60}")
    print("SCENARIO COMPARISON")
    print(f"{'='*60}")
    
    all_results = {}
    
    for scenario_name in scenarios:
        print(f"\nRunning scenario: {scenario_name}")
        
        # Get scenario configuration
        scenario_configs = SimulationParameters().get_scenario_configs()
        if scenario_name in scenario_configs:
            params = scenario_configs[scenario_name]
        else:
            # Try to load as config file
            try:
                params = SimulationParameters.load_from_file(scenario_name)
                scenario_name = Path(scenario_name).stem
            except:
                print(f"Warning: Unknown scenario '{scenario_name}', skipping")
                continue
        
        # Run simulation
        results = run_single_simulation(params, quiet=True)
        all_results[scenario_name] = results
    
    # Print comparison summary
    print(f"\n{'='*60}")
    print("COMPARISON SUMMARY")
    print(f"{'='*60}")
    
    print(f"{'Scenario':<20} {'Arrivals':<10} {'Departures':<12} {'Admission%':<12} {'LWBS%':<10} {'Avg Wait':<10}")
    print("-" * 80)
    
    for scenario_name, results in all_results.items():
        summary = results['ed_results']['summary_statistics']
        wait_stats = results['ed_results']['wait_time_statistics']
        
        # Calculate average wait time across all priorities
        total_wait_times = []
        for priority_stats in wait_stats.values():
            if 'times' in priority_stats:
                total_wait_times.extend(priority_stats['times'])
        
        avg_wait = sum(total_wait_times) / len(total_wait_times) if total_wait_times else 0
        
        print(f"{scenario_name:<20} {summary['total_arrivals']:<10} {summary['total_departures']:<12} "
              f"{summary['admission_rate']:<11.1%} {summary['lwbs_rate']:<9.1%} {avg_wait:<10.1f}")
    
    # Save comparison results
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(output_path / 'comparison_results.json', 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        print(f"\nComparison results saved to: {output_path}")
    
    return all_results


def run_comprehensive_analysis(output_dir: Optional[str] = None) -> Dict[str, Any]:
    """Run comprehensive analysis with all scenarios and comparisons"""
    import os
    from datetime import datetime
    
    # Set default output directory
    if not output_dir:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"comprehensive_analysis_{timestamp}"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n" + "="*80)
    print("COMPREHENSIVE HEALTHCARE TRIAGE ANALYSIS")
    print("="*80)
    
    # Define all scenarios to run
    all_scenarios = ['low_demand', 'high_demand', 'crisis', 'optimization_test']
    scenario_results = {}
    
    print(f"\n🔄 Running {len(all_scenarios)} scenarios...")
    
    # Run each scenario
    for i, scenario in enumerate(all_scenarios, 1):
        print(f"\n[{i}/{len(all_scenarios)}] Running {scenario.replace('_', ' ').title()} scenario...")
        
        # Load scenario configuration
        scenarios = SimulationParameters().get_scenario_configs()
        params = scenarios[scenario]
        
        # Create scenario-specific output directory
        scenario_dir = os.path.join(output_dir, scenario)
        os.makedirs(scenario_dir, exist_ok=True)
        
        # Run simulation
        results = run_single_simulation(params, scenario_dir, quiet=True)
        scenario_results[scenario] = results
        
        print(f"   ✅ {scenario.replace('_', ' ').title()} completed")
    
    print(f"\n📊 Generating scenario comparisons...")
    
    # Run comprehensive comparison
    comparison_results = run_comparison(all_scenarios, output_dir)
    
    print(f"\n📈 Running metrics demonstration...")
    
    # Run metrics demo for comprehensive analysis
    try:
        import subprocess
        import sys
        result = subprocess.run([sys.executable, 'metrics_demo.py'], 
                              capture_output=True, text=True, cwd='.')
        if result.returncode == 0:
            print("   ✅ Metrics demonstration completed")
        else:
            print(f"   ⚠️  Metrics demo completed with warnings")
    except Exception as e:
        print(f"   ⚠️  Metrics demo error: {e}")
    
    # Generate summary report
    print(f"\n📋 Generating comprehensive summary...")
    
    summary = {
        'analysis_timestamp': datetime.now().isoformat(),
        'scenarios_analyzed': all_scenarios,
        'output_directory': output_dir,
        'scenario_results': scenario_results,
        'comparison_results': comparison_results,
        'files_generated': {
            'individual_scenarios': [f"{output_dir}/{s}/" for s in all_scenarios],
            'comparisons': f"{output_dir}/comparison_results.json",
            'metrics_output': "metrics_output/",
            'summary_report': f"{output_dir}/comprehensive_summary.json"
        }
    }
    
    # Save comprehensive summary
    import json
    summary_file = os.path.join(output_dir, 'comprehensive_summary.json')
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n" + "="*80)
    print("COMPREHENSIVE ANALYSIS COMPLETE")
    print("="*80)
    print(f"📁 All results saved to: {output_dir}")
    print(f"📊 Scenarios analyzed: {', '.join([s.replace('_', ' ').title() for s in all_scenarios])}")
    print(f"📈 Metrics and visualizations: metrics_output/")
    print(f"📋 Summary report: {summary_file}")
    print("="*80)
    
    return summary


def main():
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    try:
        if args.all:
            # Run comprehensive analysis
            results = run_comprehensive_analysis(args.output)
        elif args.compare:
            # Run comparison mode
            results = run_comparison(args.compare, args.output)
        else:
            # Run single simulation
            params = load_configuration(args)
            results = run_single_simulation(params, args.output, args.quiet)
        
        # Generate analysis if requested
        if args.analyze and args.output and not args.all:
            print("\nGenerating detailed analysis...")
            # This would call visualization functions when implemented
            # from .visualization import generate_analysis_plots
            # generate_analysis_plots(results, args.output)
        
        return 0
        
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())