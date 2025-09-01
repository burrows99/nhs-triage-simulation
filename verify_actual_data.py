#!/usr/bin/env python3
"""
Verification script for actual Synthea CSV data using the DataService.

This script demonstrates that the DataService works correctly with your real
Synthea data and shows detailed analysis of the patient records.
"""

import json
import os
from src.services.data_service import DataService


def analyze_patient_data(data_service: DataService, patient_records: dict):
    """Analyze and display detailed information about patient data."""
    
    print("=== DETAILED PATIENT DATA ANALYSIS ===")
    print()
    
    # Overall statistics
    stats = data_service.get_summary_stats()
    print(f"📊 Total Patients: {stats['total_patients']}")
    print(f"📋 Total Tables: {len(stats['tables_loaded'])}")
    print()
    
    # Table breakdown
    print("📈 Data Distribution:")
    for table, count in stats['table_row_counts'].items():
        print(f"  • {table}: {count:,} records")
    print()
    
    # Sample patient analysis
    sample_patient_id = list(patient_records.keys())[0]
    sample_patient = patient_records[sample_patient_id]
    
    print(f"👤 Sample Patient Analysis (ID: {sample_patient_id})")
    print(f"   Name: {sample_patient.get('FIRST', 'N/A')} {sample_patient.get('LAST', 'N/A')}")
    print(f"   Birth Date: {sample_patient.get('BIRTHDATE', 'N/A')}")
    print(f"   Gender: {sample_patient.get('GENDER', 'N/A')}")
    print(f"   Race: {sample_patient.get('RACE', 'N/A')}")
    print(f"   Location: {sample_patient.get('CITY', 'N/A')}, {sample_patient.get('STATE', 'N/A')}")
    print()
    
    # Medical data for sample patient
    print("🏥 Medical Data for Sample Patient:")
    medical_data_counts = {}
    for key, value in sample_patient.items():
        if isinstance(value, list) and len(value) > 0:
            medical_data_counts[key] = len(value)
            print(f"   • {key}: {len(value)} records")
    print()
    
    # Show sample records from each medical data type
    print("🔍 Sample Medical Records:")
    for data_type, count in medical_data_counts.items():
        if count > 0:
            sample_record = sample_patient[data_type][0]
            print(f"\n   {data_type.upper()} Sample:")
            for k, v in list(sample_record.items())[:5]:  # Show first 5 fields
                print(f"     {k}: {v}")
            if len(sample_record) > 5:
                print(f"     ... and {len(sample_record) - 5} more fields")
    
    return medical_data_counts


def analyze_all_patients(patient_records: dict):
    """Analyze medical data distribution across all patients."""
    
    print("\n=== POPULATION-LEVEL ANALYSIS ===")
    print()
    
    # Count medical records per data type across all patients
    total_counts = {}
    patients_with_data = {}
    
    for patient_id, patient_data in patient_records.items():
        for key, value in patient_data.items():
            if isinstance(value, list):
                if key not in total_counts:
                    total_counts[key] = 0
                    patients_with_data[key] = 0
                
                total_counts[key] += len(value)
                if len(value) > 0:
                    patients_with_data[key] += 1
    
    print("📊 Medical Data Distribution Across All Patients:")
    for data_type in sorted(total_counts.keys()):
        total = total_counts[data_type]
        patients = patients_with_data[data_type]
        avg_per_patient = total / patients if patients > 0 else 0
        coverage = (patients / len(patient_records)) * 100
        
        print(f"   • {data_type}:")
        print(f"     - Total records: {total:,}")
        print(f"     - Patients with data: {patients} ({coverage:.1f}%)")
        print(f"     - Average per patient: {avg_per_patient:.1f}")
        print()
    
    return total_counts, patients_with_data


def demonstrate_usage_examples(data_service: DataService, patient_records: dict):
    """Show practical usage examples for simulation and analysis."""
    
    print("=== USAGE EXAMPLES FOR SIMULATION ===")
    print()
    
    # Example 1: Get patients with specific conditions
    print("🔍 Example 1: Find patients with hypertension")
    hypertension_patients = []
    
    for patient_id, patient_data in patient_records.items():
        conditions = patient_data.get('conditions', [])
        for condition in conditions:
            if 'hypertension' in condition.get('DESCRIPTION', '').lower():
                hypertension_patients.append({
                    'id': patient_id,
                    'name': f"{patient_data.get('FIRST', '')} {patient_data.get('LAST', '')}",
                    'condition': condition.get('DESCRIPTION', '')
                })
                break
    
    print(f"   Found {len(hypertension_patients)} patients with hypertension")
    if hypertension_patients:
        for i, patient in enumerate(hypertension_patients[:3]):  # Show first 3
            print(f"   {i+1}. {patient['name']} - {patient['condition']}")
        if len(hypertension_patients) > 3:
            print(f"   ... and {len(hypertension_patients) - 3} more")
    print()
    
    # Example 2: Get patients by age group
    print("📅 Example 2: Age distribution")
    from datetime import datetime
    
    age_groups = {'0-18': 0, '19-65': 0, '65+': 0}
    
    for patient_data in patient_records.values():
        birth_date = patient_data.get('BIRTHDATE')
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
            except:
                pass
    
    for age_group, count in age_groups.items():
        percentage = (count / len(patient_records)) * 100
        print(f"   {age_group}: {count} patients ({percentage:.1f}%)")
    print()
    
    # Example 3: Export specific patient for detailed analysis
    print("💾 Example 3: Export patient data")
    sample_id = list(patient_records.keys())[0]
    export_file = "./output/sample_patient_export.json"
    
    try:
        data_service.export_patient_record(sample_id, export_file)
        print(f"   ✅ Exported patient {sample_id} to {export_file}")
        
        # Show file size
        file_size = os.path.getsize(export_file)
        print(f"   📁 File size: {file_size:,} bytes")
    except Exception as e:
        print(f"   ❌ Export failed: {e}")
    print()
    
    # Example 4: Integration with simulation
    print("🏥 Example 4: Simulation integration")
    print("   # Use patient data for hospital simulation:")
    print("   from src.simulation.hospital import Hospital")
    print("   hospital = Hospital()")
    print("   ")
    print("   # Process patients for triage simulation")
    print("   for patient_id in data_service.get_all_patient_ids()[:10]:")
    print("       patient_data = data_service.get_patient_record(patient_id)")
    print("       ")
    print("       # Extract relevant medical history")
    print("       conditions = patient_data.get('conditions', [])")
    print("       observations = patient_data.get('observations', [])")
    print("       ")
    print("       # Use for triage decision making")
    print("       # triage_level = determine_triage_level(conditions, observations)")
    print("       # hospital.admit_patient(patient_data, triage_level)")
    print()


def main():
    """Main verification function."""
    
    print("🔍 VERIFYING ACTUAL SYNTHEA CSV DATA")
    print("=" * 50)
    print()
    
    try:
        # Initialize data service with actual CSV folder
        print("📂 Loading data from ./output/csv/...")
        data_service = DataService('./output/csv')
        
        # Process all data
        patient_records = data_service.process_all()
        print(f"✅ Successfully processed {len(patient_records)} patients")
        print()
        
        # Detailed analysis
        medical_data_counts = analyze_patient_data(data_service, patient_records)
        
        # Population analysis
        total_counts, patients_with_data = analyze_all_patients(patient_records)
        
        # Usage examples
        demonstrate_usage_examples(data_service, patient_records)
        
        # Final summary
        print("=== VERIFICATION SUMMARY ===")
        print(f"✅ Data Service Status: WORKING CORRECTLY")
        print(f"✅ Total Patients Processed: {len(patient_records)}")
        print(f"✅ Medical Data Types Available: {len([k for k in total_counts.keys() if total_counts[k] > 0])}")
        print(f"✅ Total Medical Records: {sum(total_counts.values()):,}")
        print()
        print("🎉 Your Synthea CSV data is ready for simulation and analysis!")
        print()
        print("Next steps:")
        print("1. Use data_service.get_all_patient_ids() to get patient list")
        print("2. Use data_service.get_patient_record(id) to get individual patients")
        print("3. Integrate with your hospital simulation")
        print("4. Use for LLM-based triage system testing")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()