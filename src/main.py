import simpy
import logging
import sys

# Configure comprehensive logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('output/simulation.log', mode='a'),  # Append to log file to see complete flow
        logging.StreamHandler(sys.stdout)
    ]
)

# Set specific log levels for different modules to reduce noise
logging.getLogger('matplotlib').setLevel(logging.WARNING)  # Reduce matplotlib noise
logging.getLogger('matplotlib.pyplot').setLevel(logging.WARNING)
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)  # Pillow (used by matplotlib)
logging.getLogger('simpy').setLevel(logging.INFO)
logging.getLogger('numpy').setLevel(logging.WARNING)
logging.getLogger('pandas').setLevel(logging.WARNING)
logging.getLogger('scipy').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.info("Starting NHS Emergency Department Simulation with enhanced logging")
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
    logger.info("Starting visualization generation...")
    try:
        visualizer = EDVisualizer(metrics, triage_system)
        logger.info("EDVisualizer created successfully")
        
        logger.info("Creating wait time plots...")
        visualizer.create_wait_time_plots()
        logger.info("Wait time plots completed")
        
        logger.info("Creating priority distribution plot...")
        visualizer.create_priority_distribution_plot()
        logger.info("Priority distribution plot completed")
        
        logger.info("Verifying Poisson arrivals...")
        visualizer.verify_poisson_arrivals()
        logger.info("Poisson arrivals verification completed")
        
        logger.info("All visualizations completed successfully!")
    except Exception as e:
        logger.error(f"Error during visualization: {e}")
        logger.exception("Full traceback:")
    
    print("\nSimulation completed successfully!")
    logger.info("Simulation finished")

if __name__ == '__main__':
    main()