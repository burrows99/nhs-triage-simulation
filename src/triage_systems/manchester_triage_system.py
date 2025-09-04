import numpy as np
from .base import BaseTriageSystem
from ..entities.patient import Patient
from ..entities.sub_entities.triage_assessment import TriageAssessment
from ..enums.Triage import Priority

class ManchesterTriageSystem(BaseTriageSystem):
    """Manchester Triage System implementation using fuzzy logic"""
    
    def __init__(self, system_id: str = "MTS_001"):
        self.system_id = system_id
        self.assessments_completed = 0
        
        # Mapping from MTS priority names to system priorities
        self.priority_mapping = {
            'immediate': Priority.RED,
            'very urgent': Priority.ORANGE,
            'urgent': Priority.YELLOW,
            'standard': Priority.GREEN,
            'non-urgent': Priority.BLUE
        }
        
        # MTS priority names
        self.names = {
            Priority.RED: 'immediate',
            Priority.ORANGE: 'very urgent',
            Priority.YELLOW: 'urgent',
            Priority.GREEN: 'standard',
            Priority.BLUE: 'non-urgent',
        }
        
        # MTS priority weights
        self.weights = {
            Priority.RED: 1.0,
            Priority.ORANGE: 0.8,
            Priority.YELLOW: 0.6,
            Priority.GREEN: 0.4,
        }
        
        # MTS maximum wait times
        self.max_times = {
            Priority.RED: 0,
            Priority.ORANGE: 10,
            Priority.YELLOW: 60,
            Priority.GREEN: 120,
            Priority.BLUE: 240,
        }
        
        # Fuzzy variable definitions
        self.fuzzy_vars = {
            'oxygenation': {
                'inadequate': [0, 0, 70, 80],
                'adeq. but very low': [70, 80, 85, 90],
                'adeq. but low': [85, 90, 95, 100],
                'adequate': [95, 100, 100, 100]
            },
            'sweating': {
                'little to none': [0, 0, 2, 4],
                'some': [2, 4, 5, 7],
                'significant': [5, 7, 8, 9],
                'exceptional': [8, 9, 10, 10]
            },
            'color': {
                'pale': [0, 0, 3, 5],
                'somewhat lacking': [3, 5, 7, 9],
                'full': [7, 9, 10, 10]
            },
            'heart rate': {
                'light': [0, 30, 50, 70],
                'moderate': [50, 70, 90, 110],
                'vigorous': [90, 110, 130, 150],
                'very vigorous': [130, 150, 200, 200]
            },
            'blood pressure': {
                'low': [0, 0, 80, 100],
                'normal': [80, 100, 120, 140],
                'high/normal': [120, 140, 200, 200]
            },
            'conscious level': {
                'un-responsive': [0, 0, 3, 5],
                'reduced': [3, 5, 7, 9],
                'slightly reduced': [7, 9, 12, 14],
                'normal': [12, 14, 15, 15]
            },
            'pain': {
                'little to none': [0, 0, 2, 4],
                'mild': [2, 4, 4, 6],
                'moderate': [4, 6, 6, 8],
                'severe': [6, 8, 10, 10]
            },
            'vaginal bleeding': {
                'little to none': [0, 0, 2, 4],
                'light': [2, 4, 6, 8],
                'heavy': [6, 8, 10, 10]
            },
            'pregnancy': {
                'impossible': [0, 0, 1, 2],
                'slightly possible': [1, 2, 3, 4],
                'unsure': [3, 4, 5, 6],
                'early stage': [5, 6, 7, 8],
                'late stage': [7, 8, 10, 10]
            },
            'skin temperature': {
                'cold': [0, 0, 2, 4],
                'normal': [2, 4, 5, 6],
                'warm': [5, 6, 7, 8],
                'hot': [7, 8, 9, 10],
                'very hot': [9, 10, 10, 10]
            },
            'onset': {
                'distant': [0, 0, 2, 4],
                'recent': [2, 4, 4, 6],
                'acute': [4, 6, 6, 8],
                'rapid': [6, 8, 8, 10],
                'abrupt': [8, 10, 10, 10]
            },
            'onset2': {
                'distant': [0, 0, 2, 4],
                'recent': [2, 4, 4, 6],
                'acute': [4, 6, 6, 8],
                'rapid': [6, 8, 8, 10],
                'abrupt': [8, 10, 10, 10]
            },
            'stool color': {
                'light brown': [0, 0, 2, 4],
                'brown': [2, 4, 6, 8],
                'dark brown': [6, 8, 10, 12],
                'black': [10, 12, 14, 16],
                'dark black': [14, 16, 20, 20]
            },
            'vomiting (no blood)': {
                'little to none': [0, 0, 2, 4],
                'intermittent': [2, 4, 5, 7],
                'frequent': [5, 7, 8, 10],
                'continuous': [8, 10, 10, 10]
            },
            'crying': {
                'little to none': [0, 0, 2, 4],
                'intermittent': [2, 4, 6, 8],
                'continuous': [6, 8, 10, 12],
                'in-consolable': [10, 12, 15, 15]
            },
            'joint temperature': {
                'normal': [0, 0, 3, 5],
                'warm': [3, 5, 6, 8],
                'hot': [6, 8, 9, 11],
                'very hot': [9, 11, 15, 15]
            },
            'life stage': {
                'infant': [0, 0, 1, 2],
                'toddler': [1, 2, 3, 5],
                'child': [3, 5, 12, 18],
                'adult': [12, 18, 100, 100]
            },
            'itch': {
                'little to none': [0, 0, 2, 4],
                'mild': [2, 4, 4, 6],
                'moderate': [4, 6, 6, 8],
                'severe': [6, 8, 10, 10]
            },
            'history of allergy': {
                'little to none': [0, 0, 3, 5],
                'some': [3, 5, 7, 9],
                'significant': [7, 9, 10, 10]
            },
            'rash or blistering': {
                'little to none': [0, 0, 2, 4],
                'minimal': [2, 4, 6, 8],
                'widespread': [6, 8, 10, 10]
            },
            'haemorrhage': {
                'minor': [0, 0, 3, 5],
                'major': [3, 5, 7, 9],
                'exsanguine': [7, 9, 10, 10]
            },
            'pefr': {
                'very low': [0, 0, 30, 40],
                'low': [30, 40, 60, 70],
                'normal': [60, 70, 100, 100]
            },
            'deformity': {
                'little to none': [0, 0, 3, 5],
                'moderate': [3, 5, 5, 7],
                'significant': [5, 7, 10, 10]
            },
            'mechanism of injury': {
                'minor': [0, 0, 3, 5],
                'moderate': [3, 5, 5, 7],
                'significant': [5, 7, 10, 10]
            },
            'history of respiratory': {
                'little to none': [0, 0, 3, 5],
                'some': [3, 5, 7, 9],
                'significant': [7, 9, 10, 10]
            },
            'risk of harm to others': {
                'low': [0, 0, 3, 5],
                'moderate': [3, 5, 7, 9],
                'high': [7, 9, 10, 10]
            },
            'risk of harm to self': {
                'low': [0, 0, 3, 5],
                'moderate': [3, 5, 7, 9],
                'high': [7, 9, 10, 10]
            },
            'history of psychiatric': {
                'little to none': [0, 0, 3, 5],
                'some': [3, 5, 7, 9],
                'significant': [7, 9, 10, 10]
            },
            'lethality': {
                'little to none': [0, 0, 3, 5],
                'moderate': [3, 5, 7, 9],
                'high': [7, 9, 10, 10]
            },
            'history of cardiac': {
                'little to none': [0, 0, 3, 5],
                'some': [3, 5, 7, 9],
                'significant': [7, 9, 10, 10]
            },
            'discharge or blistering': {
                'little to none': [0, 0, 2, 4],
                'minimal': [2, 4, 6, 8],
                'widespread': [6, 8, 10, 10]
            },
            'vision loss': {
                'little to none': [0, 0, 3, 5],
                'some': [3, 5, 7, 9],
                'complete': [7, 9, 10, 10]
            },
            'history of gi bleeding': {
                'little to none': [0, 0, 3, 5],
                'some': [3, 5, 7, 9],
                'significant': [7, 9, 10, 10]
            },
            'history of haematology': {
                'little to none': [0, 0, 3, 5],
                'some': [3, 5, 7, 9],
                'significant': [7, 9, 10, 10]
            },
            'ability to pass urine': {
                'normal': [0, 0, 3, 5],
                'difficult': [3, 5, 7, 9],
                'little to none': [7, 9, 10, 10]
            },
            'onset of symptoms': {
                'distant': [0, 0, 2, 4],
                'recent': [2, 4, 4, 6],
                'acute': [4, 6, 6, 8],
                'rapid': [6, 8, 8, 10],
                'abrupt': [8, 10, 10, 10]
            }
        }
    
    def trapezoidal_mf(self, x, params):
        """Trapezoidal membership function"""
        a, b, c, d = params
        if x < a or x > d:
            return 0.0
        if x < b:
            return (x - a) / (b - a + 1e-6)
        if x < c:
            return 1.0
        return (d - x) / (d - c + 1e-6)
    
    def assess_patient(self, patient: Patient, current_time: float = 0.0) -> TriageAssessment:
        """Assess patient using MTS fuzzy logic"""
        # Extract symptoms from patient for fuzzy logic
        symptoms = self._extract_symptoms_from_patient(patient)
        
        # Use internal triage method
        priority_name, max_wait_time = self.triage(symptoms)
        
        # Map to system priority
        priority = self.priority_mapping.get(priority_name, Priority.GREEN)
        
        # Simple treatment time estimation
        treatment_time = priority.value * 10
        
        # Create assessment
        assessment = TriageAssessment(
            priority=priority,
            reason=f"Manchester Triage: {patient.condition} -> {priority_name}",
            estimated_treatment_time=treatment_time,
            timestamp=current_time
        )
        
        self.assessments_completed += 1
        return assessment
    
    def _extract_symptoms_from_patient(self, patient: Patient) -> dict:
        """Extract symptoms from patient object for fuzzy logic processing"""
        # Map patient condition to symptom profiles for fuzzy logic
        condition_profiles = {
            'cardiac_arrest': {
                'airway': 0,  # Not maintained
                'conscious level': 0,  # Un-responsive
                'oxygenation': 50,  # Inadequate
                'heart rate': 150,  # Very vigorous
                'blood pressure': 60  # Low
            },
            'stroke_symptoms': {
                'neurological deficit': 1,  # Present
                'onset2': 8,  # Abrupt
                'conscious level': 5,  # Reduced
            },
            'chest_pain': {
                'pain': 8,  # Severe
                'shortness of breath': 1,  # Present
                'onset': 6,  # Acute
            },
            'abdominal_pain': {
                'pain': 6,  # Moderate to severe
                'onset of symptoms': 4,  # Recent
            },
            'broken_bone': {
                'pain': 6,  # Moderate
                'deformity': 7,  # Significant
                'mechanism of injury': 5,  # Moderate
            },
            'minor_laceration': {
                'pain': 3,  # Mild
                'haemorrhage': 2,  # Minor
            },
            'headache': {
                'pain': 4,  # Mild to moderate
                'onset of symptoms': 2,  # Recent
            },
            'fever': {
                'skin temperature': 8,  # Hot
                'onset of symptoms': 4,  # Recent
            },
            'allergic_reaction': {
                'rash or blistering': 6,  # Moderate
                'history of allergy': 7,  # Significant
                'itch': 5,  # Moderate
            }
        }
        
        # Get symptom profile for condition or use default
        symptoms = condition_profiles.get(patient.condition, {
            'pain': 3,  # Default mild pain
            'onset of symptoms': 2  # Default recent onset
        })
        
        return symptoms
    
    def triage(self, symptoms):
        """Main triage method using fuzzy logic"""
        firings = self.compute_firings(symptoms)
        return self.select_category(firings)
    
    def compute_firings(self, symptoms):
        """Compute fuzzy rule firings for given symptoms"""
        firings = {level: [] for level in Priority if level != Priority.BLUE}

        # Rule 1: IF airway IS NOT maintained THEN immediate
        firings[Priority.RED].append(1 - symptoms.get('airway', 1))

        # Rule 2: IF oxygenation IS inadequate THEN immediate
        firings[Priority.RED].append(self.get_mf('oxygenation', 'inadequate', symptoms.get('oxygenation', 100)))

        # Rule 3: IF (sweating IS significant OR exceptional) AND color IS pale AND (heart rate IS vigorous OR very vigorous) AND blood pressure IS low AND (conscious level IS reduced OR un-responsive) THEN immediate
        sweating_sig_or_exc = max(
            self.get_mf('sweating', 'significant', symptoms.get('sweating', 0)),
            self.get_mf('sweating', 'exceptional', symptoms.get('sweating', 0))
        )
        color_pale = self.get_mf('color', 'pale', symptoms.get('color', 10))
        heart_vig_or_vvig = max(
            self.get_mf('heart rate', 'vigorous', symptoms.get('heart rate', 80)),
            self.get_mf('heart rate', 'very vigorous', symptoms.get('heart rate', 80))
        )
        bp_low = self.get_mf('blood pressure', 'low', symptoms.get('blood pressure', 120))
        conscious_red_or_un = max(
            self.get_mf('conscious level', 'reduced', symptoms.get('conscious level', 15)),
            self.get_mf('conscious level', 'un-responsive', symptoms.get('conscious level', 15))
        )
        firings[Priority.RED].append(min(sweating_sig_or_exc, color_pale, heart_vig_or_vvig, bp_low, conscious_red_or_un))

        # Rule 4: IF haemorrhage IS exsanguinating THEN immediate
        firings[Priority.RED].append(self.get_mf('haemorrhage', 'exsanguine', symptoms.get('haemorrhage', 0)))

        # Rule 5: IF pain IS severe THEN very urgent
        firings[Priority.ORANGE].append(self.get_mf('pain', 'severe', symptoms.get('pain', 0)))

        # Rule 6: IF mechanism of injury IS significant THEN very urgent
        firings[Priority.ORANGE].append(self.get_mf('mechanism of injury', 'significant', symptoms.get('mechanism of injury', 0)))

        # Rule 7: IF shortness of breath IS present AND (onset IS acute OR rapid OR abrupt) THEN very urgent
        sob_present = symptoms.get('shortness of breath', 0)
        onset_acu_rap_abr = max(
            self.get_mf('onset', 'acute', symptoms.get('onset', 0)),
            self.get_mf('onset', 'rapid', symptoms.get('onset', 0)),
            self.get_mf('onset', 'abrupt', symptoms.get('onset', 0))
        )
        firings[Priority.ORANGE].append(min(sob_present, onset_acu_rap_abr))

        # Rule 8: IF neurological deficit IS present AND (onset2 IS abrupt OR rapid OR acute) THEN very urgent
        nd_present = symptoms.get('neurological deficit', 0)
        onset2_abr_rap_acu = max(
            self.get_mf('onset2', 'abrupt', symptoms.get('onset2', 0)),
            self.get_mf('onset2', 'rapid', symptoms.get('onset2', 0)),
            self.get_mf('onset2', 'acute', symptoms.get('onset2', 0))
        )
        firings[Priority.ORANGE].append(min(nd_present, onset2_abr_rap_acu))

        # Rule 9: IF (conscious level IS slightly reduced OR reduced OR un-responsive) THEN very urgent
        conscious_sli_red_un = max(
            self.get_mf('conscious level', 'slightly reduced', symptoms.get('conscious level', 15)),
            self.get_mf('conscious level', 'reduced', symptoms.get('conscious level', 15)),
            self.get_mf('conscious level', 'un-responsive', symptoms.get('conscious level', 15))
        )
        firings[Priority.ORANGE].append(conscious_sli_red_un)

        # Rule 10: IF haemorrhage IS uncontrollable major THEN very urgent
        uncontrollable = symptoms.get('uncontrollable', 0)
        haem_major = self.get_mf('haemorrhage', 'major', symptoms.get('haemorrhage', 0))
        firings[Priority.ORANGE].append(min(uncontrollable, haem_major))

        # Rule 11: IF untruthful story IS present THEN urgent
        firings[Priority.YELLOW].append(symptoms.get('untruthful story', 0))

        # Rule 12: IF neurological deficit IS present AND onset2 IS recent THEN urgent
        nd_present = symptoms.get('neurological deficit', 0)
        onset2_recent = self.get_mf('onset2', 'recent', symptoms.get('onset2', 0))
        firings[Priority.YELLOW].append(min(nd_present, onset2_recent))

        # Rule 13: IF haemorrhage IS uncontrollable minor THEN urgent
        uncontrollable = symptoms.get('uncontrollable', 0)
        haem_minor = self.get_mf('haemorrhage', 'minor', symptoms.get('haemorrhage', 0))
        firings[Priority.YELLOW].append(min(uncontrollable, haem_minor))

        # Rule 14: IF history of unconsciousness IS present THEN urgent
        firings[Priority.YELLOW].append(symptoms.get('history of unconsciousness', 0))

        # Rule 15: IF pain IS moderate THEN urgent
        firings[Priority.YELLOW].append(self.get_mf('pain', 'moderate', symptoms.get('pain', 0)))

        # Rule 16: IF swelling IS present THEN standard
        firings[Priority.GREEN].append(symptoms.get('swelling', 0))

        # Rule 17: IF deformity IS moderate OR significant THEN standard
        deform_mod_or_sig = max(
            self.get_mf('deformity', 'moderate', symptoms.get('deformity', 0)),
            self.get_mf('deformity', 'significant', symptoms.get('deformity', 0))
        )
        firings[Priority.GREEN].append(deform_mod_or_sig)

        # Rule 18: IF pain IS mild THEN standard
        firings[Priority.GREEN].append(self.get_mf('pain', 'mild', symptoms.get('pain', 0)))

        # Rule 19: IF onset of symptoms IS recent THEN standard
        firings[Priority.GREEN].append(self.get_mf('onset of symptoms', 'recent', symptoms.get('onset of symptoms', 0)))

        return firings
    
    def select_category(self, firings):
        """Select final triage category based on rule firings"""
        degrees = {}
        for level in Priority:
            if level == Priority.BLUE:
                degrees[level] = 0.0
            else:
                max_f = max(firings.get(level, [0]))
                degrees[level] = max_f * self.weights.get(level, 0.0)
        max_degree = max(degrees.values(), default=0)
        if max_degree == 0:
            return self.names[Priority.BLUE], self.max_times[Priority.BLUE]
        possible_cats = [level for level, deg in degrees.items() if deg == max_degree]
        cat_order = list(Priority)
        selected_cat = min(possible_cats, key=lambda c: cat_order.index(c))
        return self.names[selected_cat], self.max_times[selected_cat]
    
    def get_mf(self, var, term, value):
        """Get membership function value for given variable, term, and value"""
        if var not in self.fuzzy_vars or term not in self.fuzzy_vars[var]:
            raise ValueError(f"Unknown variable or term: {var}.{term}")
        return self.trapezoidal_mf(value, self.fuzzy_vars[var][term])