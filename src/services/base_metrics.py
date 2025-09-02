"""Base Metrics Service

Provides common functionality for all metric services including data storage,
basic calculations, and export capabilities.
"""

import numpy as np
import pandas as pd
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import json
from abc import ABC, abstractmethod

# Import centralized logger
from src.logger import logger
from src.models.base_record import BaseRecord


class BaseMetrics(ABC):
    """Base class for all metrics services providing common functionality"""
    
    def __init__(self, name: str = "BaseMetrics"):
        """Initialize base metrics service
        
        Args:
            name: Name identifier for this metrics service
        """
        self.name = name
        self.records: List[BaseRecord] = []
        self.active_records: Dict[str, BaseRecord] = {}
        self.counters: Dict[str, int] = defaultdict(int)
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
        logger.info(f"{self.name} metrics service initialized")
    
    def add_record(self, record: BaseRecord) -> None:
        """Add a record to active tracking
        
        Args:
            record: Record to add
        """
        if record.record_id in self.active_records:
            logger.warning(f"Record {record.record_id} already exists, updating")
        
        self.active_records[record.record_id] = record
        self.counters['total_records'] += 1
        
        # Track timing
        if self.start_time is None or record.timestamp < self.start_time:
            self.start_time = record.timestamp
    
    def complete_record(self, record_id: str, completion_time: float) -> Optional[BaseRecord]:
        """Move record from active to completed
        
        Args:
            record_id: ID of record to complete
            completion_time: Time when record was completed
            
        Returns:
            Completed record or None if not found
        """
        if record_id not in self.active_records:
            logger.warning(f"Record {record_id} not found in active records")
            return None
        
        record = self.active_records[record_id]
        record.timestamp = completion_time  # Update to completion time
        
        self.records.append(record)
        del self.active_records[record_id]
        
        self.counters['completed_records'] += 1
        
        # Update end time
        if self.end_time is None or completion_time > self.end_time:
            self.end_time = completion_time
        
        return record
    
    def get_record(self, record_id: str) -> Optional[BaseRecord]:
        """Get a record by ID from active or completed records
        
        Args:
            record_id: ID of record to retrieve
            
        Returns:
            Record if found, None otherwise
        """
        # Check active records first
        if record_id in self.active_records:
            return self.active_records[record_id]
        
        # Check completed records
        for record in self.records:
            if record.record_id == record_id:
                return record
        
        return None
    
    def get_basic_statistics(self) -> Dict[str, Any]:
        """Get basic statistics common to all metrics
        
        Returns:
            Dictionary with basic statistics
        """
        total_duration = 0
        if self.start_time is not None and self.end_time is not None:
            total_duration = self.end_time - self.start_time
        
        return {
            'service_name': self.name,
            'total_records': len(self.records),
            'active_records': len(self.active_records),
            'total_duration_minutes': total_duration,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'counters': dict(self.counters)
        }
    
    def export_data(self, json_filepath: Optional[str] = None, 
                   csv_filepath: Optional[str] = None) -> None:
        """Export metrics data to files
        
        Args:
            json_filepath: Path to export metrics as JSON
            csv_filepath: Path to export records as CSV
        """
        if json_filepath:
            metrics = self.calculate_metrics()
            with open(json_filepath, 'w') as f:
                json.dump(metrics, f, indent=2, default=str)
            logger.info(f"{self.name} metrics exported to {json_filepath}")
        
        if csv_filepath:
            if not self.records:
                logger.info(f"No {self.name} records to export")
                return
            
            # Convert records to DataFrame
            data = [self._record_to_dict(record) for record in self.records]
            df = pd.DataFrame(data)
            df.to_csv(csv_filepath, index=False)
            logger.info(f"{self.name} records exported to {csv_filepath}")
    
    def _record_to_dict(self, record: BaseRecord) -> Dict[str, Any]:
        """Convert a record to dictionary for export
        
        Args:
            record: Record to convert
            
        Returns:
            Dictionary representation of record
        """
        # Base implementation - subclasses should override for specific fields
        return {
            'record_id': record.record_id,
            'timestamp': record.timestamp
        }
    
    # Removed unused reset method
    
    @abstractmethod
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate service-specific metrics
        
        Returns:
            Dictionary containing calculated metrics
        """
        pass
    
    def __str__(self) -> str:
        """String representation of metrics service"""
        stats = self.get_basic_statistics()
        return (f"{self.name}: {stats['total_records']} completed, "
                f"{stats['active_records']} active, "
                f"{stats['total_duration_minutes']:.1f}min duration")