#!/usr/bin/env python3
"""
Hospital Management System Demo
This script provides a command-line interface to run either a hospital management demonstration
or a SimPy-based hospital simulation.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.services.hospital_factory import HospitalFactory
from src.simulation.simulation import HospitalSimulation
from demonstration import run_demonstration

def run_hospital_simulation(duration_minutes: int = 480) -> str:
    """Run a complete hospital simulation and return JSON filename"""
    hospital = HospitalFactory.create_sample_hospital()
    simulation = HospitalSimulation(hospital, duration_minutes)

    # Run simulation
    simulation.run_simulation()

    # Export to JSON
    filename = simulation.export_events_to_json()

    return filename

if __name__ == "__main__":
    print("\n" + "="*60)
    print("CHOOSE DEMONSTRATION MODE")
    print("="*60)
    print("1. Hospital Management Demo (original)")
    print("2. SimPy Hospital Simulation (new)")

    choice = input("\nEnter your choice (1 or 2): ").strip()

    if choice == "1":
        run_demonstration()
    elif choice == "2":
        print("\n🏥 RUNNING SIMPY HOSPITAL SIMULATION")
        json_file = run_hospital_simulation(120)  # 2-hour simulation
        print(f"\nSimulation complete! Events saved to: {json_file}")
        print("This JSON file can be used for React visualization.")
    else:
        print("Invalid choice. Running default hospital demo...")
        run_demonstration()
