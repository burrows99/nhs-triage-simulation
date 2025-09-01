#!/usr/bin/env python3
"""
Manchester Triage System - Main Testing and Demonstration Script

This script demonstrates the complete FMTS (Fuzzy Manchester Triage System)
implementation based on the research paper by Cremeens & Khorasani (2014).

Usage:
    python main.py

Requirements:
    pip install pandas numpy scikit-fuzzy scikit-learn
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from triage.manchester_triage_system import (
    ManchesterTriageSystem,
    ZMouseFuzzyInterface,
    KnowledgeAcquisitionSystem,
    PAPER_INFO,
    CAPABILITIES
)
from src.services import TelemetryService, MetricsService


def test_basic_triage():
    """Test basic triage functionality"""
    print("\n🏥 Testing Basic Triage Functionality")
    print("=" * 50)
    
    # Initialize services
    telemetry = TelemetryService()
    metrics = MetricsService()
    
    # Initialize the Manchester Triage System with required services
    mts = ManchesterTriageSystem(telemetry_service=telemetry, metrics_service=metrics)
    
    # Test cases representing different severity levels
    test_cases = [
        {
            'name': 'Critical Chest Pain',
            'reason': 'chest_pain',
            'symptoms': {
                'severe_pain': 'very_severe',
                'crushing_sensation': 'severe',
                'radiation': 'moderate',
                'breathless': 'severe',
                'sweating': 'severe'
            },
            'expected_category': 'RED'
        },
        {
            'name': 'Moderate Headache',
            'reason': 'headache',
            'symptoms': {
                'pain_severity': 'moderate',
                'sudden_onset': 'none',
                'neck_stiffness': 'none',
                'photophobia': 'mild',
                'confusion': 'none'
            },
            'expected_category': 'GREEN'
        },
        {
            'name': 'Minor Limb Injury',
            'reason': 'limb_injuries',
            'symptoms': {
                'deformity': 'none',
                'pain': 'mild',
                'swelling': 'mild',
                'loss_of_function': 'none',
                'bleeding': 'none'
            },
            'expected_category': 'BLUE'
        },
        {
            'name': 'Severe Abdominal Pain',
            'reason': 'abdominal_pain',
            'symptoms': {
                'pain_intensity': 'severe',
                'vomiting': 'moderate',
                'rigidity': 'severe',
                'distension': 'mild',
                'tenderness': 'severe'
            },
            'expected_category': 'ORANGE'
        }
    ]
    
    results = []
    for i, case in enumerate(test_cases, 1):
        print(f"\n📋 Case: {case['name']}")
        print(f"   Reason: {case['reason']}")
        print(f"   Symptoms: {case['symptoms']}")
        
        # Perform triage with patient ID
        patient_id = f"test_patient_{i:02d}"
        result = mts.triage_patient(case['reason'], case['symptoms'], patient_id=patient_id)
        
        print(f"   ➤ Triage Category: {result['triage_category']}")
        print(f"   ➤ Wait Time: {result['wait_time']}")
        print(f"   ➤ Fuzzy Score: {result['fuzzy_score']:.2f}")
        
        # Check if result matches expectation
        success = result['triage_category'] == case['expected_category']
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   ➤ Expected: {case['expected_category']} | Result: {status}")
        
        results.append({
            'case': case['name'],
            'expected': case['expected_category'],
            'actual': result['triage_category'],
            'success': success,
            'fuzzy_score': result['fuzzy_score']
        })
    
    # Print telemetry summary
    print(f"\n📊 Telemetry Summary:")
    stats = telemetry.get_summary_stats()
    print(f"   Total Steps: {stats['total_steps']}")
    print(f"   Unique Patients: {stats['unique_patients']}")
    print(f"   Total Duration: {stats['total_duration_ms']:.2f}ms")
    
    # Dump metrics for basic triage test
    metrics_file = mts.dump_metrics(filename="basic_triage_metrics.json")
    print(f"   Basic Triage Metrics: {metrics_file}")
    
    return results, telemetry, metrics


def test_knowledge_acquisition():
    """Test knowledge acquisition system"""
    print("\n🧠 Testing Knowledge Acquisition System")
    print("=" * 50)
    
    # Initialize knowledge acquisition system
    kas = KnowledgeAcquisitionSystem()
    
    # Start expert session
    print("\n1. Starting Expert Session")
    session_id = kas.start_expert_session("Dr_TestExpert_001")
    print(f"   Session ID: {session_id}")
    
    # Test Z-mouse interface
    print("\n2. Testing Z-Mouse Interface")
    zmouse_inputs = [
        ('chest_pain', 'very_severe', 0.95),
        ('breathing_difficulty', 'severe', 0.85),
        ('consciousness', 'moderate', 0.75)
    ]
    
    for symptom, value, confidence in zmouse_inputs:
        result = kas.zmouse.z_mouse_input(symptom, value, confidence)
        print(f"   Z-mouse: {symptom} = {value} (confidence: {confidence})")
        print(f"   ➤ Fuzzy membership: {result['fuzzy_membership']:.3f}")
    
    # Test fuzzy mark creation
    print("\n3. Testing Fuzzy Mark Creation")
    fuzzy_marks = [
        ('critical', (0, 10), [(0, 0), (8, 0.5), (9, 1), (10, 1)]),
        ('urgent', (0, 10), [(0, 0), (5, 0.5), (7, 1), (9, 0.5), (10, 0)])
    ]
    
    for term, universe, points in fuzzy_marks:
        mark = kas.zmouse.create_fuzzy_mark(term, universe, points)
        print(f"   Fuzzy mark '{term}' created with {len(points)} points")
        
        # Validate the fuzzy mark
        validation = kas.zmouse.validate_fuzzy_mark(mark)
        status = "✅ Valid" if validation['valid'] else "❌ Invalid"
        print(f"   ➤ Validation: {status}")
        if validation['errors']:
            print(f"   ➤ Errors: {validation['errors']}")
    
    # Test expert rule addition
    print("\n4. Testing Expert Rule Addition")
    expert_rules = [
        {
            'description': 'Critical cardiac emergency rule',
            'conditions': [
                {'symptom': 'chest_pain', 'value': 'very_severe'},
                {'symptom': 'sweating', 'value': 'severe'}
            ],
            'conclusion': 'red'
        },
        {
            'description': 'Respiratory distress rule',
            'conditions': [
                {'symptom': 'breathing_difficulty', 'value': 'severe'},
                {'symptom': 'cyanosis', 'value': 'moderate'}
            ],
            'conclusion': 'orange'
        }
    ]
    
    for rule in expert_rules:
        # Validate rule first
        validation = kas.validate_expert_rule(rule)
        if validation['valid']:
            success = kas.add_expert_rule(
                session_id,
                rule['description'],
                rule['conditions'],
                rule['conclusion']
            )
            status = "✅ Added" if success else "❌ Failed"
            print(f"   Rule: {rule['description']} - {status}")
        else:
            print(f"   Rule: {rule['description']} - ❌ Invalid")
            print(f"   ➤ Errors: {validation['errors']}")
    
    # Get system statistics
    print("\n5. System Statistics")
    stats = kas.get_system_statistics()
    for key, value in stats.items():
        print(f"   {key.replace('_', ' ').title()}: {value}")
    
    # End expert session
    print("\n6. Ending Expert Session")
    summary = kas.end_expert_session(session_id)
    print(f"   Session completed: {summary['session_summary']['status']}")
    print(f"   Rules added: {summary['rules_added']}")
    print(f"   Terms modified: {summary['terms_modified']}")
    
    return stats


def test_system_capabilities():
    """Test overall system capabilities"""
    print("\n🔧 Testing System Capabilities")
    print("=" * 50)
    
    # Initialize services for system capabilities test
    telemetry = TelemetryService()
    metrics = MetricsService()
    
    mts = ManchesterTriageSystem(telemetry_service=telemetry, metrics_service=metrics)
    
    # Test flowchart availability
    print("\n1. Available Flowcharts")
    flowcharts = mts.flowcharts['flowchart_id'].tolist()
    print(f"   Total flowcharts: {len(flowcharts)}")
    print(f"   Sample flowcharts: {flowcharts[:10]}")
    
    # Test linguistic value conversion
    print("\n2. Linguistic Value Conversion")
    linguistic_values = ['none', 'mild', 'moderate', 'severe', 'very_severe']
    for value in linguistic_values:
        numeric = mts.convert_linguistic_to_numeric(value)
        print(f"   '{value}' → {numeric}")
    
    # Test fuzzy system components
    print("\n3. Fuzzy System Components")
    print(f"   Input variables: 5 symptoms (symptom1-symptom5)")
    print(f"   Output variable: triage_category (1-5 scale)")
    print(f"   Fuzzy rules: {len(mts.fuzzy_rules)}")
    print(f"   Linguistic terms: {linguistic_values}")
    
    return {
        'total_flowcharts': len(flowcharts),
        'fuzzy_rules': len(mts.fuzzy_rules),
        'linguistic_terms': len(linguistic_values)
    }


def run_performance_test():
    """Run performance test with multiple triage cases"""
    print("\n⚡ Performance Testing")
    print("=" * 50)
    
    import time
    
    # Initialize services for performance testing
    telemetry = TelemetryService()
    metrics = MetricsService()
    mts = ManchesterTriageSystem(telemetry_service=telemetry, metrics_service=metrics)
    
    # Generate test cases
    test_symptoms = {
        'chest_pain': {'severe_pain': 'moderate', 'crushing_sensation': 'mild'},
        'headache': {'pain_severity': 'severe', 'sudden_onset': 'none'},
        'abdominal_pain': {'pain_intensity': 'moderate', 'vomiting': 'mild'},
        'limb_injuries': {'pain': 'mild', 'swelling': 'none'},
        'shortness_of_breath': {'difficulty_breathing': 'severe', 'wheeze': 'moderate'}
    }
    
    num_tests = 100
    print(f"\nRunning {num_tests} triage assessments...")
    
    start_time = time.time()
    results = []
    
    patient_counter = 1
    for i in range(num_tests):
        for reason, symptoms in test_symptoms.items():
            patient_id = f"perf_patient_{patient_counter:04d}"
            result = mts.triage_patient(reason, symptoms, patient_id=patient_id)
            results.append(result)
            patient_counter += 1
    
    end_time = time.time()
    total_time = end_time - start_time
    total_assessments = len(results)
    
    print(f"\n📊 Performance Results:")
    print(f"   Total assessments: {total_assessments}")
    print(f"   Total time: {total_time:.3f} seconds")
    print(f"   Average time per assessment: {(total_time/total_assessments)*1000:.2f} ms")
    print(f"   Assessments per second: {total_assessments/total_time:.1f}")
    
    # Analyze triage distribution
    categories = [r['triage_category'] for r in results]
    category_counts = {cat: categories.count(cat) for cat in set(categories)}
    
    print(f"\n📈 Triage Category Distribution:")
    for category, count in sorted(category_counts.items()):
        percentage = (count / total_assessments) * 100
        print(f"   {category}: {count} ({percentage:.1f}%)")
    
    # Print telemetry summary for performance test
    print(f"\n📊 Performance Telemetry Summary:")
    perf_stats = telemetry.get_summary_stats()
    print(f"   Total Telemetry Steps: {perf_stats['total_steps']}")
    print(f"   Unique Patients Processed: {perf_stats['unique_patients']}")
    print(f"   Total Telemetry Duration: {perf_stats['total_duration_ms']:.2f}ms")
    
    # Dump metrics for performance test
    metrics_file = mts.dump_metrics(filename="performance_test_metrics.json")
    print(f"   Performance Test Metrics: {metrics_file}")
    
    performance_results = {
        'total_assessments': total_assessments,
        'total_time': total_time,
        'avg_time_ms': (total_time/total_assessments)*1000,
        'assessments_per_second': total_assessments/total_time,
        'category_distribution': category_counts
    }
    
    return performance_results, telemetry, metrics


def main():
    """Main function to run all tests"""
    print("🏥 Manchester Triage System - Complete Testing Suite")
    print(f"Based on: {PAPER_INFO['title']}")
    print(f"Authors: {', '.join(PAPER_INFO['authors'])} ({PAPER_INFO['year']})")
    print(f"Institution: {PAPER_INFO['institution']}")
    print("=" * 70)
    
    try:
        # Test basic triage functionality
        triage_results, basic_telemetry, basic_metrics = test_basic_triage()
        
        # Test knowledge acquisition system
        knowledge_stats = test_knowledge_acquisition()
        
        # Test system capabilities
        system_capabilities = test_system_capabilities()
        
        # Run performance test
        performance_results, perf_telemetry, perf_metrics = run_performance_test()
        
        # Summary
        print("\n🎯 Test Summary")
        print("=" * 50)
        
        # Triage test results
        passed_tests = sum(1 for r in triage_results if r['success'])
        total_tests = len(triage_results)
        print(f"Triage Tests: {passed_tests}/{total_tests} passed")
        
        # System statistics
        print(f"Flowcharts Available: {system_capabilities['total_flowcharts']}")
        print(f"Fuzzy Rules: {system_capabilities['fuzzy_rules']}")
        print(f"Expert Sessions: {knowledge_stats['total_sessions']}")
        print(f"Expert Rules: {knowledge_stats['total_rules']}")
        
        # Performance
        print(f"Performance: {performance_results['assessments_per_second']:.1f} assessments/sec")
        
        # Dump telemetry data
        print("\n📁 Dumping Telemetry Data...")
        output_dir = "output/manchester_triage_system/telemetry"
        
        # Dump basic triage telemetry
        basic_file = basic_telemetry.dump_to_file(output_dir, "basic_triage_telemetry.json")
        print(f"   Basic Triage Telemetry: {basic_file}")
        
        # Dump performance test telemetry
        perf_file = perf_telemetry.dump_to_file(output_dir, "performance_test_telemetry.json")
        print(f"   Performance Test Telemetry: {perf_file}")
        
        # Generate comprehensive metrics analysis
        print("\n📊 Generating Comprehensive Metrics Analysis...")
        
        # Create combined metrics service for all data
        combined_metrics = MetricsService()
        
        # Add basic triage telemetry data
        basic_telemetry_data = {
            'metadata': {
                'session_start_time': basic_telemetry._session_start_time.isoformat(),
                'total_steps': len(basic_telemetry._steps)
            },
            'telemetry_steps': basic_telemetry.get_telemetry_data()
        }
        combined_metrics.add_telemetry_data(basic_telemetry_data)
        
        # Add performance test telemetry data
        perf_telemetry_data = {
            'metadata': {
                'session_start_time': perf_telemetry._session_start_time.isoformat(),
                'total_steps': len(perf_telemetry._steps)
            },
            'telemetry_steps': perf_telemetry.get_telemetry_data()
        }
        combined_metrics.add_telemetry_data(perf_telemetry_data)
        
        # Dump comprehensive metrics report
        metrics_file = combined_metrics.export_metrics_report(
            "output/manchester_triage_system/metrics", 
            "comprehensive_metrics_report.json"
        )
        print(f"   Comprehensive Metrics Report: {metrics_file}")
        
        # Display key metrics summary
        metrics_summary = combined_metrics.generate_system_metrics()
        
        print("\n📈 Key Metrics Summary:")
        print(f"   Total Patients Analyzed: {metrics_summary.total_patients}")
        print(f"   Average Wait Time: {metrics_summary.avg_wait_time:.2f} minutes")
        print(f"   Median Wait Time: {metrics_summary.median_wait_time:.2f} minutes")
        print(f"   Resource Utilization: {metrics_summary.resource_utilization:.1f}%")
        print(f"   Peak Arrival Hour: {metrics_summary.peak_arrival_hour}:00")
        
        print("\n🏥 Triage Category Distribution:")
        for category, count in metrics_summary.triage_category_distribution.items():
            percentage = (count / metrics_summary.total_patients) * 100
            print(f"   {category.value}: {count} patients ({percentage:.1f}%)")
        
        print("\n📋 Top Flowchart Reasons:")
        sorted_flowcharts = sorted(metrics_summary.flowchart_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        for reason, count in sorted_flowcharts:
            percentage = (count / metrics_summary.total_patients) * 100
            print(f"   {reason.value}: {count} cases ({percentage:.1f}%)")
        
        # Generate visualization plots
        print("\n📊 Generating Visualization Plots...")
        plot_files = combined_metrics.generate_all_plots(prefix="comprehensive_analysis")
        
        print("\n📈 Generated Plots:")
        for plot_type, filepath in plot_files.items():
            print(f"   {plot_type.replace('_', ' ').title()}: {filepath}")
        
        print("\n✅ All tests completed successfully!")
        print(f"\nPaper Reference: {PAPER_INFO['url']}")
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("\nPlease ensure all dependencies are installed:")
        print("pip install pandas numpy scikit-fuzzy scikit-learn")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()