"""Medical Testing Module

This module provides a simplified framework for medical testing in healthcare simulations.
It includes base classes and specialized implementations for MRI and Blood tests only.

Classes:
    BaseTest: Abstract base class for all medical tests
    MRITest: Magnetic Resonance Imaging tests
    BloodTest: Laboratory blood work and panels

Enums:
    TestStatus: Status of medical tests (ORDERED, IN_PROGRESS, COMPLETED, etc.)
    TestPriority: Priority levels (ROUTINE, URGENT, STAT)
    TestResult: Result interpretations (NORMAL, ABNORMAL, CRITICAL, INCONCLUSIVE)

Usage:
    from src.entities.testing import BaseTest, MRITest, BloodTest
    
    # Create a blood test
    cbc = BloodTest(
        test_id="CBC_001",
        test_name="Complete Blood Count",
        test_type="BLOOD_TEST",
        patient_id="PAT_001",
        ordering_doctor_id="DOC_001",
        ordered_time=0.0,
        test_panel="CBC"
    )
    
    # Start and complete the test
    cbc.start_test(current_time=30.0, technician_id="TECH_001")
    cbc.add_cbc_results(wbc=7.5, rbc=4.5, hemoglobin=14.0, hematocrit=42.0, platelets=250)
    cbc.complete_test(current_time=60.0)
"""

from .base_test import (
    BaseTest,
    TestStatus,
    TestPriority,
    TestResult
)

from .mri_test import (
    MRITest,
    MRISequence,
    MRIBodyPart
)

from .blood_test import (
    BloodTest,
    BloodTestType,
    SpecimenType
)

__all__ = [
    # Base classes and enums
    'BaseTest',
    'TestStatus',
    'TestPriority',
    'TestResult',
    
    # MRI testing
    'MRITest',
    'MRISequence',
    'MRIBodyPart',
    
    # Blood testing
    'BloodTest',
    'BloodTestType',
    'SpecimenType'
]

# Version information
__version__ = '1.0.0'
__author__ = 'Hospital Simulation System'
__description__ = 'Simplified medical testing framework for MRI and Blood tests in healthcare simulations'