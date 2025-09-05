import attr
from typing import Optional, Dict, Any, List, Union
from .base_test import BaseTest, TestStatus, TestPriority, TestResult

class BloodTestType:
    """Common blood test types and panels"""
    # Basic panels
    CBC = "CBC"  # Complete Blood Count
    CMP = "CMP"  # Comprehensive Metabolic Panel
    BMP = "BMP"  # Basic Metabolic Panel
    LIPID_PANEL = "LIPID_PANEL"
    LIVER_FUNCTION = "LIVER_FUNCTION"
    THYROID_FUNCTION = "THYROID_FUNCTION"
    
    # Cardiac markers
    TROPONIN = "TROPONIN"
    CK_MB = "CK_MB"
    BNP = "BNP"
    CARDIAC_MARKERS = "CARDIAC_MARKERS"  # Combined cardiac panel
    
    # Coagulation
    PT_INR = "PT_INR"
    PTT = "PTT"
    
    # Inflammatory markers
    ESR = "ESR"
    CRP = "CRP"
    
    # Hormones
    HBA1C = "HBA1C"
    GLUCOSE = "GLUCOSE"
    
    # Infectious disease
    BLOOD_CULTURE = "BLOOD_CULTURE"
    HEPATITIS_PANEL = "HEPATITIS_PANEL"
    
    # Blood gas analysis
    ABG = "ABG"  # Arterial Blood Gas

class SpecimenType:
    """Types of blood specimens"""
    SERUM = "SERUM"
    PLASMA = "PLASMA"
    WHOLE_BLOOD = "WHOLE_BLOOD"
    ARTERIAL_BLOOD = "ARTERIAL_BLOOD"

@attr.s(auto_attribs=True)
class BloodTest(BaseTest):
    """Blood test class for laboratory blood work"""
    
    # Blood test specific attributes
    test_panel: str = BloodTestType.CBC
    specimen_type: str = SpecimenType.SERUM
    volume_required: float = 5.0  # mL
    
    # Collection information
    collection_time: Optional[float] = None
    collection_site: str = "Antecubital vein"
    collected_by: Optional[str] = None
    
    # Processing information
    processing_time: Optional[float] = None
    analyzer_id: Optional[str] = None
    
    # Results - can store multiple values for panels
    test_results: Dict[str, Union[float, str, bool]] = attr.ib(factory=dict)
    reference_ranges: Dict[str, str] = attr.ib(factory=dict)
    abnormal_flags: Dict[str, str] = attr.ib(factory=dict)  # H, L, Critical
    
    # Quality control
    hemolyzed: bool = False
    lipemic: bool = False
    icteric: bool = False
    clotted: bool = False
    
    # Special requirements
    requires_fasting: bool = False
    temperature_sensitive: bool = False
    light_sensitive: bool = False
    
    def __attrs_post_init__(self):
        """Initialize blood test specific settings"""
        self.test_type = "BLOOD_TEST"
        self._setup_test_defaults()
        
        # Set fasting requirements
        fasting_tests = [BloodTestType.GLUCOSE, BloodTestType.LIPID_PANEL, BloodTestType.CMP]
        if self.test_panel in fasting_tests:
            self.requires_fasting = True
    
    def _setup_test_defaults(self):
        """Setup defaults based on test panel"""
        test_configs = {
            BloodTestType.CBC: {
                'duration': 30.0, 'cost': 50.0, 'volume': 3.0,
                'specimen': SpecimenType.WHOLE_BLOOD
            },
            BloodTestType.CMP: {
                'duration': 45.0, 'cost': 80.0, 'volume': 5.0,
                'specimen': SpecimenType.SERUM
            },
            BloodTestType.LIPID_PANEL: {
                'duration': 30.0, 'cost': 60.0, 'volume': 3.0,
                'specimen': SpecimenType.SERUM
            },
            BloodTestType.TROPONIN: {
                'duration': 60.0, 'cost': 120.0, 'volume': 2.0,
                'specimen': SpecimenType.SERUM
            },
            BloodTestType.BLOOD_CULTURE: {
                'duration': 2880.0, 'cost': 200.0, 'volume': 10.0,  # 48 hours
                'specimen': SpecimenType.WHOLE_BLOOD
            }
        }
        
        config = test_configs.get(self.test_panel, {
            'duration': 30.0, 'cost': 70.0, 'volume': 5.0,
            'specimen': SpecimenType.SERUM
        })
        
        self.estimated_duration = config['duration']
        self.cost = config['cost']
        self.volume_required = config['volume']
        self.specimen_type = config['specimen']
    
    def collect_specimen(self, current_time: float, collector_id: str, 
                        site: str = "Antecubital vein") -> None:
        """Record specimen collection"""
        self.collection_time = current_time
        self.collected_by = collector_id
        self.collection_site = site
        self.status = TestStatus.IN_PROGRESS
        self.notes += f" Specimen collected at {site} by {collector_id}"
    
    def assess_specimen_quality(self, hemolyzed: bool = False, lipemic: bool = False,
                              icteric: bool = False, clotted: bool = False) -> bool:
        """Assess specimen quality and determine if acceptable for testing"""
        self.hemolyzed = hemolyzed
        self.lipemic = lipemic
        self.icteric = icteric
        self.clotted = clotted
        
        # Determine if specimen is acceptable
        quality_issues = []
        if hemolyzed:
            quality_issues.append("hemolyzed")
        if lipemic:
            quality_issues.append("lipemic")
        if icteric:
            quality_issues.append("icteric")
        if clotted and self.specimen_type in [SpecimenType.SERUM, SpecimenType.PLASMA]:
            quality_issues.append("clotted")
        
        if quality_issues:
            self.quality_control_passed = False
            self.notes += f" Specimen quality issues: {', '.join(quality_issues)}"
            return False
        
        return True
    
    def add_result(self, analyte: str, value: Union[float, str, bool], 
                  reference_range: str = "", flag: str = "") -> None:
        """Add individual test result"""
        self.test_results[analyte] = value
        if reference_range:
            self.reference_ranges[analyte] = reference_range
        if flag:
            self.abnormal_flags[analyte] = flag
    
    def add_cbc_results(self, wbc: float, rbc: float, hemoglobin: float, 
                       hematocrit: float, platelets: float) -> None:
        """Add Complete Blood Count results"""
        results = {
            'WBC': wbc, 'RBC': rbc, 'Hemoglobin': hemoglobin,
            'Hematocrit': hematocrit, 'Platelets': platelets
        }
        
        references = {
            'WBC': '4.0-11.0 K/uL', 'RBC': '4.2-5.4 M/uL', 
            'Hemoglobin': '12.0-16.0 g/dL', 'Hematocrit': '36-46%',
            'Platelets': '150-450 K/uL'
        }
        
        for analyte, value in results.items():
            self.add_result(analyte, value, references[analyte])
            
        self._evaluate_cbc_flags()
    
    def add_cmp_results(self, glucose: float, bun: float, creatinine: float,
                       sodium: float, potassium: float, chloride: float) -> None:
        """Add Comprehensive Metabolic Panel results"""
        results = {
            'Glucose': glucose, 'BUN': bun, 'Creatinine': creatinine,
            'Sodium': sodium, 'Potassium': potassium, 'Chloride': chloride
        }
        
        references = {
            'Glucose': '70-100 mg/dL', 'BUN': '7-20 mg/dL', 
            'Creatinine': '0.6-1.2 mg/dL', 'Sodium': '136-145 mEq/L',
            'Potassium': '3.5-5.0 mEq/L', 'Chloride': '98-107 mEq/L'
        }
        
        for analyte, value in results.items():
            self.add_result(analyte, value, references[analyte])
            
        self._evaluate_cmp_flags()
    
    def add_abg_results(self, ph: float, pco2: float, po2: float, 
                       hco3: float, base_excess: float, o2_sat: float) -> None:
        """Add Arterial Blood Gas results"""
        results = {
            'pH': ph, 'pCO2': pco2, 'pO2': po2,
            'HCO3': hco3, 'Base_Excess': base_excess, 'O2_Sat': o2_sat
        }
        
        references = {
            'pH': '7.35-7.45', 'pCO2': '35-45 mmHg', 'pO2': '80-100 mmHg',
            'HCO3': '22-26 mEq/L', 'Base_Excess': '-2 to +2 mEq/L', 'O2_Sat': '95-100%'
        }
        
        for analyte, value in results.items():
            self.add_result(analyte, value, references[analyte])
            
        self._evaluate_abg_flags()
    
    def add_cardiac_results(self, troponin_i: float = None, ck_mb: float = None, 
                           myoglobin: float = None, troponin_t: float = None, 
                           bnp: float = None) -> None:
        """Add cardiac marker results"""
        results = {}
        references = {}
        
        if troponin_i is not None:
            results['Troponin_I'] = troponin_i
            references['Troponin_I'] = '<0.04 ng/mL'
        
        if troponin_t is not None:
            results['Troponin_T'] = troponin_t
            references['Troponin_T'] = '<0.014 ng/mL'
            
        if ck_mb is not None:
            results['CK_MB'] = ck_mb
            references['CK_MB'] = '<6.3 ng/mL'
            
        if myoglobin is not None:
            results['Myoglobin'] = myoglobin
            references['Myoglobin'] = '25-72 ng/mL'
            
        if bnp is not None:
            results['BNP'] = bnp
            references['BNP'] = '<100 pg/mL'
        
        for analyte, value in results.items():
            self.add_result(analyte, value, references[analyte])
            
        self._evaluate_cardiac_flags()
    
    def add_crp_results(self, crp: float) -> None:
        """Add C-Reactive Protein results"""
        self.add_result('CRP', crp, '<3.0 mg/L')
        
        # CRP evaluation (inflammation marker)
        if crp > 3.0:
            self.abnormal_flags['CRP'] = 'H' if crp <= 10.0 else 'Critical'
    

    def _evaluate_cbc_flags(self) -> None:
        """Evaluate CBC results and set appropriate flags"""
        if 'WBC' in self.test_results:
            wbc = self.test_results['WBC']
            if wbc < 4.0:
                self.abnormal_flags['WBC'] = 'L'
            elif wbc > 11.0:
                self.abnormal_flags['WBC'] = 'H'
                if wbc > 20.0:
                    self.abnormal_flags['WBC'] = 'Critical'
        
        if 'Platelets' in self.test_results:
            plt = self.test_results['Platelets']
            if plt < 150:
                self.abnormal_flags['Platelets'] = 'L'
                if plt < 50:
                    self.abnormal_flags['Platelets'] = 'Critical'
            elif plt > 450:
                self.abnormal_flags['Platelets'] = 'H'
    
    def _evaluate_cmp_flags(self) -> None:
        """Evaluate CMP results and set appropriate flags"""
        if 'Potassium' in self.test_results:
            k = self.test_results['Potassium']
            if k < 3.5:
                self.abnormal_flags['Potassium'] = 'L'
                if k < 3.0:
                    self.abnormal_flags['Potassium'] = 'Critical'
            elif k > 5.0:
                self.abnormal_flags['Potassium'] = 'H'
                if k > 6.0:
                    self.abnormal_flags['Potassium'] = 'Critical'
        
        if 'Creatinine' in self.test_results:
            cr = self.test_results['Creatinine']
            if cr > 1.2:
                self.abnormal_flags['Creatinine'] = 'H'
                if cr > 3.0:
                    self.abnormal_flags['Creatinine'] = 'Critical'
    
    def _evaluate_abg_flags(self) -> None:
        """Evaluate ABG results and set appropriate flags"""
        # pH evaluation
        if 'pH' in self.test_results:
            ph = self.test_results['pH']
            if ph < 7.35:
                self.abnormal_flags['pH'] = 'L' if ph >= 7.25 else 'Critical'
            elif ph > 7.45:
                self.abnormal_flags['pH'] = 'H' if ph <= 7.55 else 'Critical'
        
        # pCO2 evaluation
        if 'pCO2' in self.test_results:
            pco2 = self.test_results['pCO2']
            if pco2 < 35:
                self.abnormal_flags['pCO2'] = 'L' if pco2 >= 25 else 'Critical'
            elif pco2 > 45:
                self.abnormal_flags['pCO2'] = 'H' if pco2 <= 60 else 'Critical'
        
        # pO2 evaluation
        if 'pO2' in self.test_results:
            po2 = self.test_results['pO2']
            if po2 < 80:
                self.abnormal_flags['pO2'] = 'L' if po2 >= 60 else 'Critical'
            elif po2 > 100:
                self.abnormal_flags['pO2'] = 'H'
        
        # O2 Saturation evaluation
        if 'O2_Sat' in self.test_results:
            o2_sat = self.test_results['O2_Sat']
            if o2_sat < 95:
                self.abnormal_flags['O2_Sat'] = 'L' if o2_sat >= 90 else 'Critical'
    
    def _evaluate_cardiac_flags(self) -> None:
        """Evaluate cardiac marker results and set appropriate flags"""
        # Troponin I evaluation (cardiac injury marker)
        if 'Troponin_I' in self.test_results:
            troponin_i = self.test_results['Troponin_I']
            if troponin_i > 0.04:
                self.abnormal_flags['Troponin_I'] = 'H' if troponin_i <= 0.4 else 'Critical'
        
        # Troponin T evaluation (cardiac injury marker)
        if 'Troponin_T' in self.test_results:
            troponin_t = self.test_results['Troponin_T']
            if troponin_t > 0.014:
                self.abnormal_flags['Troponin_T'] = 'H' if troponin_t <= 0.1 else 'Critical'
        
        # CK-MB evaluation (cardiac muscle damage)
        if 'CK_MB' in self.test_results:
            ck_mb = self.test_results['CK_MB']
            if ck_mb > 6.3:
                self.abnormal_flags['CK_MB'] = 'H' if ck_mb <= 25 else 'Critical'
        
        # Myoglobin evaluation (early cardiac marker)
        if 'Myoglobin' in self.test_results:
            myoglobin = self.test_results['Myoglobin']
            if myoglobin < 25 or myoglobin > 72:
                self.abnormal_flags['Myoglobin'] = 'H' if myoglobin <= 200 else 'Critical'
        
        # BNP evaluation (heart failure marker)
        if 'BNP' in self.test_results:
            bnp = self.test_results['BNP']
            if bnp > 100:
                self.abnormal_flags['BNP'] = 'H' if bnp <= 400 else 'Critical'
    
    def has_critical_values(self) -> bool:
        """Check if any results have critical values"""
        return 'Critical' in self.abnormal_flags.values()
    
    def get_abnormal_results(self) -> Dict[str, Any]:
        """Get only abnormal results with flags"""
        abnormal = {}
        for analyte, flag in self.abnormal_flags.items():
            if flag in ['H', 'L', 'Critical']:
                abnormal[analyte] = {
                    'value': self.test_results.get(analyte),
                    'flag': flag,
                    'reference': self.reference_ranges.get(analyte, '')
                }
        return abnormal
    
    def requires_immediate_notification(self) -> bool:
        """Check if results require immediate clinical notification"""
        return self.has_critical_values() or self.result_interpretation == TestResult.CRITICAL
    
    def calculate_turnaround_time_from_collection(self) -> Optional[float]:
        """Calculate turnaround time from specimen collection"""
        if self.collection_time and self.completion_time:
            return self.completion_time - self.collection_time
        return None
    
    def get_blood_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive blood test report"""
        base_summary = self.get_test_summary()
        
        blood_specific = {
            "test_panel": self.test_panel,
            "specimen_type": self.specimen_type,
            "volume_required_ml": self.volume_required,
            "collection_site": self.collection_site,
            "collected_by": self.collected_by,
            "requires_fasting": self.requires_fasting,
            "specimen_quality": {
                "hemolyzed": self.hemolyzed,
                "lipemic": self.lipemic,
                "icteric": self.icteric,
                "clotted": self.clotted,
                "quality_passed": self.quality_control_passed
            },
            "test_results": self.test_results,
            "reference_ranges": self.reference_ranges,
            "abnormal_flags": self.abnormal_flags,
            "abnormal_results": self.get_abnormal_results(),
            "has_critical_values": self.has_critical_values(),
            "requires_immediate_notification": self.requires_immediate_notification(),
            "collection_to_result_time": self.calculate_turnaround_time_from_collection()
        }
        
        return {**base_summary, **blood_specific}
    
    def get_critical_value_alert(self) -> Optional[Dict[str, Any]]:
        """Generate critical value alert if needed"""
        if not self.has_critical_values():
            return None
            
        critical_results = {k: v for k, v in self.abnormal_flags.items() if v == 'Critical'}
        
        return {
            "alert_type": "CRITICAL_VALUE",
            "test_id": self.test_id,
            "patient_id": self.patient_id,
            "test_panel": self.test_panel,
            "critical_results": critical_results,
            "values": {k: self.test_results.get(k) for k in critical_results.keys()},
            "ordering_doctor": self.ordering_doctor_id,
            "completion_time": self.completion_time,
            "requires_immediate_callback": True
        }