import simpy
import logging
import random
import numpy as np
from src.config.config_manager import configure_logging, get_simulation_config
from src.entities.emergency_department import EmergencyDepartment
from src.triage_systems.manchester_triage import ManchesterTriage
from src.visualization.plots import EDVisualizer

# Configure logging using centralized configuration
configure_logging()
logger = logging.getLogger(__name__)
logger.info("Starting NHS Emergency Department Simulation with enhanced logging")


def run_simulation(triage_system):
    """Run the NHS triage simulation"""
    # Initialize simulation environment
    env = simpy.Environment()
    # Initialize triage system and emergency department
    
    ed = EmergencyDepartment(env, triage_system)
    
    # Start patient generation process
    env.process(ed.patient_generator())
    
    # Run the simulation using config
    sim_config = get_simulation_config()
    env.run(until=sim_config['duration'])
    
    # Get metrics summary
    metrics_summary = ed.metrics.get_summary_stats()
    
    # Print summary statistics using config
    sim_config = get_simulation_config()
    print(f"Simulation Results (Duration: {sim_config['duration']} minutes)")
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

def run_all_triage_systems():
    """Run simulations for all three triage systems"""
    from src.triage_systems.single_LLM_based_triage import SingleLLMBasedTriage
    from src.triage_systems.multi_LLM_based_triage import MultiLLMBasedTriage
    import time
    
    # Define all triage systems to test
    triage_systems = [
        ("Manchester Triage System", ManchesterTriage()),
        ("Single LLM-based Triage", SingleLLMBasedTriage()),
        ("Multi-Agent LLM-based Triage", MultiLLMBasedTriage())
    ]
    
    results = {}
    
    for system_name, triage_system in triage_systems:
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting {system_name}")
        logger.info(f"{'='*60}")
        
        try:
            start_time = time.time()
            
            # Run the simulation
            metrics = run_simulation(triage_system)
            
            # Calculate simulation time
            simulation_time = time.time() - start_time
            
            # Get metrics summary
            metrics_summary = metrics.get_summary_stats()
            
            # Store results
            results[system_name] = {
                'metrics': metrics,
                'summary': metrics_summary,
                'simulation_time': simulation_time,
                'triage_system': triage_system
            }
            
            # Create and run visualizations
            logger.info(f"Starting visualization generation for {system_name}...")
            try:
                visualizer = EDVisualizer(metrics, triage_system)
                logger.info(f"EDVisualizer created successfully for {system_name}")
                
                logger.info("Creating wait time plots...")
                visualizer.create_wait_time_plots()
                logger.info("Wait time plots completed")
                
                logger.info("Creating priority distribution plot...")
                visualizer.create_priority_distribution_plot()
                logger.info("Priority distribution plot completed")
                
                logger.info("Verifying Poisson arrivals...")
                visualizer.verify_poisson_arrivals()
                logger.info("Poisson arrivals verification completed")
                
                logger.info(f"All visualizations completed successfully for {system_name}!")
            except Exception as e:
                logger.error(f"Error during {system_name} visualization: {e}")
                logger.exception("Full traceback:")
            
            # Print individual results
            print(f"\n{'='*60}")
            print(f"{system_name} Results")
            print(f"{'='*60}")
            print(f"Simulation Time: {simulation_time:.2f} seconds")
            print(f"Total patients: {metrics_summary['total_patients']}")
            print(f"Admission rate: {metrics_summary['admitted_rate']:.2f}")
            print(f"Average wait for triage: {metrics_summary['avg_wait_for_triage']:.2f} minutes")
            print(f"Average wait for consultation: {metrics_summary['avg_wait_for_consult']:.2f} minutes")
            print(f"Average total time in system: {metrics_summary['avg_total_time']:.2f} minutes")
            
            logger.info(f"{system_name} completed successfully")
            
        except Exception as e:
            logger.error(f"Error running {system_name}: {e}")
            logger.exception("Full traceback:")
            print(f"\n{system_name} failed: {e}")
            if "ollama" in str(e).lower() or "connection" in str(e).lower():
                print(f"Note: {system_name} requires Ollama service to be running.")
                print("Start Ollama with: docker-compose up ollama ollama-downloader -d")
    
    # Print comparison summary
    if len(results) > 1:
        print(f"\n{'='*60}")
        print("COMPARISON SUMMARY")
        print(f"{'='*60}")
        
        for system_name, result in results.items():
            summary = result['summary']
            sim_time = result['simulation_time']
            print(f"{system_name}:")
            print(f"  Patients: {summary['total_patients']}, "
                  f"Avg Triage Wait: {summary['avg_wait_for_triage']:.1f}min, "
                  f"Sim Time: {sim_time:.1f}s")
        
        # Find best performing systems
        best_throughput = max(results.items(), key=lambda x: x[1]['summary']['total_patients'])
        best_triage_wait = min(results.items(), key=lambda x: x[1]['summary']['avg_wait_for_triage'])
        fastest_sim = min(results.items(), key=lambda x: x[1]['simulation_time'])
        
        print(f"\nBest Throughput: {best_throughput[0]} ({best_throughput[1]['summary']['total_patients']} patients)")
        print(f"Shortest Triage Wait: {best_triage_wait[0]} ({best_triage_wait[1]['summary']['avg_wait_for_triage']:.1f} min)")
        print(f"Fastest Simulation: {fastest_sim[0]} ({fastest_sim[1]['simulation_time']:.1f} sec)")
    
    return results

def main():
    """Main entry point for the simulation"""
    logger.info("Starting NHS Emergency Department Simulation - All Triage Systems")
    
    # Run all triage systems
    results = run_all_triage_systems()
    
    print(f"\n{'='*60}")
    print("ALL SIMULATIONS COMPLETED")
    print(f"{'='*60}")
    print(f"Systems tested: {len(results)}")
    print("Check output directories for detailed results and plots.")
    
    if len(results) == 0:
        print("\nNo systems completed successfully.")
        print("For LLM-based systems, ensure Ollama is running:")
        print("  docker-compose up ollama ollama-downloader -d")
    elif len(results) < 3:
        print(f"\nOnly {len(results)} out of 3 systems completed successfully.")
        print("Check logs for details on failed systems.")
    else:
        print("\nAll three triage systems completed successfully!")
    
    logger.info("All simulations finished")

if __name__ == '__main__':
    main()