#!/usr/bin/env python3
"""
Hospital Simulation with Manchester Triage System

This script runs a hospital simulation using real patient data from Synthea
and the Manchester Triage System for patient triage.

Usage:
    python main.py
"""

import sys
import os
import logging

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import centralized logger
from src.logger import logger

from src.simulation.real_data_hospital import SimpleHospital
from src.triage.triage_constants import TriageCategories
from src.triage.manchester_triage_system import ManchesterTriageSystem
from src.triage.llm_triage_system.llm_triage_system import LLMTriageSystem


def main():
    """Main function to run the hospital simulation"""
    logger.info("🚀 Starting Hospital Simulation with Manchester Triage System")
    logger.info("This simulation uses real Synthea patient data with MTS triage")
    logger.info("🏥 Hospital Simulation with Manchester Triage System")
    logger.info("=" * 60)
    
    try:
        manchester_triage = ManchesterTriageSystem()
        # Create hospital simulation with detailed logging
        llm_triage = LLMTriageSystem(
            model_name="hf.co/mradermacher/docmap-uk-triage-merged-qwen2.5-7b-GGUF:Q4_K_M"
        )
        
        hospital = SimpleHospital(
            csv_folder='./output/csv',
            triage_system=manchester_triage,  # Using LLM triage system instead of MTS
            sim_duration=480,    # 8 hours
            arrival_rate=40,     # 40 patients/hour (realistic rate)
            delay_scaling=0.2,  # 1 real second = 0.2 simulation minutes
            nurses=3,            # Increased to 3 for realistic triage capacity
            doctors=4,           # Increased to 4 for better doctor utilization
            beds=8,              # Increased to 8 for realistic bed capacity
            log_level=logging.INFO  # Enable detailed logging
        )
        
        logger.info(f"Simulation Parameters:")
        logger.info(f"  Duration: {hospital.sim_duration/60:.1f} hours")
        logger.info(f"  Arrival Rate: {hospital.arrival_rate} patients/hour")
        logger.info(f"  Staff: {hospital.nurses} nurses, {hospital.doctors} doctors")
        logger.info(f"  Beds: {hospital.beds}")
        logger.info(f"  Patient Data: {len(hospital.patients)} real patients available")
        
        # Run simulation
        results = hospital.run()
        
        # Display results
        logger.info("📊 Simulation Results:")
        logger.info(f"  Total Patients Processed: {results['total_patients']}")
        logger.info(f"  Average Time in Hospital: {results['avg_time']:.1f} minutes")
        
        # Category breakdown
        from collections import Counter
        category_counts = Counter(results['categories'])
        logger.info(f"🏷️  Triage Category Distribution:")
        for category in [TriageCategories.RED, TriageCategories.ORANGE, TriageCategories.YELLOW, TriageCategories.GREEN, TriageCategories.BLUE]:
            count = category_counts.get(category, 0)
            percentage = (count / results['total_patients'] * 100) if results['total_patients'] > 0 else 0
            logger.info(f"    {category}: {count} patients ({percentage:.1f}%)")
        
        # Export NHS metrics and generate plots
        logger.info(f"📊 Generating Output Files...")
        
        # All data export and chart generation is handled by the simulation's run method
        logger.info(f"✅ Simulation completed successfully!")
        logger.info(f"📋 Summary: {results['total_patients']} patients processed")
        logger.info(f"⏱️  Average patient time: {results['avg_time']:.1f} minutes")
        
    except KeyboardInterrupt:
        logger.info("⏹️  Simulation interrupted by user")
    except Exception as e:
        logger.error(f"❌ Simulation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()