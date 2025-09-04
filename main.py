#!/usr/bin/env python3
"""
Comparative Hospital Simulation

Runs hospital simulation with both Manchester Triage System and LLM-based triage
for comparative analysis. Outputs results to separate directories.
"""

import sys
import os
import logging
import argparse
from collections import Counter
from typing import List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.logger import logger
from src.simulation.real_data_hospital import SimpleHospital
from src.triage.triage_constants import TriageCategories
from src.triage.manchester_triage_system import ManchesterTriageSystem
from src.triage.llm_triage_system.single_llm_triage import SingleLLMTriage
from src.triage.llm_triage_system.mixture_llm_triage import MixtureLLMTriage


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments for the hospital simulation.
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Hospital Simulation with Multiple Triage Systems",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 main.py                                    # Run all systems with NHS realistic defaults
  python3 main.py --systems manchester single       # Run only Manchester and Single LLM systems
  python3 main.py --duration 480 --arrival-rate 20  # 8-hour simulation with 20 patients/hour
  python3 main.py --nurses 6 --doctors 3 --beds 8   # Smaller NHS A&E department
  python3 main.py --output-dir ./custom_output      # Custom output directory
  python3 main.py --help                            # Show this help message

Available Triage Systems:
  manchester    - Manchester Triage System (rule-based fuzzy logic)
  single        - Single LLM Triage System (single AI agent)
  multi-agent   - Multi-Agent LLM Triage System (6 specialized agents)
        """
    )
    
    # Simulation parameters - NHS realistic defaults
    parser.add_argument(
        '--duration', '-d',
        type=float,
        default=1440,
        help='Simulation duration in minutes (default: 1440 = 24 hours, realistic for NHS A&E analysis)'
    )
    
    parser.add_argument(
        '--arrival-rate', '-a',
        type=int,
        default=16,
        help='Patient arrival rate per hour (default: 16, based on NHS A&E data: 386-411 patients/day)'
    )
    
    # Resource allocation - NHS realistic staffing levels
    parser.add_argument(
        '--nurses', '-n',
        type=int,
        default=8,
        help='Number of nurses available (default: 8, typical NHS A&E triage + emergency care nurses)'
    )
    
    parser.add_argument(
        '--doctors', '-dr',
        type=int,
        default=4,
        help='Number of doctors available (default: 4, typical NHS A&E consultants + junior doctors)'
    )
    
    parser.add_argument(
        '--beds', '-b',
        type=int,
        default=12,
        help='Number of beds available (default: 12, typical NHS A&E department capacity)'
    )
    
    # System selection
    parser.add_argument(
        '--systems', '-s',
        nargs='*',
        choices=['manchester', 'single', 'multi-agent', 'all'],
        default=['all'],
        help='Triage systems to run (default: all). Choose from: manchester, single, multi-agent, or all'
    )
    
    # Output configuration
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        default='./output/simulation',
        help='Base output directory for simulation results (default: ./output/simulation)'
    )
    
    parser.add_argument(
        '--log-level', '-l',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    # Performance options
    parser.add_argument(
        '--delay-scaling',
        type=float,
        default=0,
        help='Delay scaling factor for simulation speed (default: 0 = no delays)'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        help='Random seed for reproducible results (optional)'
    )
    
    # Feature flags
    parser.add_argument(
        '--skip-plots',
        action='store_true',
        help='Skip generating plots and charts (faster execution)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output with detailed logging'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress non-essential output'
    )
    
    return parser.parse_args()


def get_system_configurations(args: argparse.Namespace) -> List[dict]:
    """
    Get triage system configurations based on command line arguments.
    
    Args:
        args: Parsed command line arguments
        
    Returns:
        List of system configuration dictionaries
    """
    all_systems = [
        {
            'key': 'manchester',
            'system': ManchesterTriageSystem,
            'name': 'Manchester Triage System',
            'output_dir': f'{args.output_dir}/manchester_triage_system'
        },
        {
            'key': 'single',
            'system': SingleLLMTriage,
            'name': 'Single LLM Triage System',
            'output_dir': f'{args.output_dir}/single_llm_system'
        },
        {
            'key': 'multi-agent',
            'system': MixtureLLMTriage,
            'name': 'Multi-Agent LLM Triage System',
            'output_dir': f'{args.output_dir}/multi_agent_llm_system'
        }
    ]
    
    # Filter systems based on user selection
    if 'all' in args.systems:
        return all_systems
    else:
        return [sys for sys in all_systems if sys['key'] in args.systems]


def run_simulation(triage_system, system_name: str, output_dir: str, args: argparse.Namespace):
    """Run simulation with specified triage system
    
    Args:
        triage_system: Triage system instance
        system_name: Name of the triage system for logging
        output_dir: Output directory for results
        
    Returns:
        Simulation results dictionary
    """
    logger.info(f"🏥 Starting {system_name} Simulation")
    logger.info(f"📁 Output Directory: {output_dir}")
    
    # Create initial triage system instance
    if isinstance(triage_system, type):
        if issubclass(triage_system, SingleLLMTriage):
            temp_triage = SingleLLMTriage()
        elif issubclass(triage_system, MixtureLLMTriage):
            temp_triage = MixtureLLMTriage()
        elif issubclass(triage_system, ManchesterTriageSystem):
            temp_triage = ManchesterTriageSystem()
        else:
            temp_triage = SingleLLMTriage()  # Default fallback
    else:
        temp_triage = triage_system
    
    # Set logging level based on arguments
    log_level = getattr(logging, args.log_level)
    if args.verbose:
        log_level = logging.DEBUG
    elif args.quiet:
        log_level = logging.WARNING
    
    hospital = SimpleHospital(
        csv_folder='./output/csv',
        output_dir=output_dir,
        triage_system=temp_triage,
        sim_duration=args.duration,
        arrival_rate=args.arrival_rate,
        delay_scaling=args.delay_scaling,
        nurses=args.nurses,
        doctors=args.doctors,
        beds=args.beds,
        log_level=log_level
    )
    
    # Metrics connection is now handled automatically in hospital initialization
    # No need to manually set up metrics for LLM-based systems
    
    if not args.quiet:
        logger.info(f"📊 Config: {hospital.sim_duration/60:.1f}h | {hospital.arrival_rate}/h | {hospital.nurses}N {hospital.doctors}D {hospital.beds}B | {len(hospital.patients)} patients")
        logger.info(f"🔧 Triage System: {system_name}")
        if args.seed:
            logger.info(f"🎲 Random Seed: {args.seed}")
    
    results = hospital.run()
    
    logger.info(f"📊 {system_name} Results:")
    logger.info(f"  Total Patients: {results['total_patients']}")
    logger.info(f"  Average Time: {results['avg_time']:.1f} minutes")
    
    category_counts = Counter(results['categories'])
    logger.info(f"🏷️ Triage Category Distribution:")
    for category in [TriageCategories.RED, TriageCategories.ORANGE, TriageCategories.YELLOW, TriageCategories.GREEN, TriageCategories.BLUE]:
        count = category_counts.get(category, 0)
        percentage = (count / results['total_patients'] * 100) if results['total_patients'] > 0 else 0
        logger.info(f"    {category}: {count} patients ({percentage:.1f}%)")
    
    logger.info(f"✅ {system_name} simulation completed!")
    logger.info(f"📁 Results saved to: {output_dir}")
    logger.info("=" * 80)
    
    return results


def generate_comparison_report(results_summary: dict, simulations: list, args: argparse.Namespace):
    """Generate comprehensive comparison report with logging and markdown output
    
    Args:
        results_summary: Dictionary of simulation results by system name
        simulations: List of simulation configurations
        args: Command line arguments
    """
    from src.services.report_utils import ReportUtils
    
    # Check if report should be generated
    if not ReportUtils.should_generate_report(results_summary, args.quiet):
        return
    
    # Load detailed NHS metrics for comparison
    detailed_metrics = ReportUtils.load_detailed_metrics(simulations, results_summary)
    
    # Generate systematic logging
    ReportUtils.generate_systematic_logging(results_summary, detailed_metrics)
    
    # Generate and save markdown report
    report_content = ReportUtils.generate_complete_markdown_report(results_summary, detailed_metrics, args)
    report_path = os.path.join(args.output_dir if hasattr(args, 'output_dir') else './output/simulation', 'comparison_report.md')
    
    saved_path = ReportUtils.save_markdown_report(report_content, report_path)
    
    logger.info(f"\n📄 Markdown comparison report saved to: {saved_path}")
    logger.info("=" * 80)





def main():
    """Main function to run comparative hospital simulations"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Set random seed if provided
    if args.seed:
        import random
        import numpy as np
        random.seed(args.seed)
        np.random.seed(args.seed)
        logger.info(f"🎲 Random seed set to: {args.seed}")
    
    # Configure logging based on arguments
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.WARNING)
    else:
        logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    if not args.quiet:
        logger.info("🏥 Starting Comparative Hospital Simulation")
        logger.info(f"🔄 Running systems: {', '.join(args.systems)}")
        logger.info("=" * 80)
    
    try:
        # Get system configurations based on arguments
        simulations = get_system_configurations(args)
        
        results_summary = {}
        
        # Run simulations for selected systems
        for sim_config in simulations:
            try:
                results = run_simulation(
                    triage_system=sim_config['system'],
                    system_name=sim_config['name'],
                    output_dir=sim_config['output_dir'],
                    args=args
                )
                results_summary[sim_config['name']] = results
                
            except Exception as e:
                logger.error(f"❌ {sim_config['name']} simulation failed: {e}")
                if args.verbose:
                    import traceback
                    logger.error(traceback.format_exc())
                continue
        

        
        # Generate comparative summary and markdown report
        if results_summary:
            generate_comparison_report(results_summary, simulations, args)
            
            if not args.quiet:
                logger.info("📊 COMPARATIVE SIMULATION SUMMARY")
                logger.info("=" * 80)
                
                for system_name, results in results_summary.items():
                    logger.info(f"🔧 {system_name}:")
                    logger.info(f"   📊 Patients Processed: {results['total_patients']}")
                    logger.info(f"   ⏱️  Average Time: {results['avg_time']:.1f} minutes")
                    
                    if not args.skip_plots:  # Only show detailed stats if plots aren't skipped
                        category_counts = Counter(results['categories'])
                        logger.info(f"   🏷️  Category Distribution:")
                        for category in [TriageCategories.RED, TriageCategories.ORANGE, TriageCategories.YELLOW, TriageCategories.GREEN, TriageCategories.BLUE]:
                            count = category_counts.get(category, 0)
                            percentage = (count / results['total_patients'] * 100) if results['total_patients'] > 0 else 0
                            logger.info(f"      {category}: {count} ({percentage:.1f}%)")
                    logger.info("")
                
                logger.info("✅ All simulations completed successfully!")
                logger.info("📁 Results available in:")
                for sim_config in simulations:
                    logger.info(f"   📂 {sim_config['output_dir']}/")
                
                if len(results_summary) > 1:
                    logger.info(f"📊 Comparison report generated: ./output/simulation/comparison_report.md")
        
        # Print summary for quiet mode
        elif args.quiet and results_summary:
            total_patients = sum(r['total_patients'] for r in results_summary.values())
            avg_time = sum(r['avg_time'] for r in results_summary.values()) / len(results_summary)
            print(f"Completed: {len(results_summary)} systems, {total_patients} total patients, {avg_time:.1f}min avg time")
        
    except KeyboardInterrupt:
        logger.info("⏹️ Simulation interrupted by user")
    except Exception as e:
        logger.error(f"❌ Simulation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()