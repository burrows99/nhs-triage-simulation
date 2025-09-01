import time
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, deque
from ..entities.patient import Patient, Priority, PatientStatus


@dataclass
class SimulationMetrics:
    """Comprehensive metrics data structure for ED simulation"""
    
    # Simulation metadata
    simulation_id: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    
    # Patient flow metrics
    total_arrivals: int = 0
    total_departures: int = 0
    total_admissions: int = 0
    total_discharges: int = 0
    total_lwbs: int = 0  # Left without being seen
    
    # Wait time metrics (by priority)
    wait_times: Dict[str, List[float]] = field(default_factory=lambda: {
        'IMMEDIATE': [], 'VERY_URGENT': [], 'URGENT': [], 'STANDARD': [], 'NON_URGENT': []
    })
    
    # Service time metrics
    triage_times: List[float] = field(default_factory=list)
    consultation_times: List[float] = field(default_factory=list)
    total_system_times: List[float] = field(default_factory=list)
    
    # Resource utilization metrics
    doctor_utilization: List[float] = field(default_factory=list)
    nurse_utilization: List[float] = field(default_factory=list)
    cubicle_utilization: List[float] = field(default_factory=list)
    bed_utilization: List[float] = field(default_factory=list)
    
    # Queue metrics
    queue_lengths: Dict[str, List[int]] = field(default_factory=lambda: {
        'triage': [], 'consultation': [], 'admission': []
    })
    
    # Triage performance metrics
    triage_accuracy: List[float] = field(default_factory=list)
    triage_confidence: List[float] = field(default_factory=list)
    priority_distribution: Dict[str, int] = field(default_factory=lambda: {
        'IMMEDIATE': 0, 'VERY_URGENT': 0, 'URGENT': 0, 'STANDARD': 0, 'NON_URGENT': 0
    })
    
    # Performance targets compliance
    target_breaches: Dict[str, int] = field(default_factory=lambda: {
        'IMMEDIATE': 0, 'VERY_URGENT': 0, 'URGENT': 0, 'STANDARD': 0, 'NON_URGENT': 0
    })
    
    # Time series data for plotting
    timestamps: List[float] = field(default_factory=list)
    arrivals_over_time: List[int] = field(default_factory=list)
    departures_over_time: List[int] = field(default_factory=list)
    queue_lengths_over_time: Dict[str, List[int]] = field(default_factory=lambda: {
        'IMMEDIATE': [], 'VERY_URGENT': [], 'URGENT': [], 'STANDARD': [], 'NON_URGENT': []
    })
    
    # Cost and efficiency metrics
    throughput_per_hour: float = 0.0
    average_length_of_stay: float = 0.0
    resource_efficiency: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization"""
        return {
            'simulation_metadata': {
                'simulation_id': self.simulation_id,
                'start_time': self.start_time,
                'end_time': self.end_time,
                'duration': self.duration
            },
            'patient_flow': {
                'total_arrivals': self.total_arrivals,
                'total_departures': self.total_departures,
                'total_admissions': self.total_admissions,
                'total_discharges': self.total_discharges,
                'total_lwbs': self.total_lwbs
            },
            'wait_times': dict(self.wait_times),
            'service_times': {
                'triage_times': self.triage_times,
                'consultation_times': self.consultation_times,
                'total_system_times': self.total_system_times
            },
            'resource_utilization': {
                'doctor_utilization': self.doctor_utilization,
                'nurse_utilization': self.nurse_utilization,
                'cubicle_utilization': self.cubicle_utilization,
                'bed_utilization': self.bed_utilization
            },
            'triage_performance': {
                'triage_accuracy': self.triage_accuracy,
                'triage_confidence': self.triage_confidence,
                'priority_distribution': dict(self.priority_distribution),
                'target_breaches': dict(self.target_breaches)
            },
            'performance_indicators': {
                'throughput_per_hour': self.throughput_per_hour,
                'average_length_of_stay': self.average_length_of_stay,
                'resource_efficiency': self.resource_efficiency
            },
            'time_series': {
                'timestamps': self.timestamps,
                'arrivals_over_time': self.arrivals_over_time,
                'departures_over_time': self.departures_over_time,
                'queue_lengths_over_time': dict(self.queue_lengths_over_time)
            }
        }


class MetricsCollector:
    """Comprehensive metrics collection system for ED simulation"""
    
    def __init__(self, simulation_id: str = None):
        self.simulation_id = simulation_id or f"sim_{int(time.time())}"
        self.metrics = SimulationMetrics(simulation_id=self.simulation_id)
        
        # Real-time tracking
        self.active_patients: Dict[str, Patient] = {}
        self.patient_timelines: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # Resource tracking
        self.resource_usage_history: Dict[str, deque] = {
            'doctors': deque(maxlen=1000),
            'nurses': deque(maxlen=1000),
            'cubicles': deque(maxlen=1000),
            'beds': deque(maxlen=1000)
        }
        
        # Performance targets (NHS standards)
        self.performance_targets = {
            Priority.IMMEDIATE: 0,      # Immediate
            Priority.VERY_URGENT: 10,  # 10 minutes
            Priority.URGENT: 60,       # 1 hour
            Priority.STANDARD: 120,    # 2 hours
            Priority.NON_URGENT: 240   # 4 hours
        }
        
        # Monitoring intervals
        self.last_snapshot_time = 0.0
        self.snapshot_interval = 60.0  # 1 minute intervals
        
    def start_simulation(self, current_time: float = None):
        """Initialize metrics collection for new simulation"""
        self.metrics.start_time = current_time if current_time is not None else 0.0
        self.last_snapshot_time = self.metrics.start_time
        
    def reset_metrics(self):
        """Reset all metrics (used after warmup period)"""
        # Store current time as new start time
        current_time = self.metrics.start_time if hasattr(self.metrics, 'start_time') else 0.0
        
        # Reset metrics but keep simulation_id
        simulation_id = self.simulation_id
        self.metrics = SimulationMetrics(simulation_id=simulation_id)
        
        # Clear tracking dictionaries
        self.active_patients.clear()
        self.patient_timelines.clear()
        
        # Clear resource usage history
        for key in self.resource_usage_history:
            self.resource_usage_history[key].clear()
        
        # Reset start time
        self.metrics.start_time = current_time
        self.last_snapshot_time = current_time
        
    def end_simulation(self, current_time: float = None):
        """Finalize metrics collection and calculate summary statistics"""
        self.metrics.end_time = current_time if current_time is not None else 0.0
        self.metrics.duration = self.metrics.end_time - self.metrics.start_time
        
        # Calculate final performance indicators
        self._calculate_performance_indicators()
        
    def record_patient_arrival(self, patient: Patient, arrival_time: float):
        """Record patient arrival event"""
        self.metrics.total_arrivals += 1
        self.active_patients[patient.patient_id] = patient
        self.patient_timelines[patient.patient_id]['arrival'] = arrival_time
        
        # Update priority distribution
        if patient.priority:
            self.metrics.priority_distribution[patient.priority.name] += 1
        
        # Update time series
        self._update_time_series(arrival_time, 'arrival')
        
    def record_patient_departure(self, patient: Patient, departure_time: float, 
                               departure_type: str = 'discharge'):
        """Record patient departure event"""
        self.metrics.total_departures += 1
        
        if departure_type == 'admission':
            self.metrics.total_admissions += 1
        elif departure_type == 'discharge':
            self.metrics.total_discharges += 1
        elif departure_type == 'lwbs':
            self.metrics.total_lwbs += 1
            
        # Update departures over time (increment current time slot)
        if len(self.metrics.departures_over_time) == 0:
            self.metrics.departures_over_time.append(1)
        else:
            self.metrics.departures_over_time[-1] += 1
            
        # Calculate system time
        if patient.patient_id in self.patient_timelines:
            arrival_time = self.patient_timelines[patient.patient_id].get('arrival', departure_time)
            system_time = departure_time - arrival_time
            self.metrics.total_system_times.append(system_time)
            
        # Remove from active tracking
        if patient.patient_id in self.active_patients:
            del self.active_patients[patient.patient_id]
            
        # Update time series
        self._update_time_series(departure_time, 'departure')
        
    def record_triage_completion(self, patient: Patient, triage_time: float, 
                               confidence: float, current_time: float):
        """Record triage completion event"""
        self.metrics.triage_times.append(triage_time)
        self.metrics.triage_confidence.append(confidence)
        
        if patient.priority:
            self.metrics.priority_distribution[patient.priority.name] += 1
            
        self.patient_timelines[patient.patient_id]['triage_complete'] = current_time
        
    def record_consultation_start(self, patient: Patient, current_time: float):
        """Record consultation start event"""
        self.patient_timelines[patient.patient_id]['consultation_start'] = current_time
        
        # Calculate wait time
        if patient.priority and 'triage_complete' in self.patient_timelines[patient.patient_id]:
            triage_complete_time = self.patient_timelines[patient.patient_id]['triage_complete']
            wait_time = current_time - triage_complete_time
            self.metrics.wait_times[patient.priority.name].append(wait_time)
            
            # Check for target breaches
            target_time = self.performance_targets.get(patient.priority, 240)
            if wait_time > target_time:
                self.metrics.target_breaches[patient.priority.name] += 1
                
    def record_consultation_completion(self, patient: Patient, current_time: float):
        """Record consultation completion event"""
        if 'consultation_start' in self.patient_timelines[patient.patient_id]:
            consultation_start = self.patient_timelines[patient.patient_id]['consultation_start']
            consultation_time = current_time - consultation_start
            self.metrics.consultation_times.append(consultation_time)
            
        self.patient_timelines[patient.patient_id]['consultation_complete'] = current_time
        
    def record_resource_utilization(self, current_time: float, doctors_busy: int, 
                                  nurses_busy: int, cubicles_busy: int, 
                                  beds_busy: int, total_doctors: int, 
                                  total_nurses: int, total_cubicles: int, 
                                  total_beds: int):
        """Record resource utilization snapshot"""
        
        # Calculate utilization percentages
        doctor_util = (doctors_busy / total_doctors) * 100 if total_doctors > 0 else 0
        nurse_util = (nurses_busy / total_nurses) * 100 if total_nurses > 0 else 0
        cubicle_util = (cubicles_busy / total_cubicles) * 100 if total_cubicles > 0 else 0
        bed_util = (beds_busy / total_beds) * 100 if total_beds > 0 else 0
        
        # Store utilization data
        self.metrics.doctor_utilization.append(doctor_util)
        self.metrics.nurse_utilization.append(nurse_util)
        self.metrics.cubicle_utilization.append(cubicle_util)
        self.metrics.bed_utilization.append(bed_util)
        
        # Update resource usage history
        self.resource_usage_history['doctors'].append((current_time, doctor_util))
        self.resource_usage_history['nurses'].append((current_time, nurse_util))
        self.resource_usage_history['cubicles'].append((current_time, cubicle_util))
        self.resource_usage_history['beds'].append((current_time, bed_util))
        
    def record_queue_lengths(self, current_time: float, priority_queues: Dict[Priority, int],
                           triage_queue: int = 0, admission_queue: int = 0):
        """Record queue length snapshot"""
        
        # Record priority-based queue lengths
        for priority, queue_length in priority_queues.items():
            if priority and priority.name in self.metrics.queue_lengths_over_time:
                self.metrics.queue_lengths_over_time[priority.name].append(queue_length)
                
        # Record general queue lengths
        self.metrics.queue_lengths['triage'].append(triage_queue)
        self.metrics.queue_lengths['admission'].append(admission_queue)
        
    def take_snapshot(self, current_time: float, ed_status: Dict[str, Any]):
        """Take comprehensive system snapshot for time series analysis"""
        
        if current_time - self.last_snapshot_time >= self.snapshot_interval:
            self.metrics.timestamps.append(current_time)
            
            # Initialize time series arrays if empty
            if len(self.metrics.arrivals_over_time) == 0:
                self.metrics.arrivals_over_time.append(0)
            if len(self.metrics.departures_over_time) == 0:
                self.metrics.departures_over_time.append(0)
                
            # Add new time slot for next interval
            self.metrics.arrivals_over_time.append(0)
            self.metrics.departures_over_time.append(0)
            
            # Record current system state
            if 'resource_utilization' in ed_status:
                util = ed_status['resource_utilization']
                self.record_resource_utilization(
                    current_time,
                    util.get('doctors_busy', 0),
                    util.get('nurses_busy', 0), 
                    util.get('cubicles_busy', 0),
                    util.get('beds_busy', 0),
                    util.get('total_doctors', 1),
                    util.get('total_nurses', 1),
                    util.get('total_cubicles', 1),
                    util.get('total_beds', 1)
                )
                
            if 'queue_lengths' in ed_status:
                queues = ed_status['queue_lengths']
                self.record_queue_lengths(current_time, queues)
                
            self.last_snapshot_time = current_time
            
    def _update_time_series(self, current_time: float, event_type: str):
        """Update time series data for arrivals/departures"""
        
        # Initialize if first event
        if not self.metrics.timestamps:
            self.metrics.timestamps.append(current_time)
            self.metrics.arrivals_over_time.append(0)
            self.metrics.departures_over_time.append(0)
            
        # Update counters
        if event_type == 'arrival':
            if self.metrics.arrivals_over_time:
                self.metrics.arrivals_over_time[-1] += 1
            else:
                self.metrics.arrivals_over_time.append(1)
        elif event_type == 'departure':
            if self.metrics.departures_over_time:
                self.metrics.departures_over_time[-1] += 1
            else:
                self.metrics.departures_over_time.append(1)
                
    def _calculate_performance_indicators(self):
        """Calculate final performance indicators"""
        
        # Throughput (patients per hour)
        if self.metrics.duration > 0:
            duration_hours = self.metrics.duration / 60  # Convert minutes to hours
            self.metrics.throughput_per_hour = self.metrics.total_departures / duration_hours
            
        # Average length of stay
        if self.metrics.total_system_times:
            self.metrics.average_length_of_stay = np.mean(self.metrics.total_system_times)
            
        # Resource efficiency (average utilization across all resources)
        utilizations = []
        if self.metrics.doctor_utilization:
            utilizations.append(np.mean(self.metrics.doctor_utilization))
        if self.metrics.nurse_utilization:
            utilizations.append(np.mean(self.metrics.nurse_utilization))
        if self.metrics.cubicle_utilization:
            utilizations.append(np.mean(self.metrics.cubicle_utilization))
        if self.metrics.bed_utilization:
            utilizations.append(np.mean(self.metrics.bed_utilization))
            
        if utilizations:
            self.metrics.resource_efficiency = np.mean(utilizations)
            
    def get_metrics(self) -> SimulationMetrics:
        """Get current metrics snapshot"""
        return self.metrics
        
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics for reporting"""
        
        summary = {
            'simulation_overview': {
                'duration_minutes': self.metrics.duration / 60,
                'total_patients': self.metrics.total_arrivals,
                'throughput_per_hour': self.metrics.throughput_per_hour
            },
            'wait_time_statistics': {},
            'service_time_statistics': {
                'triage': self._calculate_stats(self.metrics.triage_times),
                'consultation': self._calculate_stats(self.metrics.consultation_times),
                'total_system': self._calculate_stats(self.metrics.total_system_times)
            },
            'resource_utilization': {
                'doctors': self._calculate_stats(self.metrics.doctor_utilization),
                'nurses': self._calculate_stats(self.metrics.nurse_utilization),
                'cubicles': self._calculate_stats(self.metrics.cubicle_utilization),
                'beds': self._calculate_stats(self.metrics.bed_utilization)
            },
            'performance_targets': {
                'breach_rates': {},
                'compliance_rates': {}
            }
        }
        
        # Calculate wait time statistics by priority
        for priority, times in self.metrics.wait_times.items():
            if times:
                summary['wait_time_statistics'][priority] = self._calculate_stats(times)
                
                # Calculate breach rates
                target_time = self.performance_targets.get(
                    Priority[priority] if hasattr(Priority, priority) else Priority.NON_URGENT, 240
                )
                breaches = sum(1 for t in times if t > target_time)
                breach_rate = (breaches / len(times)) * 100
                summary['performance_targets']['breach_rates'][priority] = breach_rate
                summary['performance_targets']['compliance_rates'][priority] = 100 - breach_rate
                
        return summary
        
    def _calculate_stats(self, data: List[float]) -> Dict[str, float]:
        """Calculate basic statistics for a dataset"""
        if not data:
            return {'count': 0, 'mean': 0, 'median': 0, 'std': 0, 'min': 0, 'max': 0}
            
        return {
            'count': len(data),
            'mean': float(np.mean(data)),
            'median': float(np.median(data)),
            'std': float(np.std(data)),
            'min': float(np.min(data)),
            'max': float(np.max(data)),
            'p95': float(np.percentile(data, 95)),
            'p99': float(np.percentile(data, 99))
        }