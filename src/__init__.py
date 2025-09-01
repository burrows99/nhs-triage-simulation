"""NHS Emergency Department Triage Simulator

A comprehensive SimPy-based simulation of emergency department patient flow
with modifiable triage systems and priority calculation methods.

Based on research methodology from:
"Patient Flow Optimization in an Emergency Department Using SimPy-Based 
Simulation Modeling and Analysis: A Case Study"
"""

__version__ = "1.0.0"
__author__ = "Emergency Department Simulation Team"
__description__ = "SimPy-based Emergency Department Triage Simulation"

# Core simulation components
from .core import EmergencyDepartment, PatientGenerator, SimulationEngine

# Patient and triage entities
from .entities import Patient, Priority, PatientStatus

# Triage systems
from .triage import (
    BaseTriage,
    TriageResult,
    ManchesterTriage
)

# Configuration
from .config import SimulationParameters

__all__ = [
    # Core components
    'EmergencyDepartment',
    'PatientGenerator',
    'SimulationEngine',
    
    # Entities
    'Patient',
    'Priority',
    'PatientStatus',
    
    # Triage systems
    'BaseTriage',
    'TriageResult',
    'ManchesterTriage',
    
    # Configuration
    'SimulationParameters'
]