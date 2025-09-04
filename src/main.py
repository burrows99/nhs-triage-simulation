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

def main():
    """Run hospital simulation with optional preemption agent"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Hospital Emergency Department Simulation')
    parser.add_argument('--enable-preemption', action='store_true', 
                       help='Enable preemption agent for decision making (default: disabled)')
    parser.add_argument('--duration', type=int, default=60,
                       help='Simulation duration in minutes (default: 60)')
    parser.add_argument('--doctors', type=int, default=3,
                       help='Number of doctors (default: 3)')
    parser.add_argument('--triage-system', type=str, default='random',
                       choices=['random', 'manchester'],
                       help='Triage system to use: random or manchester (default: random)')
    
    args = parser.parse_args()
    
    # Create output/logs directory if it doesn't exist
    logs_dir = "output/logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    # Generate timestamped log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    triage_system_name = args.triage_system
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
            "num_doctors": args.doctors
        },
        source="main"
    )
    
    # Create simulation environment
    env = simpy.Environment()
    
    # Create components
    patient_provider = RandomService(arrival_rate=0.2)
    
    # Create triage system based on user choice
    if args.triage_system == 'random':
        triage_system = RandomTriageSystem(system_id="RANDOM_TRIAGE_001")
    elif args.triage_system == 'manchester':
        triage_system = ManchesterTriageSystem(system_id="MTS_001")
    else:
        raise ValueError(f"Unknown triage system: {args.triage_system}")
    
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
    
    event_handler = ConsoleEventHandler(verbose=True)
    
    # Create simulation engine
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
            "preemption_enabled": args.enable_preemption
        },
        source="main"
    )
    
    sim.run_simulation(duration=args.duration)
    
    # Log simulation completion
    logger.log_event(
        timestamp=float(args.duration),
        event_type=EventType.SIMULATION_END,
        message="Hospital simulation completed successfully",
        simulation_state=sim.simulation_state,  # Use simulation state from engine
        data={
            "duration": args.duration,
            "total_events_logged": len(logger.events),
            "simulation_status": "completed",
            "preemption_enabled": args.enable_preemption
        },
        source="main"
    )
    
    sim.print_statistics()
    
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
            "preemption_enabled": args.enable_preemption
        },
        source="main"
    )
    
    # Export detailed logs
    logger.export_to_json(json_file_path)
    
    # Generate plots in system-specific directory
    plot_files = sim.simulation_state.plot_results(system_name=triage_system_name)
    print(f"\nPlots generated in output/{triage_system_name}/:")
    for plot_type, file_path in plot_files.items():
        if plot_type != 'report':  # Don't show report path
            print(f"  {plot_type}: {os.path.basename(file_path)}")

if __name__ == "__main__":
    main()