#!/usr/bin/env python3
"""Minimal hospital simulation runner"""

import argparse
import simpy
from .entities.hospital import HospitalCore
from .entities.preemption_agent import PreemptionAgent
from .services.random import RandomService
from .simulation.simulation_engine import HospitalSimulationEngine as SimulationEngine
from .handler.console_event_handler import ConsoleEventHandler
from .entities.triage_nurse import TriageNurse
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
    
    args = parser.parse_args()
    
    # Initialize centralized logging
    logger = initialize_logger(
        log_to_console=True,
        log_to_file=True,
        log_file_path="hospital_simulation.log",
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
    
    # Initialize hospital with specified number of doctors
    hospital = HospitalCore(num_doctors=args.doctors)
    
    # Create components
    patient_provider = RandomService(arrival_rate=0.2)
    triage_system = TriageNurse(nurse_id="NURSE_001")
    
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
            "export_file": "simulation_events.json",
            "log_file": "hospital_simulation.log",
            "preemption_enabled": args.enable_preemption
        },
        source="main"
    )
    
    # Export detailed logs
    logger.export_to_json("simulation_events.json")

if __name__ == "__main__":
    main()