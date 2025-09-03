#!/usr/bin/env python3
"""
Hospital Simulation with LLM Triage System

Runs hospital simulation using real Synthea patient data with LLM-based triage.
"""

import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.logger import logger

from src.simulation.real_data_hospital import SimpleHospital
from src.triage.triage_constants import TriageCategories
from src.triage.manchester_triage_system import ManchesterTriageSystem
from src.triage.llm_triage_system.llm_triage_system import LLMTriageSystem


def main():
    """Main function to run the hospital simulation"""
    logger.info("🏥 Starting Hospital Simulation with LLM Triage System")
    logger.info("=" * 60)
    
    try:
        temp_llm_triage = LLMTriageSystem()
        
        hospital = SimpleHospital(
            csv_folder='./output/csv',
            triage_system=temp_llm_triage,
            sim_duration=480,
            arrival_rate=50,
            delay_scaling=0,
            nurses=3,
            doctors=2,
            beds=4,
            log_level=logging.INFO
        )
        
        llm_triage_with_metrics = LLMTriageSystem(
            operation_metrics=hospital.operation_metrics,
            nhs_metrics=hospital.nhs_metrics
        )
        
        hospital.triage_system = llm_triage_with_metrics
        
        logger.info(f"📊 Config: {hospital.sim_duration/60:.1f}h | {hospital.arrival_rate}/h | {hospital.nurses}N {hospital.doctors}D {hospital.beds}B | {len(hospital.patients)} patients")
        logger.info(f"🤖 Triage: LLM with operational context")
        
        results = hospital.run()
        
        logger.info("📊 Simulation Results:")
        logger.info(f"  Total Patients: {results['total_patients']}")
        logger.info(f"  Average Time: {results['avg_time']:.1f} minutes")
        
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