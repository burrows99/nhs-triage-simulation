from dataclasses import dataclass
from typing import Dict, Any
from ..patient.patient import Patient
from ...enums.priority import Priority

@dataclass
class FuzzyManchesterTriage:
    """Basic fuzzy implementation of Manchester Triage System"""
    
    # Critical symptoms that indicate immediate attention (Red)
    critical_symptoms = {
        "cardiac arrest", "severe bleeding", "unconscious", "not breathing",
        "severe trauma", "anaphylaxis", "severe burns", "stroke symptoms"
    }
    
    # Very urgent symptoms (Orange)
    very_urgent_symptoms = {
        "chest pain", "difficulty breathing", "severe pain", "high fever",
        "sepsis", "severe headache", "seizure", "severe vomiting"
    }
    
    # Urgent symptoms (Yellow)
    urgent_symptoms = {
        "moderate pain", "abdominal pain", "fever", "headache",
        "nausea", "dizziness", "rash", "cough"
    }
    
    # Standard symptoms (Green)
    standard_symptoms = {
        "mild pain", "minor cut", "bruise", "cold symptoms",
        "sore throat", "minor burn", "sprain"
    }
    
    # Non-urgent symptoms (Blue)
    non_urgent_symptoms = {
        "minor headache", "mild rash", "minor scrape", "fatigue",
        "mild nausea", "minor ache"
    }
    
    def _normalize_scores(self, scores: Dict[Priority, float]) -> Dict[Priority, float]:
        """Normalize scores to sum to 1.0"""
        total_score = sum(scores.values())
        if total_score > 0:
            return {priority: score / total_score for priority, score in scores.items()}
        return scores
    
    def _match_symptom_to_priority(self, symptom: str) -> tuple[Priority, float]:
        """Match a symptom to its priority level and weight"""
        symptom_lower = symptom.lower().strip()
        
        # Priority mapping with weights
        priority_mapping = [
            (Priority.RED, 1.0, self.critical_symptoms),
            (Priority.ORANGE, 0.8, self.very_urgent_symptoms),
            (Priority.YELLOW, 0.6, self.urgent_symptoms),
            (Priority.GREEN, 0.4, self.standard_symptoms),
            (Priority.BLUE, 0.2, self.non_urgent_symptoms)
        ]
        
        for priority, weight, symptom_set in priority_mapping:
            if any(keyword in symptom_lower for keyword in symptom_set):
                return priority, weight
        
        return Priority.GREEN, 0.0  # Default to standard if no match
    
    def calculate_symptom_urgency_score(self, patient: Patient) -> Dict[Priority, float]:
        """Calculate fuzzy scores for each priority level based on patient symptoms"""
        scores = {Priority.RED: 0.0, Priority.ORANGE: 0.0, Priority.YELLOW: 0.0, Priority.GREEN: 0.0, Priority.BLUE: 0.0}
        
        symptoms = patient.symptoms.symptoms
        if not symptoms:
            return {Priority.RED: 0.0, Priority.ORANGE: 0.0, Priority.YELLOW: 0.0, Priority.GREEN: 0.0, Priority.BLUE: 1.0}
        
        for symptom in symptoms:
            priority, weight = self._match_symptom_to_priority(symptom)
            scores[priority] += weight
        
        return self._normalize_scores(scores)
    
    def _apply_symptom_count_rule(self, scores: Dict[Priority, float], symptom_count: int) -> None:
        """Apply fuzzy rule for multiple symptoms"""
        if symptom_count > 3:
            scores[Priority.RED] *= 1.2
            scores[Priority.ORANGE] *= 1.1
        elif symptom_count > 1:
            scores[Priority.ORANGE] *= 1.1
            scores[Priority.YELLOW] *= 1.05
    
    def _apply_history_rule(self, scores: Dict[Priority, float], history: str) -> None:
        """Apply fuzzy rule for serious medical history"""
        serious_keywords = ["heart", "diabetes", "cancer", "surgery", "chronic"]
        if any(keyword in history.lower() for keyword in serious_keywords):
            scores[Priority.RED] *= 1.1
            scores[Priority.ORANGE] *= 1.05
    
    def apply_fuzzy_rules(self, scores: Dict[Priority, float], patient: Patient) -> Dict[Priority, float]:
        """Apply fuzzy rules to adjust scores based on patient context"""
        adjusted_scores = scores.copy()
        
        # Apply rules
        self._apply_symptom_count_rule(adjusted_scores, len(patient.symptoms.symptoms))
        self._apply_history_rule(adjusted_scores, patient.history)
        
        # Default to standard care if no symptoms matched
        if all(score == 0 for score in adjusted_scores.values()):
            adjusted_scores[Priority.GREEN] = 1.0
        
        return self._normalize_scores(adjusted_scores)
    
    def determine_priority(self, patient: Patient) -> Priority:
        """Determine triage priority for a patient using fuzzy Manchester Triage System"""
        # Calculate initial symptom urgency scores
        symptom_scores = self.calculate_symptom_urgency_score(patient)
        
        # Apply fuzzy rules for context adjustment
        final_scores = self.apply_fuzzy_rules(symptom_scores, patient)
        
        # Determine highest priority based on fuzzy scores
        max_priority: Priority = max(final_scores.keys(), key=lambda k: final_scores[k])
        max_score = final_scores[max_priority]
        
        # Apply threshold logic for final decision
        if max_score > 0.7:
            return max_priority
        elif max_score > 0.5:
            # If score is moderate, check for secondary priority
            sorted_priorities = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
            if len(sorted_priorities) > 1 and sorted_priorities[1][1] > 0.3:
                # Return higher urgency between top two
                priorities_order = Priority.get_priority_order()
                top_two = [sorted_priorities[0][0], sorted_priorities[1][0]]
                for priority in priorities_order:
                    if priority in top_two:
                        return priority
            return max_priority
        else:
            # Low confidence, default to standard care
            return Priority.GREEN
    
    def get_triage_info(self, patient: Patient) -> Dict[str, Any]:
        """Get comprehensive triage information for a patient"""
        priority = self.determine_priority(patient)
        symptom_scores = self.calculate_symptom_urgency_score(patient)
        final_scores = self.apply_fuzzy_rules(symptom_scores, patient)
        
        # Convert Priority enum scores to string keys for JSON serialization
        symptom_scores_str = {p.value: score for p, score in symptom_scores.items()}
        final_scores_str = {p.value: score for p, score in final_scores.items()}
        
        return {
            "patient_name": patient.name,
            "priority": priority.value,
            "priority_info": {
                "name": priority.name_display,
                "max_wait_time": priority.max_wait_time,
                "description": priority.description
            },
            "symptom_scores": symptom_scores_str,
            "final_scores": final_scores_str,
            "symptoms_analyzed": patient.symptoms.symptoms,
            "history_considered": bool(patient.history.strip())
        }