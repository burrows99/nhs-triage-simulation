#!/usr/bin/env python3
"""
Hospital Management System Demo
Demonstrates the hospital system with patient factory generated patients
"""

import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.entities.hospital.hospital import Hospital
from src.entities.doctor.doctor import Doctor
from src.entities.equipment.bed.bed import Bed
from src.entities.equipment.MRI.MRI import MRI
from src.entities.equipment.ultrasonic.ultrasonic import Ultrasonic
from src.services.patient_factory import PatientFactory
from src.enums.priority import Priority

def setup_hospital() -> Hospital:
    """Set up a hospital with doctors and equipment"""
    # Create hospital
    hospital = Hospital(id=1, name="City General Hospital")
    
    # Add doctors
    doctors = [
        Doctor(id=101, name="Dr. Smith", specialty="Emergency Medicine"),
        Doctor(id=102, name="Dr. Johnson", specialty="Cardiology"),
        Doctor(id=103, name="Dr. Williams", specialty="General Practice"),
        Doctor(id=104, name="Dr. Brown", specialty="Surgery")
    ]
    
    for doctor in doctors:
        hospital.add_doctor(doctor)
    
    # Add beds
    beds = [
        Bed(id=201, name="Bed-A1"),
        Bed(id=202, name="Bed-A2"),
        Bed(id=203, name="Bed-B1"),
        Bed(id=204, name="Bed-B2"),
        Bed(id=205, name="Bed-ICU1")
    ]
    
    
    # Add MRI machines
    mri_machines = [
        MRI(id=301, name="MRI-1"),
        MRI(id=302, name="MRI-2")
    ]
    
    # Add ultrasonic machines
    ultrasonic_machines = [
        Ultrasonic(id=401, name="Ultrasonic-1"),
        Ultrasonic(id=402, name="Ultrasonic-2")
    ]
    
    for ultrasonic in ultrasonic_machines:
        hospital.add_ultrasonic_machine(ultrasonic)

    for mri in mri_machines:
        hospital.add_mri_machine(mri)
    
    for bed in beds:
        hospital.add_bed(bed)
    
    return hospital

def demonstrate_patient_admission(hospital: Hospital, factory: PatientFactory) -> None:
    """Demonstrate patient admission with different priority levels"""
    print("\n" + "="*60)
    print("PATIENT ADMISSION DEMONSTRATION")
    print("="*60)
    
    # Create patients with different priority levels
    print("\n🚨 Creating Emergency Patient (RED Priority)...")
    emergency_patient = factory.create_emergency_patient()
    hospital.admit_patient(emergency_patient)
    
    print("\n🟠 Creating Urgent Patient (ORANGE Priority)...")
    urgent_patient = factory.create_urgent_patient()
    hospital.admit_patient(urgent_patient)
    
    print("\n🟡 Creating Standard Patient (GREEN Priority)...")
    standard_patient = factory.create_standard_patient()
    hospital.admit_patient(standard_patient)
    
    # Create a batch of mixed priority patients
    print("\n📋 Creating Mixed Priority Patients...")
    mixed_patients = factory.create_mixed_priority_patients(3)
    for patient in mixed_patients:
        hospital.admit_patient(patient)
        print()  # Add spacing between admissions

def show_hospital_status(hospital: Hospital) -> None:
    """Display current hospital status"""
    print("\n" + "="*60)
    print("HOSPITAL STATUS REPORT")
    print("="*60)
    
    # Hospital statistics
    stats = hospital.get_hospital_stats()
    print("\n📊 Hospital Statistics:")
    for key, value in stats.items():
        print(f"  • {key.replace('_', ' ').title()}: {value}")
    
    # Queue summary
    print("\n🏥 Resource Queue Summary:")
    queue_summary = hospital.get_queue_summary()
    for resource_name, queue_status in queue_summary.items():
        total_patients = sum(queue_status.values())
        if total_patients > 0:
            print(f"  • {resource_name}: {total_patients} patients")
            for priority, count in queue_status.items():
                if count > 0:
                    print(f"    - {priority}: {count}")

def demonstrate_triage_system(factory: PatientFactory) -> None:
    """Demonstrate the triage system with different patient types"""
    print("\n" + "="*60)
    print("TRIAGE SYSTEM DEMONSTRATION")
    print("="*60)
    
    # Create patients for each priority level
    priorities = [Priority.RED, Priority.ORANGE, Priority.YELLOW, Priority.GREEN, Priority.BLUE]
    
    for priority in priorities:
        print(f"\n{priority.value.upper()} Priority Patient:")
        patient = factory.create_patient(priority)
        
        # Get triage info
        from src.entities.triage.triage import FuzzyManchesterTriage
        triage = FuzzyManchesterTriage()
        triage_info = triage.get_triage_info(patient)
        
        print(f"  Patient: {patient.name}")
        print(f"  Symptoms: {', '.join(patient.symptoms.symptoms)}")
        print(f"  Priority: {triage_info['priority_info']['name']} ({triage_info['priority']})")
        print(f"  Max Wait Time: {triage_info['priority_info']['max_wait_time']}")
        print(f"  Description: {triage_info['priority_info']['description']}")

def main() -> None:
    """Main demonstration function"""
    print("🏥 HOSPITAL MANAGEMENT SYSTEM DEMO")
    print("Demonstrating Patient Factory Integration")
    
    # Initialize components
    print("\n🔧 Setting up hospital...")
    hospital = setup_hospital()
    
    print("\n👥 Initializing patient factory...")
    factory = PatientFactory()
    
    # Demonstrate triage system
    demonstrate_triage_system(factory)
    
    # Demonstrate patient admission
    demonstrate_patient_admission(hospital, factory)
    
    # Show final hospital status
    show_hospital_status(hospital)
    
    print("\n" + "="*60)
    print("DEMONSTRATION COMPLETE")
    print("="*60)
    print("\n✅ Successfully demonstrated:")
    print("  • Patient Factory generating realistic patients")
    print("  • Fuzzy Manchester Triage System")
    print("  • Routing Agent for resource assignment")
    print("  • Hospital management with priority queues")
    print("  • Comprehensive resource tracking")

if __name__ == "__main__":
    main()