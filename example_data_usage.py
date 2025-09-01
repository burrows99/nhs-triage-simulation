#!/usr/bin/env python3
"""
Example usage of the DataService for processing Synthea CSV files.

This script demonstrates how to use the generic data service to:
1. Load all Synthea CSV files dynamically
2. Normalize FHIR references
3. Build patient-centric records
4. Export and analyze the data
"""

import json
import os
from src.services.data_service import DataService


def main():
    """Main example function demonstrating DataService usage."""
    
    # Initialize the data service
    # You can specify a different folder path if your Synthea output is elsewhere
    data_service = DataService(csv_folder="./output")
    
    try:
        print("=== Synthea Data Processing Example ===")
        print()
        
        # Process all data using the complete pipeline
        patient_records = data_service.process_all()
        
        print()
        print("=== Summary Statistics ===")
        stats = data_service.get_summary_stats()
        print(json.dumps(stats, indent=2))
        
        if patient_records:
            print()
            print("=== Sample Patient Analysis ===")
            
            # Get a sample patient
            sample_patient_id = next(iter(patient_records.keys()))
            sample_record = data_service.get_patient_record(sample_patient_id)
            
            print(f"Patient ID: {sample_patient_id}")
            print(f"Patient Name: {sample_record.get('FIRST', 'N/A')} {sample_record.get('LAST', 'N/A')}")
            print(f"Birth Date: {sample_record.get('BIRTHDATE', 'N/A')}")
            print(f"Gender: {sample_record.get('GENDER', 'N/A')}")
            
            # Show what types of medical data are available
            medical_data_types = [k for k in sample_record.keys() 
                                if isinstance(sample_record[k], list) and sample_record[k]]
            
            print(f"Available medical data types: {medical_data_types}")
            
            # Show counts for each data type
            for data_type in medical_data_types:
                count = len(sample_record[data_type])
                print(f"  - {data_type}: {count} records")
            
            # Export sample patient for inspection
            output_dir = "./output/processed"
            os.makedirs(output_dir, exist_ok=True)
            
            sample_file = os.path.join(output_dir, f"patient_{sample_patient_id}.json")
            data_service.export_patient_record(sample_patient_id, sample_file)
            
            print()
            print("=== Usage Examples ===")
            print("\n# Get specific patient:")
            print(f"patient = data_service.get_patient_record('{sample_patient_id}')")
            
            print("\n# Get all patient IDs:")
            print("all_ids = data_service.get_all_patient_ids()")
            
            print("\n# Export all patients:")
            print("data_service.export_all_patients('./output/all_patients.json')")
            
            print("\n# Access specific medical data:")
            if 'Observation' in medical_data_types:
                obs_count = len(sample_record['Observation'])
                print(f"observations = patient['Observation']  # {obs_count} observations")
            
            if 'Condition' in medical_data_types:
                cond_count = len(sample_record['Condition'])
                print(f"conditions = patient['Condition']  # {cond_count} conditions")
            
            print()
            print("=== Integration with Simulation ===")
            print("# This patient data can now be used for:")
            print("# 1. Hospital simulation input")
            print("# 2. LLM-based triage systems")
            print("# 3. Manchester Triage System validation")
            print("# 4. Metrics and analysis")
            
            # Example of how to use with simulation
            print("\n# Example simulation integration:")
            print("from src.simulation.hospital import Hospital")
            print("hospital = Hospital()")
            print("for patient_id in data_service.get_all_patient_ids()[:10]:")
            print("    patient_data = data_service.get_patient_record(patient_id)")
            print("    # Use patient_data for simulation...")
            
        else:
            print("No patient records found. Please check your CSV folder path.")
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nMake sure you have Synthea CSV files in the './output' folder.")
        print("You can generate them using Synthea with commands like:")
        print("java -jar synthea-with-dependencies.jar -p 100")
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()