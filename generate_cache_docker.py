#!/usr/bin/env python3
"""
Docker-based cache generation script
Generates LLM cache using the same environment as the simulation
"""

import sys
sys.path.append('src')

from src.entities.patient import Patient
from src.triage_systems.simulation_aware_ai_triage import create_single_llm_triage, create_multi_agent_triage
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_cache():
    """Generate LLM cache using Docker environment"""
    logger.info("=== Docker-based Cache Generation ===")
    
    # Load patients with deep context (same as simulation)
    patients = Patient.get_all(deep=True)[:10]  # Small subset for testing
    patient_data_list = []
    
    for patient in patients:
        # Get comprehensive patient data including medical context
        patient_dict = patient.__dict__.copy()
        
        # Add comprehensive medical context if available
        try:
            comprehensive_context = patient.get_comprehensive_context()
            patient_dict['medical_context'] = comprehensive_context
            logger.info(f"Added comprehensive context for patient {patient.id}: {len(str(comprehensive_context))} chars")
        except Exception as e:
            logger.warning(f"Could not get comprehensive context for patient {patient.id}: {e}")
        
        patient_data_list.append(patient_dict)
    
    logger.info(f"Loaded {len(patient_data_list)} patients for cache generation")
    
    # Create triage systems
    single_llm = create_single_llm_triage()
    multi_agent = create_multi_agent_triage()
    
    # Reset progress counters
    single_llm.provider.reset_progress_counters()
    multi_agent.provider.reset_progress_counters()
    
    # Generate cache for both systems
    logger.info("Generating Single LLM cache...")
    single_llm.precompute_patient_responses(patient_data_list)
    
    logger.info("Generating Multi-Agent cache...")
    multi_agent.precompute_patient_responses(patient_data_list)
    
    # Monitor progress
    logger.info("Monitoring cache generation progress...")
    
    for i in range(60):  # Monitor for up to 60 seconds
        time.sleep(2)
        
        single_progress = single_llm.provider.get_progress_stats()
        multi_progress = multi_agent.provider.get_progress_stats()
        
        single_done = single_progress['progress_percentage'] >= 100
        multi_done = multi_progress['progress_percentage'] >= 100
        
        if i % 5 == 0:  # Log every 10 seconds
            logger.info(f"Progress Update:")
            logger.info(f"  Single LLM: {single_progress['progress_percentage']:.1f}% ({single_progress['completed_requests']}/{single_progress['total_requests']})")
            logger.info(f"  Multi-Agent: {multi_progress['progress_percentage']:.1f}% ({multi_progress['completed_requests']}/{multi_progress['total_requests']})")
        
        if single_done and multi_done:
            logger.info("✅ All cache generation completed!")
            break
    
    # Final stats
    single_stats = single_llm.get_cache_statistics()
    multi_stats = multi_agent.get_cache_statistics()
    
    logger.info(f"Final Single LLM stats: {single_stats['progress']}")
    logger.info(f"Final Multi-Agent stats: {multi_stats['progress']}")
    
    # Force save to disk
    single_llm.provider.force_save_cache()
    multi_agent.provider.force_save_cache()
    
    # Cleanup
    single_llm.shutdown()
    multi_agent.shutdown()
    
    logger.info("Docker-based cache generation completed!")

if __name__ == '__main__':
    generate_cache()