"""Triage Result Model

Unified model for triage results from both Manchester Triage System and LLM Triage System.
Provides standardized interface and validation for all triage outputs.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Union
from datetime import datetime
import re


@dataclass
class TriageResult:
    """Unified triage result model for both MTS and LLM systems.
    
    This model standardizes the output from different triage systems to ensure
    consistent handling throughout the hospital simulation.
    
    Attributes:
        triage_category: MTS category (RED, ORANGE, YELLOW, GREEN, BLUE)
        priority_score: Numeric priority (1=highest, 5=lowest)
        wait_time: Expected wait time as string (e.g., "60 min")
        confidence: Confidence score (0.0-1.0)
        reasoning: Explanation of triage decision
        system_type: Source system ("MTS" or "LLM")
        flowchart_used: MTS flowchart identifier (MTS only)
        fuzzy_score: Fuzzy inference score (MTS only)
        symptoms_processed: Processed symptoms data (MTS only)
        numeric_inputs: Numeric symptom values (MTS only)
        raw_output: Original system output for debugging
        timestamp: When triage was performed
    """
    
    # Core triage fields (required for both systems)
    triage_category: str
    priority_score: int
    wait_time: str
    confidence: float
    reasoning: str
    system_type: str
    
    # MTS-specific fields (optional)
    flowchart_used: Optional[str] = None
    fuzzy_score: Optional[float] = None
    symptoms_processed: Optional[Dict[str, Any]] = None
    numeric_inputs: Optional[list] = None
    
    # Metadata
    raw_output: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate and normalize triage result after initialization."""
        self._validate_category()
        self._validate_priority()
        self._normalize_wait_time()
        self._validate_confidence()
    
    def _validate_category(self):
        """Validate triage category is valid MTS category."""
        valid_categories = ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE']
        if self.triage_category not in valid_categories:
            raise ValueError(f"Invalid triage category: {self.triage_category}. Must be one of {valid_categories}")
    
    def _validate_priority(self):
        """Validate priority score is within valid range."""
        if not isinstance(self.priority_score, int) or not (1 <= self.priority_score <= 5):
            raise ValueError(f"Invalid priority score: {self.priority_score}. Must be integer 1-5")
    
    def _normalize_wait_time(self):
        """Normalize wait time to standard format."""
        if not self.wait_time:
            # Default wait times based on priority
            wait_times = {1: "0 min", 2: "10 min", 3: "60 min", 4: "120 min", 5: "240 min"}
            self.wait_time = wait_times.get(self.priority_score, "240 min")
        
        # Ensure wait time has "min" suffix
        if not self.wait_time.endswith(" min"):
            if self.wait_time.isdigit():
                self.wait_time += " min"
    
    def _validate_confidence(self):
        """Validate confidence is within valid range."""
        if not isinstance(self.confidence, (int, float)) or not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Invalid confidence: {self.confidence}. Must be float 0.0-1.0")
    
    @classmethod
    def from_mts_result(cls, mts_result: Dict[str, Any]) -> 'TriageResult':
        """Create TriageResult from Manchester Triage System output.
        
        Args:
            mts_result: Dictionary from MTS triage_patient method
            
        Returns:
            TriageResult instance
        """
        return cls(
            triage_category=mts_result['triage_category'],
            priority_score=mts_result['priority_score'],
            wait_time=mts_result['wait_time'],
            confidence=1.0,  # MTS is deterministic
            reasoning=f"MTS flowchart: {mts_result.get('flowchart_used', 'unknown')}, fuzzy score: {mts_result.get('fuzzy_score', 0.0):.3f}",
            system_type="MTS",
            flowchart_used=mts_result.get('flowchart_used'),
            fuzzy_score=mts_result.get('fuzzy_score'),
            symptoms_processed=mts_result.get('symptoms_processed'),
            numeric_inputs=mts_result.get('numeric_inputs'),
            raw_output=mts_result
        )
    
    @classmethod
    def from_llm_result(cls, llm_result: Dict[str, Any]) -> 'TriageResult':
        """Create TriageResult from LLM Triage System output.
        
        Args:
            llm_result: Dictionary from LLM triage_patient method
            
        Returns:
            TriageResult instance
        """
        return cls(
            triage_category=llm_result['triage_category'],
            priority_score=llm_result['priority_score'],
            wait_time=llm_result.get('wait_time', f"{llm_result['priority_score'] * 60} min"),
            confidence=llm_result.get('confidence', 0.8),
            reasoning=llm_result.get('reasoning', 'LLM triage assessment'),
            system_type="LLM",
            raw_output=llm_result
        )
    
    @classmethod
    def from_raw_result(cls, raw_result: Dict[str, Any], system_type: str) -> 'TriageResult':
        """Create TriageResult from raw system output (auto-detect format).
        
        Args:
            raw_result: Raw dictionary from triage system
            system_type: "MTS" or "LLM" to indicate source system
            
        Returns:
            TriageResult instance
        """
        if system_type.upper() == "MTS":
            return cls.from_mts_result(raw_result)
        elif system_type.upper() == "LLM":
            return cls.from_llm_result(raw_result)
        else:
            raise ValueError(f"Unknown system type: {system_type}. Must be 'MTS' or 'LLM'")
    
    def get_wait_time_minutes(self) -> int:
        """Extract numeric wait time in minutes.
        
        Returns:
            Wait time as integer minutes
        """
        match = re.search(r'(\d+)', self.wait_time)
        return int(match.group(1)) if match else 240
    
    def is_urgent(self) -> bool:
        """Check if patient requires urgent attention (RED/ORANGE).
        
        Returns:
            True if urgent (priority 1-2), False otherwise
        """
        return self.priority_score <= 2
    
    def is_emergency(self) -> bool:
        """Check if patient is emergency case (RED only).
        
        Returns:
            True if emergency (priority 1), False otherwise
        """
        return self.priority_score == 1
    
    def get_nhs_target_time(self) -> int:
        """Get NHS target time for this triage category.
        
        Returns:
            Target time in minutes according to NHS standards
        """
        # NHS target times by priority
        nhs_targets = {
            1: 0,    # RED: Immediate
            2: 10,   # ORANGE: 10 minutes
            3: 60,   # YELLOW: 1 hour
            4: 120,  # GREEN: 2 hours
            5: 240   # BLUE: 4 hours
        }
        return nhs_targets.get(self.priority_score, 240)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation of triage result
        """
        return {
            'triage_category': self.triage_category,
            'priority_score': self.priority_score,
            'wait_time': self.wait_time,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'system_type': self.system_type,
            'flowchart_used': self.flowchart_used,
            'fuzzy_score': self.fuzzy_score,
            'symptoms_processed': self.symptoms_processed,
            'numeric_inputs': self.numeric_inputs,
            'timestamp': self.timestamp.isoformat(),
            'wait_time_minutes': self.get_wait_time_minutes(),
            'is_urgent': self.is_urgent(),
            'is_emergency': self.is_emergency(),
            'nhs_target_time': self.get_nhs_target_time()
        }
    
    def __str__(self) -> str:
        """String representation for logging and debugging."""
        return f"TriageResult({self.triage_category}, P{self.priority_score}, {self.wait_time}, {self.system_type})"
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (f"TriageResult(category={self.triage_category}, priority={self.priority_score}, "
                f"wait_time='{self.wait_time}', confidence={self.confidence}, system={self.system_type})"
               )