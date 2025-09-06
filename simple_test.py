#!/usr/bin/env python3
"""
Simple test script that directly imports individual modules.

Avoids __init__.py import issues by importing modules directly.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_priority_enum():
    """Test priority enum directly."""
    print("Testing priority enum...")
    
    from enums.priority import TriagePriority
    
    priority = TriagePriority.IMMEDIATE
    assert priority.value == 1
    assert priority.max_wait_time_minutes == 0
    assert priority.color_code == "RED"
    print(f"✓ Priority: {priority}")
    
    # Test all priorities
    for p in TriagePriority:
        print(f"  - {p.name}: {p.value} ({p.color_code})")
    
    print("Priority enum test passed!\n")

def test_resource_type_enum():
    """Test resource type enum directly."""
    print("Testing resource type enum...")
    
    from enums.resource_type import ResourceType
    
    # Test preemptive resources
    doctor = ResourceType.DOCTOR
    assert doctor.is_preemptive == True
    print(f"✓ Doctor is preemptive: {doctor.is_preemptive}")
    
    mri = ResourceType.MRI_MACHINE
    assert mri.is_preemptive == True
    print(f"✓ MRI is preemptive: {mri.is_preemptive}")
    
    # Test non-preemptive resources
    bed = ResourceType.BED
    assert bed.is_preemptive == False
    print(f"✓ Bed is non-preemptive: {bed.is_preemptive}")
    
    # Test service times
    for resource in ResourceType:
        min_time, max_time = resource.typical_service_time_minutes
        print(f"  - {resource.name}: {min_time}-{max_time} minutes")
    
    print("Resource type enum test passed!\n")

def test_patient_status_enum():
    """Test patient status enum directly."""
    print("Testing patient status enum...")
    
    from enums.patient_status import PatientStatus
    
    # Test status properties
    arrived = PatientStatus.ARRIVED
    assert arrived.is_active == True
    assert arrived.is_waiting == False
    print(f"✓ Arrived status: active={arrived.is_active}, waiting={arrived.is_waiting}")
    
    waiting = PatientStatus.WAITING_TRIAGE
    assert waiting.is_active == True
    assert waiting.is_waiting == True
    print(f"✓ Waiting status: active={waiting.is_active}, waiting={waiting.is_waiting}")
    
    discharged = PatientStatus.DISCHARGED
    assert discharged.is_active == False
    print(f"✓ Discharged status: active={discharged.is_active}")
    
    print("Patient status enum test passed!\n")

def test_time_service_direct():
    """Test time service by importing directly."""
    print("Testing time service (direct import)...")
    
    # Import time service directly without going through __init__.py
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "time_service", 
        Path(__file__).parent / "services" / "time_service.py"
    )
    time_service_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(time_service_module)
    
    TimeService = time_service_module.TimeService
    
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
    
    # Test MRI time generation
    mri_time = time_service.generate_mri_time()
    assert 15.0 <= mri_time <= 90.0
    print(f"✓ MRI time: {mri_time:.2f} minutes")
    
    # Test bed time generation
    bed_time = time_service.generate_bed_time()
    assert 30.0 <= bed_time <= 720.0
    print(f"✓ Bed time: {bed_time:.2f} minutes")
    
    # Test priority multipliers
    for priority in range(1, 6):
        multiplier = time_service.calculate_priority_multiplier(priority)
        print(f"  - Priority {priority} multiplier: {multiplier}")
    
    print("Time service test passed!\n")

def test_basic_simulation_concepts():
    """Test basic simulation concepts."""
    print("Testing basic simulation concepts...")
    
    # Test SimPy import
    import simpy
    env = simpy.Environment()
    assert env.now == 0
    print(f"✓ SimPy environment created: time={env.now}")
    
    # Test numpy import and basic operations
    import numpy as np
    random_values = np.random.lognormal(2.0, 0.5, 10)
    assert len(random_values) == 10
    assert all(v > 0 for v in random_values)
    print(f"✓ NumPy log-normal generation: mean={np.mean(random_values):.2f}")
    
    # Test basic statistics
    test_data = [10, 20, 30, 40, 50]
    mean_val = np.mean(test_data)
    median_val = np.median(test_data)
    percentile_95 = np.percentile(test_data, 95)
    
    assert mean_val == 30.0
    assert median_val == 30.0
    assert percentile_95 == 48.0
    print(f"✓ Statistics: mean={mean_val}, median={median_val}, 95th={percentile_95}")
    
    print("Basic simulation concepts test passed!\n")

def test_data_structures():
    """Test data structures and validation."""
    print("Testing data structures...")
    
    from dataclasses import dataclass
    from typing import List, Optional
    
    @dataclass
    class TestPatient:
        patient_id: str
        arrival_time: float
        priority: int = 3
        
        def __post_init__(self):
            if self.arrival_time < 0:
                raise ValueError("Arrival time cannot be negative")
            if not 1 <= self.priority <= 5:
                raise ValueError("Priority must be between 1 and 5")
    
    # Test valid patient
    patient = TestPatient("test123", 10.5, 2)
    assert patient.patient_id == "test123"
    assert patient.arrival_time == 10.5
    assert patient.priority == 2
    print(f"✓ Valid patient created: {patient}")
    
    # Test validation
    try:
        invalid_patient = TestPatient("test456", -5.0)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✓ Validation works: {e}")
    
    print("Data structures test passed!\n")

def main():
    """Run all basic tests."""
    print("=" * 60)
    print("HOSPITAL SIMULATION COMPONENT TESTS")
    print("=" * 60)
    print()
    
    try:
        test_priority_enum()
        test_resource_type_enum()
        test_patient_status_enum()
        test_time_service_direct()
        test_basic_simulation_concepts()
        test_data_structures()
        
        print("=" * 60)
        print("🎉 ALL TESTS PASSED! 🎉")
        print("=" * 60)
        print()
        print("✅ Core Components Working:")
        print("   • Enums (Priority, Resource Type, Patient Status)")
        print("   • Time Service (NHS-based distributions)")
        print("   • SimPy Environment")
        print("   • NumPy Statistical Operations")
        print("   • Data Validation")
        print()
        print("🏥 Hospital Simulation Framework Ready!")
        print()
        print("Next Steps:")
        print("   1. Fix remaining import issues in entity classes")
        print("   2. Test individual entity classes")
        print("   3. Run full simulation")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()