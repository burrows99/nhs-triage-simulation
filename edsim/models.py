from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class Patient:
    """
    Represents a patient in the ED simulation.
    - pid: Unique patient ID
    - triage: Triage level (string)
    - needs_mri: Boolean indicating if MRI is needed (assumed only for red triage with 50% probability)
    - needs_ultrasound: Boolean indicating if ultrasound is needed (20% probability for all)
    - tasks: List of resources/tasks the patient needs, determined by routing agent
    - wait_times: Per-task wait times (from request to start of service); not used in global stats but available for per-patient analysis
    - start_times: Per-task start times
    - end_times: Per-task end times
    """
    pid: int
    triage: str
    needs_mri: bool = False
    needs_ultrasound: bool = False
    tasks: List[str] = field(default_factory=list)
    wait_times: Dict[str, float] = field(default_factory=dict)
    start_times: Dict[str, float] = field(default_factory=dict)
    end_times: Dict[str, float] = field(default_factory=dict)