import attr
from typing import List, Optional, Dict, Any
from ..enums.Triage import Priority
from .sub_entities.vital_signs import VitalSigns

@attr.s(auto_attribs=True)
class Patient:
    """Patient class with medical condition and priority information"""
    id: int
    arrival_time: float
    condition: str
    symptoms: List[str]
    vital_signs: VitalSigns
    priority: Optional[Priority] = None
    priority_reason: str = ""
    treatment_time: float = 0.0
    wait_time: float = 0.0
    interruption_count: int = 0
    assigned_doctor: Optional[int] = None
    treatment_start_time: Optional[float] = None
    estimated_wait_time: float = 0.0
    
    # Test results storage
    test_results: List[Any] = attr.ib(factory=list)
    
    def add_test_result(self, test_result: Any) -> None:
        """Add a test result (test object) to the patient's test results array"""
        self.test_results.append(test_result)
    
    def get_test_results_summary(self) -> Dict[str, Any]:
        """Get summary of all test results"""
        if not self.test_results:
            return {
                "total_tests": 0,
                "completed_tests": 0,
                "pending_tests": 0,
                "abnormal_results": 0,
                "critical_results": 0,
                "test_results": []
            }
        
        completed = len([t for t in self.test_results if attr.has(t.__class__) and getattr(t, 'status', None) and t.status.name == 'COMPLETED'])
        pending = len([t for t in self.test_results if attr.has(t.__class__) and getattr(t, 'status', None) and t.status.name in ['ORDERED', 'IN_PROGRESS']])
        abnormal = len([t for t in self.test_results if attr.has(t.__class__) and getattr(t, 'result_interpretation', None) and t.result_interpretation and t.result_interpretation.name == 'ABNORMAL'])
        critical = len([t for t in self.test_results if attr.has(t.__class__) and getattr(t, 'result_interpretation', None) and t.result_interpretation and t.result_interpretation.name == 'CRITICAL'])
        
        return {
            "total_tests": len(self.test_results),
            "completed_tests": completed,
            "pending_tests": pending,
            "abnormal_results": abnormal,
            "critical_results": critical,
            "test_results": self.test_results
        }
    
    def get_short_summary(self) -> Dict[str, Any]:
        """Get brief patient summary for quick reference"""
        return {
            "patient_id": self.id,
            "condition": self.condition,
            "priority": self.priority.name if self.priority else "NOT_TRIAGED",
            "status": self._get_current_status(),
            "assigned_doctor": self.assigned_doctor,
            "wait_time": self.wait_time,
            "arrival_time": self.arrival_time
        }
    
    def get_clinical_summary(self) -> Dict[str, Any]:
        """Get clinical summary for medical staff"""
        return {
            "patient_id": self.id,
            "chief_complaint": self.condition,
            "presenting_symptoms": self.symptoms,
            "triage_priority": self.priority.name if self.priority else "NOT_TRIAGED",
            "triage_rationale": self.priority_reason,
            "vital_signs_on_arrival": {
                "hr": self.vital_signs.heart_rate,
                "bp": f"{self.vital_signs.bp_systolic}/{self.vital_signs.bp_diastolic}",
                "temp": self.vital_signs.temperature,
                "rr": getattr(self.vital_signs, 'respiratory_rate', 16),  # Default if not present
                "spo2": self.vital_signs.oxygen_saturation
            },
            "care_timeline": {
                "arrival": self.arrival_time,
                "treatment_start": self.treatment_start_time,
                "interruptions": self.interruption_count
            },
            "assigned_provider": self.assigned_doctor,
            "current_status": self._get_current_status()
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive patient summary"""
        return {
            "patient_id": self.id,
            "arrival_time": self.arrival_time,
            "condition": self.condition,
            "symptoms": self.symptoms,
            "priority": self.priority.name if self.priority else None,
            "priority_reason": self.priority_reason,
            "vital_signs": {
                "heart_rate": self.vital_signs.heart_rate,
                "blood_pressure_systolic": self.vital_signs.bp_systolic,
                "blood_pressure_diastolic": self.vital_signs.bp_diastolic,
                "temperature": self.vital_signs.temperature,
                "respiratory_rate": getattr(self.vital_signs, 'respiratory_rate', 16),  # Default if not present
                "oxygen_saturation": self.vital_signs.oxygen_saturation
            },
            "treatment_info": {
                "assigned_doctor": self.assigned_doctor,
                "treatment_start_time": self.treatment_start_time,
                "estimated_treatment_time": self.treatment_time,
                "estimated_wait_time": self.estimated_wait_time,
                "actual_wait_time": self.wait_time,
                "interruption_count": self.interruption_count
            },
            "status": self._get_current_status()
        }
    
    def get_all_summaries(self) -> Dict[str, Any]:
        """Get all summary types in one comprehensive response"""
        return {
            "short_summary": self.get_short_summary(),
            "clinical_summary": self.get_clinical_summary(),
            "comprehensive_summary": self.get_summary(),
            "wait_time_analysis": self.get_wait_time_analysis()
        }
    
    def _get_current_status(self) -> str:
        """Determine patient's current status"""
        if self.assigned_doctor and self.treatment_start_time:
            return "IN_TREATMENT"
        elif self.priority:
            return "WAITING_FOR_TREATMENT"
        elif self.arrival_time:
            return "AWAITING_TRIAGE"
        else:
            return "UNKNOWN"
    
    def get_wait_time_analysis(self) -> Dict[str, Any]:
        """Analyze wait times and delays"""
        analysis = {
            "estimated_wait_time": self.estimated_wait_time,
            "actual_wait_time": self.wait_time,
            "wait_time_accuracy": None,
            "delay_status": "UNKNOWN"
        }
        
        if self.estimated_wait_time > 0 and self.wait_time > 0:
            accuracy = (1 - abs(self.wait_time - self.estimated_wait_time) / self.estimated_wait_time) * 100
            analysis["wait_time_accuracy"] = max(0, accuracy)  # Ensure non-negative
            
            if self.wait_time > self.estimated_wait_time * 1.2:  # 20% over estimate
                analysis["delay_status"] = "DELAYED"
            elif self.wait_time < self.estimated_wait_time * 0.8:  # 20% under estimate
                analysis["delay_status"] = "AHEAD_OF_SCHEDULE"
            else:
                analysis["delay_status"] = "ON_TIME"
        
        return analysis
    
    def get_clinical_summary(self) -> Dict[str, Any]:
        """Get clinical summary for medical staff"""
        return {
            "patient_id": self.id,
            "chief_complaint": self.condition,
            "presenting_symptoms": self.symptoms,
            "triage_priority": self.priority.name if self.priority else "NOT_TRIAGED",
            "triage_rationale": self.priority_reason,
            "vital_signs_on_arrival": {
                "hr": self.vital_signs.heart_rate,
                "bp": f"{self.vital_signs.bp_systolic}/{self.vital_signs.bp_diastolic}",
                "temp": self.vital_signs.temperature,
                "rr": getattr(self.vital_signs, 'respiratory_rate', 16),  # Default if not present
                "spo2": self.vital_signs.oxygen_saturation
            },
            "care_timeline": {
                "arrival": self.arrival_time,
                "treatment_start": self.treatment_start_time,
                "interruptions": self.interruption_count
            },
            "assigned_provider": self.assigned_doctor,
            "current_status": self._get_current_status()
        }