"""Telemetry Service for Manchester Triage System

This module provides telemetry capabilities to track and log each step
of the triage process for analysis and monitoring purposes.
"""

import json
import os
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class TelemetryStep:
    """Represents a single step in the telemetry log"""
    timestamp: str
    step_name: str
    step_type: str  # e.g., 'initialization', 'processing', 'result'
    data: Dict[str, Any]
    duration_ms: Optional[float] = None
    patient_id: Optional[str] = None
    flowchart_reason: Optional[str] = None


class TelemetryService:
    """Service for collecting and managing telemetry data during triage operations
    
    This service tracks each step of the Manchester Triage System process,
    including initialization, symptom processing, fuzzy inference, and results.
    """
    
    def __init__(self):
        """Initialize the telemetry service"""
        self._steps: List[TelemetryStep] = []
        self._session_start_time = datetime.now()
        self._current_patient_id: Optional[str] = None
        self._current_flowchart_reason: Optional[str] = None
        self._step_start_time: Optional[datetime] = None
    
    def start_patient_session(self, patient_id: str, flowchart_reason: str) -> None:
        """Start a new patient triage session
        
        Args:
            patient_id: Unique identifier for the patient
            flowchart_reason: The flowchart reason being used for triage
        """
        self._current_patient_id = patient_id
        self._current_flowchart_reason = flowchart_reason
        
        self.add_step(
            step_name="patient_session_start",
            step_type="initialization",
            data={
                "patient_id": patient_id,
                "flowchart_reason": flowchart_reason,
                "session_start_time": self._session_start_time.isoformat()
            }
        )
    
    def start_step_timer(self) -> None:
        """Start timing for the next step"""
        self._step_start_time = datetime.now()
    
    def add_step(self, step_name: str, step_type: str, data: Dict[str, Any]) -> None:
        """Add a telemetry step to the log
        
        Args:
            step_name: Name/identifier of the step
            step_type: Type of step (initialization, processing, result, etc.)
            data: Additional data associated with this step
        """
        duration_ms = None
        if self._step_start_time:
            duration_ms = (datetime.now() - self._step_start_time).total_seconds() * 1000
            self._step_start_time = None
        
        step = TelemetryStep(
            timestamp=datetime.now().isoformat(),
            step_name=step_name,
            step_type=step_type,
            data=data,
            duration_ms=duration_ms,
            patient_id=self._current_patient_id,
            flowchart_reason=self._current_flowchart_reason
        )
        
        self._steps.append(step)
    
    def end_patient_session(self, result: Dict[str, Any]) -> None:
        """End the current patient triage session
        
        Args:
            result: The final triage result
        """
        self.add_step(
            step_name="patient_session_end",
            step_type="result",
            data={
                "triage_result": result,
                "total_steps": len([s for s in self._steps if s.patient_id == self._current_patient_id])
            }
        )
        
        # Reset current patient context
        self._current_patient_id = None
        self._current_flowchart_reason = None
    
    def get_telemetry_data(self) -> List[Dict[str, Any]]:
        """Get all telemetry data as a list of dictionaries
        
        Returns:
            List of telemetry steps as dictionaries
        """
        return [asdict(step) for step in self._steps]
    
    def get_patient_telemetry(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get telemetry data for a specific patient
        
        Args:
            patient_id: The patient ID to filter by
            
        Returns:
            List of telemetry steps for the specified patient
        """
        patient_steps = [step for step in self._steps if step.patient_id == patient_id]
        return [asdict(step) for step in patient_steps]
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics of the telemetry data
        
        Returns:
            Dictionary containing summary statistics
        """
        total_steps = len(self._steps)
        unique_patients = len(set(step.patient_id for step in self._steps if step.patient_id))
        
        step_types = {}
        flowchart_reasons = {}
        total_duration = 0
        
        for step in self._steps:
            # Count step types
            step_types[step.step_type] = step_types.get(step.step_type, 0) + 1
            
            # Count flowchart reasons
            if step.flowchart_reason:
                flowchart_reasons[step.flowchart_reason] = flowchart_reasons.get(step.flowchart_reason, 0) + 1
            
            # Sum durations
            if step.duration_ms:
                total_duration += step.duration_ms
        
        return {
            "total_steps": total_steps,
            "unique_patients": unique_patients,
            "step_types": step_types,
            "flowchart_reasons": flowchart_reasons,
            "total_duration_ms": total_duration,
            "average_duration_per_step_ms": total_duration / total_steps if total_steps > 0 else 0,
            "session_start_time": self._session_start_time.isoformat(),
            "session_duration_ms": (datetime.now() - self._session_start_time).total_seconds() * 1000
        }
    
    def dump_to_file(self, output_path: str, filename: str = None) -> str:
        """Dump telemetry data to a JSON file
        
        Args:
            output_path: Directory path where the file should be saved
            filename: Optional filename (defaults to timestamp-based name)
            
        Returns:
            Full path to the created file
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_path, exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"telemetry_{timestamp}.json"
        
        # Ensure filename has .json extension
        if not filename.endswith('.json'):
            filename += '.json'
        
        full_path = os.path.join(output_path, filename)
        
        # Prepare data for export
        export_data = {
            "metadata": {
                "export_timestamp": datetime.now().isoformat(),
                "session_start_time": self._session_start_time.isoformat(),
                "total_steps": len(self._steps)
            },
            "summary_stats": self.get_summary_stats(),
            "telemetry_steps": self.get_telemetry_data()
        }
        
        # Custom JSON encoder to handle numpy types
        class NumpyEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                return super().default(obj)
        
        # Write to file
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, cls=NumpyEncoder)
        
        return full_path
    
    def clear(self) -> None:
        """Clear all telemetry data"""
        self._steps.clear()
        self._session_start_time = datetime.now()
        self._current_patient_id = None
        self._current_flowchart_reason = None
        self._step_start_time = None