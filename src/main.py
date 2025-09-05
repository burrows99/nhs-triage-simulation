#!/usr/bin/env python3
"""Minimal hospital simulation runner"""

import argparse
import simpy
import os
from datetime import datetime
from .entities.hospital import HospitalCore
from .entities.preemption_agent import PreemptionAgent
from .services.random import RandomService
from .simulation.simulation_engine import HospitalSimulationEngine as SimulationEngine
from .handler.console_event_handler import ConsoleEventHandler
from .triage_systems.random import RandomTriageSystem
from .triage_systems.manchester_triage_system import ManchesterTriageSystem
from .utils.logger import initialize_logger, LogLevel, EventType

def run_single_simulation(triage_system_name: str, args):
    """Run a single simulation with specified triage system"""
    print(f"\n{'='*60}")
    print(f"RUNNING SIMULATION: {triage_system_name.upper()} TRIAGE SYSTEM")
    print(f"{'='*60}")
    
    # Create output/logs directory if it doesn't exist
    logs_dir = "output/logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    # Generate timestamped log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    preemption_status = "preemption" if args.enable_preemption else "no_preemption"
    log_filename = f"hospital_sim_{timestamp}_{triage_system_name}_{preemption_status}_d{args.duration}_doc{args.doctors}.log"
    log_file_path = os.path.join(logs_dir, log_filename)
    
    # Initialize centralized logging
    logger = initialize_logger(
        log_to_console=True,
        log_to_file=True,
        log_file_path=log_file_path,
        min_level=LogLevel.INFO
    )
    
    # Log simulation start with configuration
    logger.log_event(
        timestamp=0.0,
        event_type=EventType.SIMULATION_START,
        message="Hospital simulation starting - Main execution",
        data={
            "simulation_type": "hospital_emergency_department",
            "logging_enabled": True,
            "log_file": "hospital_simulation.log",
            "preemption_enabled": args.enable_preemption,
            "duration": args.duration,
            "num_doctors": args.doctors,
            "triage_system": triage_system_name
        },
        source="main"
    )
    
    # Create simulation environment
    env = simpy.Environment()
    
    # Create components
    patient_provider = RandomService(arrival_rate=0.2)
    
    # Create triage system based on specified type
    if triage_system_name == 'random':
        triage_system = RandomTriageSystem(system_id="RANDOM_TRIAGE_001")
    elif triage_system_name == 'manchester':
        triage_system = ManchesterTriageSystem(system_id="MTS_001")
    else:
        raise ValueError(f"Unknown triage system: {triage_system_name}")
    
    # Initialize hospital with specified number of doctors and triage system
    hospital = HospitalCore(num_doctors=args.doctors, triage_system=triage_system)
    
    # Conditionally create preemption agent
    preemption_agent = None
    if args.enable_preemption:
        preemption_agent = PreemptionAgent(agent_id="PREEMPTION_AGENT_001")
        logger.log_event(
            timestamp=0.0,
            event_type=EventType.SYSTEM_STATE,
            message="Preemption agent enabled for simulation",
            data={"agent_id": "PREEMPTION_AGENT_001"},
            source="main"
        )
    else:
        logger.log_event(
            timestamp=0.0,
            event_type=EventType.SYSTEM_STATE,
            message="Preemption agent disabled - using standard queue-based assignment",
            data={"preemption_mode": "disabled"},
            source="main"
        )
    
    # Create event handler and simulation engine
    event_handler = ConsoleEventHandler(verbose=True)
    sim = SimulationEngine(
        env=env,
        hospital=hospital,
        patient_provider=patient_provider,
        triage_system=triage_system,
        preemption_agent=preemption_agent,
        event_handler=event_handler
    )
    
    # Log simulation start
    logger.log_event(
        timestamp=0.0,
        event_type=EventType.SIMULATION_START,
        message="Starting hospital simulation",
        data={
            "duration": args.duration,
            "simulation_type": "hospital_emergency_department",
            "preemption_enabled": args.enable_preemption,
            "triage_system": triage_system_name
        },
        source="main"
    )
    
    # Run simulation with error handling
    try:
        sim.run_simulation(duration=args.duration)
        
        # Log simulation completion
        logger.log_event(
            timestamp=float(args.duration),
            event_type=EventType.SIMULATION_END,
            message="Hospital simulation completed successfully",
            simulation_state=sim.simulation_state,
            data={
                "duration": args.duration,
                "total_events_logged": len(logger.events),
                "simulation_status": "completed",
                "preemption_enabled": args.enable_preemption,
                "triage_system": triage_system_name
            },
            source="main"
        )
        
        sim.print_statistics()
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        
        # Log the error with full traceback
        logger.log_event(
            timestamp=sim.env.now if hasattr(sim, 'env') else 0.0,
            event_type=EventType.SYSTEM_STATE,
            message=f"Simulation error: {str(e)}",
            simulation_state=sim.simulation_state if hasattr(sim, 'simulation_state') else None,
            data={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": error_traceback,
                "simulation_status": "failed",
                "preemption_enabled": args.enable_preemption,
                "triage_system": triage_system_name
            },
            source="main"
        )
        
        print(f"❌ Error running {triage_system_name.lower()} simulation: {e}")
        print(f"Full traceback logged to: {log_file_path}")
        print("\nFull traceback:")
        print(error_traceback)
        
        return None  # Return None to indicate failure
    
    # Create system-specific output directory
    system_output_dir = os.path.join("output", triage_system_name)
    os.makedirs(system_output_dir, exist_ok=True)
    
    # Generate timestamped JSON filename in system directory
    json_filename = f"simulation_events_{timestamp}_{triage_system_name}_{preemption_status}_d{args.duration}_doc{args.doctors}.json"
    json_file_path = os.path.join(system_output_dir, json_filename)
    
    # Log summary statistics
    stats = logger.get_summary_stats()
    logger.log_event(
        timestamp=float(args.duration),
        event_type=EventType.SYSTEM_STATE,
        message="Logging summary statistics",
        simulation_state=sim.simulation_state,
        data={
            "total_events": stats['total_events'],
            "event_types": list(stats['event_type_counts'].keys()),
            "time_range": f"{stats['time_range']['start']:.1f} - {stats['time_range']['end']:.1f} minutes",
            "export_file": json_file_path,
            "log_file": log_file_path,
            "preemption_enabled": args.enable_preemption,
            "triage_system": triage_system_name
        },
        source="main"
    )
    
    # Export detailed logs
    logger.export_to_json(json_file_path)
    
    # Export rich HTML logs
    html_file_path = log_file_path.replace('.log', '_rich.html')
    html_result = logger.export_rich_html(html_file_path)
    print(f"\n📄 {html_result}")
    
    # Generate plots in system-specific directory
    plot_files = sim.simulation_state.plot_results(system_name=triage_system_name)
    print(f"\nPlots generated in output/{triage_system_name}/:")
    for plot_type, file_path in plot_files.items():
        if plot_type != 'report':  # Don't show report path
            print(f"  {plot_type}: {os.path.basename(file_path)}")
    
    return sim

def main():
    """Run hospital simulation with optional preemption agent"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Hospital Emergency Department Simulation')
    preemption_group = parser.add_mutually_exclusive_group()
    preemption_group.add_argument('--enable-preemption', action='store_true', dest='enable_preemption',
                                 help='Enable preemption agent for decision making')
    preemption_group.add_argument('--disable-preemption', action='store_false', dest='enable_preemption',
                                 help='Disable preemption agent (use standard queue-based assignment)')
    parser.set_defaults(enable_preemption=True)
    parser.add_argument('--duration', type=int, default=5000,
                       help='Simulation duration in minutes (default: 5000 - roughly 1/2 week)')
    parser.add_argument('--doctors', type=int, default=3,
                       help='Number of doctors (default: 3)')
    parser.add_argument('--triage-system', type=str, default='all',
                       choices=['all', 'random', 'manchester'],
                       help='Triage system to use: all, random, or manchester (default: all)')
    
    args = parser.parse_args()
    
    # Determine which triage systems to run
    if args.triage_system == 'all':
        triage_systems = ['random', 'manchester']
        print("\n🏥 RUNNING COMPREHENSIVE TRIAGE SYSTEM COMPARISON")
        print("📊 Both Random and Manchester Triage Systems will be evaluated")
        print(f"⏱️  Duration: {args.duration} minutes | 👨‍⚕️ Doctors: {args.doctors} | 🚨 Preemption: {'Enabled' if args.enable_preemption else 'Disabled'}")
    else:
        triage_systems = [args.triage_system]
    
    # Run simulations for each triage system
    simulation_results = {}
    for triage_system_name in triage_systems:
        sim = run_single_simulation(triage_system_name, args)
        if sim is not None:
            simulation_results[triage_system_name] = sim
        else:
            print(f"⚠️  Skipping {triage_system_name} simulation due to error")
            continue
    
    # Print comparison summary if multiple systems were run
    if len(simulation_results) > 1:
        print(f"\n{'='*80}")
        print("📊 TRIAGE SYSTEM COMPARISON SUMMARY")
        print(f"{'='*80}")
        
        for system_name, sim in simulation_results.items():
            state = sim.simulation_state
            nhs_metrics = state.metrics_service.calculate_nhs_metrics()
            mts_summary = state.metrics_service.get_mts_compliance_summary()
            
            print(f"\n🏥 {system_name.upper()} TRIAGE SYSTEM:")
            print(f"   📈 Total Arrivals: {state.total_arrivals}")
            print(f"   ✅ Completed Treatments: {state.total_completed}")
            print(f"   ⏱️  Average Wait Time: {state.metrics_service.get_average_wait_time():.1f} minutes")
            print(f"   🎯 4-Hour Target Compliance: {nhs_metrics.get('four_hour_target_compliance', 0):.1f}%")
            print(f"   🏥 Overall MTS Compliance: {mts_summary.get('overall_compliance', 0):.1f}%")
            print(f"   🚨 Preemptions: {state.preemptions_count}")
        
        # Generate comparison charts
        print(f"\n📊 Generating comparison charts...")
        try:
            from .entities.sub_entities.simulation_state import SimulationState
            
            # Extract simulation states for comparison
            comparison_states = {name: sim.simulation_state for name, sim in simulation_results.items()}
            
            # Generate comparison plots
            comparison_plots = SimulationState.plot_comparison_charts(comparison_states)
            
            print(f"\n📈 Comparison charts generated:")
            for chart_name, file_path in comparison_plots.items():
                if chart_name != 'comparison_report':
                    chart_display_name = chart_name.replace('_', ' ').title()
                    print(f"   📊 {chart_display_name}: {file_path}")
            
            print(f"\n📋 Comprehensive comparison report: {comparison_plots.get('comparison_report', 'Not generated')}")
            
        except Exception as e:
            print(f"\n⚠️  Warning: Could not generate comparison charts: {e}")
        
        print(f"\n📁 Results saved in separate directories:")
        for system_name in simulation_results.keys():
            print(f"   📊 {system_name}: output/{system_name}/")
        print(f"   📊 comparison: output/comparison/")
        
        print(f"\n✨ Comparison complete! Check the output directories for detailed analysis.")

if __name__ == "__main__":
    main()