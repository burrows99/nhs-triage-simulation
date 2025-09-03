"""Simulation Engine for Hospital Simulation

This module contains the core simulation engine functionality extracted from SimpleHospital
to provide better separation of concerns and reusability.
"""

import simpy
import logging
from typing import Dict, List, Any, Callable, Optional
from src.logger import logger


class SimulationEngine:
    """Core simulation engine for discrete event simulation.
    
    This class handles the fundamental simulation mechanics including:
    - SimPy environment management
    - Resource initialization and management
    - Process scheduling and execution
    - Monitoring and data collection
    - Simulation time management
    """
    
    def __init__(self, duration: float, arrival_rate: float, resources: Dict[str, int], priority_resources: List[str] = None):
        """Initialize the simulation engine.
        
        Args:
            duration: Simulation duration in minutes
            arrival_rate: Entity arrival rate per hour
            resources: Dictionary of resource types and capacities
            priority_resources: List of resource names that should use PriorityResource
        """
        self.duration = duration
        self.arrival_rate = arrival_rate
        self.resources = resources
        self.priority_resources = priority_resources or []
        
        # Simulation state
        self.env = None
        self.simpy_resources = {}
        
        # Counters
        self.entity_count = 0
        self.total_time = 0
        self.categories = []
        
        # Callbacks
        self.arrival_callback = None
        
    def initialize_environment(self):
        """Initialize the SimPy environment and resources."""
        self.env = simpy.Environment()
        
        # Initialize resources based on configuration
        for resource_name, capacity in self.resources.items():
            if resource_name in self.priority_resources:
                # Priority resources for entities with different priorities
                self.simpy_resources[resource_name] = simpy.PriorityResource(self.env, capacity=capacity)
            else:
                # Regular resources
                self.simpy_resources[resource_name] = simpy.Resource(self.env, capacity=capacity)
        
        logger.info(f"🏗️  Resources initialized: {', '.join([f'{k}: {v}' for k, v in self.resources.items()])}")
    
    def get_resource(self, resource_name: str):
        """Get a SimPy resource by name.
        
        Args:
            resource_name: Name of the resource
            
        Returns:
            SimPy resource object
        """
        return self.simpy_resources.get(resource_name)
    
    def schedule_arrivals(self, arrival_process_func: Callable):
        """Schedule the patient arrival process.
        
        Args:
            arrival_process_func: Function that generates patient arrivals
        """
        self.arrival_callback = arrival_process_func
        self.env.process(arrival_process_func())
    
    # Removed schedule_monitoring method - using synchronized monitoring instead
    
    def run_simulation(self):
        """Execute the simulation with progress tracking.
        
        Returns:
            Dictionary with simulation results
        """
        if not self.env:
            raise RuntimeError("Simulation environment not initialized. Call initialize_environment() first.")
        
        self._log_simulation_start()
        self._execute_simulation_loop()
        return self._generate_simulation_results()
    
    def _log_simulation_start(self):
        """Log simulation startup information."""
        logger.info(f"🚀 STARTING SIMULATION: {self.duration/60:.1f}h duration with {self.arrival_rate} arrivals/hour")
        logger.info(f"▶️  Simulation started at {self.format_sim_time(self.env.now)}")
        logger.info(f"📊 Real-time monitoring enabled (5-minute intervals)")
    
    def _execute_simulation_loop(self):
        """Execute the main simulation loop with progress tracking."""
        progress_interval = self.duration / 10  # Log progress every 10% of simulation
        next_progress = progress_interval
        
        while self.env.now < self.duration:
            run_until = min(next_progress, self.duration)
            
            if self.env.now < run_until:
                self.env.run(until=run_until)
            
            if self.env.now >= next_progress and self.env.now < self.duration:
                self._log_progress_update(next_progress)
                next_progress += progress_interval
            
            if self.env.now >= self.duration:
                break
    
    def _log_progress_update(self, next_progress):
        """Log progress update with resource utilization."""
        progress_pct = (self.env.now / self.duration) * 100
        logger.info(f"📊 PROGRESS: {progress_pct:.0f}% complete at {self.format_sim_time(self.env.now)} | Entities processed: {self.entity_count}")
        
        resource_status = self._get_resource_status_summary()
        logger.info(f"📈 Resource utilization: {', '.join(resource_status)}")
    
    def _get_resource_status_summary(self):
        """Get current resource status for logging."""
        resource_status = []
        for name, resource in self.simpy_resources.items():
            queue_len = len(resource.queue)
            resource_status.append(f"{name.title()} queue: {queue_len}")
        return resource_status
    
    def _generate_simulation_results(self):
        """Generate and log final simulation results."""
        avg_time = self.total_time / self.entity_count if self.entity_count > 0 else 0
        
        self._log_simulation_completion(avg_time)
        
        return {
            'total_entities': self.entity_count,
            'avg_time': avg_time,
            'times': [],
            'categories': self.categories,
            'simulation_duration': self.env.now,
            'final_resource_state': {name: {'count': res.count, 'capacity': res.capacity} 
                                   for name, res in self.simpy_resources.items()}
        }
    
    def _log_simulation_completion(self, avg_time):
        """Log simulation completion information."""
        logger.info(f"🏁 SIMULATION COMPLETE at {self.format_sim_time(self.env.now)}!")
        logger.info(f"📊 Final Results: {self.entity_count} entities processed, average time: {avg_time:.1f}min")
        
        resource_states = []
        for name, resource in self.simpy_resources.items():
            resource_states.append(f"{name.title()}: {resource.count}/{resource.capacity}")
        logger.info(f"🏭 Final resource state: {', '.join(resource_states)}")
    
    def update_entity_completion(self, total_time: float, category: str = None):
        """Update counters when an entity completes its journey.
        
        Args:
            total_time: Total time spent in system
            category: Optional category for tracking
        """
        self.entity_count += 1
        self.total_time += total_time
        if category:
            self.categories.append(category)
    
    # Removed collect_monitoring_data method - using synchronized monitoring instead
    
    def log_with_sim_time(self, level: int, message: str):
        """Log message with simulation time prefix.
        
        Args:
            level: Logging level (e.g., logging.INFO)
            message: Message to log
        """
        if self.env:
            sim_time_str = self.format_sim_time(self.env.now)
        else:
            sim_time_str = "00:00 (0.0min)"
        
        # Format message with simulation time
        formatted_message = f"{message} [{sim_time_str}]"
        
        # Use centralized logger with proper level handling
        if level == logging.INFO:
            logger.info(formatted_message)
        elif level == logging.DEBUG:
            logger.debug(formatted_message)
        elif level == logging.WARNING:
            logger.warning(formatted_message)
        elif level == logging.ERROR:
            logger.error(formatted_message)
        else:
            logger.log(level, formatted_message)
    
    def format_sim_time(self, sim_time: float) -> str:
        """Format simulation time as HH:MM.
        
        Args:
            sim_time: Simulation time in minutes
            
        Returns:
            Formatted time string
        """
        hours = int(sim_time // 60)
        minutes = int(sim_time % 60)
        return f"{hours:02d}:{minutes:02d}"
    
    # Removed simple wrapper methods - access env directly for timeout/process operations
    
    def enhanced_yield_with_monitoring(self, timeout_duration: float, context: str = "", monitoring_callback: Callable = None):
        """Enhanced yield function that combines process yielding with synchronized monitoring.
        
        This eliminates timing mismatches by capturing resource utilization at the exact
        moments when resources are being used or released.
        
        Args:
            timeout_duration: Duration to yield for
            context: Context description for debugging
            monitoring_callback: Optional callback function to capture monitoring snapshots
        """
        # Capture resource state before yielding
        if monitoring_callback:
            monitoring_callback(f"Before {context}")
        
        # Perform the actual yield
        yield self.env.timeout(timeout_duration)
        
        # Capture resource state after yielding
        if monitoring_callback:
            monitoring_callback(f"After {context}")
    
    def record_resource_event(self, event_type: str, resource_name: str, entity_id: str = None, 
                            event_recorder: Callable = None, **kwargs):
        """Record resource usage events for detailed analysis.
        
        Args:
            event_type: Type of event ('request', 'acquire', 'release')
            resource_name: Name of the resource
            entity_id: Optional entity identifier
            event_recorder: Optional callback function to record the event
            **kwargs: Additional event data
        """
        # Generic event recording using simulation engine
        event_record = {
            'time': self.env.now,
            'event_type': event_type,
            'resource': resource_name,
            'entity_id': entity_id,
            **kwargs
        }
        
        # Use callback for domain-specific event recording
        if event_recorder:
            event_recorder(event_record)
        
        # Enhanced debug logging for all resource events
        logger.debug(f"🔍 RESOURCE EVENT | Type: {event_type.upper()} | Resource: {resource_name} | "
                    f"Entity: {entity_id} | Time: {self.env.now:.1f} | Extra: {kwargs}")
    
    def capture_monitoring_snapshot(self, context: str = "", resource_mapping: Dict[str, str] = None,
                                  capacity_mapping: Dict[str, int] = None, 
                                  metrics_recorder: Callable = None, entity_count: int = 0):
        """Capture a monitoring snapshot at the current simulation time.
        
        Args:
            context: Context description for debugging
            resource_mapping: Mapping of logical resource names to SimPy resource names
            capacity_mapping: Mapping of resource names to their capacities
            metrics_recorder: Callback function to record the snapshot in domain-specific metrics
            entity_count: Current count of entities processed
        """
        if not resource_mapping or not capacity_mapping:
            logger.warning("No resource mappings provided for monitoring snapshot")
            return
        
        snapshot_data = self._collect_resource_data(resource_mapping, capacity_mapping)
        self._log_snapshot_info(context, snapshot_data)
        utilization_data = self._calculate_utilization(snapshot_data)
        self._log_utilization_info(context, utilization_data)
        self._record_metrics(metrics_recorder, snapshot_data, entity_count, context)
        self._log_detailed_status(resource_mapping, capacity_mapping, context, entity_count)
    
    def _collect_resource_data(self, resource_mapping, capacity_mapping):
        """Collect current resource usage and queue data."""
        resource_usage = {}
        resource_capacity = {}
        queue_lengths = {}
        
        for logical_name, simpy_name in resource_mapping.items():
            if simpy_name in self.simpy_resources:
                resource = self.simpy_resources[simpy_name]
                resource_usage[logical_name] = resource.count
                resource_capacity[logical_name] = capacity_mapping.get(logical_name, 0)
                queue_lengths[logical_name] = len(resource.queue)
            else:
                resource_usage[logical_name] = 0
                resource_capacity[logical_name] = capacity_mapping.get(logical_name, 0)
                queue_lengths[logical_name] = 0
        
        return {
            'resource_usage': resource_usage,
            'resource_capacity': resource_capacity,
            'queue_lengths': queue_lengths
        }
    
    def _log_snapshot_info(self, context, snapshot_data):
        """Log basic snapshot information."""
        logger.info(f"📸 SNAPSHOT CAPTURED | Time: {self.env.now:.1f} | Context: {context}")
        logger.info(f"   📊 Resource Usage: {snapshot_data['resource_usage']}")
        logger.info(f"   🏥 Resource Capacity: {snapshot_data['resource_capacity']}")
        logger.info(f"   📋 Queue Lengths: {snapshot_data['queue_lengths']}")
        logger.debug(f"📸 SYNC SNAPSHOT | Time: {self.env.now:.1f} | Context: {context} | "
                    f"Usage: {snapshot_data['resource_usage']} | Capacity: {snapshot_data['resource_capacity']} | Queues: {snapshot_data['queue_lengths']}")
    
    def _calculate_utilization(self, snapshot_data):
        """Calculate resource utilization percentages."""
        utilization_debug = {}
        for resource in snapshot_data['resource_usage']:
            capacity = snapshot_data['resource_capacity'].get(resource, 0)
            if capacity > 0:
                util_pct = (snapshot_data['resource_usage'][resource] / capacity) * 100
                utilization_debug[resource] = util_pct
            else:
                utilization_debug[resource] = 0
        return utilization_debug
    
    def _log_utilization_info(self, context, utilization_data):
        """Log utilization information."""
        logger.info(f"   📊 Resource Utilization: {utilization_data}")
        logger.debug(f"📊 SYNC UTILIZATION | {context} | {utilization_data}")
    
    def _record_metrics(self, metrics_recorder, snapshot_data, entity_count, context):
        """Record metrics using the provided callback."""
        if metrics_recorder:
            metrics_recorder({
                'timestamp': self.env.now,
                'resource_usage': snapshot_data['resource_usage'],
                'resource_capacity': snapshot_data['resource_capacity'],
                'queue_lengths': snapshot_data['queue_lengths'],
                'entities_processed': entity_count,
                'context': context
            })
    
    def _log_detailed_status(self, resource_mapping, capacity_mapping, context, entity_count):
        """Log detailed resource status for debugging."""
        resource_status = []
        for logical_name, simpy_name in resource_mapping.items():
            if simpy_name in self.simpy_resources:
                resource = self.simpy_resources[simpy_name]
                capacity = capacity_mapping.get(logical_name, 0)
                resource_status.append(f"{logical_name.title()}: {resource.count}/{capacity} (Q:{len(resource.queue)})")
        
        logger.debug(f"Monitor | Time: {self.env.now:6.1f} | {context} | {' | '.join(resource_status)} | Entities: {entity_count}")