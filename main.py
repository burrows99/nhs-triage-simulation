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


def run_hospital_simulation():
    """Run hospital simulation with Manchester Triage System"""
    logger.info("🏥 Hospital Simulation with Manchester Triage System")
    logger.info("=" * 60)
    
    # Create hospital simulation with detailed logging
    hospital = SimpleHospital(
        csv_folder='./output/csv',
        sim_duration=480,    # 8 hours
        arrival_rate=12,     # 12 patients/hour
        delay_scaling=0.2,  # 1 real second = 0.2 simulation minutes
        nurses=3,
        doctors=8,
        beds=20,
        log_level=logging.INFO  # Enable detailed logging
    )
    
    logger.info(f"Simulation Parameters:")
    logger.info(f"  Duration: {hospital.sim_duration/60:.1f} hours")
    logger.info(f"  Arrival Rate: {hospital.arrival_rate} patients/hour")
    logger.info(f"  Staff: {hospital.nurses} nurses, {hospital.doctors} doctors")
    logger.info(f"  Beds: {hospital.beds}")
    logger.info(f"  Patient Data: {len(hospital.patient_ids)} real patients available")
    
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
    
    # Create output directories
    os.makedirs('./output/hospital_simulation/metrics', exist_ok=True)
    os.makedirs('./output/hospital_simulation/plots', exist_ok=True)
    
    # Export NHS metrics data
    hospital.export_nhs_data(
        json_filepath='./output/hospital_simulation/metrics/nhs_metrics.json',
        csv_filepath='./output/hospital_simulation/metrics/patient_data.csv'
    )
    
    # Generate NHS metrics plots
    plots_generated = hospital.nhs_metrics.generate_all_plots('./output/hospital_simulation/plots')
    
    logger.info(f"📁 Files Generated:")
    logger.info(f"  📊 NHS Metrics JSON: ./output/hospital_simulation/metrics/nhs_metrics.json")
    logger.info(f"  📋 Patient Data CSV: ./output/hospital_simulation/metrics/patient_data.csv")
    logger.info(f"  📈 Plots Generated: {len(plots_generated)} files in ./output/hospital_simulation/plots/")
    for plot in plots_generated:
        logger.info(f"    - {plot}")
    
    # Clean up matplotlib resources
    hospital.nhs_metrics.close_plots()
    
    return results


def main():
    """Main function to run the hospital simulation"""
    logger.info("🚀 Starting Hospital Simulation with Manchester Triage System")
    logger.info("This simulation uses real Synthea patient data with MTS triage")
    
    try:
        results = run_hospital_simulation()
        logger.info("✅ Simulation completed successfully!")
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