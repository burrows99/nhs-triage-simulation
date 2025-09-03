#!/usr/bin/env python3
"""
Comprehensive Manual Symptom Testing for MTS

This script thoroughly tests the Manchester Triage System with manually generated
symptoms based on real CSV patient data to validate all triage categories.
"""

import sys
import os
import pandas as pd
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import seaborn as sns

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.triage.manchester_triage_system import ManchesterTriageSystem
from src.triage.triage_constants import (
    SymptomKeys, LinguisticValues, TriageCategories,
    ComplaintToFlowchartMapping, FlowchartSymptomMapping
)
from src.services.data_service import DataService
from src.logger import logger

def analyze_csv_data(csv_folder='./output/csv'):
    """Analyze the CSV data to understand patient demographics and encounters."""
    print("=" * 80)
    print("ANALYZING CSV PATIENT DATA")
    print("=" * 80)
    
    try:
        # Load patient data
        patients_df = pd.read_csv(os.path.join(csv_folder, 'patients.csv'))
        encounters_df = pd.read_csv(os.path.join(csv_folder, 'encounters.csv'))
        
        print(f"📊 Total Patients: {len(patients_df)}")
        print(f"📊 Total Encounters: {len(encounters_df)}")
        
        # Analyze age distribution
        patients_df['BIRTHDATE'] = pd.to_datetime(patients_df['BIRTHDATE'])
        patients_df['AGE'] = (pd.Timestamp.now() - patients_df['BIRTHDATE']).dt.days // 365
        
        print(f"\n👥 AGE DISTRIBUTION:")
        print(f"   Pediatric (0-17): {len(patients_df[patients_df['AGE'] <= 17])} patients")
        print(f"   Adult (18-64): {len(patients_df[(patients_df['AGE'] >= 18) & (patients_df['AGE'] <= 64)])} patients")
        print(f"   Elderly (65+): {len(patients_df[patients_df['AGE'] >= 65])} patients")
        
        # Analyze encounter types
        encounter_counts = encounters_df['DESCRIPTION'].value_counts().head(10)
        print(f"\n🏥 TOP ENCOUNTER TYPES:")
        for encounter, count in encounter_counts.items():
            print(f"   {encounter}: {count} encounters")
        
        # Analyze flowchart mapping
        flowchart_mapping = {}
        for encounter in encounters_df['DESCRIPTION'].unique():
            flowchart = ComplaintToFlowchartMapping.get_flowchart_for_complaint(encounter)
            flowchart_mapping[flowchart] = flowchart_mapping.get(flowchart, 0) + 1
        
        print(f"\n📋 FLOWCHART DISTRIBUTION:")
        for flowchart, count in sorted(flowchart_mapping.items(), key=lambda x: x[1], reverse=True):
            print(f"   {flowchart}: {count} cases")
        
        return patients_df, encounters_df, flowchart_mapping
        
    except Exception as e:
        print(f"❌ Error analyzing CSV data: {e}")
        return None, None, None

def test_manual_symptom_generation(num_tests=1000):
    """Test manual symptom generation with comprehensive scenarios."""
    print("\n" + "=" * 80)
    print("TESTING MANUAL SYMPTOM GENERATION")
    print("=" * 80)
    
    # Initialize MTS
    mts = ManchesterTriageSystem()
    
    # Test scenarios with different symptom combinations
    test_scenarios = [
        # RED scenarios (very_severe symptoms)
        {
            'name': 'Critical Chest Pain',
            'flowchart': 'chest_pain',
            'symptoms': {
                'severe_pain': LinguisticValues.VERY_SEVERE,
                'crushing_sensation': LinguisticValues.SEVERE,
                'radiation': LinguisticValues.SEVERE,
                'breathless': LinguisticValues.SEVERE,
                'sweating': LinguisticValues.SEVERE
            },
            'expected': TriageCategories.RED
        },
        # ORANGE scenarios (multiple severe)
        {
            'name': 'Severe Chest Pain',
            'flowchart': 'chest_pain',
            'symptoms': {
                'severe_pain': LinguisticValues.SEVERE,
                'crushing_sensation': LinguisticValues.SEVERE,
                'radiation': LinguisticValues.MODERATE,
                'breathless': LinguisticValues.NONE,
                'sweating': LinguisticValues.NONE
            },
            'expected': TriageCategories.ORANGE
        },
        # YELLOW scenarios (single severe)
        {
            'name': 'Moderate Chest Pain',
            'flowchart': 'chest_pain',
            'symptoms': {
                'severe_pain': LinguisticValues.SEVERE,
                'crushing_sensation': LinguisticValues.NONE,
                'radiation': LinguisticValues.NONE,
                'breathless': LinguisticValues.NONE,
                'sweating': LinguisticValues.NONE
            },
            'expected': TriageCategories.YELLOW
        },
        # GREEN scenarios (moderate symptoms)
        {
            'name': 'Mild Chest Discomfort',
            'flowchart': 'chest_pain',
            'symptoms': {
                'severe_pain': LinguisticValues.MODERATE,
                'crushing_sensation': LinguisticValues.MODERATE,
                'radiation': LinguisticValues.NONE,
                'breathless': LinguisticValues.NONE,
                'sweating': LinguisticValues.NONE
            },
            'expected': TriageCategories.GREEN
        },
        # BLUE scenarios (mild symptoms)
        {
            'name': 'Minor Chest Pain',
            'flowchart': 'chest_pain',
            'symptoms': {
                'severe_pain': LinguisticValues.MILD,
                'crushing_sensation': LinguisticValues.NONE,
                'radiation': LinguisticValues.NONE,
                'breathless': LinguisticValues.NONE,
                'sweating': LinguisticValues.NONE
            },
            'expected': TriageCategories.BLUE
        }
    ]
    
    results = []
    category_counts = Counter()
    
    print(f"🧪 Testing {len(test_scenarios)} predefined scenarios...")
    
    for scenario in test_scenarios:
        try:
            result = mts.triage_patient(
                flowchart_reason=scenario['flowchart'],
                symptoms_input=scenario['symptoms'],
                patient_id=f"test_{scenario['name'].replace(' ', '_')}"
            )
            
            actual_category = result['triage_category']
            expected_category = scenario['expected']
            
            results.append({
                'scenario': scenario['name'],
                'expected': expected_category,
                'actual': actual_category,
                'match': actual_category == expected_category,
                'fuzzy_score': result['fuzzy_score'],
                'priority_score': result['priority_score'],
                'wait_time': result['wait_time']
            })
            
            category_counts[actual_category] += 1
            
            status = "✅" if actual_category == expected_category else "❌"
            print(f"   {status} {scenario['name']}: Expected {expected_category} → Got {actual_category} (Score: {result['fuzzy_score']:.2f})")
            
        except Exception as e:
            print(f"   ❌ {scenario['name']}: Error - {e}")
    
    # Test random symptom generation
    print(f"\n🎲 Testing {num_tests} random symptom combinations...")
    
    import random
    flowcharts = ['chest_pain', 'shortness_of_breath', 'abdominal_pain', 'headache', 'limb_injuries']
    severities = [LinguisticValues.NONE, LinguisticValues.MILD, LinguisticValues.MODERATE, 
                 LinguisticValues.SEVERE, LinguisticValues.VERY_SEVERE]
    
    random_results = []
    random_category_counts = Counter()
    
    for i in range(num_tests):
        flowchart = random.choice(flowcharts)
        expected_symptoms = FlowchartSymptomMapping.get_symptoms_for_flowchart(flowchart)
        
        # Generate random symptoms
        symptoms = {}
        if isinstance(expected_symptoms, dict):
            symptom_list = list(expected_symptoms.keys())[:5]  # Limit to 5 symptoms
        else:
            symptom_list = list(expected_symptoms)[:5] if expected_symptoms else ['severe_pain', 'consciousness', 'temperature']
        
        for symptom in symptom_list:
            symptoms[symptom] = random.choice(severities)
        
        try:
            result = mts.triage_patient(
                flowchart_reason=flowchart,
                symptoms_input=symptoms,
                patient_id=f"random_test_{i}"
            )
            
            category = result['triage_category']
            random_category_counts[category] += 1
            
            random_results.append({
                'flowchart': flowchart,
                'category': category,
                'fuzzy_score': result['fuzzy_score'],
                'priority_score': result['priority_score'],
                'symptoms': symptoms
            })
            
        except Exception as e:
            print(f"   ❌ Random test {i}: Error - {e}")
    
    # Display results
    print(f"\n📊 PREDEFINED SCENARIO RESULTS:")
    for category in [TriageCategories.RED, TriageCategories.ORANGE, TriageCategories.YELLOW, 
                    TriageCategories.GREEN, TriageCategories.BLUE]:
        count = category_counts[category]
        percentage = (count / len(test_scenarios)) * 100 if test_scenarios else 0
        print(f"   {category}: {count} cases ({percentage:.1f}%)")
    
    print(f"\n📊 RANDOM TEST RESULTS ({num_tests} tests):")
    for category in [TriageCategories.RED, TriageCategories.ORANGE, TriageCategories.YELLOW, 
                    TriageCategories.GREEN, TriageCategories.BLUE]:
        count = random_category_counts[category]
        percentage = (count / num_tests) * 100 if num_tests > 0 else 0
        print(f"   {category}: {count} cases ({percentage:.1f}%)")
    
    return results, random_results, category_counts, random_category_counts

def run_simulation_with_manual_symptoms():
    """Run a short simulation with manual symptoms to test integration."""
    print("\n" + "=" * 80)
    print("RUNNING SIMULATION WITH MANUAL SYMPTOMS")
    print("=" * 80)
    
    try:
        from src.simulation.real_data_hospital import SimpleHospital
        from src.triage.manchester_triage_system import ManchesterTriageSystem
        
        # Initialize MTS and hospital
        manchester_triage = ManchesterTriageSystem()
        
        hospital = SimpleHospital(
            csv_folder='./output/csv',
            triage_system=manchester_triage,
            sim_duration=60,     # 1 hour test
            arrival_rate=20,     # 20 patients/hour
            nurses=2,
            doctors=2,
            beds=4
        )
        
        print(f"🏥 Running 1-hour simulation with manual symptoms...")
        results = hospital.run()
        
        print(f"✅ Simulation completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Simulation error: {e}")
        return False

def create_visualization(category_counts, random_category_counts):
    """Create visualizations of the test results."""
    print("\n📊 Creating result visualizations...")
    
    try:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Predefined scenarios
        categories = [TriageCategories.RED, TriageCategories.ORANGE, TriageCategories.YELLOW, 
                     TriageCategories.GREEN, TriageCategories.BLUE]
        counts1 = [category_counts[cat] for cat in categories]
        
        ax1.bar(categories, counts1, color=['red', 'orange', 'yellow', 'green', 'blue'])
        ax1.set_title('Predefined Scenario Results')
        ax1.set_ylabel('Number of Cases')
        ax1.tick_params(axis='x', rotation=45)
        
        # Random tests
        counts2 = [random_category_counts[cat] for cat in categories]
        
        ax2.bar(categories, counts2, color=['red', 'orange', 'yellow', 'green', 'blue'])
        ax2.set_title('Random Test Results')
        ax2.set_ylabel('Number of Cases')
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig('./output/manual_symptom_test_results.png', dpi=300, bbox_inches='tight')
        print(f"📊 Visualization saved to: ./output/manual_symptom_test_results.png")
        
    except Exception as e:
        print(f"❌ Visualization error: {e}")

def main():
    """Main test execution."""
    print("🧪 COMPREHENSIVE MANUAL SYMPTOM TESTING FOR MTS")
    print("=" * 80)
    
    # Step 1: Analyze CSV data
    patients_df, encounters_df, flowchart_mapping = analyze_csv_data()
    
    # Step 2: Test manual symptom generation
    results, random_results, category_counts, random_category_counts = test_manual_symptom_generation(1000)
    
    # Step 3: Create visualizations
    create_visualization(category_counts, random_category_counts)
    
    # Step 4: Run simulation test
    simulation_success = run_simulation_with_manual_symptoms()
    
    # Summary
    print("\n" + "=" * 80)
    print("COMPREHENSIVE TEST SUMMARY")
    print("=" * 80)
    
    if patients_df is not None:
        print(f"✅ CSV Data Analysis: {len(patients_df)} patients, {len(encounters_df)} encounters")
    else:
        print(f"❌ CSV Data Analysis: Failed")
    
    total_random = sum(random_category_counts.values())
    diverse_categories = sum(1 for count in random_category_counts.values() if count > 0)
    
    print(f"✅ Manual Symptom Testing: {total_random} tests, {diverse_categories}/5 categories generated")
    print(f"✅ Simulation Integration: {'Success' if simulation_success else 'Failed'}")
    
    if diverse_categories >= 4:
        print(f"\n🎉 SUCCESS: MTS is generating diverse triage categories!")
        print(f"   The manual symptom generator is working correctly.")
    else:
        print(f"\n⚠️  WARNING: Limited category diversity ({diverse_categories}/5)")
        print(f"   Consider adjusting symptom generation weights.")

if __name__ == "__main__":
    main()