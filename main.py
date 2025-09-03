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
        # Create a temporary LLM triage system first (will be replaced with metrics-aware version)
        logger.info("🤖 Creating initial LLM Triage System...")
        temp_llm_triage = LLMTriageSystem()
        
        # Create hospital with temporary triage system to initialize metrics
        logger.info("🏥 Initializing hospital to set up metrics services...")
        hospital = SimpleHospital(
            csv_folder='./output/csv',
            triage_system=temp_llm_triage,  # Temporary triage system
            sim_duration=480,    # 8 hours
            arrival_rate=50,     # 50 patients/hour (higher demand)
            delay_scaling=0,  # 1 real second = 0 simulation minutes
            nurses=3,            # Triage capacity
            doctors=2,           # Reduced to 2 for realistic doctor queuing
            beds=4,              # Reduced to 4 for realistic bed queuing
            log_level=logging.INFO  # Enable detailed logging
        )
        
        # Now create LLM triage system with operational metrics
        logger.info("🤖 Creating LLM Triage System with operational metrics integration...")
        llm_triage_with_metrics = LLMTriageSystem(
            operation_metrics=hospital.operation_metrics,
            nhs_metrics=hospital.nhs_metrics
        )
        
        # Replace the temporary triage system with the metrics-aware version
        hospital.triage_system = llm_triage_with_metrics
        logger.info("✅ LLM Triage System updated with operational metrics integration")
        
        logger.info(f"Simulation Parameters:")
        logger.info(f"  Duration: {hospital.sim_duration/60:.1f} hours")
        logger.info(f"  Arrival Rate: {hospital.arrival_rate} patients/hour")
        logger.info(f"  Staff: {hospital.nurses} nurses, {hospital.doctors} doctors")
        logger.info(f"  Beds: {hospital.beds}")
        logger.info(f"  Patient Data: {len(hospital.patients)} real patients available")
        logger.info(f"  Triage System: LLM with operational context integration")
        
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