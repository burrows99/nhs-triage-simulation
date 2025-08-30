#!/usr/bin/env python3
"""
JSON Utilities for NHS Triage Simulation

Pure JSON parsing and manipulation utilities.
Contains only JSON-related logic without domain-specific validation.
"""

import json
import re
import logging
from typing import Dict, Any, Optional, Union, List

logger = logging.getLogger(__name__)

def parse_json_response(response: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON response and extract JSON content.
    
    Handles both direct JSON responses and JSON wrapped in markdown code blocks.
    
    Args:
        response (str): Raw response string containing JSON
        
    Returns:
        Optional[Dict[str, Any]]: Parsed JSON data or None if parsing fails
    """
    if not response or not isinstance(response, str):
        logger.error(f"Invalid response type: {type(response)}")
        return None
    
    response = response.strip()
    if not response:
        logger.error("Empty response received")
        return None
    
    try:
        # Try to parse as direct JSON first
        return json.loads(response)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        return extract_json_from_markdown(response)

def extract_json_from_markdown(response: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON from markdown code blocks.
    
    Handles various markdown formats:
    - ```json {...} ```
    - ``` {...} ```
    - ```JSON {...} ```
    
    Args:
        response (str): Response containing markdown-wrapped JSON
        
    Returns:
        Optional[Dict[str, Any]]: Extracted JSON data or None if extraction fails
    """
    # Pattern to match JSON in markdown code blocks (case-insensitive)
    patterns = [
        r'```(?:json|JSON)?\s*({.*?})\s*```',  # Standard markdown blocks
        r'```(?:json|JSON)?\s*(\[.*?\])\s*```',  # Array format
        r'`({.*?})`',  # Single backticks
        r'({\s*".*?})',  # Direct JSON detection
    ]
    
    for pattern in patterns:
        json_match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if json_match:
            json_str = json_match.group(1)
            try:
                parsed_json = json.loads(json_str)
                logger.debug(f"Successfully extracted JSON from markdown: {json_str[:100]}...")
                return parsed_json
            except json.JSONDecodeError as e:
                logger.debug(f"Failed to parse extracted JSON: {str(e)}")
                continue
    
    logger.error(f"No valid JSON found in response: {response[:200]}...")
    return None

def safe_json_dumps(data: Any, indent: int = 2, ensure_ascii: bool = False) -> str:
    """
    Safely serialize data to JSON string with error handling.
    
    Args:
        data (Any): Data to serialize
        indent (int): JSON indentation level
        ensure_ascii (bool): Whether to escape non-ASCII characters
        
    Returns:
        str: JSON string or error message if serialization fails
    """
    try:
        return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
    except (TypeError, ValueError) as e:
        logger.error(f"JSON serialization failed: {str(e)}")
        return f"{{\"error\": \"JSON serialization failed: {str(e)}\"}}"

def safe_json_loads(json_str: str) -> Optional[Union[Dict[str, Any], List[Any]]]:
    """
    Safely parse JSON string with error handling.
    
    Args:
        json_str (str): JSON string to parse
        
    Returns:
        Optional[Union[Dict[str, Any], List[Any]]]: Parsed JSON data or None if parsing fails
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"JSON parsing failed: {str(e)}")
        return None

def extract_value_by_keys(data: Dict[str, Any], keys: List[str]) -> Any:
    """
    Extract value from dictionary using multiple possible keys.
    
    Tries keys in order and returns the first found value.
    
    Args:
        data (Dict[str, Any]): Dictionary to search
        keys (List[str]): List of keys to try in order
        
    Returns:
        Any: First found value or None if no keys found
    """
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return None

def merge_json_objects(*objects: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple JSON objects, with later objects taking precedence.
    
    Args:
        *objects: Variable number of dictionaries to merge
        
    Returns:
        Dict[str, Any]: Merged dictionary
    """
    merged = {}
    for obj in objects:
        if isinstance(obj, dict):
            merged.update(obj)
        else:
            logger.warning(f"Skipping non-dict object in merge: {type(obj)}")
    
    return merged

def validate_json_structure(data: Any, required_keys: List[str] = None) -> bool:
    """
    Validate basic JSON structure.
    
    Args:
        data (Any): Data to validate
        required_keys (List[str], optional): List of required keys for dict validation
        
    Returns:
        bool: True if structure is valid, False otherwise
    """
    if not isinstance(data, (dict, list)):
        logger.error(f"Invalid JSON structure type: {type(data)}")
        return False
    
    if isinstance(data, dict) and required_keys:
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            logger.error(f"Missing required keys: {missing_keys}")
            return False
    
    return True

def log_json_operation(operation: str, success: bool, details: str = "") -> None:
    """
    Log JSON operations for debugging and monitoring.
    
    Args:
        operation (str): Description of the operation
        success (bool): Whether operation was successful
        details (str): Additional details about the operation
    """
    if success:
        logger.debug(f"JSON {operation} successful. {details}")
    else:
        logger.warning(f"JSON {operation} failed. {details}")