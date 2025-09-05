import attr
import random
from typing import Optional
from .patient import Patient
from .testing.mri_test import MRITest, MRISequence
from .testing.base_test import TestStatus

@attr.s(auto_attribs=True)
class MRI_Machine:
    """Simplified MRI machine for processing patient scans"""
    id: int
    name: str
    model: str = "Siemens Magnetom"
    field_strength: str = "3.0T"
    current_patient: Optional[Patient] = None
    busy: bool = False
    total_patients_treated: int = 0
    
    def process_patient_scan(self, patient: Patient) -> Patient:
        """Process patient MRI scan and update their test data randomly"""
        self.current_patient = patient
        self.busy = True
        
        # Find MRI tests in patient's test results
        for test in patient.test_results:
            if isinstance(test, MRITest):
                # Randomly update MRI test data
                test.image_quality = random.choice(["EXCELLENT", "GOOD", "FAIR"])
                test.sequences_performed = random.sample(
                    [MRISequence.T1_WEIGHTED, MRISequence.T2_WEIGHTED, MRISequence.FLAIR, MRISequence.STIR],
                    k=random.randint(2, 4)
                )
                test.slice_thickness = random.uniform(2.0, 6.0)
                
                # Random findings based on body part
                body_part = test.body_part.upper()
                findings_options = {
                    "BRAIN": [
                        "No acute intracranial abnormality. Normal brain parenchyma.",
                        "Mild cerebral atrophy consistent with age.",
                        "Small vessel disease changes noted.",
                        "Normal brain MRI with no acute findings.",
                        "Mild white matter hyperintensities.",
                        "No evidence of mass lesion or hemorrhage."
                    ],
                    "SPINE_CERVICAL": [
                        "Normal cervical spine alignment. No disc herniation.",
                        "Mild degenerative changes at C5-C6.",
                        "No evidence of spinal stenosis."
                    ],
                    "SPINE_LUMBAR": [
                        "Normal lumbar spine alignment. No disc herniation.",
                        "Mild degenerative changes at L4-L5.",
                        "No evidence of spinal stenosis."
                    ],
                    "ABDOMEN": [
                        "Normal abdominal organs. No masses detected.",
                        "Mild hepatic steatosis.",
                        "No evidence of obstruction."
                    ],
                    "CARDIAC": [
                        "Normal cardiac anatomy and function.",
                        "No evidence of pathology.",
                        "Normal ventricular function."
                    ]
                }
                
                test.findings = [
                    random.choice(findings_options.get(body_part, [f"Normal {body_part.lower()} anatomy."]))
                ]
                test.impression = f"MRI {body_part.lower()}: {random.choice(['Normal', 'Mild changes', 'No acute findings'])}"
                
                # Mark test as completed
                test.status = TestStatus.COMPLETED
        
        # Update machine status
        self.total_patients_treated += 1
        self.busy = False
        self.current_patient = None
        
        return patient
    
    def complete_mri_scan(self, patient: Patient, current_time: float, logger=None) -> Patient:
        """Complete MRI scan processing and release resources"""
        # Process the MRI scan
        updated_patient = self.process_patient_scan(patient)
        
        # Release resources
        self.busy = False
        self.current_patient = None
        self.total_patients_treated += 1
        
        # Log completion if logger provided
        if logger:
            actual_scan_time = current_time - (patient.mri_start_time or current_time)
            from ..utils.logger import EventType
            logger.log_event(
                timestamp=current_time,
                event_type=EventType.TEST_COMPLETE,
                message=f"MRI scan completed: Patient {patient.id} processed by MRI {self.id}",
                data={
                    "patient_id": patient.id,
                    "mri_id": self.id,
                    "condition": patient.condition,
                    "actual_scan_time": actual_scan_time,
                    "mri_total_patients": self.total_patients_treated
                },
                source="mri_machine"
            )
        
        return updated_patient
    
    @staticmethod
    def get_busy_machines(mri_machines: list) -> list:
        """Get list of currently busy MRI machines"""
        return [mri for mri in mri_machines if mri.busy and mri.current_patient is not None]