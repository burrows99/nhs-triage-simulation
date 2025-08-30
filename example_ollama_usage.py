#!/usr/bin/env python3
"""
Example usage of Ollama-based Single and Multi-Agent Triage Systems
with centralized configuration management.

This example demonstrates how to use the new LLM-based triage systems
that are configured through the centralized config manager instead of YAML files.
"""

import simpy
from src.config.config_manager import configure_logging, get_simulation_config
from src.entities.emergency_department import EmergencyDepartment
from src.triage_systems.single_LLM_based_triage import SingleLLMBasedTriage
from src.triage_systems.multi_LLM_based_triage import MultiLLMBasedTriage
from src.model_providers.ollama import OllamaProvider
from src.visualization.plots import EDVisualizer
import logging

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)

def run_single_llm_simulation():
    """Run simulation with Single LLM-based triage system"""
    logger.info("Starting Single LLM-based Triage Simulation")
    
    # Initialize Ollama provider (will use config defaults)
    # Note: Uses Docker service 'ollama' with llama3.2:1b model
    ollama_provider = None  # Will be auto-initialized with config
    
    # Check if Ollama is available (optional)
    if not ollama_provider.health_check():
        logger.warning("Ollama health check failed. Simulation may not work properly.")
        logger.info(f"Available models: {ollama_provider.get_available_models()}")
    
    # Initialize Single LLM triage system
    # Configuration is automatically loaded from config_manager
    triage_system = SingleLLMBasedTriage(ollama_provider)
    
    # Initialize simulation environment
    env = simpy.Environment()
    
    # Initialize emergency department with LLM triage system
    ed = EmergencyDepartment(env, triage_system)
    
    # Start patient generation process
    env.process(ed.patient_generator())
    
    # Run the simulation
    sim_config = get_simulation_config()
    logger.info(f"Running simulation for {sim_config['duration']} minutes")
    env.run(until=sim_config['duration'])
    
    # Get metrics summary
    metrics_summary = ed.metrics.get_summary_stats()
    
    # Print results
    print("\n=== Single LLM Triage Simulation Results ===")
    print(f"Total patients: {metrics_summary['total_patients']}")
    print(f"Admission rate: {metrics_summary['admitted_rate']:.2f}")
    print(f"Average wait for triage: {metrics_summary['avg_wait_for_triage']:.2f} minutes")
    print(f"Average wait for consultation: {metrics_summary['avg_wait_for_consult']:.2f} minutes")
    print(f"Average total time in system: {metrics_summary['avg_total_time']:.2f} minutes")
    
    # Create visualizations
    try:
        visualizer = EDVisualizer(ed.metrics, triage_system)
        visualizer.create_wait_time_plots()
        visualizer.create_priority_distribution_plot()
        visualizer.verify_poisson_arrivals()
        logger.info("Single LLM visualizations completed successfully!")
    except Exception as e:
        logger.error(f"Error during visualization: {e}")
    
    return ed.metrics

def run_multi_llm_simulation():
    """Run simulation with Multi-Agent LLM-based triage system"""
    logger.info("Starting Multi-Agent LLM-based Triage Simulation")
    
    # Initialize Ollama provider (will use config defaults)
    # Note: Uses Docker service 'ollama' with llama3.2:1b model
    ollama_provider = None  # Will be auto-initialized with config
    
    # Check if Ollama is available (optional)
    if not ollama_provider.health_check():
        logger.warning("Ollama health check failed. Simulation may not work properly.")
        logger.info(f"Available models: {ollama_provider.get_available_models()}")
    
    # Initialize Multi-Agent LLM triage system
    # Configuration is automatically loaded from config_manager
    # This system uses 3 agents: pediatric_risk_assessor, clinical_assessor, consensus_coordinator
    triage_system = MultiLLMBasedTriage(ollama_provider)
    
    # Initialize simulation environment
    env = simpy.Environment()
    
    # Initialize emergency department with Multi-Agent LLM triage system
    ed = EmergencyDepartment(env, triage_system)
    
    # Start patient generation process
    env.process(ed.patient_generator())
    
    # Run the simulation
    sim_config = get_simulation_config()
    logger.info(f"Running simulation for {sim_config['duration']} minutes")
    env.run(until=sim_config['duration'])
    
    # Get metrics summary
    metrics_summary = ed.metrics.get_summary_stats()
    
    # Print results
    print("\n=== Multi-Agent LLM Triage Simulation Results ===")
    print(f"Total patients: {metrics_summary['total_patients']}")
    print(f"Admission rate: {metrics_summary['admitted_rate']:.2f}")
    print(f"Average wait for triage: {metrics_summary['avg_wait_for_triage']:.2f} minutes")
    print(f"Average wait for consultation: {metrics_summary['avg_wait_for_consult']:.2f} minutes")
    print(f"Average total time in system: {metrics_summary['avg_total_time']:.2f} minutes")
    
    # Create visualizations
    try:
        visualizer = EDVisualizer(ed.metrics, triage_system)
        visualizer.create_wait_time_plots()
        visualizer.create_priority_distribution_plot()
        visualizer.verify_poisson_arrivals()
        logger.info("Multi-Agent LLM visualizations completed successfully!")
    except Exception as e:
        logger.error(f"Error during visualization: {e}")
    
    return ed.metrics

def compare_triage_systems():
    """Compare different triage systems"""
    logger.info("Starting Triage System Comparison")
    
    # You can run multiple simulations and compare results
    print("\n=== Triage System Comparison ===")
    print("1. Single LLM-based Triage")
    print("2. Multi-Agent LLM-based Triage")
    print("3. Manchester Triage System (Fuzzy Logic)")
    
    # Example: Run single LLM simulation
    single_metrics = run_single_llm_simulation()
    
    # Example: Run multi-agent LLM simulation
    # multi_metrics = run_multi_llm_simulation()
    
    # You can add comparison logic here
    print("\nComparison completed. Check output directories for visualizations.")

def demonstrate_configuration():
    """Demonstrate the configuration system"""
    from src.config.config_manager import get_ollama_config, get_manchester_triage_config
    
    print("\n=== Configuration System Demonstration ===")
    
    # Show Ollama configuration
    ollama_config = get_ollama_config()
    print("\nOllama Configuration:")
    print(f"  Timeout: {ollama_config['request']['timeout_sec']} seconds")
    print(f"  Retries: {ollama_config['request']['retries']}")
    print(f"  Temperature: {ollama_config['request']['options']['temperature']}")
    print(f"  Number of agents: {len(ollama_config['multi_agent']['agents'])}")
    
    # Show Manchester Triage configuration
    mts_config = get_manchester_triage_config()
    print("\nManchester Triage Configuration:")
    print(f"  Priority weights: {mts_config['priority_weights']}")
    print(f"  Time factor: {mts_config['time_factor']}")
    print(f"  Fuzzy rules: {len(mts_config['fuzzy_rules'])} rules")
    
    print("\nAll configurations are centrally managed in config_manager.py")
    print("No YAML files needed - everything is in Python configuration functions.")

if __name__ == "__main__":
    print("NHS Triage Simulation - Ollama LLM Integration Example")
    print("======================================================")
    
    # Demonstrate configuration
    demonstrate_configuration()
    
    # Note: Uncomment the following lines to run actual simulations
    # These require Ollama to be running locally with a suitable model
    
    print("\nTo run LLM-based simulations:")
    print("1. Start the Docker services: docker-compose up ollama ollama-downloader")
    print("2. Wait for llama3.2:1b model to download automatically")
    print("3. Run simulation: docker-compose up nhs-triage-sim")
    print("4. Or uncomment the simulation calls below for direct execution")
    
    # Uncomment to run single LLM simulation
    # run_single_llm_simulation()
    
    # Uncomment to run multi-agent LLM simulation
    # run_multi_llm_simulation()
    
    # Uncomment to run comparison
    # compare_triage_systems()
    
    print("\nExample completed. Check the code for implementation details.")