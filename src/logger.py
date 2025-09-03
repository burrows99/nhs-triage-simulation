#!/usr/bin/env python3
"""
Centralized logging configuration for the hospital simulation system.

This module provides a single logger instance that can be imported
and used across all modules in the application.
"""

import logging
import os
from datetime import datetime
from typing import Optional, Callable, Any
from functools import wraps


def setup_logger(log_level=logging.DEBUG, log_to_file=True):
    """Setup centralized logger for the entire application.
    
    Args:
        log_level: Logging level (default: INFO)
        log_to_file: Whether to log to file in addition to console
    
    Returns:
        Logger instance that can be imported by other modules
    """
    # Create main logger
    logger = logging.getLogger('hospital_simulation')
    logger.setLevel(log_level)
    
    # Avoid duplicate handlers if logger already exists
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_to_file:
        # Create logs directory relative to project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_dir = os.path.join(project_root, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(logs_dir, f'hospital_simulation_{timestamp}.log')
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Initialize the centralized logger
logger = setup_logger(log_level=logging.INFO)

# Logging decorators to reduce repetitive code
def log_data_transfer(operation_name: str = None):
    """Decorator to automatically log data transfer operations."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            logger.info(f"🔄 DATA_TRANSFER_START: {op_name} initiated")
            
            try:
                result = func(*args, **kwargs)
                if hasattr(result, '__len__'):
                    logger.info(f"📊 TRANSFER_RESULT: {op_name} completed - count: {len(result)}")
                else:
                    logger.info(f"✅ TRANSFER_SUCCESS: {op_name} completed")
                return result
            except Exception as e:
                logger.error(f"❌ TRANSFER_ERROR: {op_name} failed - {str(e)}")
                raise
        return wrapper
    return decorator

def log_calculation(calc_name: str = None):
    """Decorator to automatically log calculation operations."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            name = calc_name or f"{func.__name__}"
            logger.info(f"🔄 CALCULATION_START: {name} initiated")
            
            try:
                result = func(*args, **kwargs)
                if isinstance(result, dict) and 'mean' in result:
                    logger.info(f"📊 CALCULATION_RESULT: {name} mean={result['mean']:.2f}")
                else:
                    logger.info(f"✅ CALCULATION_SUCCESS: {name} completed")
                return result
            except Exception as e:
                logger.error(f"❌ CALCULATION_ERROR: {name} failed - {str(e)}")
                raise
        return wrapper
    return decorator

# Export the logger and decorators for use in other modules
__all__ = ['logger', 'log_data_transfer', 'log_calculation']