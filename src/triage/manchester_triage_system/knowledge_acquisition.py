"""Knowledge Acquisition Component for Medical Experts

Reference: FMTS paper Section I describes "knowledge acquisition component 
used by the medical experts to configure the meaning of linguistic terms 
and maintain the fuzzy rules."
"""

import pandas as pd
from typing import Dict, List, Any
from .zmouse_interface import ZMouseFuzzyInterface


class KnowledgeAcquisitionSystem:
    """Knowledge Acquisition Component for Medical Experts
    
    Reference: FMTS paper Section I describes "knowledge acquisition component 
    used by the medical experts to configure the meaning of linguistic terms 
    and maintain the fuzzy rules."
    """
    
    def __init__(self):
        self.zmouse = ZMouseFuzzyInterface()
        self.rule_base = []
        self.expert_sessions = []
    
    def start_expert_session(self, expert_id: str) -> str:
        """Start a knowledge acquisition session for a medical expert
        
        Reference: FMTS paper describes expert session workflow for 
        configuring the system
        """
        session = {
            'session_id': f"expert_session_{len(self.expert_sessions) + 1}",
            'expert_id': expert_id,
            'start_time': pd.Timestamp.now(),
            'modifications': [],
            'status': 'active'
        }
        
        self.expert_sessions.append(session)
        return session['session_id']
    
    def add_expert_rule(self, session_id: str, rule_description: str, 
                       conditions: List[Dict], conclusion: str) -> bool:
        """Allow experts to add new fuzzy rules
        
        Reference: Paper mentions experts can "maintain the fuzzy rules"
        
        Args:
            session_id: Active expert session ID
            rule_description: Human-readable description of the rule
            conditions: List of rule conditions
            conclusion: Rule conclusion/output
        """
        
        expert_rule = {
            'rule_id': f"expert_rule_{len(self.rule_base) + 1}",
            'session_id': session_id,
            'description': rule_description,
            'conditions': conditions,
            'conclusion': conclusion,
            'created_by': 'medical_expert',
            'timestamp': pd.Timestamp.now()
        }
        
        self.rule_base.append(expert_rule)
        return True
    
    def modify_linguistic_meaning(self, session_id: str, term: str, 
                                 new_definition: Dict[str, Any]) -> bool:
        """Allow experts to modify the meaning of linguistic terms
        
        Reference: Paper Section I - experts can "configure the meaning of linguistic terms"
        
        Args:
            session_id: Active expert session ID
            term: Linguistic term to modify
            new_definition: New definition for the term
        """
        
        modification = {
            'session_id': session_id,
            'term': term,
            'old_definition': self.zmouse.expert_configurations.get(term, {}),
            'new_definition': new_definition,
            'timestamp': pd.Timestamp.now()
        }
        
        # Update the configuration
        success = self.zmouse.configure_linguistic_term(term, new_definition)
        
        # Log the modification
        for session in self.expert_sessions:
            if session['session_id'] == session_id:
                session['modifications'].append(modification)
                break
        
        return success
    
    def end_expert_session(self, session_id: str) -> Dict[str, Any]:
        """End an expert session and return summary
        
        Reference: Knowledge acquisition workflow completion as described in FMTS paper
        """
        for session in self.expert_sessions:
            if session['session_id'] == session_id:
                session['end_time'] = pd.Timestamp.now()
                session['status'] = 'completed'
                
                return {
                    'session_summary': session,
                    'rules_added': len([r for r in self.rule_base if r['session_id'] == session_id]),
                    'terms_modified': len(session['modifications'])
                }
        
        return {}
    
    def get_expert_session(self, session_id: str) -> Dict[str, Any]:
        """Get details of a specific expert session"""
        for session in self.expert_sessions:
            if session['session_id'] == session_id:
                return session
        return {}
    
    def get_all_expert_sessions(self) -> List[Dict[str, Any]]:
        """Get all expert sessions"""
        return self.expert_sessions
    
    def get_rules_by_expert(self, expert_id: str) -> List[Dict[str, Any]]:
        """Get all rules created by a specific expert"""
        expert_sessions = [s['session_id'] for s in self.expert_sessions if s['expert_id'] == expert_id]
        return [r for r in self.rule_base if r['session_id'] in expert_sessions]
    
    def validate_expert_rule(self, rule: Dict[str, Any]) -> Dict[str, Any]:
        """Validate an expert rule before adding to the system
        
        Reference: FMTS paper implies validation of expert inputs
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate required fields
        required_fields = ['description', 'conditions', 'conclusion']
        for field in required_fields:
            if field not in rule or not rule[field]:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Missing or empty required field: {field}")
        
        # Validate conditions
        if 'conditions' in rule:
            conditions = rule['conditions']
            if not isinstance(conditions, list) or len(conditions) == 0:
                validation_result['valid'] = False
                validation_result['errors'].append("Conditions must be a non-empty list")
            else:
                for i, condition in enumerate(conditions):
                    if not isinstance(condition, dict):
                        validation_result['valid'] = False
                        validation_result['errors'].append(f"Condition {i} must be a dictionary")
                    elif 'symptom' not in condition or 'value' not in condition:
                        validation_result['valid'] = False
                        validation_result['errors'].append(f"Condition {i} must have 'symptom' and 'value' fields")
        
        # Validate conclusion
        if 'conclusion' in rule:
            conclusion = rule['conclusion']
            valid_conclusions = ['red', 'orange', 'yellow', 'green', 'blue']
            if conclusion.lower() not in valid_conclusions:
                validation_result['valid'] = False
                validation_result['errors'].append(f"Conclusion must be one of: {valid_conclusions}")
        
        return validation_result
    
    def export_expert_knowledge(self) -> Dict[str, Any]:
        """Export all expert knowledge for backup or transfer
        
        Reference: FMTS paper mentions maintaining expert configurations
        """
        return {
            'expert_sessions': self.expert_sessions,
            'rule_base': self.rule_base,
            'linguistic_configurations': self.zmouse.expert_configurations,
            'fuzzy_marks': self.zmouse.fuzzy_marks,
            'export_timestamp': pd.Timestamp.now()
        }
    
    def import_expert_knowledge(self, knowledge_data: Dict[str, Any]) -> bool:
        """Import expert knowledge from backup or transfer
        
        Reference: FMTS paper supports dynamic configuration updates
        """
        try:
            if 'expert_sessions' in knowledge_data:
                self.expert_sessions.extend(knowledge_data['expert_sessions'])
            
            if 'rule_base' in knowledge_data:
                self.rule_base.extend(knowledge_data['rule_base'])
            
            if 'linguistic_configurations' in knowledge_data:
                self.zmouse.expert_configurations.update(knowledge_data['linguistic_configurations'])
            
            if 'fuzzy_marks' in knowledge_data:
                self.zmouse.fuzzy_marks.update(knowledge_data['fuzzy_marks'])
            
            return True
        except Exception as e:
            return False