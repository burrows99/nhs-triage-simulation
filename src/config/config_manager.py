from typing import Dict, Any, List
import logging
from src.config import parameters as p

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
            'doctors': p.number_docs,
            'nurses': p.number_nurses,
            'cubicles': p.ae_cubicles
        }
    
    def get_service_time_config(self) -> Dict[str, Dict[str, float]]:
        """Get service time configuration for different processes"""
        return {
            'doctor_consult': {
                'mean': p.mean_doc_consult,
                'stdev': p.stdev_doc_consult
            },
            'nurse_triage': {
                'mean': p.mean_nurse_triage,
                'stdev': p.stdev_nurse_triage
            },
            'inpatient_wait': {
                'mean': p.mean_ip_wait,
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
                    'num_predict': 75,
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

Patient: {patient_info['patient_age']}, {patient_info['patient_gender']}
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
        """Extract basic patient information"""
        return {
            'patient_age': str(patient_data.get('age', 'Unknown')),
            'patient_gender': str(patient_data.get('gender', 'Unknown')),
            'chief_complaint': str(patient_data.get('chief_complaint', 'Not specified')),
            'medical_history': str(patient_data.get('medical_history', 'No significant history'))
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
        'cycle_data': getattr(p, 'cycle_patient_data', True)
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

# Legacy function aliases for backward compatibility
def get_base_agent_prompt() -> str:
    """Get base agent prompt"""
    return config_manager.get_base_agent_prompt()

def get_single_agent_prompt(patient_data: Dict[str, Any] = None) -> str:
    """Get single agent prompt"""
    return config_manager.get_base_agent_prompt()

def get_pediatric_assessor_prompt(patient_data: Dict[str, Any] = None) -> str:
    """Get pediatric assessor prompt"""
    return config_manager.get_base_agent_prompt()

def get_clinical_assessor_prompt(patient_data: Dict[str, Any] = None, pediatric_assessment: str = "") -> str:
    """Get clinical assessor prompt"""
    return config_manager.get_base_agent_prompt()

def get_consensus_coordinator_prompt(patient_data: Dict[str, Any] = None, pediatric_assessment: str = "", clinical_assessment: str = "") -> str:
    """Get consensus coordinator prompt"""
    return config_manager.get_base_agent_prompt()