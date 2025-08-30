import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import csv
import os
from .patient_context import PatientContext

logger = logging.getLogger(__name__)

class Patient:
    """Enhanced Patient class for NHS Triage Simulation
    
    Represents a patient in the emergency department with comprehensive tracking
    of timestamps, wait times, clinical data, and triage decisions throughout their journey.
    """
    
    # CSV field definitions for data export (simulation-specific fields)
    CSV_FIELDS = [
        'id', 'arrival_time', 'age', 'gender', 'priority', 'triage_time', 
        'wait_for_triage', 'triage_system', 'consult_time', 'wait_for_consult', 
        'discharge_time', 'total_time', 'admitted'
    ]
    
    def __init__(self, id: int, arrival_time: float = 0, **kwargs):
        # Core identification
        self.id = id
        self.arrival_time = arrival_time
        
        # Load patient data from CSV if available, otherwise use provided kwargs
        patient_data = self._load_patient_from_csv(str(id)) or {}
        
        # Patient demographics from CSV (matching patients.csv structure)
        self.age = kwargs.get('age', patient_data.get('age', 30))
        self.gender = kwargs.get('gender', patient_data.get('gender', 'Unknown'))
        
        # Simulation-specific data
        self.priority = kwargs.get('priority', 0)  # Assigned during triage
        self.triage_system = kwargs.get('triage_system', "")  # Which system performed triage
        
        # Timing data (simulation tracking)
        self.triage_time = 0
        self.wait_for_triage = 0
        self.consult_time = 0
        self.wait_for_consult = 0
        self.discharge_time = 0
        self.total_time = 0
        
        # Outcome data (simulation results)
        self.admitted = False
        
        logger.debug(f"Created Patient {self.id} (Age: {self.age}, Gender: {self.gender}) "
                    f"from {'CSV data' if patient_data else 'provided parameters'} at time {arrival_time}")
    
    def _load_patient_from_csv(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Load patient data from patients.csv file
        
        Args:
            patient_id: Patient ID to search for
            
        Returns:
            Dictionary with patient data or None if not found
        """
        csv_file = os.path.join('output', 'csv', 'patients.csv')
        if not os.path.exists(csv_file):
            logger.warning(f"Patients CSV file not found: {csv_file}")
            return None
        
        try:
            with open(csv_file, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row.get('Id') == patient_id:
                        # Parse age from birthdate if available
                        age = None
                        if row.get('BIRTHDATE'):
                            try:
                                birthdate = datetime.fromisoformat(row['BIRTHDATE'].replace('Z', '+00:00'))
                                age = (datetime.now() - birthdate).days // 365
                            except ValueError:
                                logger.warning(f"Could not parse birthdate: {row['BIRTHDATE']}")
                        
                        return {
                            'id': row.get('Id'),
                            'birthdate': row.get('BIRTHDATE'),
                            'age': age,
                            'gender': row.get('GENDER', 'Unknown'),
                            'race': row.get('RACE'),
                            'ethnicity': row.get('ETHNICITY'),
                            'address': row.get('ADDRESS'),
                            'city': row.get('CITY'),
                            'state': row.get('STATE'),
                            'medical_history': 'No significant history'  # Will be loaded from other CSV files
                        }
        except Exception as e:
            logger.error(f"Error reading patients CSV {csv_file}: {e}")
        
        return None
    
    @classmethod
    def get_all(cls, deep: bool = False) -> List['Patient']:
        """Get all patients from CSV data
        
        Args:
            deep: If True, load comprehensive medical context for each patient.
                 If False, load only basic patient data.
                 
        Returns:
            List of Patient instances
        """
        csv_file = os.path.join('output', 'csv', 'patients.csv')
        
        if not os.path.exists(csv_file):
            logger.error(f"Patients CSV file not found: {csv_file}")
            return []
        
        patients = []
        try:
            with open(csv_file, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        patient = cls.from_csv_row(row)
                        
                        # If deep=True, preload comprehensive medical context
                        if deep:
                            patient._medical_context = patient.create_patient_context()
                            logger.debug(f"Loaded deep context for Patient {patient.id}")
                        
                        patients.append(patient)
                    except Exception as e:
                        logger.error(f"Error creating patient from row: {e}")
            
            logger.info(f"Loaded {len(patients)} patients from CSV (deep={deep})")
            return patients
            
        except Exception as e:
            logger.error(f"Error reading patients CSV {csv_file}: {e}")
            return []
    
    @classmethod
    def from_csv_row(cls, row: Dict[str, str], arrival_time: float = 0) -> 'Patient':
        """Create Patient from CSV row data
        
        Args:
            row: Dictionary containing patient data from CSV
            arrival_time: Simulation arrival time
            
        Returns:
            Patient instance
        """
        # Parse age from birthdate if available
        age = 30  # Default age
        if row.get('BIRTHDATE'):
            try:
                birthdate = datetime.fromisoformat(row['BIRTHDATE'].replace('Z', '+00:00'))
                age = (datetime.now() - birthdate).days // 365
            except ValueError:
                logger.warning(f"Could not parse birthdate: {row['BIRTHDATE']}")
        
        return cls(
            id=int(row['Id']),
            arrival_time=arrival_time,
            age=age,
            gender=row.get('GENDER', 'Unknown')
        )
        
    def calculate_wait_times(self) -> None:
        """Calculate various wait times based on recorded timestamps"""
        if self.triage_time > 0:
            self.wait_for_triage = self.triage_time - self.arrival_time
        if self.consult_time > 0:
            self.wait_for_consult = self.consult_time - self.triage_time
        if self.discharge_time > 0:
            self.total_time = self.discharge_time - self.arrival_time
    
    def set_triage_result(self, priority: int, triage_system: str) -> None:
        """Set triage results from triage system"""
        self.priority = priority
        self.triage_system = triage_system
        logger.debug(f"Patient {self.id} triage result: Priority {priority} by {triage_system}")
    
    def set_outcome(self, admitted: bool) -> None:
        """Set patient outcome (admission or discharge)"""
        self.admitted = admitted
        logger.debug(f"Patient {self.id} outcome: {'Admitted' if admitted else 'Discharged'}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert patient data to dictionary for export"""
        return {
            'id': self.id,
            'arrival_time': self.arrival_time,
            'age': self.age,
            'gender': self.gender,
            'priority': self.priority,
            'triage_time': self.triage_time,
            'wait_for_triage': self.wait_for_triage,
            'triage_system': self.triage_system,
            'consult_time': self.consult_time,
            'wait_for_consult': self.wait_for_consult,
            'discharge_time': self.discharge_time,
            'total_time': self.total_time,
            'admitted': self.admitted
        }
    
    def to_csv_row(self) -> Dict[str, Any]:
        """Convert patient data to CSV-compatible row"""
        return self.to_dict()
    
    @classmethod
    def get_csv_headers(cls) -> list:
        """Get CSV headers for patient data export"""
        return cls.CSV_FIELDS
    
    @classmethod
    def export_patients_to_csv(cls, patients: list, filepath: str) -> None:
        """Export list of patients to CSV file"""
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=cls.CSV_FIELDS)
                writer.writeheader()
                
                for patient in patients:
                    writer.writerow(patient.to_csv_row())
                    
            logger.info(f"Exported {len(patients)} patients to CSV: {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export patients to CSV {filepath}: {e}")
            raise
    
    def __str__(self) -> str:
        """String representation of patient"""
        return (f"Patient {self.id}: {self.age}y {self.gender}, "
                f"Priority {self.priority}, Triage: {self.triage_system}")
    
    def create_patient_context(self) -> 'PatientContext':
        """Create and return a PatientContext object with all related medical data
        
        Returns:
            PatientContext object with comprehensive medical history
        """
        return PatientContext(patient_id=str(self.id))
    
    def get_comprehensive_context(self) -> Dict[str, Any]:
        """Get comprehensive patient context including current triage data and medical history
        
        Returns:
            Dictionary containing current patient data plus comprehensive medical history
        """
        # Get current patient data
        current_data = self.to_dict()
        
        # Get comprehensive medical history
        patient_context = self.create_patient_context()
        medical_history = patient_context.get_triage_relevant_info()
        
        # Combine current and historical data
        comprehensive_context = {
            'current_visit': current_data,
            'medical_history': medical_history,
            'risk_assessment': patient_context.get_risk_factors(),
            'active_conditions': medical_history.get('active_conditions', []),
            'active_medications': medical_history.get('active_medications', []),
            'drug_allergies': medical_history.get('drug_allergies', []),
            'recent_vital_signs': medical_history.get('recent_vital_signs', []),
            'recent_emergency_visits': medical_history.get('recent_emergency_visits', 0),
            'overall_risk_level': medical_history.get('risk_level', 'minimal')
        }
        
        return comprehensive_context
    
    def __repr__(self) -> str:
        """Detailed representation of patient"""
        return (f"Patient(id={self.id}, age={self.age}, gender='{self.gender}', "
                f"priority={self.priority}, triage_system='{self.triage_system}', "
                f"admitted={self.admitted})")