#!/usr/bin/env python3
"""
Basic test script for hospital simulation components.

Tests core functionality without running the full simulation.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_enums():
    """Test enum imports and basic functionality."""
    print("Testing enums...")
    
    from enums.priority import TriagePriority
    from enums.resource_type import ResourceType
    from enums.patient_status import PatientStatus
    
    # Test priority enum
    priority = TriagePriority.IMMEDIATE
    assert priority.value == 1
    assert priority.max_wait_time_minutes == 0
    assert priority.color_code == "RED"
    print(f"✓ Priority: {priority}")
    
    # Test resource type enum
    resource = ResourceType.DOCTOR
    assert resource.is_preemptive == True
    assert resource.typical_service_time_minutes == (15.0, 45.0)
    print(f"✓ Resource: {resource}")
    
    # Test patient status enum
    status = PatientStatus.ARRIVED
    assert status.is_active == True
    assert status.is_waiting == False
    print(f"✓ Status: {status}")
    
    print("Enums test passed!\n")

def test_time_service():
    """Test time service functionality."""
    print("Testing time service...")
    
    from services.time_service import TimeService
    
    time_service = TimeService(random_seed=42)
    
    # Test arrival time generation
    arrival_time = time_service.generate_arrival_time()
    assert 0.5 <= arrival_time <= 60.0
    print(f"✓ Arrival time: {arrival_time:.2f} minutes")
    
    # Test triage time generation
    triage_time = time_service.generate_triage_time()
    assert 2.0 <= triage_time <= 20.0
    print(f"✓ Triage time: {triage_time:.2f} minutes")
    
    # Test doctor time generation
    doctor_time = time_service.generate_doctor_time()
    assert 5.0 <= doctor_time <= 60.0
    print(f"✓ Doctor time: {doctor_time:.2f} minutes")
    
    # Test priority multiplier
    multiplier = time_service.calculate_priority_multiplier(1)
    assert multiplier == 1.8
    print(f"✓ Priority multiplier for P1: {multiplier}")
    
    print("Time service test passed!\n")

def test_patient():
    """Test patient entity."""
    print("Testing patient entity...")
    
    from entities.patient import Patient
    from enums.priority import TriagePriority
    from enums.patient_status import PatientStatus
    from enums.resource_type import ResourceType
    
    # Create patient
    patient = Patient(
        arrival_time=10.0,
        priority=TriagePriority.URGENT,
        required_resource=ResourceType.DOCTOR
    )
    
    assert patient.arrival_time == 10.0
    assert patient.priority == TriagePriority.URGENT
    assert patient.status == PatientStatus.ARRIVED
    assert patient.is_high_priority == False  # Priority 3 is not high priority
    print(f"✓ Patient created: {patient}")
    
    # Test status update
    patient.update_status(PatientStatus.WAITING_TRIAGE, 15.0)
    assert patient.status == PatientStatus.WAITING_TRIAGE
    assert len(patient.status_history) == 2
    print(f"✓ Status updated: {patient.status}")
    
    # Test priority setting
    patient.set_priority(TriagePriority.IMMEDIATE)
    assert patient.priority == TriagePriority.IMMEDIATE
    assert patient.is_high_priority == True
    print(f"✓ Priority updated: {patient.priority}")
    
    print("Patient test passed!\n")

def test_metrics_service():
    """Test metrics service basic functionality."""
    print("Testing metrics service...")
    
    from services.metrics_service import MetricsService, WaitTimeMetrics
    from enums.priority import TriagePriority
    from enums.resource_type import ResourceType
    
    metrics_service = MetricsService(output_directory="./test_output")
    
    # Add some test data
    test_data = [
        (25.5, "patient1", TriagePriority.URGENT, ResourceType.DOCTOR),
        (45.2, "patient2", TriagePriority.STANDARD, ResourceType.MRI_MACHINE),
        (15.8, "patient3", TriagePriority.IMMEDIATE, ResourceType.DOCTOR)
    ]
    
    metrics_service.wait_time_data = test_data
    
    # Test wait time analysis
    analysis = metrics_service.analyze_wait_times()
    assert analysis.sample_size == 3
    assert analysis.mean_wait_time > 0
    assert analysis.median_wait_time > 0
    print(f"✓ Wait time analysis: mean={analysis.mean_wait_time:.1f}min, median={analysis.median_wait_time:.1f}min")
    
    # Test priority filtering
    urgent_analysis = metrics_service.analyze_wait_times(priority_filter=TriagePriority.URGENT)
    assert urgent_analysis.sample_size == 1
    print(f"✓ Urgent priority analysis: {urgent_analysis.sample_size} patients")
    
    print("Metrics service test passed!\n")

def main():
    """Run all basic tests."""
    print("=" * 50)
    print("HOSPITAL SIMULATION BASIC TESTS")
    print("=" * 50)
    print()
    
    try:
        test_enums()
        test_time_service()
        test_patient()
        test_metrics_service()
        
        print("=" * 50)
        print("ALL TESTS PASSED! ✓")
        print("=" * 50)
        print()
        print("The hospital simulation components are working correctly.")
        print("You can now run the full simulation with:")
        print("  python -m entities.hospital  # For basic hospital test")
        print("  python main_simulation.py    # For full simulation")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()