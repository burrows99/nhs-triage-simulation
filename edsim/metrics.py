from typing import Dict, List, Tuple, Any
import numpy as np  # type: ignore
from numpy.typing import NDArray
from dataclasses import dataclass

from .constants import RESOURCES
from .models import Patient


@dataclass
class SimulationMetrics:
    """
    Comprehensive metrics calculation service for ED simulation analysis.
    Follows Single Responsibility Principle by centralizing all metric calculations.
    """
    
    @staticmethod
    def calculate_wait_time_statistics(
        wait_times: Dict[str, List[float]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate wait time statistics (average and median) for each resource.
        """
        return {
            r: {
                'avg': float(np.mean(wait_times[r])) if wait_times[r] else 0.0,
                'median': float(np.median(wait_times[r])) if wait_times[r] else 0.0,
                'std': float(np.std(wait_times[r])) if wait_times[r] else 0.0,
                'min': float(np.min(wait_times[r])) if wait_times[r] else 0.0,
                'max': float(np.max(wait_times[r])) if wait_times[r] else 0.0,
                'count': len(wait_times[r])
            }
            for r in RESOURCES
        }
    
    @staticmethod
    def calculate_utilization_metrics(
        resource_busy_time: Dict[str, float],
        duration: int,
        resource_capacities: Dict[str, int]
    ) -> Dict[str, float]:
        """
        Calculate resource utilization percentages.
        Utilization = (total service time) / (duration * capacity) * 100
        """
        return {
            r: (
                resource_busy_time[r] / (duration * resource_capacities[r]) * 100.0
            ) if (duration * resource_capacities[r]) > 0 else 0.0
            for r in RESOURCES
        }
    
    @staticmethod
    def calculate_queue_metrics(
        queue_lengths: List[List[float]]
    ) -> Tuple[NDArray[np.float64], Dict[str, Dict[str, float]]]:
        """
        Calculate queue timeline and queue statistics.
        Returns queue array and detailed queue metrics per resource.
        """
        # Queue timeline array: rows = [time, q_doctor, q_mri, q_us, q_bed]
        queue_arr: NDArray[np.float64] = (
            np.array(queue_lengths, dtype=float) 
            if queue_lengths 
            else np.zeros((0, 1 + len(RESOURCES)))
        )
        
        # Calculate queue statistics per resource
        queue_stats = {}
        if queue_arr.size > 0:
            for r_idx, r in enumerate(RESOURCES):
                queue_data = queue_arr[:, r_idx + 1]
                queue_stats[r] = {
                    'avg_queue': float(np.mean(queue_data)),
                    'max_queue': float(np.max(queue_data)),
                    'min_queue': float(np.min(queue_data)),
                    'std_queue': float(np.std(queue_data)),
                    'median_queue': float(np.median(queue_data))
                }
        else:
            queue_stats = {r: {
                'avg_queue': 0.0, 'max_queue': 0.0, 'min_queue': 0.0,
                'std_queue': 0.0, 'median_queue': 0.0
            } for r in RESOURCES}
        
        return queue_arr, queue_stats
    
    @staticmethod
    def calculate_urgent_care_metrics(
        urgent_mri_total: int,
        urgent_mri_bypassed: int
    ) -> Dict[str, float]:
        """
        Calculate urgent care routing metrics.
        """
        return {
            'total': float(urgent_mri_total),
            'bypassed': float(urgent_mri_bypassed),
            'bypass_rate': (
                urgent_mri_bypassed / urgent_mri_total * 100.0
            ) if urgent_mri_total > 0 else 0.0,
            'doctor_first': float(urgent_mri_total - urgent_mri_bypassed),
            'doctor_first_rate': (
                (urgent_mri_total - urgent_mri_bypassed) / urgent_mri_total * 100.0
            ) if urgent_mri_total > 0 else 0.0
        }
    
    @staticmethod
    def calculate_patient_flow_metrics(
        patients: List[Patient]
    ) -> Dict[str, Any]:  # type: ignore
        """
        Calculate comprehensive patient flow and pathway metrics.
        """
        total_patients = len(patients)
        
        if total_patients == 0:
            return {  # type: ignore
                'total_patients': 0,
                'avg_tasks_per_patient': 0.0,
                'pathway_diversity': 0.0
            }
        
        # Calculate average tasks per patient
        total_tasks = sum(len(p.tasks) for p in patients)
        avg_tasks = total_tasks / total_patients
        
        # Calculate pathway diversity (unique pathway combinations)
        unique_pathways = set(tuple(p.tasks) for p in patients)
        pathway_diversity = len(unique_pathways) / total_patients
        
        # Calculate task frequency
        task_counts: Dict[str, int] = {}
        for patient in patients:
            for task in patient.tasks:
                task_counts[task] = task_counts.get(task, 0) + 1
        
        return {  # type: ignore
            'total_patients': total_patients,
            'avg_tasks_per_patient': avg_tasks,
            'pathway_diversity': pathway_diversity,
            'unique_pathways': len(unique_pathways),
            'task_frequencies': task_counts
        }
    
    @staticmethod
    def calculate_performance_indicators(
        wait_stats: Dict[str, Dict[str, float]],
        utilization: Dict[str, float],
        queue_stats: Dict[str, Dict[str, float]],
        urgent_stats: Dict[str, float]
    ) -> Dict[str, Any]:  # type: ignore
        """
        Calculate key performance indicators (KPIs) for the simulation.
        """
        # Overall system performance
        avg_wait_time = float(np.mean([wait_stats[r]['avg'] for r in RESOURCES]))
        avg_utilization = float(np.mean([utilization[r] for r in RESOURCES]))
        avg_queue_length = float(np.mean([queue_stats[r]['avg_queue'] for r in RESOURCES]))
        
        # Identify bottlenecks
        bottleneck_resource = max(RESOURCES, key=lambda r: wait_stats[r]['avg'])
        bottleneck_wait_time = wait_stats[bottleneck_resource]['avg']
        
        # System efficiency score (0-100)
        # Higher utilization is better, but lower wait times are better
        # Balanced scoring: 50% utilization efficiency + 50% wait time efficiency
        util_efficiency = min(avg_utilization, 100.0)  # Cap at 100%
        wait_efficiency = max(0.0, 100.0 - avg_wait_time)  # Lower wait = higher efficiency
        system_efficiency = (util_efficiency + wait_efficiency) / 2
        
        return {  # type: ignore
            'avg_wait_time': avg_wait_time,
            'avg_utilization': avg_utilization,
            'avg_queue_length': avg_queue_length,
            'bottleneck_resource': bottleneck_resource,
            'bottleneck_wait_time': bottleneck_wait_time,
            'system_efficiency_score': system_efficiency,
            'urgent_bypass_rate': urgent_stats['bypass_rate']
        }
    
    @classmethod
    def calculate_comprehensive_metrics(
        cls,
        wait_times: Dict[str, List[float]],
        queue_lengths: List[List[float]],
        resource_busy_time: Dict[str, float],
        duration: int,
        resource_capacities: Dict[str, int],
        urgent_mri_total: int,
        urgent_mri_bypassed: int,
        patients: List[Patient]
    ) -> Dict[str, Any]:  # type: ignore
        """
        Calculate all metrics in one comprehensive call.
        Returns a dictionary containing all calculated metrics.
        """
        # Calculate individual metric categories
        wait_stats = cls.calculate_wait_time_statistics(wait_times)
        utilization = cls.calculate_utilization_metrics(
            resource_busy_time, duration, resource_capacities
        )
        queue_arr, queue_stats = cls.calculate_queue_metrics(queue_lengths)
        urgent_stats = cls.calculate_urgent_care_metrics(
            urgent_mri_total, urgent_mri_bypassed
        )
        flow_metrics = cls.calculate_patient_flow_metrics(patients)
        kpis = cls.calculate_performance_indicators(
            wait_stats, utilization, queue_stats, urgent_stats
        )
        
        return {  # type: ignore
            'wait_statistics': wait_stats,
            'utilization': utilization,
            'queue_array': queue_arr,
            'queue_statistics': queue_stats,
            'urgent_care_metrics': urgent_stats,
            'patient_flow_metrics': flow_metrics,
            'key_performance_indicators': kpis
        }