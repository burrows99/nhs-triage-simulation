from typing import Dict, Any, List
import logging
from src.config.parameters import p

logger = logging.getLogger(__name__)

class ConfigManager:
    """Central configuration manager for the NHS Triage System"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_simulation_config(self) -> Dict[str, Any]:
        """Get simulation runtime configuration"""
        return {
            'duration': p.sim_duration,
            'warm_up': p.warm_up,
            'patient_arrival_rate': p.inter,
            'expected_arrivals_per_hour': 60 / p.inter
        }
    
    def get_resource_config(self) -> Dict[str, int]:
        """Get ED resource configuration"""
        return {
            'doctors': p.num_doctors,
            'nurses': p.num_nurses,
            'cubicles': p.num_cubicles
        }
    
    def get_service_time_config(self) -> Dict[str, Dict[str, float]]:
        """Get service time configuration for different processes"""
        return {
            'consultation': {
                'mean': p.mean_consultation,
                'stdev': p.stdev_consultation
            },
            'triage': {
                'mean': p.mean_triage,
                'stdev': p.stdev_triage
            },
            'inpatient_wait': {
                'mean': p.mean_inpatient_wait,
                'stdev': 0  # Not specified in parameters
            }
        }
    
    def get_ollama_config(self) -> Dict[str, Any]:
        """Get Ollama LLM configuration"""
        import os
        return {
            'model': os.getenv('OLLAMA_MODEL', 'adrienbrault/biomistral-7b:Q2_K'),
            'base_url': 'http://ollama:11434',
            'request': {
                'timeout_sec': 600,
                'retries': 2,
                'options': {
                    'temperature': 0.02,
                    'top_p': 0.7,
                    'num_predict': 512,
                    'num_ctx': 1536,
                    'num_gpu': -1,
                    'num_thread': 4
                }
            },
            'cache_timeout_sec': 600,
            'precompute_timeout_sec': 300,
            'multi_agent': {
                'agents': {
                    'vital_signs_assessor': {
                        'enabled': True,
                        'weight': 0.25,
                        'focus': 'vital_signs',
                        'description': 'Analyzes blood pressure, heart rate, temperature, respiratory rate'
                    },
                    'symptom_assessor': {
                        'enabled': True,
                        'weight': 0.25,
                        'focus': 'symptoms',
                        'description': 'Evaluates chief complaint, pain levels, symptom severity'
                    },
                    'medical_history_assessor': {
                        'enabled': True,
                        'weight': 0.25,
                        'focus': 'medical_history',
                        'description': 'Reviews past conditions, medications, allergies, family history'
                    },
                    'demographic_assessor': {
                        'enabled': True,
                        'weight': 0.25,
                        'focus': 'demographics',
                        'description': 'Considers age, gender, pregnancy status, pediatric factors'
                    }
                },
                'parallel_processing': True,
                'consensus_method': 'weighted_average',
                'min_agents_required': 2
            }
        }
    
    def get_base_agent_prompt(self) -> str:
        """Get base prompt for all AI agents"""
        return """You are a medical AI assistant specializing in emergency department triage.
Your role is to assess patient priority based on medical data following NHS Manchester Triage System guidelines.

Priority Levels:
1 = Immediate (life-threatening, seen immediately)
2 = Very Urgent (potentially life-threatening, seen within 10 minutes)
3 = Urgent (serious condition, seen within 60 minutes)
4 = Standard (less urgent, seen within 120 minutes)
5 = Non-urgent (minor condition, seen within 240 minutes)

Always provide structured JSON responses with priority, reasoning, and confidence."""
    
    def get_dynamic_agent_prompt(self, agent_name: str, agent_config: Dict[str, Any], patient_data: Dict[str, Any] = None) -> str:
        """Generate dynamic agent prompt based on agent configuration"""
        base_prompt = self.get_base_agent_prompt()
        
        if not patient_data:
            return base_prompt + f"\n\nYou are the {agent_name} focusing on {agent_config.get('focus', 'general assessment')}."
        
        patient_info = self._extract_patient_info(patient_data)
        vital_signs_str = self._format_vital_signs(patient_data)
        comprehensive_context = self._get_comprehensive_context(patient_data)
        
        focus = agent_config.get('focus', 'general')
        description = agent_config.get('description', 'General medical assessment')
        
        # Focus-specific instructions
        focus_instructions = {
            'vital_signs': "Focus EXCLUSIVELY on vital signs: blood pressure, heart rate, temperature, respiratory rate, oxygen saturation. Ignore other factors.",
            'symptoms': "Focus EXCLUSIVELY on symptoms: chief complaint, pain levels, symptom severity, symptom duration. Ignore vital signs and history.",
            'medical_history': "Focus EXCLUSIVELY on medical history: past conditions, current medications, allergies, family history, chronic conditions. Ignore current symptoms.",
            'demographics': "Focus EXCLUSIVELY on demographic factors: age-specific risks, gender considerations, pregnancy status, pediatric factors. Ignore clinical data."
        }
        
        instruction = focus_instructions.get(focus, "Perform general medical assessment.")
        
        return f"""{base_prompt}

{agent_name.upper().replace('_', ' ')} SPECIALIST ASSESSMENT:

Patient: {patient_info['age']}, {patient_info['gender']}
Chief Complaint: {patient_info['chief_complaint']}
Medical History: {patient_info['medical_history']}
Vital Signs: {vital_signs_str}{comprehensive_context}

Your specialized role: {description}

SPECIALIZATION INSTRUCTIONS:
{instruction}

Based ONLY on your area of expertise ({focus}), assess the triage priority (1-5):
- 1: Immediate (life-threatening)
- 2: Urgent (serious condition)
- 3: Less urgent (stable but needs care)
- 4: Standard (routine care)
- 5: Non-urgent (minor issues)

Return JSON: {{"mts_priority": number, "confidence": "high|medium|low", "rationale": "explanation based on {focus}", "service_min": number, "focus_area": "{focus}", "key_findings": ["finding1", "finding2"]}}"""
    
    def _extract_patient_info(self, patient_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract patient information using Patient entity standard field names"""
        # Use Patient entity's standard field names as defined in CSV_FIELDS
        # ['id', 'age', 'gender', 'chief_complaint', 'medical_history', ...]
        
        return {
            # Standard Patient entity fields (primary)
            'age': str(patient_data.get('age', 'Unknown')),
            'gender': str(patient_data.get('gender', 'Unknown')),
            'chief_complaint': str(patient_data.get('chief_complaint', 'Not specified')),
            'medical_history': str(patient_data.get('medical_history', 'No significant history')),
            
            # Legacy template compatibility (secondary - for old templates)
            'patient_age': str(patient_data.get('age', 'Unknown')),
            'patient_gender': str(patient_data.get('gender', 'Unknown')),
            'reason_description': str(patient_data.get('chief_complaint', 'Not specified')),
            'patient_history': str(patient_data.get('medical_history', 'No significant history'))
        }
    
    def _format_vital_signs(self, patient_data: Dict[str, Any]) -> str:
        """Format vital signs for display"""
        vital_signs = patient_data.get('vital_signs', {})
        if not vital_signs:
            return "Not recorded"
        
        signs = []
        for key, value in vital_signs.items():
            signs.append(f"{key}: {value}")
        return ", ".join(signs) if signs else "Not recorded"
    
    def _get_comprehensive_context(self, patient_data: Dict[str, Any]) -> str:
        """Get comprehensive patient context"""
        context_parts = []
        
        # Add medications if available
        medications = patient_data.get('medications', [])
        if medications:
            context_parts.append(f"\nMedications: {', '.join(medications)}")
        
        # Add allergies if available
        allergies = patient_data.get('allergies', [])
        if allergies:
            context_parts.append(f"\nAllergies: {', '.join(allergies)}")
        
        return ''.join(context_parts)

# Global configuration manager instance
config_manager = ConfigManager()

# Convenience functions for backward compatibility
def get_simulation_config() -> Dict[str, Any]:
    """Get simulation configuration"""
    return config_manager.get_simulation_config()

def get_resource_config() -> Dict[str, int]:
    """Get resource configuration"""
    return config_manager.get_resource_config()

def get_service_time_config() -> Dict[str, Dict[str, float]]:
    """Get service time configuration"""
    return config_manager.get_service_time_config()

def get_ollama_config() -> Dict[str, Any]:
    """Get Ollama configuration"""
    return config_manager.get_ollama_config()

def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration"""
    return {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    }

def configure_logging() -> None:
    """Configure logging for the application"""
    config = get_logging_config()
    logging.basicConfig(
        level=getattr(logging, config['level']),
        format=config['format']
    )

def get_manchester_triage_config() -> Dict[str, Any]:
    """Get Manchester Triage System configuration"""
    return {
        'enabled': True,
        'use_ai_enhancement': False,
        'priority_weights': {
            1: 1.0,  # Immediate - highest weight
            2: 0.8,  # Very urgent
            3: 0.6,  # Urgent
            4: 0.4,  # Standard
            5: 0.2   # Non-urgent - lowest weight
        },
        'fuzzy_rules': {
            'severe_symptoms': {
                'priority_1_threshold': 0.8,
                'priority_2_threshold': 0.6,
                'priority_3_threshold': 0.4,
                'priority_4_threshold': 0.2
            },
            'vital_signs_critical': {
                'systolic_bp_high': 180,
                'systolic_bp_low': 90,
                'heart_rate_high': 120,
                'heart_rate_low': 50,
                'temperature_high': 38.5,
                'respiratory_rate_high': 25
            },
            'age_factors': {
                 'pediatric_threshold': 16,
                 'elderly_threshold': 65,
                 'age_weight_multiplier': 1.2
             }
         },
         'time_factor': 1.0,  # Base time multiplier for Manchester Triage
         'priority_consultation_factors': {
             1: 1.5,  # Immediate - longer consultation
             2: 1.3,  # Very urgent
             3: 1.0,  # Urgent - standard time
             4: 0.8,  # Standard - shorter
             5: 0.7   # Non-urgent - shortest
         },
         'membership_functions': {
             'low_severity': {
                 'type': 'trapezoid',
                 'params': [0, 0, 0.2, 0.4]
             },
             'moderate_severity': {
                 'type': 'triangle',
                 'params': [0.2, 0.5, 0.8]
             },
             'high_severity': {
                 'type': 'trapezoid',
                 'params': [0.6, 0.8, 1.0, 1.0]
             },
             'critical_vitals': {
                 'type': 'trapezoid',
                 'params': [0.7, 0.9, 1.0, 1.0]
             }
         }
    }

def get_visualization_config() -> Dict[str, Any]:
    """Get visualization configuration"""
    return {
        'plot_style': 'seaborn',
        'figure_size': (10, 6),
        'dpi': 300
    }

def get_output_paths(triage_system_name: str) -> Dict[str, str]:
    """Get output paths for a triage system"""
    base_path = f"output/{triage_system_name}"
    return {
        'base': base_path,
        'csv': f"{base_path}/csv",
        'json': f"{base_path}/json",
        'plots': f"{base_path}/plots"
    }

def create_output_directories(triage_system_name: str) -> None:
    """Create output directories for a triage system"""
    import os
    paths = get_output_paths(triage_system_name)
    for path in paths.values():
        os.makedirs(path, exist_ok=True)

def get_patient_generation_config() -> Dict[str, Any]:
    """Get patient generation configuration"""
    return {
        'use_synthetic_data': True,
        'deep_context': True,
        'cycle_data': getattr(p, 'cycle_patient_data', True),
        'default_priority': 4  # Standard priority for triage failures
    }

def get_triage_actions_config() -> Dict[int, List[str]]:
    """Get triage actions by priority level"""
    return {
        1: ['immediate_resuscitation', 'call_trauma_team'],
        2: ['urgent_assessment', 'prepare_treatment_room'],
        3: ['standard_assessment', 'monitor_vitals'],
        4: ['routine_assessment', 'waiting_area'],
        5: ['basic_assessment', 'self_care_advice']
    }

# Modular prompt components for shared knowledge
def get_nhs_priority_guidelines() -> str:
    """Get NHS priority level definitions - shared across all agents"""
    return """NHS Priority Levels:
1 = Immediate (life-threatening)
2 = Very Urgent (potentially life-threatening, 10min)
3 = Urgent (serious condition, 60min)
4 = Standard (less urgent, 120min)
5 = Non-urgent (minor condition, 240min)"""

def get_json_format_instructions() -> str:
    """Get strict JSON output instructions - shared across all agents"""
    return """RESPOND ONLY WITH VALID JSON. DO NOT include explanations, markdown, or any text outside the JSON."""

def get_common_medical_knowledge() -> str:
    """Get common medical assessment factors - shared across all agents"""
    return """Consider: patient demographics, vital signs, symptoms, medical history, pain levels, and functional status."""

def get_base_triage_context() -> str:
    """Get base medical AI context - foundation for all triage agents"""
    return f"""You are a medical AI for NHS emergency department triage. Analyze patient data and respond with structured assessments.

{get_nhs_priority_guidelines()}

{get_common_medical_knowledge()}

{get_json_format_instructions()}"""

# Legacy function aliases for backward compatibility
def get_base_agent_prompt() -> str:
    """Get base agent prompt"""
    return get_base_triage_context()

def get_single_agent_prompt(patient_data: Dict[str, Any] = None) -> str:
    """Get single agent system prompt using modular components"""
    return f"""{get_base_triage_context()}

RESPOND ONLY WITH THIS EXACT JSON FORMAT:
{{
  "mts_priority": <integer 1-5>,
  "confidence": "<high|medium|low>",
  "rationale": "<brief clinical reasoning>",
  "service_min": <integer minutes>,
  "focus_area": "<primary clinical concern>",
  "key_findings": ["<finding1>", "<finding2>"]
}}"""

def get_pediatric_assessor_prompt(patient_data: Dict[str, Any] = None) -> str:
    """Get pediatric assessor system prompt using modular components"""
    return f"""{get_base_triage_context()}

Specialization: Pediatric emergency medicine (patients under 16 years).
Additional considerations: age-appropriate vital signs, developmental stage, pediatric early warning scores.

RESPOND ONLY WITH THIS EXACT JSON FORMAT:
{{
  "pediatric_risk": "<low|medium|high>",
  "age_calculated": <patient age>,
  "mandatory_rules_triggered": ["<rule1>", "<rule2>"],
  "priority_recommendation": <integer 1-5>,
  "rationale": "<brief pediatric reasoning>"
}}"""

def get_clinical_assessor_prompt(patient_data: Dict[str, Any] = None, pediatric_assessment: str = "") -> str:
    """Get clinical assessor system prompt using modular components"""
    return f"""{get_base_triage_context()}

Specialization: Senior emergency medicine physician.
Additional focus: symptom severity, differential diagnosis, comorbidity impact, medication interactions.
If pediatric assessment provided, integrate those findings.

RESPOND ONLY WITH THIS EXACT JSON FORMAT:
{{
  "clinical_priority": <integer 1-5>,
  "severity_assessment": "<brief severity description>",
  "immediate_interventions": ["<action1>", "<action2>"],
  "monitoring_requirements": "<monitoring needs>",
  "rationale": "<brief clinical reasoning>",
  "confidence_level": <float 0.0-1.0>
}}"""

def get_consensus_coordinator_prompt(patient_data: Dict[str, Any] = None, pediatric_assessment: str = "", clinical_assessment: str = "") -> str:
    """Get consensus coordinator system prompt using modular components"""
    return f"""{get_base_triage_context()}

Specialization: Senior triage coordinator - synthesize multiple assessments.
Decision framework: If assessments agree, validate; if they differ, choose higher priority for safety.
Consider: pediatric and clinical inputs, resource availability, patient complexity.

RESPOND ONLY WITH THIS EXACT JSON FORMAT:
{{
  "mts_priority": <integer 1-5>,
  "confidence": "<high|medium|low>",
  "rationale": "<brief consensus reasoning>",
  "service_min": <integer minutes>,
  "consensus_method": "<agreement_type>",
  "critical_history_factors": ["<factor1>", "<factor2>"]
}}"""