#!/usr/bin/env python3
"""
Hospital Simulation Main Entry Point

This file runs the discrete event hospital simulation using the HospitalSimulationEngine.
"""

from .simulation.simulation_engine import HospitalSimulationEngine


def main():
    """Main function to run the hospital simulation."""
    # Create and configure the simulation engine
    simulation = HospitalSimulationEngine(
        num_doctors=3,
        num_mri=2,
        num_beds=4,
        simulation_time=1000,
        seed=42
    )
    
    print("Starting hospital simulation...")
    print(f"Doctors: {len([r for r in simulation.hospital.resources['Doctor']])}")
    print(f"MRI machines: {len([r for r in simulation.hospital.resources['MRI']])}")
    print(f"Beds: {len([r for r in simulation.hospital.resources['Bed']])}")
    print(f"Simulation steps: {simulation.simulation_time}")
    print()
    
    # Run the simulation
    simulation.run()
    
    print("Simulation completed!")
    print(f"Total snapshots captured: {len(simulation.hospital.history)}")
    
    # Display plots
    if simulation.hospital.plotting_service:
        print("Generating plots...")
        simulation.hospital.plotting_service.plot_queue_lengths()
        simulation.hospital.plotting_service.plot_current_patients()


if __name__ == "__main__":
    main()
