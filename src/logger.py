#!/usr/bin/env python3
"""
Centralized logging configuration for the hospital simulation system.

This module provides a single logger instance that can be imported
and used across all modules in the application.
"""

import logging
import os
from datetime import datetime


def setup_logger(log_level=logging.INFO, log_to_file=True):
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
logger = setup_logger()

# Export the logger for import by other modules
__all__ = ['logger']