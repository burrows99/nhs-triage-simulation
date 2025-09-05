import attr
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class TestStatus(Enum):
    """Status of medical test"""
    ORDERED = "ORDERED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"

class TestPriority(Enum):
    """Priority level for medical tests"""
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    STAT = "STAT"  # Immediate/Emergency

class TestResult(Enum):
    """Test result interpretation"""
    NORMAL = "NORMAL"
    ABNORMAL = "ABNORMAL"
    CRITICAL = "CRITICAL"
    INCONCLUSIVE = "INCONCLUSIVE"

@attr.s(auto_attribs=True)
class BaseTest:
    """Base class for all medical tests with common attributes and functionality"""
    
    # Core identification
    test_id: str
    test_name: str
    test_type: str
    
    # Patient and ordering information
    patient_id: str
    ordering_doctor_id: str
    ordered_time: float
    
    # Test execution
    priority: TestPriority = TestPriority.ROUTINE
    status: TestStatus = TestStatus.ORDERED
    estimated_duration: float = 30.0  # minutes
    actual_duration: Optional[float] = None
    
    # Results and interpretation
    result_value: Optional[Any] = None
    result_interpretation: Optional[TestResult] = None
    reference_range: Optional[str] = None
    units: Optional[str] = None
    
    # Timing
    start_time: Optional[float] = None
    completion_time: Optional[float] = None
    
    # Additional metadata
    notes: str = ""
    technician_id: Optional[str] = None
    equipment_id: Optional[str] = None
    cost: float = 0.0
    
    # Quality and validation
    quality_control_passed: bool = True
    requires_fasting: bool = False
    contraindications: List[str] = attr.ib(factory=list)
    
    def start_test(self, current_time: float, technician_id: Optional[str] = None) -> None:
        """Start the test execution"""
        self.status = TestStatus.IN_PROGRESS
        self.start_time = current_time
        if technician_id:
            self.technician_id = technician_id
    
    def complete_test(self, current_time: float, result_value: Any = None, 
                     interpretation: Optional[TestResult] = None) -> None:
        """Complete the test with results"""
        self.status = TestStatus.COMPLETED
        self.completion_time = current_time
        if self.start_time:
            self.actual_duration = current_time - self.start_time
        
        if result_value is not None:
            self.result_value = result_value
        if interpretation:
            self.result_interpretation = interpretation
    
    def cancel_test(self, current_time: float, reason: str = "") -> None:
        """Cancel the test"""
        self.status = TestStatus.CANCELLED
        if reason:
            self.notes += f" CANCELLED: {reason}"
    
    def fail_test(self, current_time: float, reason: str = "") -> None:
        """Mark test as failed"""
        self.status = TestStatus.FAILED
        if reason:
            self.notes += f" FAILED: {reason}"
    
    def get_turnaround_time(self) -> Optional[float]:
        """Calculate total turnaround time from order to completion"""
        if self.completion_time:
            return self.completion_time - self.ordered_time
        return None
    
    def is_critical_result(self) -> bool:
        """Check if test result is critical"""
        return self.result_interpretation == TestResult.CRITICAL
    
    def is_overdue(self, current_time: float) -> bool:
        """Check if test is overdue based on priority"""
        if self.status in [TestStatus.COMPLETED, TestStatus.CANCELLED]:
            return False
        
        time_since_order = current_time - self.ordered_time
        
        # Define time limits based on priority
        if self.priority == TestPriority.STAT:
            return time_since_order > 60  # 1 hour for STAT
        elif self.priority == TestPriority.URGENT:
            return time_since_order > 240  # 4 hours for urgent
        else:
            return time_since_order > 1440  # 24 hours for routine
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get comprehensive test summary"""
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "test_type": self.test_type,
            "patient_id": self.patient_id,
            "status": self.status.value,
            "priority": self.priority.value,
            "result_value": self.result_value,
            "result_interpretation": self.result_interpretation.value if self.result_interpretation else None,
            "turnaround_time": self.get_turnaround_time(),
            "is_critical": self.is_critical_result(),
            "cost": self.cost
        }