#!/usr/bin/env python3
"""Minimal hospital simulation runner"""

import simpy
from .entities.hospital import HospitalCore
from .entities.preemption_agent import PreemptionAgent
from .services.random import RandomService
from .simulation.simulation_engine import HospitalSimulationEngine as SimulationEngine
from .handler.console_event_handler import ConsoleEventHandler
from .entities.triage_nurse import TriageNurse

def main():
    """Run a minimal hospital simulation"""
    # Create simulation environment
    env = simpy.Environment()
    
    # Initialize hospital with 3 doctors
    hospital = HospitalCore(num_doctors=3)
    
    # Create components
    patient_provider = RandomService(arrival_rate=0.2, max_patients=10)
    triage_system = TriageNurse()
    preemption_agent = PreemptionAgent()
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
    
    print("Starting hospital simulation...")
    sim.run_simulation(duration=60)  # Run for 1 hour
    
    print("\nSimulation completed!")
    sim.print_statistics()

if __name__ == "__main__":
    main()