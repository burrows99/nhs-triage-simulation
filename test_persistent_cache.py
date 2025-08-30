#!/usr/bin/env python3
"""
Test script for persistent cache functionality.
This allows testing simulation logic separately from AI generation.
"""

import sys
import os
sys.path.append('src')

from src.entities.patient import Patient
from src.triage_systems.simulation_aware_ai_triage import create_single_llm_triage, create_multi_agent_triage
from src.main import run_simulation
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cache_generation():
    """Generate and save LLM responses to persistent cache with real-time progress"""
    logger.info("=== Testing Cache Generation with Real-Time Progress ===")
    
    # Load a small subset of patients with deep medical context for LLMs
    patients = Patient.get_all(deep=True)[:10]  # Deep context for comprehensive LLM analysis
    patient_data_list = []
    
    for patient in patients:
        # Get comprehensive patient data including medical context
        patient_dict = patient.__dict__.copy()
        
        # Add comprehensive medical context if available
        try:
            comprehensive_context = patient.get_comprehensive_context()
            patient_dict['medical_context'] = comprehensive_context
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
    
    # Monitor progress in real-time
    import time
    logger.info("Monitoring progress in real-time...")
    
    for i in range(60):  # Monitor for up to 60 seconds
        time.sleep(2)
        
        single_progress = single_llm.provider.get_progress_stats()
        multi_progress = multi_agent.provider.get_progress_stats()
        
        single_done = single_progress['progress_percentage'] >= 100
        multi_done = multi_progress['progress_percentage'] >= 100
        
        logger.info(f"Progress Update {i+1}:")
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
    
    logger.info("Cache generation completed!")

def test_cache_usage():
    """Test using cached responses for simulation"""
    logger.info("=== Testing Cache Usage ===")
    
    # Create new triage systems (should load from persistent cache)
    single_llm = create_single_llm_triage()
    multi_agent = create_multi_agent_triage()
    
    # Check cache stats
    single_stats = single_llm.get_cache_statistics()
    multi_stats = multi_agent.get_cache_statistics()
    
    logger.info(f"Single LLM loaded cache: {single_stats}")
    logger.info(f"Multi-Agent loaded cache: {multi_stats}")
    
    if single_stats['persistent_cache_size'] > 0:
        logger.info("✅ Persistent cache found! Running simulation with cached responses...")
        
        # Run a quick simulation test
        try:
            logger.info("Testing Single LLM system...")
            run_simulation(single_llm)
            
            logger.info("Testing Multi-Agent system...")
            run_simulation(multi_agent)
            
            logger.info("✅ Simulation completed successfully with cached responses!")
        except Exception as e:
            logger.error(f"❌ Simulation failed: {e}")
    else:
        logger.warning("⚠️ No persistent cache found. Run test_cache_generation() first.")
    
    # Cleanup
    single_llm.shutdown()
    multi_agent.shutdown()

def monitor_progress():
    """Monitor progress of ongoing cache generation"""
    logger.info("=== Monitoring Cache Generation Progress ===")
    
    # Create triage systems to check progress
    single_llm = create_single_llm_triage()
    multi_agent = create_multi_agent_triage()
    
    try:
        import time
        logger.info("Monitoring real-time progress (Press Ctrl+C to stop)...")
        
        while True:
            single_progress = single_llm.provider.get_progress_stats()
            multi_progress = multi_agent.provider.get_progress_stats()
            
            # Check if there's any active progress
            if single_progress['total_requests'] == 0 and multi_progress['total_requests'] == 0:
                logger.info("No active cache generation found. Run 'generate' first.")
                break
            
            logger.info("\n" + "="*60)
            logger.info(f"Single LLM Progress: {single_progress['progress_percentage']:.1f}%")
            logger.info(f"  Total: {single_progress['total_requests']}, Completed: {single_progress['completed_requests']}, Failed: {single_progress['failed_requests']}")
            logger.info(f"  Success Rate: {single_progress['success_rate']:.1f}%")
            
            logger.info(f"Multi-Agent Progress: {multi_progress['progress_percentage']:.1f}%")
            logger.info(f"  Total: {multi_progress['total_requests']}, Completed: {multi_progress['completed_requests']}, Failed: {multi_progress['failed_requests']}")
            logger.info(f"  Success Rate: {multi_progress['success_rate']:.1f}%")
            
            # Check if both are complete
            if (single_progress['progress_percentage'] >= 100 and 
                multi_progress['progress_percentage'] >= 100):
                logger.info("\n✅ All cache generation completed!")
                break
            
            time.sleep(3)
            
    except KeyboardInterrupt:
        logger.info("\nMonitoring stopped by user.")
    finally:
        single_llm.shutdown()
        multi_agent.shutdown()

def clear_cache():
    """Clear all persistent cache"""
    logger.info("=== Clearing Persistent Cache ===")
    
    single_llm = create_single_llm_triage()
    single_llm.provider.clear_persistent_cache()
    single_llm.shutdown()
    
    logger.info("✅ Persistent cache cleared!")

def main():
    """Main test function"""
    if len(sys.argv) < 2:
        print("Usage: python test_persistent_cache.py [generate|use|monitor|clear]")
        print("  generate - Generate and save LLM responses to cache with progress tracking")
        print("  use      - Test simulation using cached responses")
        print("  monitor  - Monitor real-time progress of ongoing cache generation")
        print("  clear    - Clear all persistent cache")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'generate':
        test_cache_generation()
    elif command == 'use':
        test_cache_usage()
    elif command == 'monitor':
        monitor_progress()
    elif command == 'clear':
        clear_cache()
    else:
        print(f"Unknown command: {command}")
        print("Use 'generate', 'use', 'monitor', or 'clear'")

if __name__ == '__main__':
    main()