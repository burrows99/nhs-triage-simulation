"""Triage Result Model

Unified model for triage results from both Manchester Triage System and LLM Triage System.
Provides standardized interface and validation for all triage outputs.
"""

import attr
from typing import Dict, Any, Optional
from datetime import datetime
import re


@attr.s(auto_attribs=True)
class TriageResult:
    """Unified triage result model for both MTS and LLM systems.
    
    This model standardizes the output from different triage systems to ensure
    consistent handling throughout the hospital simulation.
    
    Uses attrs for automatic getters/setters and validation.
    """
    
    # Core triage fields (required for both systems)
    triage_category: str = attr.ib(validator=attr.validators.in_(["RED", "ORANGE", "YELLOW", "GREEN", "BLUE"]))
    priority_score: int = attr.ib(validator=attr.validators.and_(
        attr.validators.instance_of(int),
        attr.validators.in_(range(1, 6))
    ))
    wait_time: str = attr.ib(
        validator=attr.validators.instance_of(str),
        converter=lambda value: TriageResult._normalize_wait_time_converter(value) if value else ""
    )
    confidence: float = attr.ib(validator=attr.validators.and_(
        attr.validators.instance_of((int, float)),
        lambda instance, attribute, value: 0.0 <= value <= 1.0 or attr.validators._fail("confidence must be between 0.0 and 1.0", attribute, value)
    ))
    reasoning: str = attr.ib(validator=attr.validators.instance_of(str))
    system_type: str = attr.ib(validator=attr.validators.in_(["MTS", "LLM"]))
    
    # MTS-specific fields (optional)
    flowchart_used: Optional[str] = attr.ib(default=None, validator=attr.validators.optional(attr.validators.instance_of(str)))
    fuzzy_score: Optional[float] = attr.ib(default=None, validator=attr.validators.optional(attr.validators.instance_of((int, float))))
    symptoms_processed: Optional[Dict[str, Any]] = attr.ib(default=None, validator=attr.validators.optional(attr.validators.instance_of(dict)))
    numeric_inputs: Optional[list] = attr.ib(default=None, validator=attr.validators.optional(attr.validators.instance_of(list)))
    
    # Metadata
    raw_output: Optional[Dict[str, Any]] = attr.ib(default=None, validator=attr.validators.optional(attr.validators.instance_of(dict)))
    timestamp: datetime = attr.ib(factory=datetime.now, validator=attr.validators.instance_of(datetime))
    
    @staticmethod
    def _normalize_wait_time_converter(value):
        """Normalize wait time to standard format with 'min' suffix."""
        if not value:
            return value
        if not value.endswith(" min") and value.isdigit():
            return f"{value} min"
        return value
    
    @classmethod
    def from_mts_result(cls, mts_result: Dict[str, Any]) -> 'TriageResult':
        """Create TriageResult from Manchester Triage System output.
        
        Args:
            mts_result: Dictionary from MTS triage_patient method
            
        Returns:
            TriageResult instance
        """
        # Build comprehensive MTS reasoning from available fields
        reasoning_parts = []
        
        # Add flowchart information
        flowchart = mts_result.get('flowchart_used', 'unknown')
        reasoning_parts.append(f"Flowchart: {flowchart}")
        
        # Add fuzzy score with interpretation
        fuzzy_score = mts_result.get('fuzzy_score', 0.0)
        reasoning_parts.append(f"Fuzzy Score: {fuzzy_score:.3f}")
        
        # Add symptoms processed information
        symptoms_processed = mts_result.get('symptoms_processed', {})
        if symptoms_processed:
            symptom_count = len(symptoms_processed)
            reasoning_parts.append(f"Symptoms Evaluated: {symptom_count}")
        
        # Add numeric inputs summary
        numeric_inputs = mts_result.get('numeric_inputs', [])
        if numeric_inputs:
            reasoning_parts.append(f"Numeric Inputs: {len(numeric_inputs)} values")
        
        # Add triage category explanation
        category = mts_result['triage_category']
        wait_time = mts_result['wait_time']
        reasoning_parts.append(f"Result: {category} category with {wait_time} target time")
        
        # Combine all reasoning parts
        mts_reasoning = "MTS Assessment - " + ", ".join(reasoning_parts)
        
        return cls(
            triage_category=mts_result['triage_category'],
            priority_score=int(mts_result['priority_score']),
            wait_time=mts_result['wait_time'],
            confidence=1.0,  # MTS is deterministic
            reasoning=mts_reasoning,
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
            priority_score=int(llm_result['priority_score']),
            wait_time=llm_result['wait_time'],
            confidence=float(llm_result['confidence']),
            reasoning=llm_result['reasoning'],
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
        """Extract numeric wait time in minutes using intelligent parsing.
        
        Implements Single Responsibility Principle: Only handles wait time extraction
        Implements Open/Closed Principle: Extensible for new wait time patterns
        
        Returns:
            Wait time as integer minutes based on clinical urgency and triage category
        """
        # PRODUCTION FIX: Intelligent wait time parsing to prevent bottlenecks
        wait_time_lower = self.wait_time.lower()
        
        # Priority 1: Extract explicit numeric values with context
        numeric_patterns = [
            r'(\d+)\s*(?:minutes?|mins?)',  # "10 minutes", "5 mins"
            r'within\s+(\d+)\s*(?:minutes?|mins?)',  # "within 10 minutes"
            r'ideally\s*<?\s*(\d+)\s*(?:minutes?|mins?)',  # "ideally <10 minutes"
            r'(\d+)\s*(?:-\d+)?\s*(?:minutes?|mins?)',  # "5-10 minutes" -> 5
        ]
        
        for pattern in numeric_patterns:
            match = re.search(pattern, wait_time_lower)
            if match:
                return int(match.group(1))
        
        # Priority 2: Clinical urgency keywords based on triage category
        urgency_mappings = {
            # RED category - immediate/critical
            ('immediate', 'critical', 'urgent', 'emergency', 'resuscitation'): 0,
            ('within minutes', 'asap', 'stat', 'now'): 5,
            
            # ORANGE category - very urgent
            ('very urgent', 'high priority', 'fast track'): 15,
            ('urgent', 'priority'): 30,
            
            # YELLOW category - urgent
            ('standard urgent', 'moderate'): 60,
            
            # GREEN/BLUE category - standard/non-urgent
            ('standard', 'routine', 'non-urgent', 'low priority'): 120,
            ('discharge', 'self-care', 'gp', 'primary care'): 240
        }
        
        for keywords, minutes in urgency_mappings.items():
            if any(keyword in wait_time_lower for keyword in keywords):
                return minutes
        
        # Priority 3: Fallback based on triage category (SOLID: Dependency Inversion)
        category_defaults = {
            'RED': 0,      # Immediate
            'ORANGE': 15,  # Very urgent
            'YELLOW': 60,  # Urgent  
            'GREEN': 120,  # Standard
            'BLUE': 240    # Non-urgent
        }
        
        if self.triage_category in category_defaults:
            return category_defaults[self.triage_category]
        
        # Priority 4: Fallback based on priority score
        priority_defaults = {1: 0, 2: 15, 3: 60, 4: 120, 5: 240}
        return priority_defaults.get(self.priority_score, 60)
        
        # Final fallback: Conservative default for unknown cases
        return 60  # Changed from 240 to prevent bottlenecks
    
    def is_urgent(self) -> bool:
        """Check if patient requires urgent attention (RED/ORANGE).
        
        Returns:
            True if urgent (priority 1-2), False otherwise
        """
        return self.priority_score <= 2
    

    
    def __str__(self) -> str:
        """String representation for logging and debugging."""
        return f"TriageResult({self.triage_category}, P{self.priority_score}, {self.wait_time}, {self.system_type})"
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (f"TriageResult(category={self.triage_category}, priority={self.priority_score}, "
                f"wait_time='{self.wait_time}', confidence={self.confidence}, system={self.system_type})"
               )