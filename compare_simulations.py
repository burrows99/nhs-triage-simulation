#!/usr/bin/env python3
"""
Comparison script between fake patient simulation and real patient data simulation.

This script runs both simulations and compares the results to show the impact
of using real patient data versus synthetic/fake patient generation.
"""

import sys
import os

# Add project root to path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.simulation.hospital import FakeHospital
from src.simulation.real_data_hospital import RealDataHospital
import json
from datetime import datetime


def format_metrics(metrics, title):
    """Format metrics for display."""
    print(f"\n{'='*60}")
    print(f"{title.center(60)}")
    print(f"{'='*60}")
    
    if not metrics:
        print("No metrics available")
        return
    
    print(f"Data Source: {metrics.get('data_source', 'N/A')}")
    if 'real_patients_used' in metrics:
        print(f"Real Patients Available: {metrics['real_patients_used']}")
    print(f"Total Patients Processed: {metrics.get('total_patients', 0)}")
    print(f"Average Triage Wait: {metrics.get('avg_triage_wait', 0):.1f} min")
    
    print("\nAverage Assessment Wait by Category:")
    assess_waits = metrics.get('avg_assess_wait_by_category', {})
    if assess_waits:
        for category in ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE']:
            if category in assess_waits:
                print(f"  {category}: {assess_waits[category]:.1f} min")
    else:
        print("  No category data available")
    
    print(f"\nAverage Total Time: {metrics.get('avg_total_time', 0):.1f} min")
    print(f"MTS Target Breaches: {metrics.get('mts_breach_count', 0)}")
    print(f"4-Hour Breaches: {metrics.get('four_hour_breach_count', 0)} "
          f"({metrics.get('four_hour_breach_pct', 0):.1f}%)")


def compare_metrics(fake_metrics, real_metrics):
    """Compare metrics between fake and real patient simulations."""
    print(f"\n{'='*60}")
    print(f"{'COMPARISON ANALYSIS'.center(60)}")
    print(f"{'='*60}")
    
    if not fake_metrics or not real_metrics:
        print("Cannot compare - missing metrics")
        return
    
    # Compare key metrics
    comparisons = [
        ('Total Patients', 'total_patients'),
        ('Avg Triage Wait (min)', 'avg_triage_wait'),
        ('Avg Total Time (min)', 'avg_total_time'),
        ('MTS Breaches', 'mts_breach_count'),
        ('4-Hour Breaches', 'four_hour_breach_count'),
        ('4-Hour Breach %', 'four_hour_breach_pct')
    ]
    
    print(f"{'Metric':<25} {'Fake Data':<15} {'Real Data':<15} {'Difference':<15}")
    print("-" * 70)
    
    for metric_name, metric_key in comparisons:
        fake_val = fake_metrics.get(metric_key, 0)
        real_val = real_metrics.get(metric_key, 0)
        
        if isinstance(fake_val, (int, float)) and isinstance(real_val, (int, float)):
            if fake_val != 0:
                diff_pct = ((real_val - fake_val) / fake_val) * 100
                diff_str = f"{diff_pct:+.1f}%"
            else:
                diff_str = "N/A"
            
            print(f"{metric_name:<25} {fake_val:<15.1f} {real_val:<15.1f} {diff_str:<15}")
        else:
            print(f"{metric_name:<25} {fake_val:<15} {real_val:<15} {'N/A':<15}")
    
    # Category-specific comparison
    print("\nAssessment Wait Time Comparison by Category:")
    print(f"{'Category':<10} {'Fake Data':<15} {'Real Data':<15} {'Difference':<15}")
    print("-" * 55)
    
    fake_assess = fake_metrics.get('avg_assess_wait_by_category', {})
    real_assess = real_metrics.get('avg_assess_wait_by_category', {})
    
    for category in ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE']:
        fake_wait = fake_assess.get(category, 0)
        real_wait = real_assess.get(category, 0)
        
        if fake_wait > 0 and real_wait > 0:
            diff_pct = ((real_wait - fake_wait) / fake_wait) * 100
            diff_str = f"{diff_pct:+.1f}%"
        elif fake_wait > 0 or real_wait > 0:
            diff_str = "N/A"
        else:
            diff_str = "No data"
        
        print(f"{category:<10} {fake_wait:<15.1f} {real_wait:<15.1f} {diff_str:<15}")


def analyze_real_data_characteristics(real_hospital):
    """Analyze characteristics of the real patient data."""
    print(f"\n{'='*60}")
    print(f"{'REAL PATIENT DATA ANALYSIS'.center(60)}")
    print(f"{'='*60}")
    
    if not real_hospital.patient_records:
        print("No real patient data available")
        return
    
    # Age distribution
    age_groups = {'0-18': 0, '19-65': 0, '65+': 0, 'Unknown': 0}
    condition_counts = {}
    gender_counts = {'M': 0, 'F': 0, 'Unknown': 0}
    
    for patient_data in real_hospital.patient_records.values():
        # Age analysis
        birth_date = patient_data.get('BIRTHDATE', '')
        if birth_date:
            try:
                birth_year = int(birth_date.split('-')[0])
                age = 2024 - birth_year
                if age <= 18:
                    age_groups['0-18'] += 1
                elif age <= 65:
                    age_groups['19-65'] += 1
                else:
                    age_groups['65+'] += 1
            except (ValueError, IndexError):
                age_groups['Unknown'] += 1
        else:
            age_groups['Unknown'] += 1
        
        # Gender analysis
        gender = patient_data.get('GENDER', 'Unknown')
        gender_counts[gender] = gender_counts.get(gender, 0) + 1
        
        # Condition analysis
        conditions = patient_data.get('conditions', [])
        for condition in conditions:
            desc = condition.get('DESCRIPTION', 'Unknown')
            condition_counts[desc] = condition_counts.get(desc, 0) + 1
    
    total_patients = len(real_hospital.patient_records)
    
    print(f"Total Real Patients: {total_patients}")
    print("\nAge Distribution:")
    for age_group, count in age_groups.items():
        if count > 0:
            pct = (count / total_patients) * 100
            print(f"  {age_group}: {count} ({pct:.1f}%)")
    
    print("\nGender Distribution:")
    for gender, count in gender_counts.items():
        if count > 0:
            pct = (count / total_patients) * 100
            print(f"  {gender}: {count} ({pct:.1f}%)")
    
    print("\nTop 10 Most Common Conditions:")
    sorted_conditions = sorted(condition_counts.items(), key=lambda x: x[1], reverse=True)
    for i, (condition, count) in enumerate(sorted_conditions[:10]):
        pct = (count / sum(condition_counts.values())) * 100
        print(f"  {i+1:2d}. {condition}: {count} ({pct:.1f}%)")


def main():
    """Main comparison function."""
    print("🏥 HOSPITAL SIMULATION COMPARISON")
    print("Comparing Fake Patient Generation vs Real Synthea Patient Data")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Simulation parameters
    sim_duration = 480  # 8 hours
    
    print(f"\nSimulation Parameters:")
    print(f"- Duration: {sim_duration} minutes ({sim_duration/60:.1f} hours)")
    print(f"- Triage Nurses: 2")
    print(f"- Doctors: 6")
    print(f"- Beds: 15")
    print(f"- Peak Arrival Rate: 15 patients/hour")
    print(f"- Off-peak Arrival Rate: 5 patients/hour")
    
    # Run fake patient simulation
    print("\n🤖 Running FAKE patient simulation...")
    try:
        fake_hospital = FakeHospital(
            sim_duration=sim_duration,
            triage_nurse_capacity=2,
            doctor_capacity=6,
            bed_capacity=15
        )
        fake_metrics = fake_hospital.run_simulation()
        format_metrics(fake_metrics, "FAKE PATIENT SIMULATION RESULTS")
    except Exception as e:
        print(f"Error running fake simulation: {e}")
        fake_metrics = {}
    
    # Run real patient simulation
    print("\n👥 Running REAL patient data simulation...")
    try:
        real_hospital = RealDataHospital(
            csv_folder='./output/csv',
            sim_duration=sim_duration,
            triage_nurse_capacity=2,
            doctor_capacity=6,
            bed_capacity=15
        )
        real_metrics = real_hospital.run_simulation()
        format_metrics(real_metrics, "REAL PATIENT DATA SIMULATION RESULTS")
        
        # Analyze real data characteristics
        analyze_real_data_characteristics(real_hospital)
        
    except Exception as e:
        print(f"Error running real data simulation: {e}")
        import traceback
        traceback.print_exc()
        real_metrics = {}
    
    # Compare results
    if fake_metrics and real_metrics:
        compare_metrics(fake_metrics, real_metrics)
    
    # Summary and insights
    print(f"\n{'='*60}")
    print(f"{'KEY INSIGHTS'.center(60)}")
    print(f"{'='*60}")
    
    if fake_metrics and real_metrics:
        print("✅ Successfully compared both simulation approaches")
        print("\n🔍 Key Differences:")
        
        # Highlight significant differences
        if real_metrics.get('avg_total_time', 0) > fake_metrics.get('avg_total_time', 0):
            print("• Real patients tend to have longer total treatment times")
        
        real_breach_pct = real_metrics.get('four_hour_breach_pct', 0)
        fake_breach_pct = fake_metrics.get('four_hour_breach_pct', 0)
        
        if abs(real_breach_pct - fake_breach_pct) > 5:
            print(f"• Significant difference in 4-hour breach rates: "
                  f"Real {real_breach_pct:.1f}% vs Fake {fake_breach_pct:.1f}%")
        
        print("\n💡 Benefits of Real Patient Data:")
        print("• More realistic patient complexity and acuity distribution")
        print("• Actual medical conditions drive triage decisions")
        print("• Better representation of patient demographics")
        print("• More accurate resource utilization patterns")
        print("• Enables validation against real-world benchmarks")
        
    else:
        print("❌ Could not complete full comparison due to simulation errors")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n🎯 Next Steps:")
    print("1. Use real patient data for more accurate triage system testing")
    print("2. Validate triage algorithms against actual patient outcomes")
    print("3. Analyze specific patient cohorts (e.g., elderly, pediatric)")
    print("4. Compare with real hospital performance metrics")


if __name__ == "__main__":
    main()