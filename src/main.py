import simpy
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simulation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
import random
import numpy as np
from src.config.parameters import p
from src.entities.emergency_department import EmergencyDepartment
from src.triage_systems.manchester_triage import ManchesterTriage
from src.visualization.plots import EDVisualizer

def run_simulation(triage_system):
    """Run the NHS triage simulation"""
    # Initialize simulation environment
    env = simpy.Environment()
    # Initialize triage system and emergency department
    
    ed = EmergencyDepartment(env, triage_system)
    
    # Start patient generation process
    env.process(ed.patient_generator())
    
    # Run the simulation
    env.run(until=p.sim_duration)
    
    # Get metrics summary
    metrics_summary = ed.metrics.get_summary_stats()
    
    # Print summary statistics
    print(f"Simulation Results (Duration: {p.sim_duration} minutes)")
    print(f"Total patients: {metrics_summary['total_patients']}")
    print(f"Admission rate: {metrics_summary['admitted_rate']:.2f}")
    print(f"Average wait for triage: {metrics_summary['avg_wait_for_triage']:.2f} minutes")
    print(f"Average wait for consultation: {metrics_summary['avg_wait_for_consult']:.2f} minutes")
    print(f"Average total time in system: {metrics_summary['avg_total_time']:.2f} minutes")
    
    # Print wait times by priority
    print("\nAverage wait times by priority (1-5):")
    for priority, wait_time in metrics_summary['avg_wait_by_priority'].items():
        print(f"  Priority {priority}: {wait_time:.2f} minutes")
    
    return ed.metrics

def main():
    """Main entry point for the simulation"""

    triage_system = ManchesterTriage()

    # Run the simulation
    metrics = run_simulation(triage_system)
    
    # Create and run visualizations
    visualizer = EDVisualizer(metrics, triage_system)
    visualizer.create_wait_time_plots()
    visualizer.create_priority_distribution_plot()
    visualizer.verify_poisson_arrivals()
    
    print("\nSimulation completed successfully!")

if __name__ == '__main__':
    main()