#!/usr/bin/env python3
"""
Simple test script for the DataService to verify functionality.

This script creates sample CSV files to test the DataService without requiring
actual Synthea output files.
"""

import os
import pandas as pd
import tempfile
import shutil
from src.services.data_service import DataService


def create_sample_data(test_dir: str):
    """Create sample CSV files that mimic Synthea output structure."""
    
    # Sample Patient data
    patients_data = {
        'id': ['patient-1', 'patient-2', 'patient-3'],
        'BIRTHDATE': ['1990-01-15', '1985-03-22', '1992-07-08'],
        'DEATHDATE': [None, None, None],
        'SSN': ['123-45-6789', '987-65-4321', '555-12-3456'],
        'DRIVERS': ['S12345678', 'D87654321', 'L55512345'],
        'PASSPORT': [None, 'P123456789', None],
        'PREFIX': ['Mr.', 'Ms.', 'Dr.'],
        'FIRST': ['John', 'Jane', 'Robert'],
        'LAST': ['Doe', 'Smith', 'Johnson'],
        'SUFFIX': [None, None, 'Jr.'],
        'MAIDEN': [None, 'Brown', None],
        'MARITAL': ['M', 'S', 'M'],
        'RACE': ['white', 'black', 'asian'],
        'ETHNICITY': ['nonhispanic', 'hispanic', 'nonhispanic'],
        'GENDER': ['M', 'F', 'M'],
        'BIRTHPLACE': ['Boston, MA', 'New York, NY', 'Chicago, IL'],
        'ADDRESS': ['123 Main St', '456 Oak Ave', '789 Pine Rd'],
        'CITY': ['Boston', 'New York', 'Chicago'],
        'STATE': ['MA', 'NY', 'IL'],
        'COUNTY': ['Suffolk County', 'New York County', 'Cook County'],
        'ZIP': ['02101', '10001', '60601'],
        'LAT': [42.3601, 40.7128, 41.8781],
        'LON': [-71.0589, -74.0060, -87.6298],
        'HEALTHCARE_EXPENSES': [5000.50, 7500.25, 3200.75],
        'HEALTHCARE_COVERAGE': [4500.00, 7000.00, 3000.00]
    }
    
    patients_df = pd.DataFrame(patients_data)
    patients_df.to_csv(os.path.join(test_dir, 'Patient.csv'), index=False)
    
    # Sample Observations data with FHIR references
    observations_data = {
        'id': ['obs-1', 'obs-2', 'obs-3', 'obs-4', 'obs-5'],
        'DATE': ['2023-01-15', '2023-01-15', '2023-02-20', '2023-02-20', '2023-03-10'],
        'PATIENT': ['Patient/patient-1', 'Patient/patient-1', 'Patient/patient-2', 'Patient/patient-2', 'Patient/patient-3'],
        'ENCOUNTER': ['Encounter/enc-1', 'Encounter/enc-1', 'Encounter/enc-2', 'Encounter/enc-2', 'Encounter/enc-3'],
        'CODE': ['8302-2', '29463-7', '8302-2', '72166-2', '8310-5'],
        'DESCRIPTION': ['Body Height', 'Body Weight', 'Body Height', 'Tobacco smoking status', 'Body Temperature'],
        'VALUE': ['175.5', '70.2', '162.3', 'Never smoker', '98.6'],
        'UNITS': ['cm', 'kg', 'cm', None, 'degF'],
        'TYPE': ['numeric', 'numeric', 'numeric', 'text', 'numeric']
    }
    
    observations_df = pd.DataFrame(observations_data)
    observations_df.to_csv(os.path.join(test_dir, 'Observation.csv'), index=False)
    
    # Sample Conditions data
    conditions_data = {
        'id': ['cond-1', 'cond-2', 'cond-3'],
        'START': ['2023-01-15', '2023-02-20', '2023-03-10'],
        'STOP': [None, '2023-03-01', None],
        'PATIENT': ['Patient/patient-1', 'Patient/patient-2', 'Patient/patient-3'],
        'ENCOUNTER': ['Encounter/enc-1', 'Encounter/enc-2', 'Encounter/enc-3'],
        'CODE': ['44054006', '195662009', '38341003'],
        'DESCRIPTION': ['Hypertension', 'Acute viral pharyngitis', 'Hypertensive disorder']
    }
    
    conditions_df = pd.DataFrame(conditions_data)
    conditions_df.to_csv(os.path.join(test_dir, 'Condition.csv'), index=False)
    
    # Sample Encounters data
    encounters_data = {
        'id': ['enc-1', 'enc-2', 'enc-3'],
        'START': ['2023-01-15T10:00:00Z', '2023-02-20T14:30:00Z', '2023-03-10T09:15:00Z'],
        'STOP': ['2023-01-15T11:30:00Z', '2023-02-20T15:45:00Z', '2023-03-10T10:30:00Z'],
        'PATIENT': ['Patient/patient-1', 'Patient/patient-2', 'Patient/patient-3'],
        'ORGANIZATION': ['Organization/org-1', 'Organization/org-1', 'Organization/org-2'],
        'PROVIDER': ['Practitioner/prac-1', 'Practitioner/prac-2', 'Practitioner/prac-1'],
        'PAYER': ['Payer/payer-1', 'Payer/payer-2', 'Payer/payer-1'],
        'ENCOUNTERCLASS': ['ambulatory', 'ambulatory', 'emergency'],
        'CODE': ['185349003', '185349003', '50849002'],
        'DESCRIPTION': ['Encounter for check up', 'Encounter for check up', 'Emergency room admission'],
        'BASE_ENCOUNTER_COST': [200.00, 150.00, 500.00],
        'TOTAL_CLAIM_COST': [250.00, 200.00, 750.00],
        'PAYER_COVERAGE': [200.00, 180.00, 600.00],
        'REASONCODE': [None, '195662009', '38341003'],
        'REASONDESCRIPTION': [None, 'Acute viral pharyngitis', 'Hypertensive disorder']
    }
    
    encounters_df = pd.DataFrame(encounters_data)
    encounters_df.to_csv(os.path.join(test_dir, 'Encounter.csv'), index=False)
    
    print(f"Created sample data in {test_dir}")
    print(f"- Patient.csv: {len(patients_df)} patients")
    print(f"- Observation.csv: {len(observations_df)} observations")
    print(f"- Condition.csv: {len(conditions_df)} conditions")
    print(f"- Encounter.csv: {len(encounters_df)} encounters")


def test_data_service():
    """Test the DataService with sample data."""
    
    # Create temporary directory for test data
    test_dir = tempfile.mkdtemp(prefix='synthea_test_')
    
    try:
        print("=== DataService Test ===")
        print(f"Using temporary directory: {test_dir}")
        print()
        
        # Create sample data
        create_sample_data(test_dir)
        print()
        
        # Initialize DataService
        data_service = DataService(csv_folder=test_dir)
        
        # Test the complete pipeline
        print("Testing complete processing pipeline...")
        patient_records = data_service.process_all()
        print()
        
        # Verify results
        print("=== Verification ===")
        print(f"Total patients processed: {len(patient_records)}")
        
        # Check a specific patient
        if 'patient-1' in patient_records:
            patient_1 = patient_records['patient-1']
            print(f"Patient 1 name: {patient_1['FIRST']} {patient_1['LAST']}")
            print(f"Patient 1 observations: {len(patient_1.get('Observation', []))}")
            print(f"Patient 1 conditions: {len(patient_1.get('Condition', []))}")
            print(f"Patient 1 encounters: {len(patient_1.get('Encounter', []))}")
        
        # Test individual methods
        print("\n=== Testing Individual Methods ===")
        
        # Test get_all_patient_ids
        all_ids = data_service.get_all_patient_ids()
        print(f"All patient IDs: {all_ids}")
        
        # Test get_patient_record
        if all_ids:
            sample_id = all_ids[0]
            sample_record = data_service.get_patient_record(sample_id)
            print(f"Sample patient record keys: {list(sample_record.keys())}")
        
        # Test summary stats
        stats = data_service.get_summary_stats()
        print(f"\nSummary stats: {stats}")
        
        # Test export functionality
        if all_ids:
            export_file = os.path.join(test_dir, 'test_export.json')
            data_service.export_patient_record(all_ids[0], export_file)
            print(f"\nExported patient to: {export_file}")
            print(f"Export file exists: {os.path.exists(export_file)}")
        
        print("\n✅ All tests passed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(test_dir)
        print(f"\nCleaned up temporary directory: {test_dir}")


if __name__ == "__main__":
    test_data_service()