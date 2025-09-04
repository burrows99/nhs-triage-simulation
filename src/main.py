#!/usr/bin/env python3
"""Minimal hospital simulation runner"""

import simpy
from .entities.hospital import HospitalCore
from .entities.preemption_agent import PreemptionAgent
from .services.random import RandomService
from .simulation.simulation_engine import HospitalSimulationEngine as SimulationEngine
from .handler.console_event_handler import ConsoleEventHandler
from .entities.triage_nurse import TriageNurse
from .utils.logger import initialize_logger, LogLevel, EventType

def main():
    """Run a minimal hospital simulation"""
    # Initialize centralized logging
    logger = initialize_logger(
        log_to_console=True,
        log_to_file=True,
        log_file_path="hospital_simulation.log",
        min_level=LogLevel.INFO
    )
    
    # Log simulation start
    logger.log_event(
        timestamp=0.0,
        event_type=EventType.SIMULATION_START,
        message="Hospital simulation starting - Main execution",
        data={
            "simulation_type": "hospital_emergency_department",
            "logging_enabled": True,
            "log_file": "hospital_simulation.log"
        },
        source="main"
    )
    
    # Create simulation environment
    env = simpy.Environment()
    
    # Initialize hospital with 3 doctors
    hospital = HospitalCore(num_doctors=3)
    
    # Create components
    patient_provider = RandomService(arrival_rate=0.2, max_patients=10)
    triage_system = TriageNurse(nurse_id="NURSE_001")
    preemption_agent = PreemptionAgent(agent_id="PREEMPTION_AGENT_001")
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
            "duration": 60,
            "simulation_type": "hospital_emergency_department"
        },
        source="main"
    )
    
    sim.run_simulation(duration=60)  # Run for 1 hour
    
    # Log simulation completion
    logger.log_event(
        timestamp=60.0,
        event_type=EventType.SIMULATION_END,
        message="Hospital simulation completed successfully",
        simulation_state=sim.simulation_state,  # Use simulation state from engine
        data={
            "duration": 60,
            "total_events_logged": len(logger.events),
            "simulation_status": "completed"
        },
        source="main"
    )
    
    sim.print_statistics()
    
    # Log summary statistics
    stats = logger.get_summary_stats()
    logger.log_event(
        timestamp=60.0,
        event_type=EventType.SYSTEM_STATE,
        message="Logging summary statistics",
        simulation_state=sim.simulation_state,
        data={
            "total_events": stats['total_events'],
            "event_types": list(stats['event_type_counts'].keys()),
            "time_range": f"{stats['time_range']['start']:.1f} - {stats['time_range']['end']:.1f} minutes",
            "export_file": "simulation_events.json",
            "log_file": "hospital_simulation.log"
        },
        source="main"
    )
    
    # Export detailed logs
    logger.export_to_json("simulation_events.json")

if __name__ == "__main__":
    main()