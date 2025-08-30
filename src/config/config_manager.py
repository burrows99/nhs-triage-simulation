"""Configuration management system for NHS Triage Simulation

This module provides centralized configuration management, extracting hardcoded values
and configuration logic from across the codebase into reusable functions.
"""

import logging
import sys
import os
from typing import Dict, List, Any, Tuple
from .parameters import p
from .constants import SymptomSeverity, LogMessages, PriorityLabels, PlotTitles


class ConfigManager:
    """Centralized configuration manager for the NHS Triage Simulation"""
    
    def __init__(self):
        self._logging_configured = False
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get comprehensive logging configuration"""
        return {
            'level': logging.DEBUG,
            'format': '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            'handlers': [
                logging.FileHandler('output/simulation.log', mode='a'),
                logging.StreamHandler(sys.stdout)
            ],
            'module_levels': {
                'matplotlib': logging.WARNING,
                'matplotlib.pyplot': logging.WARNING,
                'matplotlib.font_manager': logging.WARNING,
                'PIL': logging.WARNING,
                'simpy': logging.INFO,
                'numpy': logging.WARNING,
                'pandas': logging.WARNING,
                'scipy': logging.WARNING
            }
        }
    
    def configure_logging(self) -> None:
        """Configure logging with centralized settings"""
        if self._logging_configured:
            return
            
        config = self.get_logging_config()
        
        # Configure basic logging
        logging.basicConfig(
            level=config['level'],
            format=config['format'],
            handlers=config['handlers']
        )
        
        # Set module-specific log levels
        for module_name, level in config['module_levels'].items():
            logging.getLogger(module_name).setLevel(level)
        
        self._logging_configured = True
        logger = logging.getLogger(__name__)
        logger.info("Logging configuration applied successfully")
    
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
        """Get service time parameters for different processes"""
        return {
            'triage': {
                'mean': p.mean_nurse_triage,
                'stdev': p.stdev_nurse_triage
            },
            'consultation': {
                'mean': p.mean_doc_consult,
                'stdev': p.stdev_doc_consult
            },
            'admission_wait': {
                'mean': p.mean_ip_wait
            }
        }
    
    def get_manchester_triage_config(self) -> Dict[str, Any]:
        """Get Manchester Triage System specific configuration"""
        return {
            'priority_weights': [0.05, 0.15, 0.3, 0.3, 0.2],  # Priorities 1-5
            'membership_functions': {
                'very_low': {'type': 'trapezoid', 'params': [0, 0, 0.1, 0.3]},
                'low': {'type': 'triangle', 'params': [0.2, 0.4, 0.6]},
                'medium': {'type': 'triangle', 'params': [0.4, 0.6, 0.8]},
                'high': {'type': 'triangle', 'params': [0.6, 0.8, 1.0]},
                'very_high': {'type': 'trapezoid', 'params': [0.7, 0.9, 1, 1]}
            },
            'fuzzy_rules': [
                {'conditions': ['very_high'], 'output': 1},
                {'conditions': ['high'], 'output': 2},
                {'conditions': ['medium'], 'output': 3},
                {'conditions': ['low'], 'output': 4},
                {'conditions': ['very_low'], 'output': 5}
            ],
            'time_factor': 1.2,  # MTS takes longer than simple triage
            'priority_consultation_factors': {
                1: 1.5,  # Immediate - 1.5x base time
                2: 1.3,  # Very urgent - 1.3x base time
                3: 1.0,  # Urgent - 1.0x base time
                4: 0.8,  # Standard - 0.8x base time
                5: 0.7   # Non-urgent - 0.7x base time
            }
        }
    
    def get_triage_actions_config(self) -> Dict[int, List[str]]:
        """Get recommended actions by priority level"""
        return {
            1: ["Immediate resuscitation", "Life-saving interventions", "Continuous monitoring"],
            2: ["Urgent review", "Rapid assessment", "Close monitoring"],
            3: ["Routine monitoring", "Standard assessment", "Regular checks"],
            4: ["Standard care", "Routine assessment", "Periodic monitoring"],
            5: ["Basic care", "Routine check", "Standard monitoring"]
        }
    
    def get_visualization_config(self) -> Dict[str, Any]:
        """Get visualization and plotting configuration"""
        return {
            'output_base_dir': 'output',
            'plot_formats': ['png'],
            'figure_size': (10, 6),
            'dpi': 300,
            'style': 'default',
            'colors': {
                'priority_1': '#FF0000',  # Red - Immediate
                'priority_2': '#FF8C00',  # Orange - Very Urgent
                'priority_3': '#FFD700',  # Yellow - Urgent
                'priority_4': '#32CD32',  # Green - Standard
                'priority_5': '#0000FF'   # Blue - Non-Urgent
            }
        }
    
    def get_patient_generation_config(self) -> Dict[str, Any]:
        """Get patient generation parameters"""
        return {
            'severity_distribution': SymptomSeverity.LEVELS,
            'priority_weights': [0.05, 0.15, 0.3, 0.3, 0.2],
            'admission_probability': 0.3,  # 30% of patients get admitted
            'default_priority': 3  # Default to Urgent if triage fails
        }
    
    def get_output_paths_config(self, triage_system_name: str) -> Dict[str, str]:
        """Get output directory paths for different data types"""
        base_dir = f"output/{triage_system_name}"
        return {
            'base': base_dir,
            'plots': f"{base_dir}/plots",
            'json': f"{base_dir}/json",
            'csv': f"{base_dir}/csv",
            'logs': "output"
        }
    
    def get_validation_config(self) -> Dict[str, Any]:
        """Get validation and error handling configuration"""
        return {
            'required_patient_keys': ['id', 'severity'],
            'required_triage_keys': {'priority', 'rationale', 'recommended_actions'},
            'priority_range': (1, 5),
            'severity_range': (0.0, 1.0),
            'max_retries': 3,
            'timeout_seconds': 30
        }
    
    def create_output_directories(self, triage_system_name: str) -> None:
        """Create all necessary output directories"""
        paths = self.get_output_paths_config(triage_system_name)
        for path in paths.values():
            os.makedirs(path, exist_ok=True)
    
    def get_performance_thresholds(self) -> Dict[str, float]:
        """Get performance monitoring thresholds"""
        return {
            'max_wait_time_minutes': 240,  # 4 hours max wait
            'target_triage_time_minutes': 15,  # Target triage within 15 minutes
            'target_consultation_time_minutes': 60,  # Target consultation within 1 hour
            'min_throughput_patients_per_hour': 10,
            'max_queue_length': 20
        }
    
    def get_ollama_config(self) -> Dict[str, Any]:
        """Get Ollama LLM configuration for triage systems"""
        return {
            'model': 'llama3.2:1b',
            'base_url': 'http://ollama:11434',  # Docker service name
            'request': {
                'timeout_sec': 60,  # Longer timeout for real LLM processing
                'retries': 2,       # More retries for reliability
                'options': {
                    'temperature': 0.02,
                    'top_p': 0.7,
                    'num_predict': 75,  # Adequate response length
                    'num_ctx': 1536,    # Full context for medical reasoning
                    'num_gpu': -1,
                    'num_thread': 4
                }
            },
            'single_agent': {
                'options': {
                    'temperature': 0.3,
                    'num_predict': 150
                }
            },
            'multi_agent': {
                'agents': [
                    {'name': 'pediatric_risk_assessor'},
                    {'name': 'clinical_assessor'},
                    {'name': 'consensus_coordinator'}
                ]
            }
        }
    
    def get_base_agent_prompt(self) -> str:
        """Get base agent system prompt template"""
        return """
**Required Context:**
- Patient: {patient_age}, {patient_gender}
- History: {patient_history}
- Vitals: {vital_signs}
- MTS Guidelines: {mts_priorities}

**MANDATORY STEP 1: CRITICAL HISTORY ASSESSMENT (ALWAYS FIRST):**

**ESSENTIAL HISTORY FACTORS - EVALUATE EVERY PATIENT:**
- **Cardiac Risk**: Known CAD, previous MI, diabetes, hypertension, cardiac medications, smoking history
- **Respiratory History**: Asthma, COPD, home oxygen, previous intubations, chronic respiratory conditions
- **Medications (Critical)**: Anticoagulants, immunosuppressants, insulin, psychiatric medications, recent changes
- **High-Risk Conditions**: Active cancer, immunocompromised state, dialysis, pregnancy status, transplant
- **Recent Medical Events**: Surgery, hospitalizations, functional decline, new symptom progression
- **Social/Behavioral**: Substance use, mental health history, recent travel, living situation
- **Pediatric-Specific**: Birth history, immunization status, previous serious infections, developmental issues

**HISTORY-MODIFIED ACUITY RULES (MANDATORY APPLICATION):**
- Known cardiac disease + chest symptoms → Consider upgrading priority
- Anticoagulants + trauma/bleeding → Consider upgrading priority
- Immunocompromised + fever/infection → Consider upgrading priority
- Previous respiratory failure + shortness of breath → Consider upgrading priority
- Cancer patient + new concerning symptoms → Consider upgrading priority
- Mental health history + psychiatric presentation → Assess suicide/violence risk
- **If critical history missing or unclear → Err toward higher acuity for patient safety**

**Age Handling Instructions:**
- If patient_age is empty/unknown, calculate from birthdate in patient demographics
- For pediatric rules: if age unclear, err on side of caution (assume younger age category)
- Always state actual age used in your reasoning

**Response Format Rules:**
- Strict JSON output only
- Required fields:
  - "mts_priority" (1-5)
  - "confidence" (high|medium|low)
  - "rationale" (brief justification including history factors)
  - "service_min" (estimate minutes for treatment)
  - "critical_history_factors" (list of relevant history elements)
  - "history_risk_modifier" (increases|decreases|neutral)
- No additional text or formatting
**Response Limits:**
- Max JSON length: 2500 chars (increased for history)
- Min explanation: 20 chars
- Max explanation: 600 chars
"""
    
    def get_single_agent_prompt(self) -> str:
        """Get single agent system prompt template"""
        return """
Triage Assessment Required - EVIDENCE-BASED PRIORITIZATION:

**MANDATORY PEDIATRIC RULES (NON-NEGOTIABLE):**
- Infants <3 months with fever ≥38°C → Priority 2 (Seiger 2011)
- Oxygen saturation <92% → Priority 2 (Van Veen 2008)
- Non-blanching rash → Priority 1 (Nijman 2011)
- Altered consciousness in children → Priority 2 (Van Veen 2008)
- Not feeding in infants <1 year → Priority 2 (PMC5016055)

Patient: {patient_age}, {patient_gender}
Chief Complaint: {reason_description}
Medical History: {patient_history}
Vital Signs: {vital_signs}
Full Patient Data: {clinical_context}

MTS Priorities (REAL-WORLD DISTRIBUTION - PMC5016055):
1=Life threat (0.4% of cases), 2=Very urgent (16.4%),
3=Urgent (43.6%), 4=Standard (34.0%), 5=Non-urgent (0.6%)

**Critical Instructions:**
1. FIRST: Calculate patient age from birthdate if patient_age is empty (use clinical_context)
2. NEVER assign Priority 1 unless life-threatening condition confirmed
3. For infants <3 months with fever, ALWAYS assign Priority 2
4. Target distribution: P1(0.4%), P2(16.4%), P3(43.6%), P4(34.0%), P5(0.6%)
5. If age unclear, err on side of caution for pediatric rules
6. Apply evidence-based mandatory rules FIRST, then general assessment
7. Service time estimates: P1=30-60min, P2=25-40min, P3=20-30min, P4=15-25min, P5=10-20min
8. Always state the actual age you calculated/used in your rationale

Return JSON: {{"mts_priority": number, "confidence": "high|medium|low", "rationale": "evidence-based clinical reason", "service_min": number, "mandatory_rule_applied": boolean}}
"""
    
    def get_pediatric_assessor_prompt(self) -> str:
        """Get pediatric risk assessor system prompt template"""
        return """
PEDIATRIC-SPECIFIC RISK ASSESSMENT (EVIDENCE-BASED - MANDATORY FIRST LAYER):

**MANDATORY RULES (NON-NEGOTIABLE - Seiger 2011, Van Veen 2008, Nijman 2011):**
1. Infants <3 months with fever ≥38°C → Priority 2 (Seiger 2011: OR 4.2, CI 2.3-7.7)
2. Oxygen saturation <92% → Priority 2 (Van Veen 2008: BMJ validation)
3. Non-blanching rash → Priority 1 (Nijman 2011: meningitis risk)
4. Altered consciousness in children → Priority 2 (Van Veen 2008)
5. Not feeding in infants <1 year → Priority 2 (PMC5016055)
6. Severe dehydration signs → Priority 2
7. Respiratory distress with accessory muscles → Priority 2

Patient Data: {clinical_context}
Age: {patient_age} | Gender: {patient_gender}
Vitals: {vital_signs}

**Assessment Focus:**
- Calculate exact age if missing from birthdate
- Apply mandatory pediatric rules strictly
- Assess developmental appropriateness
- Consider parental concern level

Return JSON: {{"pediatric_risk": "high|medium|low", "mandatory_rules_triggered": ["rule_list"], "age_calculated": "actual_age", "priority_recommendation": number, "rationale": "pediatric-specific reasoning"}}
"""
    
    def get_clinical_assessor_prompt(self) -> str:
        """Get clinical assessor system prompt template"""
        return """
CLINICAL ASSESSMENT LAYER (EVIDENCE-BASED GENERAL MEDICINE):

Patient: {patient_age}, {patient_gender}
Chief Complaint: {reason_description}
History: {patient_history}
Vitals: {vital_signs}
Pediatric Assessment: {pediatric_assessment}

**Clinical Decision Rules:**
- Chest pain + cardiac risk factors → Consider Priority 2-3
- Shortness of breath + history → Priority 2-3
- Severe pain (>7/10) → Priority 2-3
- Vital sign abnormalities → Upgrade priority
- Mental health crisis → Priority 2-3
- Trauma mechanism → Priority 1-3

**Integration Rules:**
- If pediatric assessment suggests high risk → Follow pediatric recommendation
- Adult patients → Apply standard MTS flowcharts
- Consider comorbidities and medications
- Assess functional status changes

Return JSON: {{"clinical_priority": number, "confidence": "high|medium|low", "key_findings": ["finding_list"], "rationale": "clinical reasoning", "service_min": number}}
"""
    
    def get_consensus_coordinator_prompt(self) -> str:
        """Get consensus coordinator system prompt template"""
        return """
CONSENSUS COORDINATION (FINAL DECISION LAYER):

Pediatric Assessment: {pediatric_assessment}
Clinical Assessment: {clinical_assessment}
Patient Context: {clinical_context}

**Consensus Rules:**
1. If pediatric mandatory rule triggered → Use pediatric priority
2. If assessments differ by >1 priority level → Use higher priority (safety)
3. If both agree → Confirm final priority
4. Consider real-world distribution targets
5. Ensure rationale integrates both assessments

**Final Validation:**
- Priority 1: Life-threatening confirmed?
- Priority 2: Urgent care needed within 10 minutes?
- Priority 3-5: Appropriate for wait times?

**Distribution Check (PMC5016055):**
P1(0.4%), P2(16.4%), P3(43.6%), P4(34.0%), P5(0.6%)

Return JSON: {{"mts_priority": number, "confidence": "high|medium|low", "rationale": "integrated clinical reasoning", "service_min": number, "consensus_method": "description", "critical_history_factors": ["factors"], "history_risk_modifier": "increases|decreases|neutral"}}
"""


# Global configuration manager instance
config_manager = ConfigManager()


# Convenience functions for easy access
def get_logging_config() -> Dict[str, Any]:
    """Get logging configuration"""
    return config_manager.get_logging_config()


def configure_logging() -> None:
    """Configure application logging"""
    config_manager.configure_logging()


def get_simulation_config() -> Dict[str, Any]:
    """Get simulation configuration"""
    return config_manager.get_simulation_config()


def get_resource_config() -> Dict[str, int]:
    """Get resource configuration"""
    return config_manager.get_resource_config()


def get_service_time_config() -> Dict[str, Dict[str, float]]:
    """Get service time configuration"""
    return config_manager.get_service_time_config()


def get_manchester_triage_config() -> Dict[str, Any]:
    """Get Manchester Triage System configuration"""
    return config_manager.get_manchester_triage_config()


def get_visualization_config() -> Dict[str, Any]:
    """Get visualization configuration"""
    return config_manager.get_visualization_config()


def get_output_paths(triage_system_name: str) -> Dict[str, str]:
    """Get output paths for a triage system"""
    return config_manager.get_output_paths_config(triage_system_name)


def create_output_directories(triage_system_name: str) -> None:
    """Create output directories for a triage system"""
    config_manager.create_output_directories(triage_system_name)


def get_patient_generation_config() -> Dict[str, Any]:
    """Get patient generation configuration"""
    return config_manager.get_patient_generation_config()


def get_triage_actions_config() -> Dict[int, List[str]]:
    """Get triage actions configuration"""
    return config_manager.get_triage_actions_config()


def get_ollama_config() -> Dict[str, Any]:
    """Get Ollama LLM configuration"""
    return config_manager.get_ollama_config()


def get_base_agent_prompt() -> str:
    """Get base agent system prompt template"""
    return config_manager.get_base_agent_prompt()


def get_single_agent_prompt() -> str:
    """Get single agent system prompt template"""
    return config_manager.get_single_agent_prompt()


def get_pediatric_assessor_prompt() -> str:
    """Get pediatric risk assessor system prompt template"""
    return config_manager.get_pediatric_assessor_prompt()


def get_clinical_assessor_prompt() -> str:
    """Get clinical assessor system prompt template"""
    return config_manager.get_clinical_assessor_prompt()


def get_consensus_coordinator_prompt() -> str:
    """Get consensus coordinator system prompt template"""
    return config_manager.get_consensus_coordinator_prompt()