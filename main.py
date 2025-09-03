#!/usr/bin/env python3
"""
Comparative Hospital Simulation

Runs hospital simulation with both Manchester Triage System and LLM-based triage
for comparative analysis. Outputs results to separate directories.
"""

import sys
import os
import logging
from collections import Counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.logger import logger
from src.simulation.real_data_hospital import SimpleHospital
from src.triage.triage_constants import TriageCategories
from src.triage.manchester_triage_system import ManchesterTriageSystem
from src.triage.llm_triage_system.single_llm_triage import SingleLLMTriage
from src.triage.llm_triage_system.mixture_llm_triage import MixtureLLMTriage


def run_simulation(triage_system, system_name: str, output_dir: str):
    """Run simulation with specified triage system
    
    Args:
        triage_system: Triage system instance
        system_name: Name of the triage system for logging
        output_dir: Output directory for results
        
    Returns:
        Simulation results dictionary
    """
    logger.info(f"🏥 Starting {system_name} Simulation")
    logger.info(f"📁 Output Directory: {output_dir}")
    
    # Create initial triage system instance
    if isinstance(triage_system, type):
        if issubclass(triage_system, SingleLLMTriage):
            temp_triage = SingleLLMTriage()
        elif issubclass(triage_system, MixtureLLMTriage):
            temp_triage = MixtureLLMTriage()
        elif issubclass(triage_system, ManchesterTriageSystem):
            temp_triage = ManchesterTriageSystem()
        else:
            temp_triage = SingleLLMTriage()  # Default fallback
    else:
        temp_triage = triage_system
    
    hospital = SimpleHospital(
        csv_folder='./output/csv',
        output_dir=output_dir,
        triage_system=temp_triage,
        sim_duration=480,
        arrival_rate=50,
        delay_scaling=0,
        nurses=3,
        doctors=2,
        beds=4,
        log_level=logging.INFO
    )
    
    # Set up triage system with metrics if it's LLM-based
    if isinstance(triage_system, type) and issubclass(triage_system, (SingleLLMTriage, MixtureLLMTriage)):
        if issubclass(triage_system, MixtureLLMTriage):
            triage_with_metrics = MixtureLLMTriage(
                operation_metrics=hospital.operation_metrics,
                nhs_metrics=hospital.nhs_metrics
            )
        else:
            triage_with_metrics = SingleLLMTriage(
                operation_metrics=hospital.operation_metrics,
                nhs_metrics=hospital.nhs_metrics
            )
        hospital.triage_system = triage_with_metrics
    
    logger.info(f"📊 Config: {hospital.sim_duration/60:.1f}h | {hospital.arrival_rate}/h | {hospital.nurses}N {hospital.doctors}D {hospital.beds}B | {len(hospital.patients)} patients")
    logger.info(f"🔧 Triage System: {system_name}")
    
    results = hospital.run()
    
    logger.info(f"📊 {system_name} Results:")
    logger.info(f"  Total Patients: {results['total_patients']}")
    logger.info(f"  Average Time: {results['avg_time']:.1f} minutes")
    
    category_counts = Counter(results['categories'])
    logger.info(f"🏷️ Triage Category Distribution:")
    for category in [TriageCategories.RED, TriageCategories.ORANGE, TriageCategories.YELLOW, TriageCategories.GREEN, TriageCategories.BLUE]:
        count = category_counts.get(category, 0)
        percentage = (count / results['total_patients'] * 100) if results['total_patients'] > 0 else 0
        logger.info(f"    {category}: {count} patients ({percentage:.1f}%)")
    
    logger.info(f"✅ {system_name} simulation completed!")
    logger.info(f"📁 Results saved to: {output_dir}")
    logger.info("=" * 80)
    
    return results


def main():
    """Main function to run comparative hospital simulations"""
    logger.info("🏥 Starting Comparative Hospital Simulation")
    logger.info("🔄 Running both Manchester Triage System and LLM-based Triage")
    logger.info("=" * 80)
    
    try:
        # Simulation configurations
        simulations = [
            {
                'system': ManchesterTriageSystem,
                'name': 'Manchester Triage System',
                'output_dir': './output/simulation/manchester_triage_system'
            },
            {
                'system': SingleLLMTriage,
                'name': 'Single LLM Triage System',
                'output_dir': './output/simulation/single_llm_system'
            },
            {
                'system': MixtureLLMTriage,
                'name': 'Multi-Agent LLM Triage System',
                'output_dir': './output/simulation/multi_agent_llm_system'
            }
        ]
        
        results_summary = {}
        
        # Run simulations for both systems
        for sim_config in simulations:
            try:
                results = run_simulation(
                    triage_system=sim_config['system'],
                    system_name=sim_config['name'],
                    output_dir=sim_config['output_dir']
                )
                results_summary[sim_config['name']] = results
                
            except Exception as e:
                logger.error(f"❌ {sim_config['name']} simulation failed: {e}")
                continue
        
        # Generate comparative summary
        logger.info("📊 COMPARATIVE SIMULATION SUMMARY")
        logger.info("=" * 80)
        
        for system_name, results in results_summary.items():
            logger.info(f"🔧 {system_name}:")
            logger.info(f"   📊 Patients Processed: {results['total_patients']}")
            logger.info(f"   ⏱️  Average Time: {results['avg_time']:.1f} minutes")
            
            category_counts = Counter(results['categories'])
            logger.info(f"   🏷️  Category Distribution:")
            for category in [TriageCategories.RED, TriageCategories.ORANGE, TriageCategories.YELLOW, TriageCategories.GREEN, TriageCategories.BLUE]:
                count = category_counts.get(category, 0)
                percentage = (count / results['total_patients'] * 100) if results['total_patients'] > 0 else 0
                logger.info(f"      {category}: {count} ({percentage:.1f}%)")
            logger.info("")
        
        logger.info("✅ All simulations completed successfully!")
        logger.info("📁 Results available in:")
        logger.info("   📂 ./output/simulation/manchester_triage_system/")
        logger.info("   📂 ./output/simulation/llm_based_system/")
        
    except KeyboardInterrupt:
        logger.info("⏹️ Simulation interrupted by user")
    except Exception as e:
        logger.error(f"❌ Simulation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()