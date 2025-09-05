import attr
import random
from typing import Optional
from .patient import Patient
from .testing.blood_test import BloodTest, BloodTestType
from .testing.base_test import TestStatus

@attr.s(auto_attribs=True)
class BloodTestNurse:
    """Simplified blood test nurse for processing patient blood tests"""
    id: int
    name: str
    specialization: str = "Blood Testing"
    current_patient: Optional[Patient] = None
    busy: bool = False
    total_patients_treated: int = 0
    
    def process_patient_blood_tests(self, patient: Patient) -> Patient:
        """Process patient blood tests and update their test data randomly"""
        self.current_patient = patient
        self.busy = True
        
        # Find blood tests in patient's test results
        for test in patient.test_results:
            if isinstance(test, BloodTest):
                # Randomly generate results based on test panel type
                test_panel = test.test_panel
                
                if test_panel == BloodTestType.CBC:
                    test.add_cbc_results(
                        wbc=random.uniform(4.0, 11.0),
                        rbc=random.uniform(4.0, 5.5),
                        hemoglobin=random.uniform(12.0, 16.0),
                        hematocrit=random.uniform(36.0, 48.0),
                        platelets=random.uniform(150, 400)
                    )
                elif test_panel == BloodTestType.CMP:
                    test.add_cmp_results(
                        glucose=random.uniform(70, 140),
                        bun=random.uniform(7, 25),
                        creatinine=random.uniform(0.6, 1.3),
                        sodium=random.uniform(135, 145),
                        potassium=random.uniform(3.5, 5.0),
                        chloride=random.uniform(96, 108)
                    )
                elif test_panel == BloodTestType.ABG:
                    test.add_abg_results(
                        ph=random.uniform(7.35, 7.45),
                        pco2=random.uniform(35, 45),
                        po2=random.uniform(80, 100),
                        hco3=random.uniform(22, 28),
                        base_excess=random.uniform(-2, 2),
                        o2_sat=random.uniform(95, 100)
                    )
                elif test_panel == BloodTestType.CARDIAC_MARKERS:
                    test.add_cardiac_results(
                        troponin_i=random.uniform(0.0, 0.04),
                        ck_mb=random.uniform(0, 6.3),
                        myoglobin=random.uniform(25, 72)
                    )
                elif test_panel == BloodTestType.CRP:
                    test.add_crp_results(
                        crp=random.uniform(0.0, 3.0)
                    )
                elif test_panel == BloodTestType.TROPONIN:
                    test.add_cardiac_results(
                        troponin_t=random.uniform(0.0, 0.014)
                    )
                
                # Set test status to completed
                test.status = TestStatus.COMPLETED
                
                # Add interpretation
                test.interpretation = {
                    "summary": "Blood test results within normal limits",
                    "abnormal_values": [],
                    "clinical_significance": "No immediate concerns identified"
                }
        
        return patient
    
    def complete_blood_test(self, patient: Patient, current_time: float, logger=None) -> Patient:
        """Complete blood test processing and release resources"""
        # Process the blood test
        updated_patient = self.process_patient_blood_tests(patient)
        
        # Release resources
        self.busy = False
        self.current_patient = None
        self.total_patients_treated += 1
        
        # Log completion if logger provided
        if logger:
            actual_test_time = current_time - (patient.blood_test_start_time or current_time)
            from ..utils.logger import EventType
            logger.log_event(
                timestamp=current_time,
                event_type=EventType.TEST_COMPLETE,
                message=f"Blood test completed: Patient {patient.id} processed by Nurse {self.id}",
                data={
                    "patient_id": patient.id,
                    "nurse_id": self.id,
                    "condition": patient.condition,
                    "actual_test_time": actual_test_time,
                    "nurse_total_patients": self.total_patients_treated
                },
                source="blood_test_nurse"
            )
        
        return updated_patient
    
    @staticmethod
    def get_busy_nurses(blood_nurses: list) -> list:
        """Get list of currently busy blood test nurses"""
        return [nurse for nurse in blood_nurses if nurse.busy and nurse.current_patient is not None]