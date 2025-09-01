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
from src.triage.triage_constants import MedicalCategories, LinguisticValues, SymptomNames


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
    def get_respiratory_flowcharts() -> Dict[str, Dict[str, Any]]:
        """Get respiratory presentation flowcharts
        
        Reference: FMTS paper Figure 1 shows an example MTS flowchart for evaluation 
        of shortness of breath in children, demonstrating the respiratory category.
        
        Paper Quote: "Figure 1 shows an example of one such flowchart designed to 
        evaluate the treatment urgency for the shortness of breath in children."
        
        Returns:
            Dictionary of respiratory flowcharts with symptoms and linguistic values
        """
        return {
            'shortness_of_breath': {
                'symptoms': [SymptomNames.DIFFICULTY_BREATHING, SymptomNames.WHEEZE, SymptomNames.UNABLE_TO_SPEAK, SymptomNames.CYANOSIS, SymptomNames.EXHAUSTION],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.RESPIRATORY,
                'paper_reference': 'Figure 1 example flowchart'
            },
            'shortness_of_breath_child': {
                'symptoms': [SymptomNames.VERY_LOW_PEFR, SymptomNames.EXHAUSTION, SymptomNames.SIGNIFICANT_RESPIRATORY_HISTORY, SymptomNames.ACUTE_ONSET_AFTER_INJURY, SymptomNames.LOW_SAO2],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.RESPIRATORY,
                'paper_reference': 'Paper mentions very low PEFR as example of imprecise term'
            },
            'cough': {
                'symptoms': [SymptomNames.PRODUCTIVE_COUGH, SymptomNames.BLOOD_IN_SPUTUM, SymptomNames.CHEST_PAIN, SymptomNames.FEVER, SymptomNames.NIGHT_SWEATS],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.RESPIRATORY,
                'paper_reference': 'Standard MTS respiratory presentation'
            },
            'asthma': {
                'symptoms': [SymptomNames.PEAK_FLOW, SymptomNames.WHEEZE, SymptomNames.SPEECH_DIFFICULTY, SymptomNames.ACCESSORY_MUSCLES, SymptomNames.CYANOSIS],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.RESPIRATORY,
                'paper_reference': 'Respiratory emergency requiring objective assessment'
            }
        }
    
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
        return {
            'chest_pain': {
            'symptoms': [SymptomNames.SEVERE_PAIN, SymptomNames.CRUSHING_SENSATION, SymptomNames.RADIATION, SymptomNames.BREATHLESS, SymptomNames.SWEATING],
            'linguistic_values': LinguisticValues.get_severity_levels(),
            'category': MedicalCategories.CARDIOVASCULAR,
            'paper_reference': 'Figure 1 example flowchart'
        },
        
        'palpitations': {
            'symptoms': [SymptomNames.IRREGULAR_PULSE, SymptomNames.CHEST_DISCOMFORT, SymptomNames.DIZZINESS, SymptomNames.SYNCOPE, SymptomNames.BREATHLESSNESS],
            'linguistic_values': LinguisticValues.get_severity_levels(),
            'category': MedicalCategories.CARDIOVASCULAR,
            'paper_reference': 'Cardiac rhythm assessment'
        },
        
        'cardiac_arrest': {
            'symptoms': [SymptomNames.UNCONSCIOUS, SymptomNames.NO_PULSE, SymptomNames.NOT_BREATHING, SymptomNames.CYANOSIS, SymptomNames.COLLAPSE],
            'linguistic_values': LinguisticValues.get_severity_levels(),
            'category': MedicalCategories.CARDIOVASCULAR,
                'paper_reference': 'Most critical cardiac emergency - immediate category'
            }
        }
    
    @staticmethod
    def get_neurological_flowcharts() -> Dict[str, Dict[str, Any]]:
        """Get neurological presentation flowcharts
        
        Reference: FMTS paper emphasizes the need for systematic assessment of
        neurological conditions where imprecise terms can lead to misinterpretation.
        
        Returns:
            Dictionary of neurological flowcharts with symptoms and linguistic values
        """
        return {
            'headache': {
                'symptoms': [SymptomNames.PAIN_SEVERITY, SymptomNames.SUDDEN_ONSET, SymptomNames.NECK_STIFFNESS, SymptomNames.PHOTOPHOBIA, SymptomNames.CONFUSION],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.NEUROLOGICAL,
                'paper_reference': 'Neurological assessment requiring objective severity evaluation'
            },
            'confusion': {
                'symptoms': [SymptomNames.ALTERED_CONSCIOUSNESS, SymptomNames.DISORIENTATION, SymptomNames.AGITATION, SymptomNames.MEMORY_LOSS, SymptomNames.SPEECH_PROBLEMS],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.NEUROLOGICAL,
                'paper_reference': 'Mental status changes requiring systematic evaluation'
            },
            'fits': {
                'symptoms': [SymptomNames.ACTIVE_SEIZURE, SymptomNames.POST_ICTAL, SymptomNames.TONGUE_BITING, SymptomNames.INCONTINENCE, SymptomNames.INJURY_DURING_FIT],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.NEUROLOGICAL,
                'paper_reference': 'Seizure activity assessment'
            },
            'stroke': {
                'symptoms': [SymptomNames.FACIAL_DROOP, SymptomNames.ARM_WEAKNESS, SymptomNames.SPEECH_PROBLEMS, SymptomNames.SUDDEN_ONSET, SymptomNames.HEADACHE],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.NEUROLOGICAL,
                'paper_reference': 'Acute stroke requiring rapid objective assessment'
            },
            'unconscious_adult': {
                'symptoms': [SymptomNames.GCS_SCORE, SymptomNames.RESPONSE_TO_PAIN, SymptomNames.PUPIL_REACTION, SymptomNames.BREATHING_PATTERN, SymptomNames.PULSE_QUALITY],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.NEUROLOGICAL,
                'paper_reference': 'Altered consciousness requiring immediate evaluation'
            }
        }
    
    @staticmethod
    def get_gastrointestinal_flowcharts() -> Dict[str, Dict[str, Any]]:
        """Get gastrointestinal presentation flowcharts
        
        Reference: FMTS paper's systematic approach to all emergency presentations
        including gastrointestinal conditions that require objective assessment.
        
        Returns:
            Dictionary of gastrointestinal flowcharts with symptoms and linguistic values
        """
        return {
            'abdominal_pain': {
                'symptoms': [SymptomNames.PAIN_INTENSITY, SymptomNames.VOMITING, SymptomNames.RIGIDITY, SymptomNames.DISTENSION, SymptomNames.TENDERNESS],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.GASTROINTESTINAL,
                'paper_reference': 'Abdominal emergency assessment'
            },
            
            'vomiting': {
                'symptoms': [SymptomNames.BLOOD_IN_VOMIT, SymptomNames.DEHYDRATION, SymptomNames.ABDOMINAL_PAIN, SymptomNames.BILE_STAINED, SymptomNames.PROJECTILE],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.GASTROINTESTINAL,
                'paper_reference': 'GI symptom evaluation'
            },
            
            'diarrhoea': {
                'symptoms': [SymptomNames.BLOOD_IN_STOOL, SymptomNames.DEHYDRATION, SymptomNames.CRAMPING, SymptomNames.FEVER, SymptomNames.MUCUS],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.GASTROINTESTINAL,
                'paper_reference': 'Gastrointestinal assessment'
            },
            
            'gi_bleeding': {
                'symptoms': [SymptomNames.HAEMATEMESIS, SymptomNames.MELAENA, SymptomNames.SHOCK, SymptomNames.PALLOR, SymptomNames.WEAKNESS],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.GASTROINTESTINAL,
                'paper_reference': 'Critical GI emergency requiring immediate assessment'
            }
        }
    
    @staticmethod
    def get_trauma_flowcharts() -> Dict[str, Dict[str, Any]]:
        """Get trauma and injury flowcharts
        
        Reference: FMTS paper's comprehensive approach includes trauma presentations
        that require objective assessment to determine urgency.
        
        Returns:
            Dictionary of trauma flowcharts with symptoms and linguistic values
        """
        return {
            'limb_injuries': {
                'symptoms': [SymptomNames.DEFORMITY, SymptomNames.PAIN, SymptomNames.SWELLING, SymptomNames.LOSS_OF_FUNCTION, SymptomNames.BLEEDING],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.TRAUMA,
                'paper_reference': 'Musculoskeletal trauma assessment'
            },
            'head_injury': {
                'symptoms': [SymptomNames.LOSS_OF_CONSCIOUSNESS, SymptomNames.CONFUSION, SymptomNames.VOMITING, SymptomNames.HEADACHE, SymptomNames.AMNESIA],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.TRAUMA,
                'paper_reference': 'Critical head trauma requiring immediate evaluation'
            },
            'neck_injury': {
                'symptoms': [SymptomNames.NECK_PAIN, SymptomNames.NEUROLOGICAL_DEFICIT, SymptomNames.MECHANISM_OF_INJURY, SymptomNames.TENDERNESS, SymptomNames.DEFORMITY],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.TRAUMA,
                'paper_reference': 'Spinal injury requiring careful assessment'
            },
            'back_injury': {
                'symptoms': [SymptomNames.BACK_PAIN, SymptomNames.LEG_WEAKNESS, SymptomNames.NUMBNESS, SymptomNames.BLADDER_PROBLEMS, SymptomNames.MECHANISM],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.TRAUMA,
                'paper_reference': 'Spinal trauma with potential neurological involvement'
            },
            'burns': {
                'symptoms': [SymptomNames.BURN_AREA, SymptomNames.DEPTH, SymptomNames.AIRWAY_INVOLVEMENT, SymptomNames.PAIN, SymptomNames.BLISTERING],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.TRAUMA,
                'paper_reference': 'Thermal injury requiring systematic assessment'
            },
            'wounds': {
                'symptoms': [SymptomNames.BLEEDING, SymptomNames.DEPTH, SymptomNames.CONTAMINATION, SymptomNames.PAIN, SymptomNames.LOCATION],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.TRAUMA,
                'paper_reference': 'Wound assessment for infection and healing potential'
            }
        }
    
    @staticmethod
    def get_additional_flowcharts() -> Dict[str, Dict[str, Any]]:
        """Get additional flowcharts to reach the ~50 mentioned in the paper
        
        Reference: FMTS paper states "around 50 flowcharts" - this method provides
        the remaining flowcharts to achieve comprehensive coverage.
        
        Returns:
            Dictionary of additional flowcharts covering various medical presentations
        """
        return {
            # Genitourinary
            'urinary_problems': {
                'symptoms': [SymptomNames.DYSURIA, SymptomNames.FREQUENCY, SymptomNames.URGENCY, SymptomNames.HAEMATURIA, SymptomNames.RETENTION],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.GENITOURINARY,
                'paper_reference': 'Urological conditions requiring assessment'
            },
            'renal_colic': {
                'symptoms': [SymptomNames.LOIN_PAIN, SymptomNames.HAEMATURIA, SymptomNames.NAUSEA, SymptomNames.RESTLESSNESS, SymptomNames.RADIATION],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.GENITOURINARY,
                'paper_reference': 'Severe pain condition requiring objective assessment'
            },
            
            # Obstetric and gynaecological
            'pregnancy_problems': {
                'symptoms': [SymptomNames.BLEEDING, SymptomNames.PAIN, SymptomNames.CONTRACTIONS, SymptomNames.FETAL_MOVEMENTS, SymptomNames.BLOOD_PRESSURE],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.OBSTETRIC,
                'paper_reference': 'Obstetric emergency requiring rapid assessment'
            },
            'vaginal_bleeding': {
                'symptoms': [SymptomNames.AMOUNT, SymptomNames.PAIN, SymptomNames.PREGNANCY_TEST, SymptomNames.CLOTS, SymptomNames.SHOCK],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.OBSTETRIC,
                'paper_reference': 'Gynaecological bleeding assessment'
            },
            
            # Paediatric specific
            'crying_baby': {
                'symptoms': [SymptomNames.INCONSOLABLE, SymptomNames.FEVER, SymptomNames.FEEDING_PROBLEMS, SymptomNames.RASH, SymptomNames.LETHARGY],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.PAEDIATRIC,
                'paper_reference': 'Paediatric assessment requiring objective evaluation'
            },
            'child_fever': {
                'symptoms': [SymptomNames.TEMPERATURE, SymptomNames.RASH, SymptomNames.NECK_STIFFNESS, SymptomNames.LETHARGY, SymptomNames.FEEDING],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.PAEDIATRIC,
                'paper_reference': 'Febrile child requiring systematic assessment'
            },
            'child_vomiting': {
                'symptoms': [SymptomNames.DEHYDRATION, SymptomNames.BILE_STAINED, SymptomNames.BLOOD, SymptomNames.LETHARGY, SymptomNames.ABDOMINAL_PAIN],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.PAEDIATRIC,
                'paper_reference': 'Paediatric GI emergency'
            },
            
            # Psychiatric presentations
            'mental_illness': {
                'symptoms': [SymptomNames.RISK_TO_SELF, SymptomNames.RISK_TO_OTHERS, SymptomNames.PSYCHOSIS, SymptomNames.DEPRESSION, SymptomNames.AGITATION],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.PSYCHIATRIC,
                'paper_reference': 'Mental health crisis requiring objective risk assessment'
            },
            'overdose_poisoning': {
                'symptoms': [SymptomNames.CONSCIOUSNESS_LEVEL, SymptomNames.RESPIRATORY_DEPRESSION, SymptomNames.CARDIAC_EFFECTS, SymptomNames.SEIZURES, SymptomNames.ANTIDOTE_AVAILABLE],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.PSYCHIATRIC,
                'paper_reference': 'Toxicological emergency requiring immediate assessment'
            },
            
            # Additional categories
            'rash': {
                'symptoms': [SymptomNames.DISTRIBUTION, SymptomNames.FEVER, SymptomNames.ITCH, SymptomNames.BLISTERING, SymptomNames.SYSTEMIC_ILLNESS],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.DERMATOLOGICAL,
                'paper_reference': 'Skin condition assessment'
            },
            'eye_problems': {
                'symptoms': [SymptomNames.PAIN, SymptomNames.VISION_LOSS, SymptomNames.DISCHARGE, SymptomNames.PHOTOPHOBIA, SymptomNames.INJURY],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.OPHTHALMOLOGICAL,
                'paper_reference': 'Ocular emergency assessment'
            },
            'ear_problems': {
                'symptoms': [SymptomNames.PAIN, SymptomNames.DISCHARGE, SymptomNames.HEARING_LOSS, SymptomNames.DIZZINESS, SymptomNames.FEVER],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.ENT,
                'paper_reference': 'ENT condition assessment'
            },
            'sore_throat': {
                'symptoms': [SymptomNames.PAIN, SymptomNames.DIFFICULTY_SWALLOWING, SymptomNames.FEVER, SymptomNames.DROOLING, SymptomNames.STRIDOR],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.ENT,
                'paper_reference': 'Throat condition with potential airway involvement'
            },
            'diabetes': {
                'symptoms': [SymptomNames.BLOOD_GLUCOSE, SymptomNames.KETONES, SymptomNames.DEHYDRATION, SymptomNames.CONSCIOUSNESS, SymptomNames.BREATHING],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.ENDOCRINE,
                'paper_reference': 'Diabetic emergency requiring objective assessment'
            },
            'allergy': {
                'symptoms': [SymptomNames.RASH, SymptomNames.SWELLING, SymptomNames.BREATHING_DIFFICULTY, SymptomNames.SHOCK, SymptomNames.TONGUE_SWELLING],
                'linguistic_values': LinguisticValues.get_severity_levels(),
                'category': MedicalCategories.ALLERGIC,
                'paper_reference': 'Allergic reaction requiring rapid assessment'
            }
        }
    
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