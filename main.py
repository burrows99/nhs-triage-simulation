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

from src.simulation.real_data_hospital import SimpleHospital
from src.triage.triage_constants import TriageCategories


def run_hospital_simulation():
    """Run hospital simulation with Manchester Triage System"""
    print("\n🏥 Hospital Simulation with Manchester Triage System")
    print("=" * 60)
    
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
    
    print(f"\nSimulation Parameters:")
    print(f"  Duration: {hospital.sim_duration/60:.1f} hours")
    print(f"  Arrival Rate: {hospital.arrival_rate} patients/hour")
    print(f"  Staff: {hospital.nurses} nurses, {hospital.doctors} doctors")
    print(f"  Beds: {hospital.beds}")
    print(f"  Patient Data: {len(hospital.patient_ids)} real patients available")
    
    # Run simulation
    results = hospital.run()
    
    # Display results
    print("\n📊 Simulation Results:")
    print(f"  Total Patients Processed: {results['total_patients']}")
    print(f"  Average Time in Hospital: {results['avg_time']:.1f} minutes")
    
    # Category breakdown
    from collections import Counter
    category_counts = Counter(results['categories'])
    print(f"\n🏷️  Triage Category Distribution:")
    for category in [TriageCategories.RED, TriageCategories.ORANGE, TriageCategories.YELLOW, TriageCategories.GREEN, TriageCategories.BLUE]:
        count = category_counts.get(category, 0)
        percentage = (count / results['total_patients'] * 100) if results['total_patients'] > 0 else 0
        print(f"    {category}: {count} patients ({percentage:.1f}%)")
    
    # Export NHS metrics and generate plots
    print(f"\n📊 Generating Output Files...")
    
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
    
    print(f"\n📁 Files Generated:")
    print(f"  📊 NHS Metrics JSON: ./output/hospital_simulation/metrics/nhs_metrics.json")
    print(f"  📋 Patient Data CSV: ./output/hospital_simulation/metrics/patient_data.csv")
    print(f"  📈 Plots Generated: {len(plots_generated)} files in ./output/hospital_simulation/plots/")
    for plot in plots_generated:
        print(f"    - {plot}")
    
    # Clean up matplotlib resources
    hospital.nhs_metrics.close_plots()
    
    return results


def main():
    """Main function to run the hospital simulation"""
    print("🚀 Starting Hospital Simulation with Manchester Triage System")
    print("This simulation uses real Synthea patient data with MTS triage")
    
    try:
        results = run_hospital_simulation()
        print("\n✅ Simulation completed successfully!")
        print(f"📋 Summary: {results['total_patients']} patients processed")
        print(f"⏱️  Average patient time: {results['avg_time']:.1f} minutes")
        
    except KeyboardInterrupt:
        print("\n⏹️  Simulation interrupted by user")
    except Exception as e:
        print(f"\n❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()