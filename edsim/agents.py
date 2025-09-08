import random
from dataclasses import dataclass
from typing import List, Dict, Union

from .models import Patient
from .constants import SCENARIO_FACTOR

@dataclass
class RoutingAgent:
    """
    Agent responsible for routing patients to their initial and subsequent tasks/resources.
    - single_llm_accuracy: Probability (0-1) for single_llm scenario to correctly route red patients needing MRI directly to MRI
    - multi_llm_accuracy: Probability (0-1) for multi_llm scenario to correctly route red patients needing MRI directly to MRI
    Assumptions:
    - All patients always see a doctor unless specifically routed to MRI first (for critical cases).
    - Ultrasound is added if needed, after initial routing.
    - All patients end with bed assignment.
    - Rule-based is deterministic; LLM-based introduces probabilistic misrouting to simulate AI errors.
    """
    single_llm_accuracy: float = 0.8
    multi_llm_accuracy: float = 0.7

    def route(self, patient: Patient, scenario: str) -> List[str]:
        tasks: List[str] = []
        if scenario == 'rule_based':
            # Deterministic rule-based routing: doctor first, then imaging if needed, then bed
            tasks.append('doctor')
            if patient.needs_mri:
                tasks.append('mri')
            if patient.needs_ultrasound:
                tasks.append('ultrasound')
            tasks.append('bed')
        elif scenario == 'single_llm':
            # Single LLM routing: probabilistic accuracy for critical (red + MRI) cases
            if patient.triage == 'red' and patient.needs_mri and random.random() < self.single_llm_accuracy:
                tasks.append('mri')
            else:
                tasks.append('doctor')
            if patient.needs_ultrasound:
                tasks.append('ultrasound')
            tasks.append('bed')
        elif scenario == 'multi_llm':
            # Multi-LLM (mixture-of-agents) routing: uses accuracy to simulate ensemble variability
            if patient.triage == 'red' and patient.needs_mri and random.random() < self.multi_llm_accuracy:
                tasks.append('mri')
            else:
                tasks.append('doctor')
            if patient.needs_ultrasound:
                tasks.append('ultrasound')
            tasks.append('bed')
        return tasks
    
    def mock_llm_evaluation(self, patients: List[Patient], scenario: str) -> Dict[str, Union[float, int, str]]:
        """
        Comprehensive evaluation of routing decisions across all patient pathways.
        This method belongs in RoutingAgent as it evaluates routing decisions.
        """
        # Urgent MRI routing analysis (existing functionality)
        urgent_patients = [p for p in patients if p.triage == 'red' and p.needs_mri]
        total_urgent = len(urgent_patients)
        correct_bypasses = sum(1 for p in urgent_patients if p.tasks and p.tasks[0] == 'mri')
        simulated_accuracy = correct_bypasses / total_urgent if total_urgent > 0 else 0.0
        set_factor = SCENARIO_FACTOR[scenario]
        difference = abs(simulated_accuracy - set_factor)
        
        # Comprehensive routing pattern analysis
        total_patients = len(patients)
        
        # Analyze routing pathways
        doctor_only = sum(1 for p in patients if p.tasks == ['doctor', 'bed'])
        doctor_mri_bed = sum(1 for p in patients if p.tasks == ['doctor', 'mri', 'bed'])
        doctor_ultrasound_bed = sum(1 for p in patients if p.tasks == ['doctor', 'ultrasound', 'bed'])
        doctor_both_imaging_bed = sum(1 for p in patients if p.tasks == ['doctor', 'mri', 'ultrasound', 'bed'])
        direct_mri = sum(1 for p in patients if p.tasks and p.tasks[0] == 'mri')
        direct_ultrasound = sum(1 for p in patients if p.tasks and p.tasks[0] == 'ultrasound')
        
        # Triage distribution analysis
        triage_counts = {}
        for triage_level in ['red', 'orange', 'yellow', 'green', 'blue']:
            triage_counts[triage_level] = sum(1 for p in patients if p.triage == triage_level)
        
        # Imaging needs analysis
        mri_needed = sum(1 for p in patients if p.needs_mri)
        ultrasound_needed = sum(1 for p in patients if p.needs_ultrasound)
        both_imaging = sum(1 for p in patients if p.needs_mri and p.needs_ultrasound)
        no_imaging = sum(1 for p in patients if not p.needs_mri and not p.needs_ultrasound)
        
        note = (
            "Comprehensive evaluation: Assessed routing patterns across all patient pathways including "
            "urgent MRI routing, direct imaging access, doctor-only pathways, and triage-based routing efficiency. "
            "Ground truth: bypass doctor for urgent cases, optimize pathways based on patient needs."
        )
        
        return {
            # Existing urgent MRI metrics
            'simulated_accuracy': simulated_accuracy,
            'set_factor': set_factor,
            'difference': difference,
            'total_urgent': total_urgent,
            'correct_bypasses': correct_bypasses,
            
            # Comprehensive routing metrics
            'total_patients': total_patients,
            'doctor_only': doctor_only,
            'doctor_mri_bed': doctor_mri_bed,
            'doctor_ultrasound_bed': doctor_ultrasound_bed,
            'doctor_both_imaging_bed': doctor_both_imaging_bed,
            'direct_mri': direct_mri,
            'direct_ultrasound': direct_ultrasound,
            
            # Triage distribution
            'triage_red': triage_counts['red'],
            'triage_orange': triage_counts['orange'],
            'triage_yellow': triage_counts['yellow'],
            'triage_green': triage_counts['green'],
            'triage_blue': triage_counts['blue'],
            
            # Imaging needs
            'mri_needed': mri_needed,
            'ultrasound_needed': ultrasound_needed,
            'both_imaging': both_imaging,
            'no_imaging': no_imaging,
            
            'note': note
        }