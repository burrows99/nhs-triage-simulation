from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import json
from pathlib import Path


@dataclass
class SimulationParameters:
    """Configuration parameters for emergency department simulation"""
    
    # Simulation timing
    duration: float = 24 * 60  # 24 hours in minutes
    warmup_period: float = 2 * 60  # 2 hours warmup
    random_seed: Optional[int] = 42
    
    # Patient arrival configuration
    arrival_rate: float = 0.5  # patients per minute
    arrival_pattern: str = 'constant'  # 'constant' or 'variable'
    
    # Resource allocation
    num_triage_nurses: int = 2
    num_doctors: int = 4
    num_cubicles: int = 8
    num_admission_beds: int = 20
    
    # Triage system configuration (only Manchester supported currently)
    triage_system_type: str = 'manchester'
    
    # Performance targets (minutes)
    max_wait_time_p1: float = 0    # Immediate
    max_wait_time_p2: float = 10   # Very urgent
    max_wait_time_p3: float = 60   # Urgent
    max_wait_time_p4: float = 120  # Standard
    max_wait_time_p5: float = 240  # Non-urgent
    
    # Optimization settings
    optimization_enabled: bool = False
    optimization_interval: float = 4 * 60  # 4 hours
    target_wait_time: float = 60.0
    
    # Consultation time parameters by priority
    consultation_times: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        'IMMEDIATE': {'mean': 45, 'std': 15},
        'VERY_URGENT': {'mean': 35, 'std': 12},
        'URGENT': {'mean': 25, 'std': 10},
        'STANDARD': {'mean': 20, 'std': 8},
        'NON_URGENT': {'mean': 15, 'std': 5}
    })
    
    # Admission probabilities by priority
    admission_probabilities: Dict[str, float] = field(default_factory=lambda: {
        'IMMEDIATE': 0.8,
        'VERY_URGENT': 0.4,
        'URGENT': 0.2,
        'STANDARD': 0.1,
        'NON_URGENT': 0.05
    })
    
    # CSV data configuration
    csv_directory: str = 'output/csv'  # Relative path from project root
    
    # Metrics output configuration
    metrics_output_directory: str = 'metrics_output'  # Relative path from project root
    
    # Monitoring and reporting
    monitoring_interval: float = 60  # Monitor every hour
    enable_detailed_logging: bool = True
    log_patient_journeys: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert parameters to dictionary"""
        return {
            'simulation': {
                'duration': self.duration,
                'warmup_period': self.warmup_period,
                'random_seed': self.random_seed
            },
            'patient_arrival': {
                'arrival_rate': self.arrival_rate,
                'arrival_pattern': self.arrival_pattern
            },
            'resources': {
                'num_triage_nurses': self.num_triage_nurses,
                'num_doctors': self.num_doctors,
                'num_cubicles': self.num_cubicles,
                'num_admission_beds': self.num_admission_beds
            },
            'triage_system': {
                'type': self.triage_system_type
            },
            'performance_targets': {
                'max_wait_time_p1': self.max_wait_time_p1,
                'max_wait_time_p2': self.max_wait_time_p2,
                'max_wait_time_p3': self.max_wait_time_p3,
                'max_wait_time_p4': self.max_wait_time_p4,
                'max_wait_time_p5': self.max_wait_time_p5
            },
            'optimization': {
                'enabled': self.optimization_enabled,
                'optimization_interval': self.optimization_interval,
                'target_wait_time': self.target_wait_time
            },
            'consultation_times': self.consultation_times,
            'admission_probabilities': self.admission_probabilities,
            'data_sources': {
                'csv_directory': self.csv_directory,
                'metrics_output_directory': self.metrics_output_directory
            },
            'monitoring': {
                'monitoring_interval': self.monitoring_interval,
                'enable_detailed_logging': self.enable_detailed_logging,
                'log_patient_journeys': self.log_patient_journeys
            }
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'SimulationParameters':
        """Create parameters from dictionary"""
        params = cls()
        
        # Update simulation parameters
        if 'simulation' in config_dict:
            sim_config = config_dict['simulation']
            params.duration = sim_config.get('duration', params.duration)
            params.warmup_period = sim_config.get('warmup_period', params.warmup_period)
            params.random_seed = sim_config.get('random_seed', params.random_seed)
        
        # Update patient arrival parameters
        if 'patient_arrival' in config_dict:
            arrival_config = config_dict['patient_arrival']
            params.arrival_rate = arrival_config.get('arrival_rate', params.arrival_rate)
            params.arrival_pattern = arrival_config.get('arrival_pattern', params.arrival_pattern)
        
        # Update resource parameters
        if 'resources' in config_dict:
            resource_config = config_dict['resources']
            params.num_triage_nurses = resource_config.get('num_triage_nurses', params.num_triage_nurses)
            params.num_doctors = resource_config.get('num_doctors', params.num_doctors)
            params.num_cubicles = resource_config.get('num_cubicles', params.num_cubicles)
            params.num_admission_beds = resource_config.get('num_admission_beds', params.num_admission_beds)
        
        # Update triage system parameters
        if 'triage_system' in config_dict:
            triage_config = config_dict['triage_system']
            params.triage_system_type = triage_config.get('type', params.triage_system_type)
        
        # Update performance targets
        if 'performance_targets' in config_dict:
            perf_config = config_dict['performance_targets']
            params.max_wait_time_p1 = perf_config.get('max_wait_time_p1', params.max_wait_time_p1)
            params.max_wait_time_p2 = perf_config.get('max_wait_time_p2', params.max_wait_time_p2)
            params.max_wait_time_p3 = perf_config.get('max_wait_time_p3', params.max_wait_time_p3)
            params.max_wait_time_p4 = perf_config.get('max_wait_time_p4', params.max_wait_time_p4)
            params.max_wait_time_p5 = perf_config.get('max_wait_time_p5', params.max_wait_time_p5)
        
        # Update optimization parameters
        if 'optimization' in config_dict:
            opt_config = config_dict['optimization']
            params.optimization_enabled = opt_config.get('enabled', params.optimization_enabled)
            params.optimization_interval = opt_config.get('optimization_interval', params.optimization_interval)
            params.target_wait_time = opt_config.get('target_wait_time', params.target_wait_time)
        
        # Update other parameters
        if 'consultation_times' in config_dict:
            params.consultation_times.update(config_dict['consultation_times'])
        
        if 'admission_probabilities' in config_dict:
            params.admission_probabilities.update(config_dict['admission_probabilities'])
        
        # Update data source parameters
        if 'data_sources' in config_dict:
            data_config = config_dict['data_sources']
            params.csv_directory = data_config.get('csv_directory', params.csv_directory)
            params.metrics_output_directory = data_config.get('metrics_output_directory', params.metrics_output_directory)
        
        if 'monitoring' in config_dict:
            mon_config = config_dict['monitoring']
            params.monitoring_interval = mon_config.get('monitoring_interval', params.monitoring_interval)
            params.enable_detailed_logging = mon_config.get('enable_detailed_logging', params.enable_detailed_logging)
            params.log_patient_journeys = mon_config.get('log_patient_journeys', params.log_patient_journeys)
        
        return params
    
    def save_to_file(self, filepath: str) -> None:
        """Save parameters to JSON file"""
        config_dict = self.to_dict()
        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'SimulationParameters':
        """Load parameters from JSON file"""
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)
    
    def validate(self) -> bool:
        """Validate parameter values"""
        errors = []
        
        # Validate positive values
        if self.duration <= 0:
            errors.append("Duration must be positive")
        
        if self.arrival_rate <= 0:
            errors.append("Arrival rate must be positive")
        
        if self.num_triage_nurses <= 0:
            errors.append("Number of triage nurses must be positive")
        
        if self.num_doctors <= 0:
            errors.append("Number of doctors must be positive")
        
        if self.num_cubicles <= 0:
            errors.append("Number of cubicles must be positive")
        
        # Validate wait time targets are in ascending order
        wait_times = [self.max_wait_time_p1, self.max_wait_time_p2, 
                     self.max_wait_time_p3, self.max_wait_time_p4, self.max_wait_time_p5]
        
        if wait_times != sorted(wait_times):
            errors.append("Wait time targets must be in ascending order by priority")
        
        # Validate probabilities
        for priority, prob in self.admission_probabilities.items():
            if not 0 <= prob <= 1:
                errors.append(f"Admission probability for {priority} must be between 0 and 1")
        
        if errors:
            print("Parameter validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        return True
    
    def get_scenario_configs(self) -> Dict[str, 'SimulationParameters']:
        """Get predefined scenario configurations"""
        scenarios = {}
        
        # Low demand scenario
        low_demand = SimulationParameters(
            arrival_rate=0.3,
            num_doctors=3,
            num_cubicles=6,
            duration=12 * 60  # 12 hours
        )
        scenarios['low_demand'] = low_demand
        
        # High demand scenario
        high_demand = SimulationParameters(
            arrival_rate=0.8,
            num_doctors=6,
            num_cubicles=12,
            num_triage_nurses=3,
            duration=24 * 60  # 24 hours
        )
        scenarios['high_demand'] = high_demand
        
        # Crisis scenario (pandemic-like)
        crisis = SimulationParameters(
            arrival_rate=1.2,
            num_doctors=8,
            num_cubicles=16,
            num_triage_nurses=4,
            num_admission_beds=30,
            optimization_enabled=True,
            duration=48 * 60  # 48 hours
        )
        scenarios['crisis'] = crisis
        
        # Optimization test scenario
        optimization_test = SimulationParameters(
            arrival_rate=0.6,
            optimization_enabled=True,
            optimization_interval=2 * 60,  # 2 hours
            target_wait_time=45.0,
            duration=16 * 60  # 16 hours
        )
        scenarios['optimization_test'] = optimization_test
        
        return scenarios