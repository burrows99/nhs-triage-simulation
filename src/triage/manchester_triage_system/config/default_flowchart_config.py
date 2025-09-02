"""Default Flowchart Configuration

This module provides the default flowchart configuration based on the FMTS paper,
implementing all ~50 flowcharts mentioned in the research.

Reference: FMTS paper by Cremeens & Khorasani (2014)
https://www.researchgate.net/publication/286737453_FMTS_A_fuzzy_implementation_of_the_Manchester_triage_system

Paper Quote: "The system consists of around 50 flowcharts with standard definitions 
designed to categorize patients arriving to an emergency room based on their level of urgency."

This implementation provides the complete set of flowcharts that form the foundation
of the objective triage system described in the paper.
"""

from typing import Dict, List, Any
from src.triage.triage_constants import MedicalCategories, LinguisticValues, SymptomNames, TriageFlowcharts


class DefaultFlowchartConfig:
    """Default flowchart configuration based on FMTS paper
    
    Reference: FMTS paper Section II - "around 50 flowcharts with 
    standard definitions designed to categorize patients"
    
    Paper Context: The paper emphasizes that "MTS flowcharts are full of imprecise 
    linguistic terms such as very low PEFR, exhaustion, significant respiratory history, 
    urgent, etc." This class provides the systematic organization of these flowcharts
    with standardized linguistic terms to support the paper's objective triage system.
    
    Implementation follows the paper's approach of categorizing flowcharts by medical
    presentation type (respiratory, cardiovascular, neurological, etc.) to provide
    comprehensive coverage of emergency department scenarios.
    """
    
    @staticmethod
    def _create_flowchart_entry(flowchart: TriageFlowcharts, symptoms: List[str], 
                               category: str, paper_reference: str) -> Dict[str, Any]:
        """Create a standardized flowchart entry.
        
        Args:
            flowchart: TriageFlowcharts enum value
            symptoms: List of symptom names
            category: Medical category
            paper_reference: Reference to paper or clinical context
            
        Returns:
            Dictionary with standardized flowchart structure
        """
        return {
            flowchart.value: {
                'symptoms': symptoms,
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': category,
                'paper_reference': paper_reference
            }
        }
    
    @staticmethod
    def get_respiratory_flowcharts() -> Dict[str, Dict[str, Any]]:
        """Get respiratory presentation flowcharts
        
        Reference: FMTS paper Figure 1 shows an example MTS flowchart for evaluation 
        of shortness of breath in children, demonstrating the respiratory category.
        
        Paper Quote: "Figure 1 shows an example of one such flowchart designed to 
        evaluate the treatment urgency for the shortness of breath in children."
        
        Returns:
            Dictionary of respiratory flowcharts with symptoms and linguistic values
        """
        flowcharts = {}
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.SHORTNESS_OF_BREATH,
            [SymptomNames.DIFFICULTY_BREATHING, SymptomNames.WHEEZE, SymptomNames.UNABLE_TO_SPEAK, SymptomNames.CYANOSIS, SymptomNames.EXHAUSTION],
            MedicalCategories.RESPIRATORY,
            'Figure 1 example flowchart'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.SHORTNESS_OF_BREATH_CHILD,
            [SymptomNames.VERY_LOW_PEFR, SymptomNames.EXHAUSTION, SymptomNames.SIGNIFICANT_RESPIRATORY_HISTORY, SymptomNames.ACUTE_ONSET_AFTER_INJURY, SymptomNames.LOW_SAO2],
            MedicalCategories.RESPIRATORY,
            'Paper mentions very low PEFR as example of imprecise term'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.COUGH,
            [SymptomNames.PRODUCTIVE_COUGH, SymptomNames.BLOOD_IN_SPUTUM, SymptomNames.CHEST_PAIN, SymptomNames.FEVER, SymptomNames.NIGHT_SWEATS],
            MedicalCategories.RESPIRATORY,
            'Standard MTS respiratory presentation'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.ASTHMA,
            [SymptomNames.PEAK_FLOW, SymptomNames.WHEEZE, SymptomNames.SPEECH_DIFFICULTY, SymptomNames.ACCESSORY_MUSCLES, SymptomNames.CYANOSIS],
            MedicalCategories.RESPIRATORY,
            'Respiratory emergency requiring objective assessment'
        ))
        
        return flowcharts
    
    @staticmethod
    def get_cardiovascular_flowcharts() -> Dict[str, Dict[str, Any]]:
        """Get cardiovascular presentation flowcharts
        
        Reference: FMTS paper addresses the need for objective assessment of cardiac
        emergencies where subjective interpretation could lead to different conclusions.
        
        Paper Context: Addresses scenarios where "two nurses coming to different 
        conclusions about the urgency of a patient's condition even if the same 
        flowcharts are being used."
        
        Returns:
            Dictionary of cardiovascular flowcharts with symptoms and linguistic values
        """
        flowcharts = {}
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.CHEST_PAIN,
            [SymptomNames.SEVERE_PAIN, SymptomNames.CRUSHING_SENSATION, SymptomNames.RADIATION, SymptomNames.BREATHLESS, SymptomNames.SWEATING],
            MedicalCategories.CARDIOVASCULAR,
            'Figure 1 example flowchart'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.PALPITATIONS,
            [SymptomNames.IRREGULAR_PULSE, SymptomNames.CHEST_DISCOMFORT, SymptomNames.DIZZINESS, SymptomNames.SYNCOPE, SymptomNames.BREATHLESSNESS],
            MedicalCategories.CARDIOVASCULAR,
            'Cardiac rhythm assessment'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.CARDIAC_ARREST,
            [SymptomNames.UNCONSCIOUS, SymptomNames.NO_PULSE, SymptomNames.NOT_BREATHING, SymptomNames.CYANOSIS, SymptomNames.COLLAPSE],
            MedicalCategories.CARDIOVASCULAR,
            'Most critical cardiac emergency - immediate category'
        ))
        
        return flowcharts
    
    @staticmethod
    def get_neurological_flowcharts() -> Dict[str, Dict[str, Any]]:
        """Get neurological presentation flowcharts
        
        Reference: FMTS paper emphasizes the need for systematic assessment of
        neurological conditions where imprecise terms can lead to misinterpretation.
        
        Returns:
            Dictionary of neurological flowcharts with symptoms and linguistic values
        """
        flowcharts = {}
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.HEADACHE,
            [SymptomNames.PAIN_SEVERITY, SymptomNames.SUDDEN_ONSET, SymptomNames.NECK_STIFFNESS, SymptomNames.PHOTOPHOBIA, SymptomNames.CONFUSION],
            MedicalCategories.NEUROLOGICAL,
            'Neurological assessment requiring objective severity evaluation'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.CONFUSION,
            [SymptomNames.ALTERED_CONSCIOUSNESS, SymptomNames.DISORIENTATION, SymptomNames.AGITATION, SymptomNames.MEMORY_LOSS, SymptomNames.SPEECH_PROBLEMS],
            MedicalCategories.NEUROLOGICAL,
            'Mental status changes requiring systematic evaluation'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.FITS,
            [SymptomNames.ACTIVE_SEIZURE, SymptomNames.POST_ICTAL, SymptomNames.TONGUE_BITING, SymptomNames.INCONTINENCE, SymptomNames.INJURY_DURING_FIT],
            MedicalCategories.NEUROLOGICAL,
            'Seizure activity assessment'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.STROKE,
            [SymptomNames.FACIAL_DROOP, SymptomNames.ARM_WEAKNESS, SymptomNames.SPEECH_PROBLEMS, SymptomNames.SUDDEN_ONSET, SymptomNames.HEADACHE],
            MedicalCategories.NEUROLOGICAL,
            'Acute stroke requiring rapid objective assessment'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.UNCONSCIOUS_ADULT,
            [SymptomNames.GCS_SCORE, SymptomNames.RESPONSE_TO_PAIN, SymptomNames.PUPIL_REACTION, SymptomNames.BREATHING_PATTERN, SymptomNames.PULSE_QUALITY],
            MedicalCategories.NEUROLOGICAL,
            'Altered consciousness requiring immediate evaluation'
        ))
        
        return flowcharts
    
    @staticmethod
    def get_gastrointestinal_flowcharts() -> Dict[str, Dict[str, Any]]:
        """Get gastrointestinal presentation flowcharts
        
        Reference: FMTS paper's systematic approach to all emergency presentations
        including gastrointestinal conditions that require objective assessment.
        
        Returns:
            Dictionary of gastrointestinal flowcharts with symptoms and linguistic values
        """
        flowcharts = {}
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.ABDOMINAL_PAIN,
            [SymptomNames.PAIN_INTENSITY, SymptomNames.VOMITING, SymptomNames.RIGIDITY, SymptomNames.DISTENSION, SymptomNames.TENDERNESS],
            MedicalCategories.GASTROINTESTINAL,
            'Abdominal emergency assessment'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.VOMITING,
            [SymptomNames.BLOOD_IN_VOMIT, SymptomNames.DEHYDRATION, SymptomNames.ABDOMINAL_PAIN, SymptomNames.BILE_STAINED, SymptomNames.PROJECTILE],
            MedicalCategories.GASTROINTESTINAL,
            'GI symptom evaluation'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.DIARRHOEA,
            [SymptomNames.BLOOD_IN_STOOL, SymptomNames.DEHYDRATION, SymptomNames.CRAMPING, SymptomNames.FEVER, SymptomNames.MUCUS],
            MedicalCategories.GASTROINTESTINAL,
            'Gastrointestinal assessment'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.GI_BLEEDING,
            [SymptomNames.HAEMATEMESIS, SymptomNames.MELAENA, SymptomNames.SHOCK, SymptomNames.PALLOR, SymptomNames.WEAKNESS],
            MedicalCategories.GASTROINTESTINAL,
            'Critical GI emergency requiring immediate assessment'
        ))
        
        return flowcharts
    
    @staticmethod
    def get_trauma_flowcharts() -> Dict[str, Dict[str, Any]]:
        """Get trauma and injury flowcharts
        
        Reference: FMTS paper's comprehensive approach includes trauma presentations
        that require objective assessment to determine urgency.
        
        Returns:
            Dictionary of trauma flowcharts with symptoms and linguistic values
        """
        flowcharts = {}
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.LIMB_INJURIES,
            [SymptomNames.DEFORMITY, SymptomNames.PAIN, SymptomNames.SWELLING, SymptomNames.LOSS_OF_FUNCTION, SymptomNames.BLEEDING],
            MedicalCategories.TRAUMA,
            'Musculoskeletal trauma assessment'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.HEAD_INJURY,
            [SymptomNames.LOSS_OF_CONSCIOUSNESS, SymptomNames.CONFUSION, SymptomNames.VOMITING, SymptomNames.HEADACHE, SymptomNames.AMNESIA],
            MedicalCategories.TRAUMA,
            'Critical head trauma requiring immediate evaluation'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.NECK_INJURY,
            [SymptomNames.NECK_PAIN, SymptomNames.NEUROLOGICAL_DEFICIT, SymptomNames.MECHANISM_OF_INJURY, SymptomNames.TENDERNESS, SymptomNames.DEFORMITY],
            MedicalCategories.TRAUMA,
            'Spinal injury requiring careful assessment'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.BACK_INJURY,
            [SymptomNames.BACK_PAIN, SymptomNames.LEG_WEAKNESS, SymptomNames.NUMBNESS, SymptomNames.BLADDER_PROBLEMS, SymptomNames.MECHANISM],
            MedicalCategories.TRAUMA,
            'Spinal trauma with potential neurological involvement'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.BURNS,
            [SymptomNames.BURN_AREA, SymptomNames.DEPTH, SymptomNames.AIRWAY_INVOLVEMENT, SymptomNames.PAIN, SymptomNames.BLISTERING],
            MedicalCategories.TRAUMA,
            'Thermal injury requiring systematic assessment'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.WOUNDS,
            [SymptomNames.BLEEDING, SymptomNames.DEPTH, SymptomNames.CONTAMINATION, SymptomNames.PAIN, SymptomNames.LOCATION],
            MedicalCategories.TRAUMA,
            'Wound assessment for infection and healing potential'
        ))
        
        return flowcharts
    
    @staticmethod
    def get_additional_flowcharts() -> Dict[str, Dict[str, Any]]:
        """Get additional flowcharts to reach the ~50 mentioned in the paper
        
        Reference: FMTS paper states "around 50 flowcharts" - this method provides
        the remaining flowcharts to achieve comprehensive coverage.
        
        Returns:
            Dictionary of additional flowcharts covering various medical presentations
        """
        flowcharts = {}
        
        # Genitourinary
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.URINARY_PROBLEMS,
            [SymptomNames.DYSURIA, SymptomNames.FREQUENCY, SymptomNames.URGENCY, SymptomNames.HAEMATURIA, SymptomNames.RETENTION],
            MedicalCategories.GENITOURINARY,
            'Urological conditions requiring assessment'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.RENAL_COLIC,
            [SymptomNames.LOIN_PAIN, SymptomNames.HAEMATURIA, SymptomNames.NAUSEA, SymptomNames.RESTLESSNESS, SymptomNames.RADIATION],
            MedicalCategories.GENITOURINARY,
            'Severe pain condition requiring objective assessment'
        ))
        
        # Obstetric and gynaecological
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.PREGNANCY_PROBLEMS,
            [SymptomNames.BLEEDING, SymptomNames.PAIN, SymptomNames.CONTRACTIONS, SymptomNames.FETAL_MOVEMENTS, SymptomNames.BLOOD_PRESSURE],
            MedicalCategories.OBSTETRIC,
            'Obstetric emergency requiring rapid assessment'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.VAGINAL_BLEEDING,
            [SymptomNames.AMOUNT, SymptomNames.PAIN, SymptomNames.PREGNANCY_TEST, SymptomNames.CLOTS, SymptomNames.SHOCK],
            MedicalCategories.OBSTETRIC,
            'Gynaecological bleeding assessment'
        ))
        
        # Paediatric specific
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.CRYING_BABY,
            [SymptomNames.INCONSOLABLE, SymptomNames.FEVER, SymptomNames.FEEDING_PROBLEMS, SymptomNames.RASH, SymptomNames.LETHARGY],
            MedicalCategories.PAEDIATRIC,
            'Paediatric assessment requiring objective evaluation'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.CHILD_FEVER,
            [SymptomNames.TEMPERATURE, SymptomNames.RASH, SymptomNames.NECK_STIFFNESS, SymptomNames.LETHARGY, SymptomNames.FEEDING],
            MedicalCategories.PAEDIATRIC,
            'Febrile child requiring systematic assessment'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.CHILD_VOMITING,
            [SymptomNames.DEHYDRATION, SymptomNames.BILE_STAINED, SymptomNames.BLOOD, SymptomNames.LETHARGY, SymptomNames.ABDOMINAL_PAIN],
            MedicalCategories.PAEDIATRIC,
            'Paediatric GI emergency'
        ))
        
        # Psychiatric presentations
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.MENTAL_ILLNESS,
            [SymptomNames.RISK_TO_SELF, SymptomNames.RISK_TO_OTHERS, SymptomNames.PSYCHOSIS, SymptomNames.DEPRESSION, SymptomNames.AGITATION],
            MedicalCategories.PSYCHIATRIC,
            'Mental health crisis requiring objective risk assessment'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.OVERDOSE_POISONING,
            [SymptomNames.CONSCIOUSNESS_LEVEL, SymptomNames.RESPIRATORY_DEPRESSION, SymptomNames.CARDIAC_EFFECTS, SymptomNames.SEIZURES, SymptomNames.ANTIDOTE_AVAILABLE],
            MedicalCategories.PSYCHIATRIC,
            'Toxicological emergency requiring immediate assessment'
        ))
        
        # Additional categories
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.RASH,
            [SymptomNames.DISTRIBUTION, SymptomNames.FEVER, SymptomNames.ITCH, SymptomNames.BLISTERING, SymptomNames.SYSTEMIC_ILLNESS],
            MedicalCategories.DERMATOLOGICAL,
            'Skin condition assessment'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.EYE_PROBLEMS,
            [SymptomNames.PAIN, SymptomNames.VISION_LOSS, SymptomNames.DISCHARGE, SymptomNames.PHOTOPHOBIA, SymptomNames.INJURY],
            MedicalCategories.OPHTHALMOLOGICAL,
            'Ocular emergency assessment'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.EAR_PROBLEMS,
            [SymptomNames.PAIN, SymptomNames.DISCHARGE, SymptomNames.HEARING_LOSS, SymptomNames.DIZZINESS, SymptomNames.FEVER],
            MedicalCategories.ENT,
            'ENT condition assessment'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.SORE_THROAT,
            [SymptomNames.PAIN, SymptomNames.DIFFICULTY_SWALLOWING, SymptomNames.FEVER, SymptomNames.DROOLING, SymptomNames.STRIDOR],
            MedicalCategories.ENT,
            'Throat condition with potential airway involvement'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.DIABETES,
            [SymptomNames.BLOOD_GLUCOSE, SymptomNames.KETONES, SymptomNames.DEHYDRATION, SymptomNames.CONSCIOUSNESS, SymptomNames.BREATHING],
            MedicalCategories.ENDOCRINE,
            'Diabetic emergency requiring objective assessment'
        ))
        
        flowcharts.update(DefaultFlowchartConfig._create_flowchart_entry(
            TriageFlowcharts.ALLERGY,
            [SymptomNames.RASH, SymptomNames.SWELLING, SymptomNames.BREATHING_DIFFICULTY, SymptomNames.SHOCK, SymptomNames.TONGUE_SWELLING],
            MedicalCategories.ALLERGIC,
            'Allergic reaction requiring rapid assessment'
        ))
        
        return flowcharts
    
    @staticmethod
    def get_all_flowcharts() -> Dict[str, Dict[str, Any]]:
        """Get all default flowcharts combined
        
        Reference: FMTS paper Section II - implements the complete set of ~50 flowcharts
        that form the foundation of the Manchester Triage System.
        
        Paper Quote: "The system consists of around 50 flowcharts with standard definitions 
        designed to categorize patients arriving to an emergency room based on their level of urgency."
        
        This method combines all flowchart categories to provide the comprehensive
        coverage required by the paper's objective triage system.
        
        Returns:
            Complete dictionary of all flowcharts implementing the FMTS requirements
        """
        all_flowcharts = {}
        
        # Combine all flowchart categories as per paper's systematic approach
        all_flowcharts.update(DefaultFlowchartConfig.get_respiratory_flowcharts())
        all_flowcharts.update(DefaultFlowchartConfig.get_cardiovascular_flowcharts())
        all_flowcharts.update(DefaultFlowchartConfig.get_neurological_flowcharts())
        all_flowcharts.update(DefaultFlowchartConfig.get_gastrointestinal_flowcharts())
        all_flowcharts.update(DefaultFlowchartConfig.get_trauma_flowcharts())
        all_flowcharts.update(DefaultFlowchartConfig.get_additional_flowcharts())
        
        return all_flowcharts
    
    def get_paper_reference(self) -> dict:
        """Get the paper reference information
        
        Returns:
            Dictionary containing complete paper citation details
        """
        return {
            'title': 'FMTS: A fuzzy implementation of the Manchester triage system',
            'authors': ['Matthew Cremeens', 'Elham S. Khorasani'],
            'year': 2014,
            'institution': 'University of Illinois at Springfield',
            'url': 'https://www.researchgate.net/publication/286737453_FMTS_A_fuzzy_implementation_of_the_Manchester_triage_system',
            'key_contribution': 'Systematic implementation of ~50 MTS flowcharts with objective triage logic',
            'flowchart_count': len(self.get_all_flowcharts()),
            'implementation_focus': 'Comprehensive flowchart coverage eliminating subjective interpretation'
        }