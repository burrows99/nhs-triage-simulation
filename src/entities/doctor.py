import attr
from typing import Optional, List, Dict, Any
from .patient import Patient
from ..enums.Triage import Priority
from .testing.base_test import TestPriority
from .testing.blood_test import BloodTestType, BloodTest

from .testing.mri_test import MRITest
from ..triage_systems.manchester_triage_system import ManchesterTriageSystem

@attr.s(auto_attribs=True)
class Doctor:
    """Doctor resource with specialization and current assignment"""
    id: int
    name: str
    specialization: str
    current_patient: Optional[Patient] = None
    busy: bool = False
    total_patients_treated: int = 0
    
    # MTS instance for condition assessment
    _mts: ManchesterTriageSystem = attr.ib(factory=lambda: ManchesterTriageSystem(), init=False)
    
    def diagnose(self, patient: Patient) -> Dict[str, Any]:
        """Analyze patient and recommend diagnostic tests based on clinical presentation"""
        patient_summary = patient.get_clinical_summary()
        recommended_tests = []
        
        # Get patient details
        condition = patient_summary.get('chief_complaint', '').lower()
        symptoms = [s.lower() for s in patient_summary.get('presenting_symptoms', [])]
        priority = patient_summary.get('triage_priority', 'GREEN')
        vital_signs = patient_summary.get('vital_signs_on_arrival', {})
        
        # Use MTS condition profiles for enhanced assessment
        mts_symptoms = self._get_mts_symptom_profile(patient)
        severity_assessment = self._assess_condition_severity(condition, mts_symptoms)
        
        # Mandatory tests for high-priority patients
        if priority in [Priority.RED.name, Priority.ORANGE.name]:
            recommended_tests.extend(self._get_critical_care_tests(condition, symptoms, vital_signs, patient))
        
        # Condition-specific test recommendations
        recommended_tests.extend(self._get_condition_specific_tests(condition, symptoms, patient))
        
        # Symptom-based test recommendations
        recommended_tests.extend(self._get_symptom_based_tests(symptoms, patient))
        
        # Enhance recommendations using MTS severity assessment
        recommended_tests.extend(self._get_mts_enhanced_tests(severity_assessment, condition, patient))
        
        # Add only one random test (MRI or Blood test)
        import random
        
        # Randomly choose between MRI or Blood test
        test_choice = random.choice(['MRI', 'BLOOD'])
        
        if test_choice == 'MRI':
            # Create a random MRI test
            mri_test = MRITest(
                test_id=f"MRI_{patient.id}_{random.randint(1000, 9999)}",
                test_name="Diagnostic MRI",
                test_type="MRITest",
                patient_id=str(patient.id),
                ordering_doctor_id=str(self.id),
                ordered_time=0.0,
                body_part=random.choice(["BRAIN", "SPINE_LUMBAR", "ABDOMEN", "CARDIAC"]),
                priority=TestPriority.ROUTINE
            )
            patient.add_test_result(mri_test)
            unique_tests = [mri_test]
        else:
            # Create a random Blood test
            blood_test = BloodTest(
                test_id=f"BLOOD_{patient.id}_{random.randint(1000, 9999)}",
                test_name="Blood Panel",
                test_type="BloodTest",
                patient_id=str(patient.id),
                ordering_doctor_id=str(self.id),
                ordered_time=0.0,
                test_panel=random.choice([BloodTestType.CBC, BloodTestType.CMP, BloodTestType.ABG, BloodTestType.CARDIAC_MARKERS]),
                priority=TestPriority.ROUTINE
            )
            patient.add_test_result(blood_test)
            unique_tests = [blood_test]
        
        return {
            'patient_id': patient.id,
            'doctor_id': self.id,
            'doctor_name': self.name,
            'specialization': self.specialization,
            'patient_priority': priority,
            'chief_complaint': condition,
            'recommended_tests': unique_tests,
            'total_tests_recommended': len(unique_tests),
            'critical_care_required': priority in [Priority.RED.name, Priority.ORANGE.name],
            'diagnostic_reasoning': self._generate_diagnostic_reasoning(condition, symptoms, priority),
            'mts_assessment': {
                'symptom_profile': mts_symptoms,
                'severity_assessment': severity_assessment,
                'mts_enhanced': True
            },
            'tests_added_to_patient': True
        }
    
    def _remove_duplicate_tests(self, tests: List[Any]) -> List[Any]:
        """Remove duplicate tests based on test type and name"""
        unique_tests = []
        seen = set()
        
        for test in tests:
            # Create a unique key based on test type and name
            test_key = f"{test.__class__.__name__}_{test.test_name}"
            if test_key not in seen:
                unique_tests.append(test)
                seen.add(test_key)
        
        return unique_tests
    
    def _get_mts_enhanced_tests(self, severity_assessment: Dict[str, Any], 
                               condition: str, patient: Patient) -> List[Any]:
        """Get additional tests based on MTS severity assessment and fuzzy logic"""
        tests = []
        current_time = 0.0
        
        # Extract MTS-specific data
        mts_firings = severity_assessment.get('mts_firings', {})
        fuzzy_assessments = severity_assessment.get('indicators', {}).get('fuzzy_assessments', {})
        mts_category = severity_assessment.get('mts_category', 'standard')
        
        # MTS fuzzy logic-driven test recommendations
        tests.extend(self._get_fuzzy_logic_tests(mts_firings, fuzzy_assessments, patient, current_time))
        
        # Traditional severity-based tests
        if severity_assessment['requires_immediate_workup']:
            # Arterial Blood Gas for critical patients
            abg_test = BloodTest(
                test_id=f"ABG_{patient.id}_{len(tests)+1}",
                test_name="Arterial Blood Gas",
                test_type="BloodTest",
                patient_id=str(patient.id),
                ordering_doctor_id=str(self.id),
                ordered_time=current_time,
                test_panel="ABG",
                priority=TestPriority.STAT
            )
            abg_test.notes = f"Critical severity (MTS: {mts_category}, score: {severity_assessment['severity_score']:.1f})"
            tests.append(abg_test)
            
        elif severity_assessment['requires_extended_workup']:
            # Inflammatory Markers for moderate severity
            crp_test = BloodTest(
                test_id=f"CRP_{patient.id}_{len(tests)+1}",
                test_name="Inflammatory Markers",
                test_type="BloodTest",
                patient_id=str(patient.id),
                ordering_doctor_id=str(self.id),
                ordered_time=current_time,
                test_panel=BloodTestType.CRP,
                priority=TestPriority.URGENT
            )
            crp_test.notes = f"Extended workup (MTS: {mts_category}, score: {severity_assessment['severity_score']:.1f})"
            tests.append(crp_test)
        
        return tests
    
    def _get_fuzzy_logic_tests(self, mts_firings: Dict, fuzzy_assessments: Dict[str, float], 
                              patient: Patient, current_time: float) -> List[Any]:
        """Generate test recommendations based on MTS fuzzy rule firings"""
        tests = []
        
        # High RED priority firings - immediate life-threatening conditions
        red_firings = mts_firings.get(Priority.RED, [])
        if red_firings and max(red_firings) > 0.7:
            # Critical oxygenation issues - use blood test for assessment
            if fuzzy_assessments.get('o2_inadequate', 0) > 0.5:
                # Immediate blood gas analysis
                blood_gas = BloodTest(
                    test_id=f"ABG_{patient.id}_{len(tests)+1}",
                    test_name="Arterial Blood Gas",
                    test_type="BloodTest",
                    patient_id=str(patient.id),
                    ordering_doctor_id=str(self.id),
                    ordered_time=current_time,
                    test_panel=BloodTestType.ABG,
                    priority=TestPriority.STAT
                )
                blood_gas.notes = f"Critical oxygenation (O2 inadequate membership: {fuzzy_assessments.get('o2_inadequate', 0):.2f})"
                tests.append(blood_gas)
            
            # Severe consciousness impairment - use MRI for neurological assessment
            if fuzzy_assessments.get('consciousness_unresponsive', 0) > 0.5:
                # Immediate neurological MRI
                neuro_mri = MRITest(
                    test_id=f"NEURO_MRI_{patient.id}_{len(tests)+1}",
                    test_name="Emergency Brain MRI",
                    test_type="MRITest",
                    patient_id=str(patient.id),
                    ordering_doctor_id=str(self.id),
                    ordered_time=current_time,
                    body_part="BRAIN",
                    priority=TestPriority.STAT
                )
                neuro_mri.notes = f"Unresponsive state (consciousness membership: {fuzzy_assessments.get('consciousness_unresponsive', 0):.2f})"
                tests.append(neuro_mri)
        
        # High ORANGE priority firings - very urgent conditions
        orange_firings = mts_firings.get(Priority.ORANGE, [])
        if orange_firings and max(orange_firings) > 0.6:
            # Severe pain assessment
            if fuzzy_assessments.get('pain_severe', 0) > 0.6:
                # Pain management workup
                pain_assess = BloodTest(
                    test_id=f"PAIN_WORKUP_{patient.id}_{len(tests)+1}",
                    test_name="Pain Management Workup",
                    test_type="BloodTest",
                    patient_id=str(patient.id),
                    ordering_doctor_id=str(self.id),
                    ordered_time=current_time,
                    test_panel=BloodTestType.CMP,
                    priority=TestPriority.URGENT
                )
                pain_assess.notes = f"Severe pain (pain severe membership: {fuzzy_assessments.get('pain_severe', 0):.2f})"
                tests.append(pain_assess)
        
        # Cardiac instability based on fuzzy heart rate assessment - use blood test for cardiac markers
        if (fuzzy_assessments.get('hr_vigorous', 0) > 0.5 or 
            fuzzy_assessments.get('hr_very_vigorous', 0) > 0.3):
            # Cardiac markers blood test
            cardiac_markers = BloodTest(
                test_id=f"CARDIAC_MARKERS_{patient.id}_{len(tests)+1}",
                test_name="Cardiac Markers",
                test_type="BloodTest",
                patient_id=str(patient.id),
                ordering_doctor_id=str(self.id),
                ordered_time=current_time,
                test_panel=BloodTestType.CARDIAC_MARKERS,
                priority=TestPriority.URGENT
            )
            hr_vigorous = fuzzy_assessments.get('hr_vigorous', 0)
            hr_very_vigorous = fuzzy_assessments.get('hr_very_vigorous', 0)
            cardiac_markers.notes = f"Cardiac instability (HR vigorous: {hr_vigorous:.2f}, very vigorous: {hr_very_vigorous:.2f})"
            tests.append(cardiac_markers)
        
        return tests
    
    def _get_condition_specific_tests(self, condition: str, symptoms: List[str], patient: Patient) -> List[Any]:
        """Get tests based on specific medical conditions"""
        tests = []
        current_time = 0.0
        
        # Chest pain workup - use blood test for cardiac markers
        if 'chest_pain' in condition:
            cardiac_markers = BloodTest(
                test_id=f"CARDIAC_MARKERS_{patient.id}_{len(tests)+1}",
                test_name="Cardiac Markers",
                test_type="BloodTest",
                patient_id=str(patient.id),
                ordering_doctor_id=str(self.id),
                ordered_time=current_time,
                test_panel=BloodTestType.CARDIAC_MARKERS,
                priority=TestPriority.URGENT
            )
            cardiac_markers.notes = "Evaluate for pneumothorax, pneumonia, or cardiac enlargement"
            tests.append(cardiac_markers)
        
        # Add other condition-specific tests as needed
        return tests
    
    def _get_symptom_based_tests(self, symptoms: List[str], patient: Patient) -> List[Any]:
        """Get tests based on specific symptoms"""
        tests = []
        current_time = 0.0
        
        # Fever workup - use blood test for infection markers
        if any(symptom in ['fever', 'high temperature', 'pyrexia'] for symptom in symptoms):
            # Blood test for infection markers
            infection_markers = BloodTest(
                test_id=f"INFECTION_MARKERS_{patient.id}_{len(tests)+1}",
                test_name="Infection Markers",
                test_type="BloodTest",
                patient_id=str(patient.id),
                ordering_doctor_id=str(self.id),
                ordered_time=current_time,
                test_panel=BloodTestType.CRP,
                priority=TestPriority.ROUTINE
            )
            infection_markers.notes = "Fever workup - infection evaluation"
            tests.append(infection_markers)
        
        return tests
    
    def _get_critical_care_tests(self, condition: str, symptoms: List[str], vital_signs: Dict, patient: Patient) -> List[Any]:
        """Get mandatory tests for RED/ORANGE priority patients"""
        tests = []
        current_time = 0.0  # This should be passed from the simulation
        
        # Basic critical care workup
        # Complete Blood Count
        cbc_test = BloodTest(
            test_id=f"CBC_{patient.id}_{len(tests)+1}",
            test_name="Complete Blood Count",
            test_type="BloodTest",
            patient_id=str(patient.id),
            ordering_doctor_id=str(self.id),
            ordered_time=current_time,
            test_panel=BloodTestType.CBC,
            priority=TestPriority.STAT
        )
        cbc_test.notes = "Critical care baseline assessment"
        tests.append(cbc_test)
        
        # Comprehensive Metabolic Panel
        cmp_test = BloodTest(
            test_id=f"CMP_{patient.id}_{len(tests)+1}",
            test_name="Comprehensive Metabolic Panel",
            test_type="BloodTest",
            patient_id=str(patient.id),
            ordering_doctor_id=str(self.id),
            ordered_time=current_time,
            test_panel=BloodTestType.CMP,
            priority=TestPriority.STAT
        )
        cmp_test.notes = "Electrolyte and organ function assessment"
        tests.append(cmp_test)
        
        # Cardiac-specific critical tests - use blood test for cardiac markers
        if any(cardiac in condition for cardiac in ['chest_pain', 'cardiac', 'heart']):
            troponin_test = BloodTest(
                test_id=f"TROPONIN_{patient.id}_{len(tests)+1}",
                test_name="Troponin",
                test_type="BloodTest",
                patient_id=str(patient.id),
                ordering_doctor_id=str(self.id),
                ordered_time=current_time,
                test_panel=BloodTestType.TROPONIN,
                priority=TestPriority.STAT
            )
            troponin_test.notes = "Rule out myocardial infarction"
            tests.append(troponin_test)
        
        # Neurological critical tests - use MRI for brain imaging
        if any(neuro in condition for neuro in ['stroke', 'head', 'neurological', 'seizure']):
            brain_mri = MRITest(
                test_id=f"BRAIN_MRI_{patient.id}_{len(tests)+1}",
                test_name="Brain MRI",
                test_type="MRITest",
                patient_id=str(patient.id),
                ordering_doctor_id=str(self.id),
                ordered_time=current_time,
                body_part="BRAIN",
                priority=TestPriority.STAT
            )
            brain_mri.notes = "Rule out intracranial hemorrhage or mass effect"
            tests.append(brain_mri)
        
        return tests
        
    def _generate_diagnostic_reasoning(self, condition: str, symptoms: List[str], priority: str) -> str:
        """Generate clinical reasoning for test recommendations"""
        reasoning_parts = []
        
        if priority in [Priority.RED.name, Priority.ORANGE.name]:
            reasoning_parts.append(f"High-priority ({priority}) patient requires immediate diagnostic workup.")
        
        if 'chest_pain' in condition:
            reasoning_parts.append("Chest pain requires cardiac and pulmonary evaluation to rule out life-threatening conditions.")
        
        if 'abdominal_pain' in condition:
            reasoning_parts.append("Abdominal pain workup to exclude surgical emergencies and organ dysfunction.")
        
        if any(neuro in condition for neuro in ['stroke', 'headache', 'neurological']):
            reasoning_parts.append("Neurological symptoms require urgent imaging to rule out stroke or intracranial pathology.")
        
        if any('fever' in symptom for symptom in symptoms):
            reasoning_parts.append("Fever workup includes infection screening and source identification.")
        
        if not reasoning_parts:
            reasoning_parts.append("Standard diagnostic workup based on clinical presentation and symptoms.")
        
        return " ".join(reasoning_parts)
    
    def _get_mts_symptom_profile(self, patient: Patient) -> Dict[str, Any]:
        """Extract MTS symptom profile for enhanced diagnostic assessment"""
        return self._mts._extract_symptoms_from_patient(patient)
    
    def _assess_condition_severity(self, condition: str, mts_symptoms: Dict[str, Any]) -> Dict[str, Any]:
        """Assess condition severity using MTS fuzzy logic principles"""
        # Use MTS fuzzy logic for more accurate assessment
        mts_firings = self._mts.compute_firings(mts_symptoms)
        mts_category, mts_wait_time = self._mts.select_category(mts_firings)
        
        # Calculate fuzzy membership values for key indicators
        fuzzy_assessments = self._calculate_fuzzy_memberships(mts_symptoms)
        
        severity_indicators = {
            'pain_level': mts_symptoms.get('pain', 0),
            'onset_urgency': mts_symptoms.get('onset', 0),
            'vital_instability': self._calculate_vital_instability_fuzzy(mts_symptoms),
            'neurological_involvement': mts_symptoms.get('neurological deficit', 0),
            'cardiac_involvement': mts_symptoms.get('heart rate', 0),
            'respiratory_involvement': mts_symptoms.get('shortness of breath', 0),
            'mts_priority_score': self._convert_mts_priority_to_score(mts_category),
            'fuzzy_assessments': fuzzy_assessments
        }
        
        # Enhanced severity calculation using MTS fuzzy logic
        severity_score = self._calculate_enhanced_severity_score(severity_indicators, mts_firings)
        
        return {
            'severity_score': min(severity_score, 10.0),
            'severity_category': self._categorize_severity(severity_score),
            'indicators': severity_indicators,
            'requires_immediate_workup': severity_score >= 7.0 or mts_category in ['immediate', 'very urgent'],
            'requires_extended_workup': severity_score >= 5.0 or mts_category in ['urgent'],
            'mts_category': mts_category,
            'mts_wait_time': mts_wait_time,
            'mts_firings': mts_firings
        }
    
    def _calculate_vital_instability(self, mts_symptoms: Dict[str, Any]) -> float:
        """Calculate vital sign instability score based on MTS parameters"""
        instability_score = 0.0
        
        # Heart rate instability
        hr = mts_symptoms.get('heart rate', 0)
        if hr > 130 or hr < 50:  # Very abnormal
            instability_score += 3.0
        elif hr > 110 or hr < 60:  # Moderately abnormal
            instability_score += 1.5
        
        # Blood pressure instability
        bp = mts_symptoms.get('blood pressure', 100)
        if bp < 80 or bp > 180:  # Very abnormal
            instability_score += 3.0
        elif bp < 90 or bp > 140:  # Moderately abnormal
            instability_score += 1.5
        
        # Oxygenation issues
        o2 = mts_symptoms.get('oxygenation', 100)
        if o2 < 80:  # Critical
            instability_score += 4.0
        elif o2 < 90:  # Concerning
            instability_score += 2.0
        
        # Consciousness level
        consciousness = mts_symptoms.get('conscious level', 15)
        if consciousness < 5:  # Severely reduced
            instability_score += 4.0
        elif consciousness < 10:  # Moderately reduced
            instability_score += 2.0
        
        return min(instability_score, 10.0)
    
    def _calculate_fuzzy_memberships(self, mts_symptoms: Dict[str, Any]) -> Dict[str, float]:
        """Calculate fuzzy membership values for key clinical indicators using MTS"""
        fuzzy_assessments = {}
        
        try:
            # Pain assessment using MTS fuzzy logic
            pain_value = mts_symptoms.get('pain', 0)
            fuzzy_assessments['pain_severe'] = self._mts.get_mf('pain', 'severe', pain_value)
            fuzzy_assessments['pain_moderate'] = self._mts.get_mf('pain', 'moderate', pain_value)
            
            # Consciousness level assessment
            consciousness = mts_symptoms.get('conscious level', 15)
            fuzzy_assessments['consciousness_reduced'] = self._mts.get_mf('conscious level', 'reduced', consciousness)
            fuzzy_assessments['consciousness_unresponsive'] = self._mts.get_mf('conscious level', 'un-responsive', consciousness)
            
            # Heart rate assessment
            hr = mts_symptoms.get('heart rate', 80)
            fuzzy_assessments['hr_vigorous'] = self._mts.get_mf('heart rate', 'vigorous', hr)
            fuzzy_assessments['hr_very_vigorous'] = self._mts.get_mf('heart rate', 'very vigorous', hr)
            
            # Blood pressure assessment
            bp = mts_symptoms.get('blood pressure', 120)
            fuzzy_assessments['bp_low'] = self._mts.get_mf('blood pressure', 'low', bp)
            
            # Oxygenation assessment
            o2 = mts_symptoms.get('oxygenation', 100)
            fuzzy_assessments['o2_inadequate'] = self._mts.get_mf('oxygenation', 'inadequate', o2)
            fuzzy_assessments['o2_very_low'] = self._mts.get_mf('oxygenation', 'adeq. but very low', o2)
            
        except (ValueError, KeyError) as e:
            # Fallback to basic assessments if MTS fuzzy variables are not available
            fuzzy_assessments['error'] = str(e)
            
        return fuzzy_assessments
    
    def _calculate_vital_instability_fuzzy(self, mts_symptoms: Dict[str, Any]) -> float:
        """Calculate vital instability using MTS fuzzy logic"""
        instability_score = 0.0
        
        try:
            # Use MTS fuzzy membership functions for more accurate assessment
            hr = mts_symptoms.get('heart rate', 80)
            bp = mts_symptoms.get('blood pressure', 120)
            o2 = mts_symptoms.get('oxygenation', 100)
            consciousness = mts_symptoms.get('conscious level', 15)
            
            # Heart rate instability using fuzzy logic
            hr_vigorous = self._mts.get_mf('heart rate', 'vigorous', hr)
            hr_very_vigorous = self._mts.get_mf('heart rate', 'very vigorous', hr)
            instability_score += max(hr_vigorous * 2.0, hr_very_vigorous * 4.0)
            
            # Blood pressure instability
            bp_low = self._mts.get_mf('blood pressure', 'low', bp)
            instability_score += bp_low * 3.0
            
            # Oxygenation issues
            o2_inadequate = self._mts.get_mf('oxygenation', 'inadequate', o2)
            o2_very_low = self._mts.get_mf('oxygenation', 'adeq. but very low', o2)
            instability_score += max(o2_inadequate * 4.0, o2_very_low * 2.0)
            
            # Consciousness level
            consciousness_reduced = self._mts.get_mf('conscious level', 'reduced', consciousness)
            consciousness_unresponsive = self._mts.get_mf('conscious level', 'un-responsive', consciousness)
            instability_score += max(consciousness_reduced * 2.0, consciousness_unresponsive * 4.0)
            
        except (ValueError, KeyError):
            # Fallback to original calculation if MTS fuzzy variables fail
            return self._calculate_vital_instability(mts_symptoms)
            
        return min(instability_score, 10.0)
    
    def _convert_mts_priority_to_score(self, mts_category: str) -> float:
        """Convert MTS priority category to numerical score"""
        priority_scores = {
            'immediate': 10.0,
            'very urgent': 8.0,
            'urgent': 6.0,
            'standard': 4.0,
            'non-urgent': 2.0
        }
        return priority_scores.get(mts_category, 3.0)
    
    def _calculate_enhanced_severity_score(self, severity_indicators: Dict[str, Any], 
                                         mts_firings: Dict) -> float:
        """Calculate enhanced severity score using MTS fuzzy rule firings"""
        # Base severity calculation
        base_score = sum([
            severity_indicators['pain_level'] * 0.15,
            severity_indicators['onset_urgency'] * 0.2,
            severity_indicators['vital_instability'] * 0.25,
            severity_indicators['neurological_involvement'] * 0.1,
            severity_indicators['cardiac_involvement'] * 0.05,
            severity_indicators['respiratory_involvement'] * 0.05
        ])
        
        # MTS priority influence (20% weight)
        mts_score = severity_indicators['mts_priority_score'] * 0.2
        
        # Fuzzy rule firing influence (additional boost for critical conditions)
        firing_boost = 0.0
        if mts_firings:
            # Check for immediate (RED) priority firings
            red_firings = mts_firings.get(Priority.RED, [])
            if red_firings and max(red_firings) > 0.5:
                firing_boost += 2.0  # Significant boost for high RED firing
            
            # Check for very urgent (ORANGE) priority firings
            orange_firings = mts_firings.get(Priority.ORANGE, [])
            if orange_firings and max(orange_firings) > 0.5:
                firing_boost += 1.0  # Moderate boost for high ORANGE firing
        
        total_score = base_score + mts_score + firing_boost
        return min(total_score, 10.0)
    
    def _categorize_severity(self, severity_score: float) -> str:
        """Categorize severity based on score"""
        if severity_score >= 8.0:
            return "CRITICAL"
        elif severity_score >= 6.0:
            return "SEVERE"
        elif severity_score >= 4.0:
            return "MODERATE"
        elif severity_score >= 2.0:
            return "MILD"
        else:
            return "MINIMAL"
    
    def _enhance_test_recommendations_with_mts(self, tests: List[Dict[str, Any]], 
                                             severity_assessment: Dict[str, Any], 
                                             condition: str) -> List[Dict[str, Any]]:
        """Enhance test recommendations using MTS severity assessment"""
        enhanced_tests = tests.copy()
        
        # Add severity-based additional tests
        if severity_assessment['requires_immediate_workup']:
            # Add comprehensive critical care workup
            enhanced_tests.extend([
                {
                    'test_type': BloodTest.__name__,
                    'test_name': 'Arterial Blood Gas',
                    'test_panel': 'ABG',
                    'priority': TestPriority.STAT.value,
                    'reason': f"Critical severity assessment (score: {severity_assessment['severity_score']:.1f})"
                },
                {
                    'test_type': BasicTest.__name__,
                    'test_name': 'Continuous Monitoring',
                    'basic_test_type': 'VITAL_SIGNS_MONITORING',
                    'priority': TestPriority.STAT.value,
                    'reason': 'Vital instability detected'
                }
            ])
        
        elif severity_assessment['requires_extended_workup']:
            # Add extended diagnostic workup
            enhanced_tests.append({
                'test_type': BloodTest.__name__,
                'test_name': 'Inflammatory Markers',
                'test_panel': BloodTestType.CRP,
                'priority': TestPriority.URGENT.value,
                'reason': f"Moderate severity assessment (score: {severity_assessment['severity_score']:.1f})"
            })
        
        # Add condition-specific enhancements based on MTS profiles
        if 'cardiac' in condition or 'chest_pain' in condition:
            if severity_assessment['indicators']['cardiac_involvement'] > 5:
                enhanced_tests.append({
                    'test_type': 'IMAGING',
                    'test_name': 'Echocardiogram',
                    'modality': 'ULTRASOUND',
                    'body_part': 'CARDIAC',
                    'priority': TestPriority.URGENT.value,
                    'reason': 'Significant cardiac involvement detected'
                })
        
        return enhanced_tests