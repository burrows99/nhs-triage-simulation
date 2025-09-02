#!/usr/bin/env python3
"""
Base Triage System Factory

Provides a factory pattern for creating different triage system implementations.
"""

from typing import Dict, Any, Optional
from src.logger import logger


class TriageSystemFactory:
    """Factory for creating different triage system implementations."""
    
    @staticmethod
    def create_manchester_triage_system(**kwargs) -> 'ManchesterTriageSystem':
        """Create a Manchester Triage System instance.
        
        Returns:
            ManchesterTriageSystem: Configured Manchester triage system
        """
        try:
            from src.triage.manchester_triage_system.manchester_triage_system import ManchesterTriageSystem
            return ManchesterTriageSystem()
        except ImportError as e:
            logger.error(f"Failed to import Manchester Triage System: {e}")
            raise

# For backward compatibility, also provide direct access to systems
__all__ = ['TriageSystemFactory']