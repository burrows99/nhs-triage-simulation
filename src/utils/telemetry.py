"""Telemetry system for tracking triage decision-making processes

This module provides comprehensive telemetry capabilities to track and log
the decision-making steps for all triage systems in the NHS ED simulation.
"""

import json
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class DecisionStepType(Enum):
    """Types of decision steps in triage process"""
    INPUT_VALIDATION = "input_validation"
    DATA_PREPROCESSING = "data_preprocessing"
    FUZZY_LOGIC = "fuzzy_logic"
    LLM_PROMPT_GENERATION = "llm_prompt_generation"
    LLM_INFERENCE = "llm_inference"
    RESPONSE_PARSING = "response_parsing"
    PRIORITY_ASSIGNMENT = "priority_assignment"
    FALLBACK_HANDLING = "fallback_handling"
    FINAL_VALIDATION = "final_validation"

@dataclass
class DecisionStep:
    """Represents a single step in the triage decision process"""
    step_id: str
    step_type: DecisionStepType
    timestamp: float
    duration_ms: float
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    metadata: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None

@dataclass
class PatientTelemetry:
    """Complete telemetry data for a patient's triage process"""
    patient_id: int
    triage_system: str
    start_timestamp: float
    end_timestamp: float
    total_duration_ms: float
    decision_steps: List[DecisionStep]
    final_priority: int
    final_rationale: str
    success: bool
    error_count: int
    metadata: Dict[str, Any]

class TelemetryCollector:
    """Collects and manages telemetry data for triage decisions"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.completed_sessions: List[PatientTelemetry] = []
        self.step_counter = 0
        
    def start_patient_session(self, patient_id: int, triage_system: str, 
                            patient_data: Dict[str, Any]) -> str:
        """Start a new telemetry session for a patient"""
        session_id = f"{triage_system}_{patient_id}_{int(time.time() * 1000)}"
        
        self.active_sessions[session_id] = {
            'patient_id': patient_id,
            'triage_system': triage_system,
            'start_timestamp': time.time(),
            'decision_steps': [],
            'patient_data': patient_data,
            'metadata': {
                'session_id': session_id,
                'patient_severity': patient_data.get('severity', 'unknown'),
                'arrival_time': patient_data.get('arrival_time', 'unknown')
            }
        }
        
        logger.debug(f"Started telemetry session {session_id} for Patient {patient_id}")
        return session_id
    
    def log_decision_step(self, session_id: str, step_type: DecisionStepType,
                         input_data: Dict[str, Any], output_data: Dict[str, Any],
                         duration_ms: float, success: bool = True, 
                         error_message: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log a decision step in the triage process"""
        
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found, cannot log step")
            return ""
            
        self.step_counter += 1
        step_id = f"step_{self.step_counter:04d}"
        
        step = DecisionStep(
            step_id=step_id,
            step_type=step_type,
            timestamp=time.time(),
            duration_ms=duration_ms,
            input_data=self._sanitize_data(input_data),
            output_data=self._sanitize_data(output_data),
            metadata=metadata or {},
            success=success,
            error_message=error_message
        )
        
        self.active_sessions[session_id]['decision_steps'].append(step)
        
        logger.debug(f"Logged {step_type.value} step {step_id} for session {session_id}")
        return step_id
    
    def end_patient_session(self, session_id: str, final_priority: int,
                          final_rationale: str, success: bool = True) -> Optional[PatientTelemetry]:
        """End a telemetry session and create final telemetry record"""
        
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found, cannot end session")
            return None
            
        session = self.active_sessions[session_id]
        end_time = time.time()
        
        # Calculate error count
        error_count = sum(1 for step in session['decision_steps'] if not step.success)
        
        telemetry = PatientTelemetry(
            patient_id=session['patient_id'],
            triage_system=session['triage_system'],
            start_timestamp=session['start_timestamp'],
            end_timestamp=end_time,
            total_duration_ms=(end_time - session['start_timestamp']) * 1000,
            decision_steps=session['decision_steps'],
            final_priority=final_priority,
            final_rationale=final_rationale,
            success=success,
            error_count=error_count,
            metadata=session['metadata']
        )
        
        self.completed_sessions.append(telemetry)
        del self.active_sessions[session_id]
        
        logger.info(f"Completed telemetry session {session_id} for Patient {telemetry.patient_id}")
        return telemetry
    
    def _sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize data for logging (remove sensitive info, limit size)"""
        if not isinstance(data, dict):
            return {'value': str(data)[:1000]}  # Limit string length
            
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, (str, int, float, bool)):
                sanitized[key] = value if isinstance(value, str) and len(str(value)) < 1000 else str(value)[:1000]
            elif isinstance(value, (list, dict)):
                sanitized[key] = str(value)[:500]  # Limit complex types
            else:
                sanitized[key] = str(type(value))
                
        return sanitized
    
    def get_patient_telemetry(self, patient_id: int) -> List[PatientTelemetry]:
        """Get all telemetry records for a specific patient"""
        return [t for t in self.completed_sessions if t.patient_id == patient_id]
    
    def get_system_telemetry(self, triage_system: str) -> List[PatientTelemetry]:
        """Get all telemetry records for a specific triage system"""
        return [t for t in self.completed_sessions if t.triage_system == triage_system]
    
    def export_telemetry_json(self, output_path: str) -> None:
        """Export all telemetry data to JSON file"""
        try:
            telemetry_data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_sessions': len(self.completed_sessions),
                'sessions': [asdict(session) for session in self.completed_sessions]
            }
            
            with open(output_path, 'w') as f:
                json.dump(telemetry_data, f, indent=2, default=str)
                
            logger.info(f"Exported telemetry data to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export telemetry data: {e}")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics of telemetry data"""
        if not self.completed_sessions:
            return {'total_sessions': 0}
            
        systems = {}
        total_duration = 0
        total_errors = 0
        
        for session in self.completed_sessions:
            system_name = session.triage_system
            if system_name not in systems:
                systems[system_name] = {
                    'count': 0,
                    'avg_duration_ms': 0,
                    'total_errors': 0,
                    'success_rate': 0
                }
            
            systems[system_name]['count'] += 1
            systems[system_name]['total_errors'] += session.error_count
            total_duration += session.total_duration_ms
            total_errors += session.error_count
        
        # Calculate averages
        for system_name, stats in systems.items():
            system_sessions = [s for s in self.completed_sessions if s.triage_system == system_name]
            stats['avg_duration_ms'] = sum(s.total_duration_ms for s in system_sessions) / len(system_sessions)
            stats['success_rate'] = sum(1 for s in system_sessions if s.success) / len(system_sessions)
        
        return {
            'total_sessions': len(self.completed_sessions),
            'avg_duration_ms': total_duration / len(self.completed_sessions),
            'total_errors': total_errors,
            'systems': systems
        }

# Global telemetry collector instance
telemetry_collector = TelemetryCollector()

def get_telemetry_collector() -> TelemetryCollector:
    """Get the global telemetry collector instance"""
    return telemetry_collector