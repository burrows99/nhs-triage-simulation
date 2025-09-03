"""Production-Quality JSON Response Handler for LLM Triage Systems

Centralized JSON processing with proper error handling, validation, and recovery.
Designed for production use with clear separation of concerns.
"""

import json
import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

from src.logger import logger


class ValidationError(Exception):
    """Raised when JSON schema validation fails."""
    pass


class JSONParsingError(Exception):
    """Raised when JSON parsing fails completely."""
    pass


class ResponseQuality(Enum):
    """Quality levels for JSON responses."""
    PERFECT = "perfect"  # Valid JSON, all fields correct
    REPAIRED = "repaired"  # JSON was fixed, all fields correct
    DEGRADED = "degraded"  # Some fields missing/invalid but functional
    FAILED = "failed"  # Cannot be processed


@dataclass
class JSONProcessingResult:
    """Result of JSON processing with quality metrics."""
    data: Optional[Dict[str, Any]]
    quality: ResponseQuality
    errors: List[str]
    warnings: List[str]
    raw_response: str
    processing_time_ms: float


class TriageJSONHandler:
    """Production-quality JSON handler for triage responses."""
    
    # Required schema for triage responses
    REQUIRED_SCHEMA = {
        'triage_category': {
            'type': str,
            'valid_values': ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE'],
            'required': True
        },
        'priority_score': {
            'type': int,
            'valid_range': (1, 5),
            'required': True
        },
        'confidence': {
            'type': float,
            'valid_range': (0.0, 1.0),
            'required': True
        },
        'reasoning': {
            'type': str,
            'max_length': 500,
            'required': True
        },
        'wait_time': {
            'type': str,
            'max_length': 100,
            'required': True
        }
    }
    
    def __init__(self, strict_mode: bool = True):
        """Initialize JSON handler.
        
        Args:
            strict_mode: If True, fail fast on validation errors
        """
        self.strict_mode = strict_mode
        self._category_to_priority = {
            'RED': 1, 'ORANGE': 2, 'YELLOW': 3, 'GREEN': 4, 'BLUE': 5
        }
    
    def process_response(self, raw_response: str) -> JSONProcessingResult:
        """Process raw LLM response into validated JSON.
        
        Args:
            raw_response: Raw response from LLM API
            
        Returns:
            JSONProcessingResult with processed data and quality metrics
        """
        import time
        start_time = time.time()
        
        result = JSONProcessingResult(
            data=None,
            quality=ResponseQuality.FAILED,
            errors=[],
            warnings=[],
            raw_response=raw_response,
            processing_time_ms=0.0
        )
        
        try:
            # Step 1: Extract and parse JSON
            json_data = self._extract_and_parse_json(raw_response)
            if json_data is None:
                result.errors.append("No valid JSON found in response")
                if self.strict_mode:
                    raise JSONParsingError("Failed to extract valid JSON")
                return result
            
            result.quality = ResponseQuality.PERFECT
            
            # Step 2: Validate schema
            validation_errors = self._validate_schema(json_data)
            if validation_errors:
                result.errors.extend(validation_errors)
                if self.strict_mode:
                    raise ValidationError(f"Schema validation failed: {validation_errors}")
                result.quality = ResponseQuality.DEGRADED
            
            # Step 3: Normalize and clean data
            normalized_data = self._normalize_data(json_data)
            result.data = normalized_data
            
            # Step 4: Final consistency check
            consistency_warnings = self._check_consistency(normalized_data)
            result.warnings.extend(consistency_warnings)
            
            logger.info(f"✅ JSON processed successfully (Quality: {result.quality.value})")
            
        except (JSONParsingError, ValidationError) as e:
            result.errors.append(str(e))
            logger.error(f"❌ JSON processing failed: {e}")
            if self.strict_mode:
                raise
        
        except Exception as e:
            result.errors.append(f"Unexpected error: {e}")
            logger.error(f"❌ Unexpected JSON processing error: {e}")
            if self.strict_mode:
                raise
        
        finally:
            result.processing_time_ms = (time.time() - start_time) * 1000
        
        return result
    
    def _extract_and_parse_json(self, raw_response: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from raw response.
        
        Args:
            raw_response: Raw response text
            
        Returns:
            Parsed JSON data or None if parsing fails
        """
        # Try direct parsing first
        try:
            return json.loads(raw_response.strip())
        except json.JSONDecodeError:
            pass
        
        # Extract JSON from response
        json_str = self._extract_json_string(raw_response)
        if not json_str:
            return None
        
        # Try parsing extracted JSON
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # Try repairing JSON
        repaired_json = self._repair_json(json_str)
        if repaired_json:
            try:
                return json.loads(repaired_json)
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _extract_json_string(self, text: str) -> Optional[str]:
        """Extract JSON string from text.
        
        Args:
            text: Input text containing JSON
            
        Returns:
            Extracted JSON string or None
        """
        # Find JSON object boundaries
        start_idx = text.find('{')
        if start_idx == -1:
            return None
        
        # Find matching closing brace
        brace_count = 0
        end_idx = start_idx
        
        for i, char in enumerate(text[start_idx:], start_idx):
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break
        
        if brace_count != 0:
            # Try finding last closing brace
            end_idx = text.rfind('}') + 1
            if end_idx == 0:
                return None
        
        return text[start_idx:end_idx]
    
    def _repair_json(self, json_str: str) -> Optional[str]:
        """Attempt to repair malformed JSON.
        
        Args:
            json_str: Malformed JSON string
            
        Returns:
            Repaired JSON string or None
        """
        try:
            # Common repairs
            repaired = json_str
            
            # Fix missing commas
            repaired = re.sub(r'("[^"]*")\s+("[^"]*"\s*:)', r'\1, \2', repaired)
            repaired = re.sub(r'(\d+)\s+("[^"]*"\s*:)', r'\1, \2', repaired)
            repaired = re.sub(r'(true|false|null)\s+("[^"]*"\s*:)', r'\1, \2', repaired)
            
            # Fix missing colons
            repaired = re.sub(r'("[^"]*")\s+(["\d\[\{])', r'\1: \2', repaired)
            
            # Fix trailing commas
            repaired = re.sub(r',\s*}', '}', repaired)
            repaired = re.sub(r',\s*]', ']', repaired)
            
            # Fix spacing
            repaired = re.sub(r'"\s*:\s*', '": ', repaired)
            repaired = re.sub(r',\s*"', ', "', repaired)
            
            return repaired
            
        except Exception:
            return None
    
    def _validate_schema(self, data: Dict[str, Any]) -> List[str]:
        """Validate JSON data against required schema.
        
        Args:
            data: JSON data to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        for field, schema in self.REQUIRED_SCHEMA.items():
            if schema['required'] and field not in data:
                errors.append(f"Missing required field: {field}")
                continue
            
            if field not in data:
                continue
            
            value = data[field]
            expected_type = schema['type']
            
            # Type validation
            if not isinstance(value, expected_type):
                # Try type conversion
                try:
                    if expected_type == int:
                        data[field] = int(value)
                    elif expected_type == float:
                        data[field] = float(value)
                    elif expected_type == str:
                        data[field] = str(value)
                except (ValueError, TypeError):
                    errors.append(f"Field '{field}' must be {expected_type.__name__}, got {type(value).__name__}")
                    continue
            
            # Value validation
            if 'valid_values' in schema and data[field] not in schema['valid_values']:
                errors.append(f"Field '{field}' must be one of {schema['valid_values']}, got '{data[field]}'")
            
            if 'valid_range' in schema:
                min_val, max_val = schema['valid_range']
                if not (min_val <= data[field] <= max_val):
                    errors.append(f"Field '{field}' must be between {min_val} and {max_val}, got {data[field]}")
            
            if 'max_length' in schema and len(str(data[field])) > schema['max_length']:
                errors.append(f"Field '{field}' exceeds maximum length of {schema['max_length']}")
        
        return errors
    
    def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize and clean data.
        
        Args:
            data: Raw JSON data
            
        Returns:
            Normalized data
        """
        normalized = data.copy()
        
        # Ensure priority_score matches triage_category
        if 'triage_category' in normalized and 'priority_score' in normalized:
            expected_priority = self._category_to_priority.get(normalized['triage_category'])
            if expected_priority and normalized['priority_score'] != expected_priority:
                logger.warning(f"Priority score mismatch: {normalized['triage_category']} should be {expected_priority}, got {normalized['priority_score']}")
                normalized['priority_score'] = expected_priority
        
        # Clean string fields
        for field in ['reasoning', 'wait_time']:
            if field in normalized and isinstance(normalized[field], str):
                normalized[field] = normalized[field].strip()
        
        return normalized
    
    def _check_consistency(self, data: Dict[str, Any]) -> List[str]:
        """Check data consistency and generate warnings.
        
        Args:
            data: Normalized JSON data
            
        Returns:
            List of consistency warnings
        """
        warnings = []
        
        # Check category-priority consistency
        if 'triage_category' in data and 'priority_score' in data:
            expected_priority = self._category_to_priority.get(data['triage_category'])
            if expected_priority and data['priority_score'] != expected_priority:
                warnings.append(f"Priority score {data['priority_score']} doesn't match category {data['triage_category']} (expected {expected_priority})")
        
        # Check confidence-category consistency
        if 'confidence' in data and 'triage_category' in data:
            if data['triage_category'] == 'RED' and data['confidence'] < 0.7:
                warnings.append(f"Low confidence ({data['confidence']}) for high-priority RED category")
        
        return warnings