from typing import Dict, List, Any, Optional
from datetime import datetime


class Patient:
    """Comprehensive Patient model for hospital simulation.
    
    This model consolidates patient data and functionality from across the codebase,
    replacing scattered patient data structures with a unified model.
    """
    
    def __init__(self, patient_id: str, age: int = 30, gender: str = "Unknown",
                 presenting_complaint: str = "", symptoms: Optional[Dict[str, Any]] = None,
                 vital_signs: Optional[Dict[str, Any]] = None, conditions: Optional[List[str]] = None,
                 raw_data: Optional[Dict[str, Any]] = None):
        """Initialize Patient with comprehensive data.
        
        Args:
            patient_id: Unique patient identifier
            age: Patient age in years
            gender: Patient gender
            presenting_complaint: Chief complaint or reason for visit
            symptoms: Dictionary of symptoms and their values
            vital_signs: Dictionary of vital signs data
            conditions: List of medical conditions
            raw_data: Original raw patient data for reference
        """
        # Core identification
        self.patient_id = patient_id
        self.age = age
        self.gender = gender
        
        # Clinical data
        self.presenting_complaint = presenting_complaint
        self.symptoms = symptoms or {}
        self.vital_signs = vital_signs or {'numeric_values': {}, 'categories': {}}
        self.conditions = conditions or []
        
        # Timestamps for NHS quality indicators
        self.arrival_time: float = 0
        self.initial_assessment_start: float = 0
        self.treatment_start: float = 0
        self.departure_time: float = 0
        
        # Triage information
        self.triage_category: str = ""
        self.triage_priority: int = 0
        self.triage_result: Optional[Dict[str, Any]] = None
        
        # Status flags
        self.left_without_being_seen: bool = False
        self.is_reattendance: bool = False
        self.admitted: bool = False
        
        # Disposition and outcome
        self.disposal: str = ""  # discharged/admitted/transferred
        
        # Raw data preservation
        self.raw_data = raw_data or {}
        
        # Journey tracking
        self.journey_events: List[Dict[str, Any]] = []
    
    @property
    def record_id(self) -> str:
        """Compatibility property for BaseMetrics system."""
        return self.patient_id
    
    @property
    def timestamp(self) -> float:
        """Compatibility property for BaseMetrics system."""
        return self.arrival_time
    
    def record_arrival(self, arrival_time: float) -> None:
        """Record patient arrival time."""
        self.arrival_time = arrival_time
        self.add_journey_event('arrival', arrival_time)
    
    def record_initial_assessment(self, assessment_time: float) -> None:
        """Record start of initial assessment (triage)."""
        self.initial_assessment_start = assessment_time
        self.add_journey_event('initial_assessment_start', assessment_time)
    
    def record_treatment_start(self, treatment_time: float) -> None:
        """Record start of treatment (doctor consultation)."""
        self.treatment_start = treatment_time
        self.add_journey_event('treatment_start', treatment_time)
    
    def record_departure(self, departure_time: float, disposal: str = "", admitted: bool = False) -> None:
        """Record patient departure."""
        self.departure_time = departure_time
        self.disposal = disposal
        self.admitted = admitted
        self.add_journey_event('departure', departure_time, {'disposal': disposal, 'admitted': admitted})
    
    def set_triage_result(self, category: str, priority: int = 0, triage_result: Optional[Dict[str, Any]] = None) -> None:
        """Set triage category and results."""
        self.triage_category = category
        self.triage_priority = priority
        self.triage_result = triage_result or {}
        self.add_journey_event('triage_completed', self.initial_assessment_start, 
                              {'category': category, 'priority': priority})
    
    def add_journey_event(self, event_type: str, timestamp: float, data: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the patient's journey log."""
        event = {
            'event_type': event_type,
            'timestamp': timestamp,
            'data': data or {}
        }
        self.journey_events.append(event)
    
    def total_time_in_ae(self) -> float:
        """Calculate total time in A&E (minutes) - NHS Quality Indicator."""
        if self.departure_time == 0 or self.arrival_time == 0:
            return 0
        return self.departure_time - self.arrival_time
    
    def time_to_initial_assessment(self) -> float:
        """Calculate time to initial assessment (minutes) - NHS Quality Indicator."""
        if self.initial_assessment_start == 0 or self.arrival_time == 0:
            return 0
        return self.initial_assessment_start - self.arrival_time
    
    def time_to_treatment(self) -> float:
        """Calculate time to treatment (minutes) - NHS Quality Indicator."""
        if self.treatment_start == 0 or self.arrival_time == 0:
            return 0
        return self.treatment_start - self.arrival_time
    
    def get_condition_count(self) -> int:
        """Get number of medical conditions."""
        return len(self.conditions)
    
    def get_observation_count(self) -> int:
        """Get number of observations from raw data."""
        if 'observations' in self.raw_data:
            return len(self.raw_data['observations'])
        return 0
    
    def get_context(self) -> Dict[str, Any]:
        """Get all related medical context data excluding direct patient CSV fields.
        
        Returns all related data like conditions, observations, medications, procedures,
        encounters, etc. but excludes direct patient demographic fields from the CSV.
        
        Returns:
            Dictionary containing all related medical context data
        """
        if not self.raw_data:
            return {}
        
        # Direct patient CSV fields to exclude (demographic/administrative data)
        patient_direct_fields = {
            'Id', 'BIRTHDATE', 'DEATHDATE', 'SSN', 'DRIVERS', 'PASSPORT', 
            'PREFIX', 'FIRST', 'LAST', 'SUFFIX', 'MAIDEN', 'MARITAL', 
            'RACE', 'ETHNICITY', 'GENDER', 'BIRTHPLACE', 'ADDRESS', 
            'CITY', 'STATE', 'COUNTY', 'ZIP', 'LAT', 'LON', 
            'HEALTHCARE_EXPENSES', 'HEALTHCARE_COVERAGE'
        }
        
        # Return all related medical data (conditions, observations, medications, etc.)
        context = {}
        for key, value in self.raw_data.items():
            if key not in patient_direct_fields:
                context[key] = value
        
        return context
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert patient to dictionary for export/serialization."""
        return {
            'patient_id': self.patient_id,
            'age': self.age,
            'gender': self.gender,
            'presenting_complaint': self.presenting_complaint,
            'symptoms': self.symptoms,
            'vital_signs': self.vital_signs,
            'conditions': self.conditions,
            'arrival_time': self.arrival_time,
            'initial_assessment_start': self.initial_assessment_start,
            'treatment_start': self.treatment_start,
            'departure_time': self.departure_time,
            'triage_category': self.triage_category,
            'triage_priority': self.triage_priority,
            'left_without_being_seen': self.left_without_being_seen,
            'is_reattendance': self.is_reattendance,
            'admitted': self.admitted,
            'disposal': self.disposal,
            'total_time_in_ae': self.total_time_in_ae(),
            'time_to_initial_assessment': self.time_to_initial_assessment(),
            'time_to_treatment': self.time_to_treatment(),
            'condition_count': self.get_condition_count(),
            'observation_count': self.get_observation_count(),
            'journey_events': self.journey_events
        }
    
    @classmethod
    def from_raw_data(cls, patient_id: str, raw_data: Dict[str, Any], 
                     data_cleanup_service=None) -> 'Patient':
        """Create Patient from raw data using data cleanup service.
        
        Args:
            patient_id: Patient identifier
            raw_data: Raw patient data dictionary
            data_cleanup_service: Service to process raw data
            
        Returns:
            Patient instance with processed data
        """
        if data_cleanup_service:
            summary = data_cleanup_service.get_patient_summary(raw_data)
            return cls(
                patient_id=patient_id,
                age=summary.get('age', 30),
                gender=summary.get('gender', 'Unknown'),
                presenting_complaint=summary.get('chief_complaint', ''),
                symptoms=summary.get('symptoms', {}),
                vital_signs=summary.get('vital_signs', {'numeric_values': {}, 'categories': {}}),
                conditions=summary.get('conditions', []),
                raw_data=raw_data
            )
        else:
            # Fallback to basic extraction
            return cls(
                patient_id=patient_id,
                age=raw_data.get('age', 30),
                gender=raw_data.get('GENDER', 'Unknown'),
                presenting_complaint=raw_data.get('presenting_complaint', ''),
                raw_data=raw_data
            )
    
    def __str__(self) -> str:
        """String representation of patient."""
        return f"Patient({self.patient_id}, {self.age}y {self.gender}, {self.triage_category})"
    
    def __repr__(self) -> str:
        """Detailed representation of patient."""
        return (f"Patient(id={self.patient_id}, age={self.age}, gender={self.gender}, "
                f"category={self.triage_category}, complaint='{self.presenting_complaint}')")