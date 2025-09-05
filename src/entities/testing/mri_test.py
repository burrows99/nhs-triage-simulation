import attr
from typing import Optional, Dict, Any, List
from .base_test import BaseTest, TestStatus, TestPriority, TestResult

class MRISequence:
    """MRI sequence types"""
    T1_WEIGHTED = "T1_WEIGHTED"
    T2_WEIGHTED = "T2_WEIGHTED"
    FLAIR = "FLAIR"
    STIR = "STIR"  # Short Tau Inversion Recovery
    DWI = "DWI"  # Diffusion Weighted Imaging
    PERFUSION = "PERFUSION"
    ANGIOGRAPHY = "ANGIOGRAPHY"
    SPECTROSCOPY = "SPECTROSCOPY"

class MRIBodyPart:
    """Body parts for MRI scanning"""
    BRAIN = "BRAIN"
    SPINE_CERVICAL = "SPINE_CERVICAL"
    SPINE_THORACIC = "SPINE_THORACIC"
    SPINE_LUMBAR = "SPINE_LUMBAR"
    KNEE = "KNEE"
    SHOULDER = "SHOULDER"
    ABDOMEN = "ABDOMEN"
    PELVIS = "PELVIS"
    CARDIAC = "CARDIAC"

@attr.s(auto_attribs=True)
class MRITest(BaseTest):
    """MRI (Magnetic Resonance Imaging) test with specialized functionality"""
    
    # MRI-specific attributes
    body_part: str = MRIBodyPart.BRAIN
    sequences: List[str] = attr.ib(factory=lambda: [MRISequence.T1_WEIGHTED, MRISequence.T2_WEIGHTED])
    field_strength: float = 1.5  # Tesla (1.5T or 3.0T typically)
    contrast_used: bool = False
    contrast_agent: Optional[str] = None
    
    # Safety and contraindications
    has_pacemaker: bool = False
    has_metal_implants: bool = False
    claustrophobic: bool = False
    weight_limit_exceeded: bool = False
    
    # Image quality and findings
    image_quality: Optional[str] = None  # "EXCELLENT", "GOOD", "FAIR", "POOR"
    motion_artifacts: bool = False
    findings: List[str] = attr.ib(factory=list)
    
    def __attrs_post_init__(self):
        """Initialize MRI-specific settings"""
        self.test_type = "MRI"
        self.estimated_duration = 45.0  # MRI typically takes 30-60 minutes
        self.cost = 1200.0  # Typical MRI cost
        
        # Add MRI-specific contraindications
        if self.has_pacemaker:
            self.contraindications.append("Pacemaker - MRI contraindicated")
        if self.has_metal_implants:
            self.contraindications.append("Metal implants - requires safety assessment")
        if self.claustrophobic:
            self.contraindications.append("Claustrophobia - may require sedation")
        if self.weight_limit_exceeded:
            self.contraindications.append("Weight exceeds scanner limit")
    
    def add_contrast(self, agent: str = "Gadolinium") -> None:
        """Add contrast agent to the MRI study"""
        self.contrast_used = True
        self.contrast_agent = agent
        self.estimated_duration += 15.0  # Additional time for contrast
        self.cost += 200.0  # Additional cost for contrast
    
    def add_sequence(self, sequence: str) -> None:
        """Add an additional MRI sequence"""
        if sequence not in self.sequences:
            self.sequences.append(sequence)
            self.estimated_duration += 10.0  # Additional time per sequence
    
    def assess_image_quality(self, quality: str, has_motion: bool = False) -> None:
        """Assess the quality of MRI images"""
        self.image_quality = quality
        self.motion_artifacts = has_motion
        
        if quality in ["POOR", "FAIR"] or has_motion:
            self.notes += f" Image quality: {quality}. Motion artifacts: {has_motion}"
    
    def add_finding(self, finding: str, severity: str = "MILD") -> None:
        """Add a radiological finding"""
        finding_entry = f"{finding} ({severity})"
        self.findings.append(finding_entry)
        
        # Determine result interpretation based on findings
        if severity in ["SEVERE", "CRITICAL"]:
            self.result_interpretation = TestResult.CRITICAL
        elif severity in ["MODERATE", "SIGNIFICANT"]:
            self.result_interpretation = TestResult.ABNORMAL
        elif not self.result_interpretation:  # Only set if not already set
            self.result_interpretation = TestResult.NORMAL if not self.findings else TestResult.ABNORMAL
    
    def requires_radiologist_review(self) -> bool:
        """Check if MRI requires urgent radiologist review"""
        urgent_findings = [
            "hemorrhage", "stroke", "mass effect", "herniation", 
            "fracture", "cord compression", "aneurysm"
        ]
        
        for finding in self.findings:
            if any(urgent in finding.lower() for urgent in urgent_findings):
                return True
        
        return self.result_interpretation == TestResult.CRITICAL
    
    def get_mri_report(self) -> Dict[str, Any]:
        """Generate comprehensive MRI report"""
        base_summary = self.get_test_summary()
        
        mri_specific = {
            "body_part": self.body_part,
            "sequences_performed": self.sequences,
            "field_strength": f"{self.field_strength}T",
            "contrast_used": self.contrast_used,
            "contrast_agent": self.contrast_agent,
            "image_quality": self.image_quality,
            "motion_artifacts": self.motion_artifacts,
            "findings": self.findings,
            "contraindications": self.contraindications,
            "requires_urgent_review": self.requires_radiologist_review()
        }
        
        return {**base_summary, **mri_specific}
    
    def estimate_radiation_dose(self) -> float:
        """MRI uses no ionizing radiation"""
        return 0.0  # MRI is radiation-free
    
    def get_safety_checklist(self) -> Dict[str, bool]:
        """Get MRI safety checklist status"""
        return {
            "pacemaker_cleared": not self.has_pacemaker,
            "metal_implants_assessed": not self.has_metal_implants or "Metal implants" not in str(self.contraindications),
            "claustrophobia_managed": not self.claustrophobic or "sedation" in self.notes.lower(),
            "weight_within_limits": not self.weight_limit_exceeded,
            "contrast_contraindications_checked": not self.contrast_used or self.contrast_agent is not None
        }