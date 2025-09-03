"""Operation Metrics Service

Tracks operational metrics for hospital simulation including resource utilization,
queue lengths, throughput, and system performance indicators.
"""

import numpy as np
import pandas as pd
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import attr

from .base_metrics import BaseMetrics, BaseRecord
from .statistics_utils import StatisticsUtils
from src.logger import logger
from src.models.resource_event import ResourceEvent
from src.models.system_snapshot import SystemSnapshot


class OperationMetrics(BaseMetrics):
    """Operational metrics tracking service
    
    Tracks resource utilization, queue performance, throughput, and system efficiency.
    """
    
    def __init__(self):
        """Initialize Operation Metrics Service
        
        Uses synchronized monitoring instead of time-based intervals.
        """
        super().__init__("OperationMetrics")
        
        self.last_snapshot_time = 0.0
        self.snapshot_counter = 0  # Counter for unique snapshot IDs
        
        # Resource tracking
        self.resource_events: List[ResourceEvent] = []
        self.system_snapshots: List[SystemSnapshot] = []
        
        # Performance tracking
        self.throughput_data: Dict[str, List[Tuple[float, int]]] = defaultdict(list)  # time -> count
        self.wait_times: Dict[str, List[float]] = defaultdict(list)  # resource -> wait_times
        self.service_times: Dict[str, List[float]] = defaultdict(list)  # resource -> service_times
        
        # Real-time metrics
        self.current_utilization: Dict[str, float] = {}
        self.peak_utilization: Dict[str, float] = {}
        self.average_queue_length: Dict[str, float] = defaultdict(float)
        
        logger.info("Operation metrics service initialized")
    
    def record_resource_event(self, event_type: str, resource_name: str, 
                            entity_id: str, timestamp: float, **kwargs) -> ResourceEvent:
        """Record a resource usage event
        
        Args:
            event_type: Type of event ('request', 'acquire', 'release')
            resource_name: Name of the resource ('triage', 'doctor', 'bed')
            entity_id: ID of entity using resource (usually patient_id)
            timestamp: Time of the event
            **kwargs: Additional event data (queue_length, wait_time, etc.)
            
        Returns:
            Created ResourceEvent
        """
        logger.info(f"🔄 DATA_TRANSFER_START: OperationMetrics.record_resource_event() initiated")
        logger.info(f"📊 TRANSFER_SOURCE: ResourceEvent - {event_type} for {resource_name} by {entity_id}")
        logger.info(f"📍 TRANSFER_DESTINATION: Operation metrics event storage")
        
        event_id = f"{resource_name}_{event_type}_{entity_id}_{timestamp}"
        
        event = ResourceEvent(
            event_id=event_id,
            timestamp=timestamp,
            event_type=event_type,
            resource_name=resource_name,
            entity_id=entity_id,
            queue_length=kwargs.get('queue_length', 0),
            wait_time=kwargs.get('wait_time', 0.0),
            service_time=kwargs.get('service_time', 0.0),
            priority=kwargs.get('priority', 5)
        )
        
        self.resource_events.append(event)
        self.add_record(event)
        logger.info(f"📊 TRANSFER_RESULT: Event stored - total_events={len(self.resource_events)}")
        
        # Update performance tracking
        if event_type == 'acquire' and event.wait_time > 0:
            self.wait_times[resource_name].append(event.wait_time)
            logger.info(f"📊 WAIT_TIME_UPDATE: {resource_name} wait_time={event.wait_time:.2f}min added")
        
        if event_type == 'release' and event.service_time > 0:
            self.service_times[resource_name].append(event.service_time)
            logger.info(f"📊 SERVICE_TIME_UPDATE: {resource_name} service_time={event.service_time:.2f}min added")
        
        logger.info(f"✅ DATA_TRANSFER_SUCCESS: Resource event recorded for {resource_name} {event_type} at {timestamp:.2f}")
        
        return event
    
    def record_system_snapshot(self, timestamp: float, resource_usage: Dict[str, int],
                             resource_capacity: Dict[str, int], queue_lengths: Dict[str, int],
                             entities_processed: int = 0) -> SystemSnapshot:
        """Record a system state snapshot
        
        Args:
            timestamp: Time of snapshot
            resource_usage: Current usage for each resource
            resource_capacity: Total capacity for each resource
            queue_lengths: Current queue length for each resource
            entities_processed: Total entities processed so far
            
        Returns:
            Created SystemSnapshot
        """
        # Generate unique snapshot ID using timestamp and counter
        self.snapshot_counter += 1
        snapshot_id = f"snapshot_{timestamp}_{self.snapshot_counter}"
        
        snapshot = SystemSnapshot(
            snapshot_id=snapshot_id,
            timestamp=timestamp,
            resource_usage=resource_usage.copy(),
            resource_capacity=resource_capacity.copy(),
            queue_lengths=queue_lengths.copy(),
            entities_processed=entities_processed
        )
        
        self.system_snapshots.append(snapshot)
        self.add_record(snapshot)
        
        # Update real-time metrics
        for resource_name in resource_usage:
            utilization = snapshot.get_utilization(resource_name)
            self.current_utilization[resource_name] = utilization
            
            # Track peak utilization
            if resource_name not in self.peak_utilization or utilization > self.peak_utilization[resource_name]:
                self.peak_utilization[resource_name] = utilization
        
        self.last_snapshot_time = timestamp
        return snapshot
    
    # Removed should_take_snapshot method - using synchronized monitoring instead
    
    # Removed unused record_throughput method
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate operational metrics
        
        Returns:
            Dictionary containing operational performance metrics
        """
        if not self.system_snapshots:
            return {
                'error': 'No system snapshots available',
                **self.get_basic_statistics()
            }
        
        # Calculate utilization metrics
        utilization_metrics = self._calculate_utilization_metrics()
        
        # Calculate queue metrics
        queue_metrics = self._calculate_queue_metrics()
        
        # Calculate throughput metrics
        throughput_metrics = self._calculate_throughput_metrics()
        
        # Calculate wait time metrics
        wait_time_metrics = self._calculate_wait_time_metrics()
        
        # Calculate service time metrics
        service_time_metrics = self._calculate_service_time_metrics()
        
        # System performance metrics
        system_metrics = self._calculate_system_metrics()
        
        metrics = {
            'utilization': utilization_metrics,
            'queues': queue_metrics,
            'throughput': throughput_metrics,
            'wait_times': wait_time_metrics,
            'service_times': service_time_metrics,
            'system_performance': system_metrics,
            'monitoring_points': len(self.system_snapshots),
            'total_resource_events': len(self.resource_events)
        }
        
        # Add base statistics
        metrics.update(self.get_basic_statistics())
        
        return metrics
    
    def _calculate_utilization_metrics(self) -> Dict[str, Any]:
        """Calculate resource utilization metrics"""
        if not self.system_snapshots:
            logger.warning("⚠️  No system snapshots available for utilization calculation")
            return {}
        
        logger.debug(f"🔍 UTILIZATION CALC | Processing {len(self.system_snapshots)} snapshots")
        
        # Get all resource names
        all_resources = set()
        for snapshot in self.system_snapshots:
            all_resources.update(snapshot.resource_usage.keys())
        
        logger.debug(f"📊 RESOURCES FOUND | {all_resources}")
        
        utilization_metrics = {}
        
        for resource in all_resources:
            utilizations = []
            for snapshot in self.system_snapshots:
                if resource in snapshot.resource_usage:
                    util = snapshot.get_utilization(resource)
                    utilizations.append(util)
            
            logger.debug(f"📈 {resource.upper()} UTILIZATION | Samples: {len(utilizations)} | "
                        f"Values: {utilizations[:5]}{'...' if len(utilizations) > 5 else ''}")
            
            if utilizations:
                avg_util = float(np.mean(utilizations))
                peak_util = float(np.max(utilizations))
                min_util = float(np.min(utilizations))
                
                utilization_metrics[resource] = {
                    'average_utilization_pct': avg_util,
                    'peak_utilization_pct': peak_util,
                    'min_utilization_pct': min_util,
                    'current_utilization_pct': float(self.current_utilization.get(resource, 0)),
                    'utilization_std_dev': float(np.std(utilizations))
                }
                
                logger.debug(f"✅ {resource.upper()} METRICS | Avg: {avg_util:.1f}% | Peak: {peak_util:.1f}% | Min: {min_util:.1f}%")
            else:
                logger.warning(f"⚠️  No utilization data for resource: {resource}")
        
        return utilization_metrics
    
    def _calculate_queue_metrics(self) -> Dict[str, Any]:
        """Calculate queue performance metrics"""
        if not self.system_snapshots:
            return {}
        
        # Get all resource names
        all_resources = set()
        for snapshot in self.system_snapshots:
            all_resources.update(snapshot.queue_lengths.keys())
        
        queue_metrics = {}
        
        for resource in all_resources:
            queue_lengths = []
            for snapshot in self.system_snapshots:
                if resource in snapshot.queue_lengths:
                    queue_lengths.append(snapshot.queue_lengths[resource])
            
            if queue_lengths:
                # Filter out any NaN or invalid values
                valid_queue_lengths = [q for q in queue_lengths if not (pd.isna(q) or np.isnan(q) if isinstance(q, (int, float)) else False)]
                
                if valid_queue_lengths:
                    # Calculate metrics with valid data only
                    mean_val = np.mean(valid_queue_lengths)
                    max_val = np.max(valid_queue_lengths)
                    min_val = np.min(valid_queue_lengths)
                    std_val = np.std(valid_queue_lengths)
                    
                    # Ensure all values are valid before conversion
                    queue_metrics[resource] = {
                        'average_queue_length': float(mean_val) if not np.isnan(mean_val) else 0.0,
                        'peak_queue_length': int(max_val) if not np.isnan(max_val) else 0,
                        'min_queue_length': int(min_val) if not np.isnan(min_val) else 0,
                        'queue_length_std_dev': float(std_val) if not np.isnan(std_val) else 0.0,
                        'time_with_queue': float(sum(1 for q in valid_queue_lengths if q > 0) / len(valid_queue_lengths) * 100) if valid_queue_lengths else 0.0
                    }
                else:
                    # No valid data - provide default values
                    queue_metrics[resource] = {
                        'average_queue_length': 0.0,
                        'peak_queue_length': 0,
                        'min_queue_length': 0,
                        'queue_length_std_dev': 0.0,
                        'time_with_queue': 0.0
                    }
        
        return queue_metrics
    
    def _calculate_throughput_metrics(self) -> Dict[str, Any]:
        """Calculate throughput metrics using centralized calculations"""
        throughput_metrics = {}
        
        for resource, data in self.throughput_data.items():
            if data:
                times, counts = zip(*data)
                total_time = max(times) - min(times) if len(times) > 1 else 1
                total_count = sum(counts)
                
                throughput_metrics[resource] = {
                    'total_processed': total_count,
                    'throughput_per_hour': StatisticsUtils.calculate_throughput_rate(total_count, total_time),
                    'average_processing_rate': total_count / len(data) if data else 0
                }
        
        return throughput_metrics
    
    def _calculate_wait_time_metrics(self) -> Dict[str, Any]:
        """Calculate wait time metrics using centralized statistics"""
        wait_time_metrics = {}
        
        for resource, wait_times in self.wait_times.items():
            if wait_times:
                stats = StatisticsUtils.calculate_basic_stats(wait_times)
                wait_time_metrics[resource] = {
                    'average_wait_time_minutes': stats['mean'],
                    'max_wait_time_minutes': stats['max'],
                    'min_wait_time_minutes': stats['min'],
                    'wait_time_std_dev': stats['std_dev'],
                    '95th_percentile_wait_time': stats['95th_percentile'],
                    'total_wait_events': stats['count']
                }
        
        return wait_time_metrics
    
    def _calculate_service_time_metrics(self) -> Dict[str, Any]:
        """Calculate service time metrics using centralized statistics"""
        service_time_metrics = {}
        
        for resource, service_times in self.service_times.items():
            if service_times:
                stats = StatisticsUtils.calculate_basic_stats(service_times)
                service_time_metrics[resource] = {
                    'average_service_time_minutes': stats['mean'],
                    'max_service_time_minutes': stats['max'],
                    'min_service_time_minutes': stats['min'],
                    'service_time_std_dev': stats['std_dev'],
                    '95th_percentile_service_time': stats['95th_percentile'],
                    'total_service_events': stats['count']
                }
        
        return service_time_metrics
    
    def _calculate_system_metrics(self) -> Dict[str, Any]:
        """Calculate overall system performance metrics"""
        if not self.system_snapshots:
            return {}
        
        # System efficiency metrics
        total_entities = [s.entities_processed for s in self.system_snapshots if s.entities_processed > 0]
        
        # Calculate system load over time
        total_queue_lengths = []
        total_utilizations = []
        
        for snapshot in self.system_snapshots:
            total_queue = sum(snapshot.queue_lengths.values())
            total_queue_lengths.append(total_queue)
            
            # Calculate average utilization across all resources
            utilizations = [snapshot.get_utilization(resource) for resource in snapshot.resource_usage]
            if utilizations:
                # Filter out any NaN values before calculating mean
                valid_utilizations = [u for u in utilizations if not np.isnan(u)]
                if valid_utilizations:
                    mean_util = np.mean(valid_utilizations)
                    if not np.isnan(mean_util):
                        total_utilizations.append(mean_util)
        
        system_metrics = {
            'simulation_duration_minutes': self.end_time - self.start_time if self.end_time and self.start_time else 0,
            'total_snapshots': len(self.system_snapshots)
        }
        
        if total_queue_lengths:
            system_metrics.update({
                'average_system_queue_length': np.mean(total_queue_lengths),
                'peak_system_queue_length': np.max(total_queue_lengths),
                'system_congestion_pct': sum(1 for q in total_queue_lengths if q > 0) / len(total_queue_lengths) * 100
            })
        
        if total_utilizations:
            system_metrics.update({
                'average_system_utilization_pct': np.mean(total_utilizations),
                'peak_system_utilization_pct': np.max(total_utilizations)
            })
        
        if total_entities:
            system_metrics.update({
                'final_entities_processed': max(total_entities),
                'processing_rate_per_hour': (max(total_entities) / system_metrics['simulation_duration_minutes']) * 60 if system_metrics['simulation_duration_minutes'] > 0 else 0
            })
        
        return system_metrics
    
    # Removed unused get_resource_summary method
    
    def _record_to_dict(self, record: BaseRecord) -> Dict[str, Any]:
        """Convert record to dictionary for export"""
        if isinstance(record, ResourceEvent):
            return {
                'event_id': record.event_id,
                'timestamp': record.timestamp,
                'event_type': record.event_type,
                'resource_name': record.resource_name,
                'entity_id': record.entity_id,
                'queue_length': record.queue_length,
                'wait_time': record.wait_time,
                'service_time': record.service_time,
                'priority': record.priority
            }
        elif isinstance(record, SystemSnapshot):
            return {
                'snapshot_id': record.snapshot_id,
                'timestamp': record.timestamp,
                'resource_usage': record.resource_usage,
                'resource_capacity': record.resource_capacity,
                'queue_lengths': record.queue_lengths,
                'entities_processed': record.entities_processed
            }
        else:
            return super()._record_to_dict(record)