#!/usr/bin/env python3
"""
Example usage of the simplified triage systems

This script demonstrates how to use the three triage systems:
1. ManchesterTriage - NHS Manchester Triage System with fuzzy logic
2. AITriage - AI-powered triage system

Each system accepts arrays of patients and returns priorities with reasons and service times.
"""

import sys
sys.path.append('src')

from src.entities.patient import Patient, Priority
from src.triage import ManchesterTriage, TriageResult
from typing import List


def create_sample_patients() -> List[Patient]:
    """Create sample patients for demonstration"""
    patients = []
    
    # Patient 1: High priority - chest pain with abnormal vitals
    patient1 = Patient(
        patient_id="P001",
        arrival_time=0.0,
        age=55,
        gender="male",
        chief_complaint="severe chest pain"
    )
    patient1.add_vital_sign("systolic_bp", 180)
    patient1.add_vital_sign("heart_rate", 110)
    patient1.add_vital_sign("pain_score", 9)
    patient1.medical_history = {"conditions": ["diabetes", "hypertension"]}
    patients.append(patient1)
    
    # Patient 2: Medium priority - difficulty breathing
    patient2 = Patient(
        patient_id="P002",
        arrival_time=5.0,
        age=34,
        gender="female",
        chief_complaint="difficulty breathing"
    )
    patient2.add_vital_sign("respiratory_rate", 28)
    patient2.add_vital_sign("oxygen_saturation", 92)
    patient2.add_vital_sign("pain_score", 6)
    patients.append(patient2)
    
    # Patient 3: Low priority - minor injury
    patient3 = Patient(
        patient_id="P003",
        arrival_time=10.0,
        age=25,
        gender="male",
        chief_complaint="minor cut on hand"
    )
    patient3.add_vital_sign("systolic_bp", 120)
    patient3.add_vital_sign("heart_rate", 75)
    patient3.add_vital_sign("pain_score", 3)
    patients.append(patient3)
    
    # Patient 4: Pediatric case - fever
    patient4 = Patient(
        patient_id="P004",
        arrival_time=15.0,
        age=2,
        gender="female",
        chief_complaint="high fever"
    )
    patient4.add_vital_sign("temperature", 39.5)
    patient4.add_vital_sign("heart_rate", 140)  # High for age
    patient4.add_vital_sign("pain_score", 5)
    patients.append(patient4)
    
    # Patient 5: Elderly with multiple issues
    patient5 = Patient(
        patient_id="P005",
        arrival_time=20.0,
        age=82,
        gender="female",
        chief_complaint="dizziness and confusion"
    )
    patient5.add_vital_sign("systolic_bp", 95)
    patient5.add_vital_sign("heart_rate", 55)
    patient5.add_vital_sign("pain_score", 2)
    patient5.medical_history = {"conditions": ["heart disease", "diabetes"]}
    patients.append(patient5)
    
    return patients


def print_triage_results(system_name: str, results: List[TriageResult]):
    """Print triage results in a formatted way"""
    print(f"\n{'='*60}")
    print(f"{system_name.upper()} RESULTS")
    print(f"{'='*60}")
    
    # Sort by priority (most urgent first)
    sorted_results = sorted(results, key=lambda r: r.priority.value)
    
    for result in sorted_results:
        priority_color = {
            Priority.IMMEDIATE: "🔴",
            Priority.VERY_URGENT: "🟠", 
            Priority.URGENT: "🟡",
            Priority.STANDARD: "🟢",
            Priority.NON_URGENT: "🔵"
        }
        
        color = priority_color.get(result.priority, "⚪")
        
        print(f"\n{color} Patient {result.patient.patient_id}:")
        print(f"   Priority: {result.priority.name} (Level {result.priority.value})")
        print(f"   Complaint: {result.patient.chief_complaint}")
        print(f"   Age: {result.patient.age} years")
        print(f"   Reason: {result.reason}")
        print(f"   Service Time: {result.service_time:.1f} minutes")
        print(f"   Confidence: {result.confidence_score:.2f}")


def demonstrate_manchester_triage(patients: List[Patient]):
    """Demonstrate Manchester Triage System on patients"""
    print(f"\n{'='*80}")
    print("MANCHESTER TRIAGE SYSTEM DEMONSTRATION")
    print(f"{'='*80}")
    print(f"Assessing {len(patients)} patients using Manchester Triage System...")
    
    # Initialize Manchester triage system
    manchester = ManchesterTriage()
    
    # Assess patients
    manchester_results = manchester.assess_patients(patients)
    
    # Print results
    print_triage_results("Manchester Triage System", manchester_results)
    
    # Manchester Triage System Analysis
    print(f"\n{'='*60}")
    print("MANCHESTER TRIAGE ANALYSIS")
    print(f"{'='*60}")
    
    # Priority distribution
    priority_counts = {p.name: 0 for p in Priority}
    total_service_time = 0
    
    for result in manchester_results:
        priority_counts[result.priority.name] += 1
        total_service_time += result.service_time
    
    print(f"\nPriority Distribution:")
    for priority_name, count in priority_counts.items():
        percentage = count / len(patients) * 100
        print(f"  {priority_name}: {count} patients ({percentage:.1f}%)")
    
    print(f"\nAverage Service Time: {total_service_time/len(patients):.1f} minutes")
    
    # System statistics
    print(f"\n{'='*60}")
    print("SYSTEM STATISTICS")
    print(f"{'='*60}")
    
    manchester_stats = manchester.get_statistics()
    
    print(f"\nManchester Triage System:")
    print(f"  Patients processed: {manchester_stats['patients_processed']}")
    print(f"  Average confidence: {manchester_stats['average_confidence']:.2f}")
    print(f"  Priority distribution: {manchester_stats['priority_distribution']}")
    
    return manchester_results


def demonstrate_batch_processing():
    """Demonstrate batch processing of patients"""
    print(f"\n{'='*80}")
    print("BATCH PROCESSING DEMONSTRATION")
    print(f"{'='*80}")
    
    # Create larger batch of patients
    patients = create_sample_patients()
    
    # Add more patients for batch demo
    for i in range(5, 15):
        patient = Patient(
            patient_id=f"P{i+1:03d}",
            arrival_time=i * 5.0,
            age=np.random.randint(1, 90),
            gender=np.random.choice(["male", "female"]),
            chief_complaint=np.random.choice([
                "chest pain", "difficulty breathing", "abdominal pain",
                "fever", "headache", "back pain", "nausea", "dizziness"
            ])
        )
        
        # Add random vital signs
        patient.add_vital_sign("systolic_bp", np.random.randint(80, 200))
        patient.add_vital_sign("heart_rate", np.random.randint(50, 150))
        patient.add_vital_sign("pain_score", np.random.randint(0, 10))
        
        patients.append(patient)
    
    print(f"Processing {len(patients)} patients in batch...")
    
    # Process with Manchester Triage
    manchester = ManchesterTriage()
    results = manchester.assess_patients(patients)
    
    # Summary statistics
    priority_counts = {p.name: 0 for p in Priority}
    total_service_time = 0
    
    for result in results:
        priority_counts[result.priority.name] += 1
        total_service_time += result.service_time
    
    print(f"\nBatch Processing Results:")
    print(f"  Total patients: {len(patients)}")
    print(f"  Average service time: {total_service_time/len(patients):.1f} minutes")
    print(f"  Priority distribution:")
    
    for priority_name, count in priority_counts.items():
        percentage = count / len(patients) * 100
        print(f"    {priority_name}: {count} patients ({percentage:.1f}%)")


def main():
    """Main demonstration function"""
    print("NHS Emergency Department Triage System Demonstration")
    print("Based on fuzzy Manchester Triage System research")
    
    # Create sample patients
    patients = create_sample_patients()
    
    print(f"\nCreated {len(patients)} sample patients for demonstration:")
    for patient in patients:
        print(f"  - {patient.patient_id}: {patient.age}y {patient.gender}, {patient.chief_complaint}")
    
    # Demonstrate Manchester triage system
    demonstrate_manchester_triage(patients)
    
    # Demonstrate batch processing
    demonstrate_batch_processing()
    
    print(f"\n{'='*80}")
    print("DEMONSTRATION COMPLETE")
    print(f"{'='*80}")
    print("\nKey Features Demonstrated:")
    print("✓ Array-based patient processing")
    print("✓ Priority assignment with detailed reasons")
    print("✓ Service time estimation")
    print("✓ Confidence scoring")
    print("✓ Manchester Triage System with fuzzy logic")
    print("✓ System statistics and analysis")
    print("✓ Batch processing capabilities")
    print("\nNote: AI triage system to be implemented later")


if __name__ == "__main__":
    import numpy as np
    main()