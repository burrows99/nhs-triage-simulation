import simpy
import numpy as np
from typing import Dict, Any, Optional, List
from .emergency_department import EmergencyDepartment
from .patient_generator import PatientGenerator
from ..triage.manchester_triage import ManchesterTriage
# AI triage system to be implemented later


class SimulationEngine:
    """Main simulation engine for emergency department simulation"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize simulation engine
        
        Args:
            config: Simulation configuration parameters
        """
        self.config = config or self._default_config()
        self.env = None
        self.ed = None
        self.patient_generator = None
        self.results = None
        
    def _default_config(self) -> Dict[str, Any]:
        """Default simulation configuration"""
        return {
            'simulation': {
                'duration': 24 * 60,  # 24 hours in minutes
                'warmup_period': 2 * 60,  # 2 hours warmup
                'random_seed': 42
            },
            'resources': {
                'num_triage_nurses': 2,
                'num_doctors': 4,
                'num_cubicles': 8,
                'num_admission_beds': 20
            },
            'patient_arrival': {
                'arrival_rate': 0.5,  # patients per minute
                'arrival_pattern': 'constant'  # or 'variable'
            },
            'triage_system': {
                'type': 'manchester',  # 'manchester', 'adaptive', 'custom'
                'priority_calculator': 'manchester',  # 'manchester', 'weighted', 'custom'
                'base_triage_time': 5.0,
                'triage_time_std': 2.0
            },
            'performance_targets': {
                'max_wait_time_p1': 0,    # Immediate
                'max_wait_time_p2': 10,   # Very urgent
                'max_wait_time_p3': 60,   # Urgent
                'max_wait_time_p4': 120,  # Standard
                'max_wait_time_p5': 240   # Non-urgent
            },
            'optimization': {
                'enabled': False,
                'optimization_interval': 4 * 60,  # 4 hours
                'target_wait_time': 60.0
            }
        }
    
    def setup_simulation(self) -> None:
        """Setup simulation environment and components"""
        # Set random seed for reproducibility
        if self.config['simulation']['random_seed']:
            np.random.seed(self.config['simulation']['random_seed'])
        
        # Create SimPy environment
        self.env = simpy.Environment()
        
        # Setup triage system
        triage_system = self._create_triage_system()
        
        # Create Emergency Department
        self.ed = EmergencyDepartment(
            env=self.env,
            num_triage_nurses=self.config['resources']['num_triage_nurses'],
            num_doctors=self.config['resources']['num_doctors'],
            num_cubicles=self.config['resources']['num_cubicles'],
            num_admission_beds=self.config['resources']['num_admission_beds'],
            triage_system=triage_system
        )
        
        # Create patient generator
        self.patient_generator = PatientGenerator(
            env=self.env,
            ed=self.ed,
            arrival_rate=self.config['patient_arrival']['arrival_rate']
        )
        
        # Setup optimization if enabled
        if self.config['optimization']['enabled']:
            self.env.process(self._optimization_process())
        
        # Setup variable arrival pattern if configured
        if self.config['patient_arrival']['arrival_pattern'] == 'variable':
            self.env.process(self._variable_arrival_process())
        
        print(f"Simulation setup complete:")
        print(f"  Duration: {self.config['simulation']['duration']} minutes")
        print(f"  Resources: {self.config['resources']['num_doctors']} doctors, {self.config['resources']['num_cubicles']} cubicles")
        print(f"  Arrival rate: {self.config['patient_arrival']['arrival_rate']} patients/minute")
        print(f"  Triage system: {self.config['triage_system']['type']}")
    
    def _create_triage_system(self):
        """Create and configure triage system"""
        triage_config = self.config['triage_system']
        
        # Create Manchester triage system (only supported system currently)
        return ManchesterTriage()
    
    def _optimization_process(self):
        """Process for dynamic resource optimization during simulation"""
        optimization_interval = self.config['optimization']['optimization_interval']
        target_wait_time = self.config['optimization']['target_wait_time']
        
        while True:
            yield self.env.timeout(optimization_interval)
            
            # Get resource optimization suggestions
            suggestions = self.ed.optimize_resources(target_wait_time)
            
            print(f"Time {self.env.now:.1f}: Resource optimization suggestions: {suggestions}")
            
            # Apply optimizations (in a real system, this would require approval)
            # For simulation purposes, we can implement automatic adjustments
            current_status = self.ed.get_current_status()
            
            # Log current performance
            print(f"  Current patients in system: {current_status['patients_in_system']}")
            print(f"  Queue lengths: {current_status['queue_lengths']}")
    
    def _variable_arrival_process(self):
        """Process for variable patient arrival rates (e.g., daily patterns)"""
        base_rate = self.config['patient_arrival']['arrival_rate']
        
        while True:
            # Simulate daily variation in arrival rates
            current_hour = (self.env.now / 60) % 24
            
            # Peak hours: 10-14 and 18-22
            if (10 <= current_hour <= 14) or (18 <= current_hour <= 22):
                multiplier = 1.5  # 50% increase during peak hours
            elif (2 <= current_hour <= 6):
                multiplier = 0.5  # 50% decrease during night hours
            else:
                multiplier = 1.0  # Normal rate
            
            new_rate = base_rate * multiplier
            self.patient_generator.set_arrival_rate(new_rate)
            
            # Check every hour
            yield self.env.timeout(60)
    
    def run_simulation(self) -> Dict[str, Any]:
        """Run the complete simulation"""
        if not self.env:
            self.setup_simulation()
        
        print(f"\nStarting simulation...")
        print(f"Warmup period: {self.config['simulation']['warmup_period']} minutes")
        
        # Run simulation
        try:
            self.env.run(until=self.config['simulation']['duration'])
            print(f"\nSimulation completed at time {self.env.now:.1f} minutes")
        except Exception as e:
            print(f"Simulation error: {e}")
            raise
        
        # Collect results
        self.results = self._collect_results()
        
        return self.results
    
    def _collect_results(self) -> Dict[str, Any]:
        """Collect and compile simulation results"""
        # Get ED results
        ed_results = self.ed.get_simulation_results()
        
        # Get patient generator statistics
        arrival_stats = self.patient_generator.get_arrival_statistics()
        
        # Get Poisson verification
        poisson_verification = self.patient_generator.verify_poisson_process()
        
        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(ed_results)
        
        # Compile comprehensive results
        results = {
            'simulation_config': self.config,
            'simulation_summary': {
                'duration': self.config['simulation']['duration'],
                'warmup_period': self.config['simulation']['warmup_period'],
                'final_time': self.env.now
            },
            'ed_results': ed_results,
            'arrival_statistics': arrival_stats,
            'poisson_verification': poisson_verification,
            'performance_metrics': performance_metrics,
            'resource_recommendations': self._generate_recommendations(ed_results)
        }
        
        return results
    
    def _calculate_performance_metrics(self, ed_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate key performance indicators"""
        metrics = {}
        
        # Wait time performance
        wait_time_stats = ed_results.get('wait_time_statistics', {})
        targets = self.config['performance_targets']
        
        wait_time_performance = {}
        for priority_name, stats in wait_time_stats.items():
            target_key = f"max_wait_time_p{priority_name[-1]}"  # Extract priority number
            if target_key in targets:
                target_time = targets[target_key]
                breach_rate = sum(1 for t in stats.get('times', []) if t > target_time) / len(stats.get('times', [1]))
                wait_time_performance[priority_name] = {
                    'target_time': target_time,
                    'actual_mean': stats.get('mean', 0),
                    'breach_rate': breach_rate,
                    'performance_score': max(0, 1 - breach_rate)
                }
        
        metrics['wait_time_performance'] = wait_time_performance
        
        # Overall ED performance score
        summary_stats = ed_results.get('summary_statistics', {})
        
        metrics['overall_performance'] = {
            'throughput': summary_stats.get('total_departures', 0) / (self.config['simulation']['duration'] / 60),  # patients per hour
            'admission_rate': summary_stats.get('admission_rate', 0),
            'lwbs_rate': summary_stats.get('lwbs_rate', 0),
            'bed_occupancy': self._calculate_bed_occupancy(ed_results)
        }
        
        return metrics
    
    def _calculate_bed_occupancy(self, ed_results: Dict[str, Any]) -> float:
        """Calculate average bed occupancy rate"""
        # This is a simplified calculation
        # In a real implementation, you'd track bed usage over time
        total_beds = self.config['resources']['num_cubicles'] + self.config['resources']['num_admission_beds']
        summary_stats = ed_results.get('summary_statistics', {})
        total_patients = summary_stats.get('total_arrivals', 0)
        
        if total_patients == 0:
            return 0.0
        
        # Estimate based on system times
        system_stats = ed_results.get('system_time_statistics', {})
        avg_system_time = system_stats.get('mean', 120)  # Default 2 hours
        
        # Little's Law: L = λW
        arrival_rate = total_patients / self.config['simulation']['duration']
        avg_patients_in_system = arrival_rate * avg_system_time
        
        return min(1.0, avg_patients_in_system / total_beds)
    
    def _generate_recommendations(self, ed_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations for ED improvement"""
        recommendations = {
            'resource_optimization': self.ed.optimize_resources(),
            'process_improvements': [],
            'priority_system_adjustments': []
        }
        
        # Analyze wait times for recommendations
        wait_time_stats = ed_results.get('wait_time_statistics', {})
        
        for priority_name, stats in wait_time_stats.items():
            if stats.get('mean', 0) > 60:  # If average wait > 1 hour
                recommendations['process_improvements'].append(
                    f"High wait times for {priority_name} patients (avg: {stats.get('mean', 0):.1f} min)"
                )
        
        # Analyze LWBS rate
        summary_stats = ed_results.get('summary_statistics', {})
        lwbs_rate = summary_stats.get('lwbs_rate', 0)
        
        if lwbs_rate > 0.05:  # If LWBS rate > 5%
            recommendations['process_improvements'].append(
                f"High LWBS rate ({lwbs_rate:.1%}) - consider increasing triage capacity"
            )
        
        return recommendations
    
    def get_results(self) -> Optional[Dict[str, Any]]:
        """Get simulation results"""
        return self.results
    
    def print_summary(self) -> None:
        """Print simulation summary"""
        if not self.results:
            print("No results available. Run simulation first.")
            return
        
        print("\n" + "="*60)
        print("EMERGENCY DEPARTMENT SIMULATION RESULTS")
        print("="*60)
        
        # Summary statistics
        summary = self.results['ed_results']['summary_statistics']
        print(f"\nSUMMARY STATISTICS:")
        print(f"  Total Arrivals: {summary['total_arrivals']}")
        print(f"  Total Departures: {summary['total_departures']}")
        print(f"  Admissions: {summary['total_admissions']} ({summary['admission_rate']:.1%})")
        print(f"  Discharges: {summary['total_discharges']}")
        print(f"  LWBS: {summary['lwbs_count']} ({summary['lwbs_rate']:.1%})")
        
        # Wait time statistics
        wait_stats = self.results['ed_results']['wait_time_statistics']
        if wait_stats:
            print(f"\nWAIT TIME STATISTICS (minutes):")
            for priority, stats in wait_stats.items():
                print(f"  {priority}: Mean={stats['mean']:.1f}, Median={stats['median']:.1f}, Max={stats['max']:.1f}")
        
        # System performance
        system_stats = self.results['ed_results']['system_time_statistics']
        if system_stats:
            print(f"\nSYSTEM TIME STATISTICS (minutes):")
            print(f"  Mean: {system_stats['mean']:.1f}")
            print(f"  Median: {system_stats['median']:.1f}")
            print(f"  Max: {system_stats['max']:.1f}")
        
        # Performance metrics
        performance = self.results['performance_metrics']
        print(f"\nPERFORMANCE METRICS:")
        overall = performance['overall_performance']
        print(f"  Throughput: {overall['throughput']:.1f} patients/hour")
        print(f"  Bed Occupancy: {overall['bed_occupancy']:.1%}")
        
        # Recommendations
        recommendations = self.results['resource_recommendations']
        if recommendations['process_improvements']:
            print(f"\nRECOMMENDATIONS:")
            for rec in recommendations['process_improvements']:
                print(f"  • {rec}")
        
        print("\n" + "="*60)