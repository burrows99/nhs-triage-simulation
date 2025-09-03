#!/usr/bin/env python3
"""
Test script to demonstrate Manchester Triage System output format
Shows priority, wait time, and other triage data from MTS
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.triage.manchester_triage_system import ManchesterTriageSystem
from src.triage.triage_constants import SymptomKeys, LinguisticValues

def test_mts_output_examples():
    """Test MTS with different symptom combinations to show output format"""
    
    print("=" * 80)
    print("MANCHESTER TRIAGE SYSTEM - OUTPUT EXAMPLES")
    print("=" * 80)
    
    # Initialize MTS
    mts = ManchesterTriageSystem()
    
    # Test cases with different severity levels
    test_cases = [
        {
            'name': 'MILD SYMPTOMS (Expected: BLUE)',
            'flowchart': 'chest_pain',
            'symptoms': {
                SymptomKeys.PAIN_LEVEL: LinguisticValues.MILD,
                SymptomKeys.CONSCIOUSNESS: LinguisticValues.ALERT,
                SymptomKeys.TEMPERATURE: LinguisticValues.NORMAL
            }
        },
        {
            'name': 'MODERATE SYMPTOMS (Expected: GREEN/YELLOW)',
            'flowchart': 'chest_pain',
            'symptoms': {
                SymptomKeys.PAIN_LEVEL: LinguisticValues.MODERATE,
                'crushing_sensation': LinguisticValues.MODERATE,
                SymptomKeys.CONSCIOUSNESS: LinguisticValues.ALERT
            }
        },
        {
            'name': 'SEVERE SYMPTOMS (Expected: YELLOW/ORANGE)',
            'flowchart': 'chest_pain',
            'symptoms': {
                SymptomKeys.PAIN_LEVEL: LinguisticValues.SEVERE,
                'crushing_sensation': LinguisticValues.MODERATE,
                'radiation': LinguisticValues.MODERATE
            }
        },
        {
            'name': 'MULTIPLE SEVERE (Expected: ORANGE)',
            'flowchart': 'chest_pain',
            'symptoms': {
                SymptomKeys.PAIN_LEVEL: LinguisticValues.SEVERE,
                'crushing_sensation': LinguisticValues.SEVERE,
                'radiation': LinguisticValues.MODERATE
            }
        },
        {
            'name': 'VERY SEVERE (Expected: RED)',
            'flowchart': 'chest_pain',
            'symptoms': {
                SymptomKeys.PAIN_LEVEL: LinguisticValues.VERY_SEVERE,
                'crushing_sensation': LinguisticValues.SEVERE,
                'radiation': LinguisticValues.SEVERE
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print("-" * 60)
        
        try:
            # Perform triage
            result = mts.triage_patient(
                flowchart_reason=test_case['flowchart'],
                symptoms_input=test_case['symptoms'],
                patient_id=f"test_patient_{i}"
            )
            
            # Display MTS output format
            print(f"📋 MTS OUTPUT:")
            print(f"   Triage Category: {result.get('triage_category', result.get('category', 'N/A'))}")
            print(f"   Wait Time: {result.get('wait_time', 'N/A')}")
            print(f"   Fuzzy Score: {result.get('fuzzy_score', 'N/A')}")
            print(f"   Priority Score: {result.get('priority_score', 'N/A')}")
            print(f"   Flowchart Used: {result.get('flowchart_used', 'N/A')}")
            
            # Show additional data if available
            if 'symptoms_processed' in result:
                print(f"   Symptoms Processed: {result['symptoms_processed']}")
            if 'numeric_inputs' in result:
                print(f"   Numeric Inputs: {result['numeric_inputs']}")
                
            print(f"\n📊 FULL RESULT STRUCTURE:")
            for key, value in result.items():
                print(f"   {key}: {value}")
                
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            print(f"   Symptoms provided: {test_case['symptoms']}")
    
    print("\n" + "=" * 80)
    print("MTS OUTPUT ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_mts_output_examples()