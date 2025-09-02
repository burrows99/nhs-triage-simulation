"""Centralized Triage Constants

This module provides centralized constants for triage operations to ensure
consistent key usage across the codebase and prevent key errors.
"""

from typing import Dict, List
from enum import Enum


class TriageFlowcharts(Enum):
    """Available flowchart reasons in the Manchester Triage System"""
    # Respiratory
    SHORTNESS_OF_BREATH = "shortness_of_breath"
    SHORTNESS_OF_BREATH_CHILD = "shortness_of_breath_child"
    COUGH = "cough"
    ASTHMA = "asthma"
    
    # Cardiovascular
    CHEST_PAIN = "chest_pain"
    PALPITATIONS = "palpitations"
    CARDIAC_ARREST = "cardiac_arrest"
    
    # Neurological
    HEADACHE = "headache"
    CONFUSION = "confusion"
    FITS = "fits"
    STROKE = "stroke"
    UNCONSCIOUS_ADULT = "unconscious_adult"
    
    # Gastrointestinal
    ABDOMINAL_PAIN = "abdominal_pain"
    VOMITING = "vomiting"
    DIARRHOEA = "diarrhoea"
    GI_BLEEDING = "gi_bleeding"
    
    # Trauma
    LIMB_INJURIES = "limb_injuries"
    HEAD_INJURY = "head_injury"
    NECK_INJURY = "neck_injury"
    BACK_INJURY = "back_injury"
    BURNS = "burns"
    WOUNDS = "wounds"
    
    # Genitourinary
    URINARY_PROBLEMS = "urinary_problems"
    RENAL_COLIC = "renal_colic"
    
    # Obstetric
    PREGNANCY_PROBLEMS = "pregnancy_problems"
    VAGINAL_BLEEDING = "vaginal_bleeding"
    
    # Paediatric
    CRYING_BABY = "crying_baby"
    CHILD_FEVER = "child_fever"
    CHILD_VOMITING = "child_vomiting"
    
    # Psychiatric
    MENTAL_ILLNESS = "mental_illness"
    OVERDOSE_POISONING = "overdose_poisoning"
    
    # Additional
    RASH = "rash"
    EYE_PROBLEMS = "eye_problems"
    EAR_PROBLEMS = "ear_problems"
    SORE_THROAT = "sore_throat"
    DIABETES = "diabetes"
    ALLERGY = "allergy"
    
    @classmethod
    def get_common_flowcharts(cls) -> List[str]:
        """Get commonly used flowcharts for general triage"""
        return [
            cls.CHEST_PAIN.value,
            cls.SHORTNESS_OF_BREATH.value,
            cls.ABDOMINAL_PAIN.value,
            cls.HEADACHE.value,
            cls.LIMB_INJURIES.value
        ]
    
    @classmethod
    def get_all_flowcharts(cls) -> List[str]:
        """Get all available flowcharts"""
        return [flowchart.value for flowchart in cls]



class SymptomKeys:
    """Standardized symptom keys for different flowcharts"""
    
    # Common symptoms across flowcharts
    PAIN_LEVEL = "severe_pain"
    BREATHING_DIFFICULTY = "breathless"
    CONSCIOUSNESS = "consciousness_level"
    BLEEDING = "bleeding"
    TEMPERATURE = "temperature"
    
    # Chest pain specific
    CRUSHING_SENSATION = "crushing_sensation"
    RADIATION = "radiation"
    SWEATING = "sweating"
    
    # Respiratory specific
    WHEEZE = "wheeze"
    CYANOSIS = "cyanosis"
    
    # Neurological specific
    CONFUSION_LEVEL = "confusion"
    SEIZURE = "seizure"
    
    # Trauma specific
    MECHANISM = "mechanism"
    DEFORMITY = "deformity"


class LinguisticValues:
    """Standardized linguistic values for symptoms"""
    
    # Severity levels
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    VERY_SEVERE = "very_severe"
    
    # Consciousness levels
    ALERT = "alert"
    CONFUSED = "confused"
    DROWSY = "drowsy"
    UNCONSCIOUS = "unconscious"
    
    # Temperature levels
    NORMAL = "normal"
    ELEVATED = "elevated"
    HIGH = "high"
    VERY_HIGH = "very_high"
    
    @classmethod
    def get_severity_levels(cls) -> List[str]:
        """Get all severity levels in order"""
        return [cls.NONE, cls.MILD, cls.MODERATE, cls.SEVERE, cls.VERY_SEVERE]
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        """Alias for get_severity_levels for consistency"""
        return cls.get_severity_levels()
    
    @classmethod
    def get_numeric_mapping(cls) -> Dict[str, float]:
        """Get numeric mapping for linguistic values"""
        return {
            cls.NONE: 0.0,
            cls.MILD: 2.0,
            cls.MODERATE: 5.0,
            cls.SEVERE: 8.0,
            cls.VERY_SEVERE: 10.0
        }
    
    @classmethod
    def get_consciousness_levels(cls) -> List[str]:
        """Get consciousness levels"""
        return [cls.ALERT, cls.CONFUSED, cls.DROWSY, cls.UNCONSCIOUS]
    
    @classmethod
    def get_temperature_levels(cls) -> List[str]:
        """Get temperature levels"""
        return [cls.NORMAL, cls.ELEVATED, cls.HIGH, cls.VERY_HIGH]


class FlowchartSymptomMapping:
    """Mapping of flowcharts to their expected symptoms"""
    
    CHEST_PAIN_SYMPTOMS = {
        SymptomKeys.PAIN_LEVEL: LinguisticValues.get_severity_levels(),
        SymptomKeys.CRUSHING_SENSATION: LinguisticValues.get_severity_levels(),
        SymptomKeys.RADIATION: LinguisticValues.get_severity_levels(),
        SymptomKeys.BREATHING_DIFFICULTY: LinguisticValues.get_severity_levels(),
        SymptomKeys.SWEATING: LinguisticValues.get_severity_levels()
    }
    
    SHORTNESS_OF_BREATH_SYMPTOMS = {
        SymptomKeys.BREATHING_DIFFICULTY: LinguisticValues.get_severity_levels(),
        SymptomKeys.WHEEZE: LinguisticValues.get_severity_levels(),
        SymptomKeys.CYANOSIS: LinguisticValues.get_severity_levels(),
        SymptomKeys.CONSCIOUSNESS: LinguisticValues.get_consciousness_levels(),
        SymptomKeys.TEMPERATURE: LinguisticValues.get_temperature_levels()
    }
    
    ABDOMINAL_PAIN_SYMPTOMS = {
        SymptomKeys.PAIN_LEVEL: LinguisticValues.get_severity_levels(),
        SymptomKeys.BLEEDING: LinguisticValues.get_severity_levels(),
        SymptomKeys.TEMPERATURE: LinguisticValues.get_temperature_levels(),
        SymptomKeys.CONSCIOUSNESS: LinguisticValues.get_consciousness_levels()
    }
    
    HEADACHE_SYMPTOMS = {
        SymptomKeys.PAIN_LEVEL: LinguisticValues.get_severity_levels(),
        SymptomKeys.CONFUSION_LEVEL: LinguisticValues.get_severity_levels(),
        SymptomKeys.CONSCIOUSNESS: LinguisticValues.get_consciousness_levels(),
        SymptomKeys.TEMPERATURE: LinguisticValues.get_temperature_levels()
    }
    
    LIMB_INJURIES_SYMPTOMS = {
        SymptomKeys.PAIN_LEVEL: LinguisticValues.get_severity_levels(),
        SymptomKeys.DEFORMITY: LinguisticValues.get_severity_levels(),
        SymptomKeys.BLEEDING: LinguisticValues.get_severity_levels(),
        SymptomKeys.MECHANISM: LinguisticValues.get_severity_levels()
    }
    
    @classmethod
    def get_symptoms_for_flowchart(cls, flowchart: str) -> Dict[str, List[str]]:
        """Get symptom mapping for a specific flowchart"""
        mapping = {
            TriageFlowcharts.CHEST_PAIN.value: cls.CHEST_PAIN_SYMPTOMS,
            TriageFlowcharts.SHORTNESS_OF_BREATH.value: cls.SHORTNESS_OF_BREATH_SYMPTOMS,
            TriageFlowcharts.ABDOMINAL_PAIN.value: cls.ABDOMINAL_PAIN_SYMPTOMS,
            TriageFlowcharts.HEADACHE.value: cls.HEADACHE_SYMPTOMS,
            TriageFlowcharts.LIMB_INJURIES.value: cls.LIMB_INJURIES_SYMPTOMS
        }
        return mapping.get(flowchart, cls.CHEST_PAIN_SYMPTOMS)  # Default to chest pain
    
    # Note: Random symptom generation removed - simulation now uses only real patient symptoms


class MedicalConditions:
    """Standardized medical condition names"""
    
    # Cardiac conditions
    CHEST_PAIN = "chest pain"
    ANGINA = "angina"
    MYOCARDIAL_INFARCTION = "myocardial infarction"
    HEART_ATTACK = "heart attack"
    CARDIAC_ARREST = "cardiac arrest"
    
    # Respiratory conditions
    ASTHMA = "asthma"
    COPD = "copd"
    SHORTNESS_OF_BREATH = "shortness of breath"
    DYSPNEA = "dyspnea"
    RESPIRATORY_FAILURE = "respiratory failure"
    PNEUMONIA = "pneumonia"
    
    # Neurological conditions
    HEADACHE = "headache"
    MIGRAINE = "migraine"
    SEIZURE = "seizure"
    STROKE = "stroke"
    
    # Gastrointestinal conditions
    NAUSEA = "nausea"
    VOMITING = "vomiting"
    APPENDICITIS = "appendicitis"
    
    # Other conditions
    DIZZINESS = "dizziness"
    SEVERE_TRAUMA = "severe trauma"
    FRACTURE = "fracture"
    SEPSIS = "sepsis"
    ANAPHYLAXIS = "anaphylaxis"
    
    # Additional medical conditions
    SEVERE_ASTHMA = "severe asthma"
    MODERATE_ASTHMA = "moderate asthma"
    DIABETIC_KETOACIDOSIS = "diabetic ketoacidosis"
    HYPERTENSION = "hypertension"
    URINARY_TRACT_INFECTION = "urinary tract infection"
    CELLULITIS = "cellulitis"
    BRONCHITIS = "bronchitis"
    SINUSITIS = "sinusitis"
    
    @classmethod
    def get_cardiac_conditions(cls) -> List[str]:
        """Get cardiac-related conditions"""
        return [cls.CHEST_PAIN, cls.ANGINA, cls.MYOCARDIAL_INFARCTION, cls.HEART_ATTACK, cls.CARDIAC_ARREST]
    
    @classmethod
    def get_respiratory_conditions(cls) -> List[str]:
        """Get respiratory-related conditions"""
        return [cls.ASTHMA, cls.COPD, cls.SHORTNESS_OF_BREATH, cls.DYSPNEA, cls.RESPIRATORY_FAILURE, cls.PNEUMONIA]
    
    @classmethod
    def get_neurological_conditions(cls) -> List[str]:
        """Get neurological-related conditions"""
        return [cls.HEADACHE, cls.MIGRAINE, cls.SEIZURE, cls.STROKE]


class VitalSignCategories:
    """Standardized vital sign category names"""
    
    # Blood pressure categories
    BP_NORMAL = "normal"
    BP_ELEVATED = "elevated"
    BP_HIGH = "high"
    BP_HYPERTENSIVE = "hypertensive"
    BP_HYPERTENSIVE_CRISIS = "hypertensive_crisis"
    BP_HYPOTENSIVE = "hypotensive"
    
    # Heart rate categories
    HR_NORMAL = "normal"
    HR_ELEVATED = "elevated"
    HR_HIGH = "high"
    HR_TACHYCARDIC = "tachycardic"
    HR_BRADYCARDIC = "bradycardic"
    
    # Temperature categories
    TEMP_NORMAL = "normal"
    TEMP_ELEVATED = "elevated"
    TEMP_HIGH = "high"
    TEMP_FEVER = "fever"
    TEMP_HIGH_FEVER = "high_fever"
    TEMP_HYPOTHERMIC = "hypothermic"
    
    # Respiratory rate categories
    RESP_NORMAL = "normal"
    RESP_ELEVATED = "elevated"
    RESP_HIGH = "high"
    RESP_TACHYPNEIC = "tachypneic"
    RESP_BRADYPNEIC = "bradypneic"


class MedicalCategories:
    """Medical category constants for flowchart organization"""
    
    RESPIRATORY = "respiratory"
    CARDIOVASCULAR = "cardiovascular"
    NEUROLOGICAL = "neurological"
    GASTROINTESTINAL = "gastrointestinal"
    TRAUMA = "trauma"
    GENITOURINARY = "genitourinary"
    OBSTETRIC = "obstetric"
    PAEDIATRIC = "paediatric"
    PSYCHIATRIC = "psychiatric"
    DERMATOLOGICAL = "dermatological"
    OPHTHALMOLOGICAL = "ophthalmological"
    ENT = "ent"
    ENDOCRINE = "endocrine"
    ALLERGIC = "allergic"
    
    @classmethod
    def get_all_categories(cls) -> List[str]:
        """Get all medical categories"""
        return [
            cls.RESPIRATORY, cls.CARDIOVASCULAR, cls.NEUROLOGICAL, cls.GASTROINTESTINAL, cls.TRAUMA,
            cls.GENITOURINARY, cls.OBSTETRIC, cls.PAEDIATRIC, cls.PSYCHIATRIC, cls.DERMATOLOGICAL,
            cls.OPHTHALMOLOGICAL, cls.ENT, cls.ENDOCRINE, cls.ALLERGIC
        ]


class FuzzyCategories:
    """Fuzzy triage category constants (lowercase for fuzzy logic)"""
    
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"
    
    @classmethod
    def get_all_categories(cls) -> List[str]:
        """Get all fuzzy categories in order"""
        return [cls.RED, cls.ORANGE, cls.YELLOW, cls.GREEN, cls.BLUE]
    
    @classmethod
    def get_category_set(cls) -> set:
        """Get fuzzy categories as a set for validation"""
        return {cls.RED, cls.ORANGE, cls.YELLOW, cls.GREEN, cls.BLUE}
    
    @classmethod
    def get_membership_functions(cls) -> Dict[str, List[float]]:
        """Get fuzzy membership functions for triage categories"""
        return {
            cls.RED: [1, 1, 2],
            cls.ORANGE: [1, 2, 3],
            cls.YELLOW: [2, 3, 4],
            cls.GREEN: [3, 4, 5],
            cls.BLUE: [4, 5, 5]
        }


class WaitTimeDisplays:
    """Wait time display constants"""
    
    IMMEDIATE = "Immediate"
    TEN_MIN = "10 min"
    SIXTY_MIN = "60 min"
    ONE_TWENTY_MIN = "120 min"
    TWO_FORTY_MIN = "240 min"
    
    @classmethod
    def get_wait_time_displays(cls) -> List[str]:
        """Get wait time displays in order"""
        return [cls.IMMEDIATE, cls.TEN_MIN, cls.SIXTY_MIN, cls.ONE_TWENTY_MIN, cls.TWO_FORTY_MIN]
    
    @classmethod
    def get_all_wait_times(cls) -> List[str]:
        """Alias for get_wait_time_displays for consistency"""
        return cls.get_wait_time_displays()


class SymptomNames:
    """Comprehensive symptom name constants for flowcharts"""
    
    # Respiratory symptoms
    DIFFICULTY_BREATHING = "difficulty_breathing"
    WHEEZE = "wheeze"
    UNABLE_TO_SPEAK = "unable_to_speak"
    CYANOSIS = "cyanosis"
    EXHAUSTION = "exhaustion"
    VERY_LOW_PEFR = "very_low_pefr"
    SIGNIFICANT_RESPIRATORY_HISTORY = "significant_respiratory_history"
    ACUTE_ONSET_AFTER_INJURY = "acute_onset_after_injury"
    LOW_SAO2 = "low_sao2"
    PRODUCTIVE_COUGH = "productive_cough"
    BLOOD_IN_SPUTUM = "blood_in_sputum"
    CHEST_PAIN = "chest_pain"
    FEVER = "fever"
    NIGHT_SWEATS = "night_sweats"
    PEAK_FLOW = "peak_flow"
    SPEECH_DIFFICULTY = "speech_difficulty"
    ACCESSORY_MUSCLES = "accessory_muscles"
    
    # Cardiovascular symptoms
    SEVERE_PAIN = "severe_pain"
    CRUSHING_SENSATION = "crushing_sensation"
    RADIATION = "radiation"
    BREATHLESS = "breathless"
    SWEATING = "sweating"
    IRREGULAR_PULSE = "irregular_pulse"
    CHEST_DISCOMFORT = "chest_discomfort"
    DIZZINESS = "dizziness"
    SYNCOPE = "syncope"
    BREATHLESSNESS = "breathlessness"
    UNCONSCIOUS = "unconscious"
    NO_PULSE = "no_pulse"
    NOT_BREATHING = "not_breathing"
    COLLAPSE = "collapse"
    
    # Neurological symptoms
    PAIN_SEVERITY = "pain_severity"
    SUDDEN_ONSET = "sudden_onset"
    NECK_STIFFNESS = "neck_stiffness"
    PHOTOPHOBIA = "photophobia"
    CONFUSION = "confusion"
    ALTERED_CONSCIOUSNESS = "altered_consciousness"
    DISORIENTATION = "disorientation"
    AGITATION = "agitation"
    MEMORY_LOSS = "memory_loss"
    SPEECH_PROBLEMS = "speech_problems"
    ACTIVE_SEIZURE = "active_seizure"
    POST_ICTAL = "post_ictal"
    TONGUE_BITING = "tongue_biting"
    INCONTINENCE = "incontinence"
    INJURY_DURING_FIT = "injury_during_fit"
    FACIAL_DROOP = "facial_droop"
    ARM_WEAKNESS = "arm_weakness"
    GCS_SCORE = "gcs_score"
    RESPONSE_TO_PAIN = "response_to_pain"
    PUPIL_REACTION = "pupil_reaction"
    BREATHING_PATTERN = "breathing_pattern"
    PULSE_QUALITY = "pulse_quality"
    
    # Gastrointestinal symptoms
    PAIN_INTENSITY = "pain_intensity"
    VOMITING = "vomiting"
    RIGIDITY = "rigidity"
    DISTENSION = "distension"
    TENDERNESS = "tenderness"
    BLOOD_IN_VOMIT = "blood_in_vomit"
    DEHYDRATION = "dehydration"
    ABDOMINAL_PAIN = "abdominal_pain"
    BILE_STAINED = "bile_stained"
    PROJECTILE = "projectile"
    BLOOD_IN_STOOL = "blood_in_stool"
    CRAMPING = "cramping"
    MUCUS = "mucus"
    HAEMATEMESIS = "haematemesis"
    MELAENA = "melaena"
    SHOCK = "shock"
    PALLOR = "pallor"
    WEAKNESS = "weakness"
    
    # Trauma symptoms
    DEFORMITY = "deformity"
    PAIN = "pain"
    SWELLING = "swelling"
    LOSS_OF_FUNCTION = "loss_of_function"
    BLEEDING = "bleeding"
    LOSS_OF_CONSCIOUSNESS = "loss_of_consciousness"
    HEADACHE = "headache"
    AMNESIA = "amnesia"
    NECK_PAIN = "neck_pain"
    NEUROLOGICAL_DEFICIT = "neurological_deficit"
    MECHANISM_OF_INJURY = "mechanism_of_injury"
    BACK_PAIN = "back_pain"
    LEG_WEAKNESS = "leg_weakness"
    NUMBNESS = "numbness"
    BLADDER_PROBLEMS = "bladder_problems"
    MECHANISM = "mechanism"
    BURN_AREA = "burn_area"
    DEPTH = "depth"
    AIRWAY_INVOLVEMENT = "airway_involvement"
    BLISTERING = "blistering"
    CONTAMINATION = "contamination"
    LOCATION = "location"
    
    # Additional symptoms
    DYSURIA = "dysuria"
    FREQUENCY = "frequency"
    URGENCY = "urgency"
    HAEMATURIA = "haematuria"
    RETENTION = "retention"
    LOIN_PAIN = "loin_pain"
    NAUSEA = "nausea"
    RESTLESSNESS = "restlessness"
    CONTRACTIONS = "contractions"
    FETAL_MOVEMENTS = "fetal_movements"
    BLOOD_PRESSURE = "blood_pressure"
    AMOUNT = "amount"
    PREGNANCY_TEST = "pregnancy_test"
    CLOTS = "clots"
    INCONSOLABLE = "inconsolable"
    FEEDING_PROBLEMS = "feeding_problems"
    RASH = "rash"
    LETHARGY = "lethargy"
    TEMPERATURE = "temperature"
    FEEDING = "feeding"
    BLOOD = "blood"
    RISK_TO_SELF = "risk_to_self"
    RISK_TO_OTHERS = "risk_to_others"
    PSYCHOSIS = "psychosis"
    DEPRESSION = "depression"
    CONSCIOUSNESS_LEVEL = "consciousness_level"
    RESPIRATORY_DEPRESSION = "respiratory_depression"
    CARDIAC_EFFECTS = "cardiac_effects"
    SEIZURES = "seizures"
    ANTIDOTE_AVAILABLE = "antidote_available"
    DISTRIBUTION = "distribution"
    ITCH = "itch"
    SYSTEMIC_ILLNESS = "systemic_illness"
    VISION_LOSS = "vision_loss"
    DISCHARGE = "discharge"
    INJURY = "injury"
    HEARING_LOSS = "hearing_loss"
    DIFFICULTY_SWALLOWING = "difficulty_swallowing"
    DROOLING = "drooling"
    STRIDOR = "stridor"
    BLOOD_GLUCOSE = "blood_glucose"
    KETONES = "ketones"
    CONSCIOUSNESS = "consciousness"
    BREATHING = "breathing"
    BREATHING_DIFFICULTY = "breathing_difficulty"
    TONGUE_SWELLING = "tongue_swelling"


class CommonSymptoms:
    """Common symptom name constants"""
    
    PAIN = "pain"
    FEVER = "fever"
    BLEEDING = "bleeding"
    CHEST_PAIN = "chest_pain"
    DIZZINESS = "dizziness"
    
    # Symptom collections
    PAIN_RELATED = ["pain", "ache", "discomfort", "soreness"]
    BLEEDING_RELATED = ["bleeding", "blood_in_sputum", "blood_in_stool"]
    FEVER_RELATED = ["fever", "night_sweats", "temperature"]


class CommonStrings:
    """Common string constants used across the application"""
    
    # Default values
    UNKNOWN = "Unknown"
    GENERAL_COMPLAINT = "General complaint"
    
    # Wait time strings
    WAIT_0_MIN = "0 min"
    WAIT_10_MIN = "10 min"
    WAIT_60_MIN = "60 min"
    WAIT_120_MIN = "120 min"
    WAIT_240_MIN = "240 min"
    
    # Symptom keywords
    PAIN_KEYWORDS = ['pain', 'ache', 'discomfort', 'soreness']
    CARDIAC_KEYWORD = 'cardiac'
    RESPIRATORY_KEYWORD = 'respiratory'
    NEUROLOGICAL_KEYWORD = 'neurological'
    
    # Additional medical terms
    CHEST_PAIN_SYMPTOM = 'chest_pain'
    SHORTNESS_OF_BREATH_TERM = 'shortness of breath'
    FEVER_TERM = 'fever'
    INFECTION_TERM = 'infection'
    TRAUMA_TERM = 'trauma'
    NEUROLOGICAL_TERM = 'Neurological'
    FEVER_DISPLAY = 'Fever'
    
    @classmethod
    def get_wait_times(cls) -> List[str]:
        """Get all wait time strings in order"""
        return [cls.WAIT_0_MIN, cls.WAIT_10_MIN, cls.WAIT_60_MIN, cls.WAIT_120_MIN, cls.WAIT_240_MIN]


class FlowchartNames:
    """Standardized flowchart display names"""
    
    CHEST_PAIN_DISPLAY = "Chest pain"
    SHORTNESS_OF_BREATH_DISPLAY = "Shortness of breath"
    ABDOMINAL_PAIN_DISPLAY = "Abdominal pain"
    HEADACHE_DISPLAY = "Headache"
    NAUSEA_VOMITING_DISPLAY = "Nausea and vomiting"
    PAIN_ASSESSMENT_DISPLAY = "Pain assessment"
    INJURY_DISPLAY = "Injury"
    
    # Assessment and emergency types
    GENERAL_ASSESSMENT = "general_assessment"
    CARDIAC_EMERGENCY = "cardiac_emergency"
    MEDICAL_EMERGENCY = "medical_emergency"
    VITAL_SIGNS_EMERGENCY = "vital_signs_emergency"
    VITAL_SIGNS_CONCERN = "vital_signs_concern"
    PAIN_ASSESSMENT = "pain_assessment"
    HYPERTENSION_ASSESSMENT = "hypertension_assessment"
    
    @classmethod
    def get_condition_to_flowchart_mapping(cls) -> Dict[str, str]:
        """Map medical conditions to flowchart display names"""
        return {
            MedicalConditions.CHEST_PAIN: cls.CHEST_PAIN_DISPLAY,
            MedicalConditions.ANGINA: cls.CHEST_PAIN_DISPLAY,
            MedicalConditions.MYOCARDIAL_INFARCTION: cls.CHEST_PAIN_DISPLAY,
            MedicalConditions.HEART_ATTACK: cls.CHEST_PAIN_DISPLAY,
            MedicalConditions.ASTHMA: cls.SHORTNESS_OF_BREATH_DISPLAY,
            MedicalConditions.COPD: cls.SHORTNESS_OF_BREATH_DISPLAY,
            MedicalConditions.HEADACHE: cls.HEADACHE_DISPLAY,
            MedicalConditions.MIGRAINE: cls.HEADACHE_DISPLAY,
            MedicalConditions.APPENDICITIS: cls.ABDOMINAL_PAIN_DISPLAY,
            MedicalConditions.NAUSEA: cls.NAUSEA_VOMITING_DISPLAY,
            MedicalConditions.VOMITING: cls.NAUSEA_VOMITING_DISPLAY
        }


class TriageCategories:
    """Triage category constants"""
    RED = "RED"
    ORANGE = "ORANGE"
    YELLOW = "YELLOW"
    GREEN = "GREEN"
    BLUE = "BLUE"
    
    @classmethod
    def get_all_categories(cls) -> List[str]:
        """Get all triage categories"""
        return [cls.RED, cls.ORANGE, cls.YELLOW, cls.GREEN, cls.BLUE]
    
    @classmethod
    def get_priority_mapping(cls) -> Dict[str, int]:
        """Get priority mapping (1=highest, 5=lowest)"""
        return {
            cls.RED: 1,
            cls.ORANGE: 2,
            cls.YELLOW: 3,
            cls.GREEN: 4,
            cls.BLUE: 5
        }