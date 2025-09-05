from typing import Dict
from ..entities.sub_entities.simulation_state import SimulationState

class MetricsService:
    def __init__(self, simulation_state: SimulationState):
        self.simulation_state = simulation_state
    
    def get_average_wait_time(self) -> float:
        """Calculate average wait time"""
        if self.simulation_state.total_completed > 0:
            return self.simulation_state.total_wait_time / self.simulation_state.total_completed
        return 0.0
    
    def get_average_treatment_time(self) -> float:
        """Calculate average treatment time"""
        if self.simulation_state.total_completed > 0:
            return self.simulation_state.total_treatment_time / self.simulation_state.total_completed
        return 0.0
    
    def calculate_nhs_metrics(self) -> Dict:
        """Calculate NHS-specific performance metrics based on simulation data"""
        metrics = {}
        
        # Core NHS Emergency Department Metrics
        
        # 1. 4-Hour Target Performance (NHS England standard: 95% within 4 hours)
        if self.simulation_state.total_completed > 0:
            patients_within_4_hours = sum(1 for patient in self.simulation_state.completed_patients 
                                        if (patient.wait_time + patient.treatment_time) <= 240)  # 4 hours = 240 minutes
            metrics['four_hour_target_compliance'] = (patients_within_4_hours / self.simulation_state.total_completed) * 100
            metrics['four_hour_breaches'] = self.simulation_state.total_completed - patients_within_4_hours
            metrics['four_hour_breach_rate'] = ((self.simulation_state.total_completed - patients_within_4_hours) / self.simulation_state.total_completed) * 100
        else:
            metrics['four_hour_target_compliance'] = 0.0
            metrics['four_hour_breaches'] = 0
            metrics['four_hour_breach_rate'] = 0.0
        
        # 2. Manchester Triage System (MTS) Time Target Compliance
        mts_compliance = self.calculate_mts_time_target_compliance()
        metrics.update(mts_compliance)
        
        # 3. Patient Flow and Throughput Metrics
        metrics['total_ed_attendances'] = self.simulation_state.total_arrivals
        metrics['patients_currently_in_ed'] = self.simulation_state.patients_in_system
        metrics['ed_occupancy_rate'] = (self.simulation_state.patients_in_system / max(1, self.simulation_state.total_arrivals)) * 100 if self.simulation_state.total_arrivals > 0 else 0.0
        
        # 4. Time-based Performance Indicators
        metrics['average_door_to_doctor_time'] = self.get_average_wait_time()  # Time from arrival to first physician contact
        metrics['average_ed_length_of_stay'] = self.get_average_wait_time() + self.get_average_treatment_time()
        metrics['median_wait_time'] = self._calculate_median_wait_time()
        
        # 5. Resource Utilization Metrics
        metrics['doctor_utilization_percentage'] = self.simulation_state.doctor_utilization * 100
        metrics['mri_utilization_percentage'] = self.simulation_state.mri_utilization * 100
        metrics['blood_nurse_utilization_percentage'] = self.simulation_state.blood_nurse_utilization * 100
        metrics['bed_utilization_percentage'] = self.simulation_state.bed_utilization * 100
        metrics['triage_utilization_percentage'] = self.simulation_state.triage_utilization * 100
        
        # Resource counts
        metrics['busy_doctors_count'] = len(self.simulation_state.busy_doctors)
        metrics['available_doctors_count'] = len(self.simulation_state.available_doctors)
        metrics['busy_mri_machines_count'] = len(self.simulation_state.busy_mri_machines)
        metrics['available_mri_machines_count'] = len(self.simulation_state.available_mri_machines)
        metrics['busy_blood_nurses_count'] = len(self.simulation_state.busy_blood_nurses)
        metrics['available_blood_nurses_count'] = len(self.simulation_state.available_blood_nurses)
        metrics['busy_beds_count'] = len(self.simulation_state.busy_beds)
        metrics['available_beds_count'] = len(self.simulation_state.available_beds)
        
        # Overall resource efficiency
        total_resources = (len(self.simulation_state.busy_doctors) + len(self.simulation_state.available_doctors) +
                          len(self.simulation_state.busy_mri_machines) + len(self.simulation_state.available_mri_machines) +
                          len(self.simulation_state.busy_blood_nurses) + len(self.simulation_state.available_blood_nurses) +
                          len(self.simulation_state.busy_beds) + len(self.simulation_state.available_beds))
        busy_resources = (len(self.simulation_state.busy_doctors) + len(self.simulation_state.busy_mri_machines) +
                         len(self.simulation_state.busy_blood_nurses) + len(self.simulation_state.busy_beds))
        metrics['overall_resource_utilization_percentage'] = (busy_resources / max(1, total_resources)) * 100
        
        # 6. Quality and Safety Indicators
        metrics['preemption_events_count'] = self.simulation_state.preemptions_count
        if self.simulation_state.total_arrivals > 0:
            metrics['preemption_rate_per_100_patients'] = (self.simulation_state.preemptions_count / self.simulation_state.total_arrivals) * 100
        else:
            metrics['preemption_rate_per_100_patients'] = 0.0
        
        # 7. Queue Performance by Priority
        queue_metrics = {}
        for priority, length in self.simulation_state.queue_lengths.items():
            queue_metrics[f'{priority.name.lower()}_queue_length'] = length
        metrics.update(queue_metrics)
        
        # 8. Conversion and Admission Metrics
        if self.simulation_state.total_arrivals > 0:
            metrics['ed_conversion_rate'] = (self.simulation_state.total_completed / self.simulation_state.total_arrivals) * 100  # Percentage of patients who complete treatment
            metrics['patients_still_waiting'] = self.simulation_state.total_arrivals - self.simulation_state.total_completed
        else:
            metrics['ed_conversion_rate'] = 0.0
            metrics['patients_still_waiting'] = 0
        
        # 9. Time-based Targets Summary
        metrics['simulation_duration_minutes'] = self.simulation_state.simulation_duration
        metrics['current_simulation_time'] = self.simulation_state.current_time
        metrics['simulation_progress_percentage'] = (self.simulation_state.current_time / self.simulation_state.simulation_duration) * 100 if self.simulation_state.simulation_duration > 0 else 0.0
        
        return metrics
    
    def calculate_mts_time_target_compliance(self) -> Dict:
        """Calculate Manchester Triage System time target compliance by priority"""
        # Official Manchester Triage System target times (in minutes)
        mts_targets = {
            'RED': 0,      # Immediate - seen immediately
            'ORANGE': 10,  # Very urgent - within 10 minutes
            'YELLOW': 60,  # Urgent - within 60 minutes (1 hour)
            'GREEN': 120,  # Standard - within 120 minutes (2 hours)
            'BLUE': 240    # Non-urgent - within 240 minutes (4 hours)
        }
        
        mts_compliance = {}
        overall_stats = {
            'total_patients_assessed': 0,
            'total_compliant_patients': 0,
            'overall_mts_compliance': 0.0
        }
        
        for priority, target_time in mts_targets.items():
            # Get all patients with this priority
            priority_patients = [p for p in self.simulation_state.completed_patients 
                               if p.priority and p.priority.name == priority]
            
            if priority_patients:
                # Calculate compliance for this priority
                compliant_patients = sum(1 for p in priority_patients 
                                       if p.wait_time <= target_time)
                total_patients = len(priority_patients)
                compliance_rate = (compliant_patients / total_patients) * 100
                
                # Store detailed metrics for this priority
                mts_compliance[f'{priority.lower()}_mts_compliance'] = compliance_rate
                mts_compliance[f'{priority.lower()}_mts_breaches'] = total_patients - compliant_patients
                mts_compliance[f'{priority.lower()}_total_patients'] = total_patients
                mts_compliance[f'{priority.lower()}_compliant_patients'] = compliant_patients
                mts_compliance[f'{priority.lower()}_target_time'] = target_time
                
                # Add to overall statistics
                overall_stats['total_patients_assessed'] += total_patients
                overall_stats['total_compliant_patients'] += compliant_patients
                
                # Calculate average wait time for this priority
                if priority_patients:
                    avg_wait_time = sum(p.wait_time for p in priority_patients) / len(priority_patients)
                    mts_compliance[f'{priority.lower()}_avg_wait_time'] = avg_wait_time
                else:
                    mts_compliance[f'{priority.lower()}_avg_wait_time'] = 0.0
            else:
                # No patients with this priority
                mts_compliance[f'{priority.lower()}_mts_compliance'] = 0.0
                mts_compliance[f'{priority.lower()}_mts_breaches'] = 0
                mts_compliance[f'{priority.lower()}_total_patients'] = 0
                mts_compliance[f'{priority.lower()}_compliant_patients'] = 0
                mts_compliance[f'{priority.lower()}_target_time'] = target_time
                mts_compliance[f'{priority.lower()}_avg_wait_time'] = 0.0
        
        # Calculate overall MTS compliance
        if overall_stats['total_patients_assessed'] > 0:
            overall_stats['overall_mts_compliance'] = (
                overall_stats['total_compliant_patients'] / 
                overall_stats['total_patients_assessed']
            ) * 100
        
        # Add overall statistics to the result
        mts_compliance.update(overall_stats)
        
        return mts_compliance
    
    def get_mts_compliance_summary(self) -> Dict:
        """Get a summary of MTS compliance for reporting"""
        compliance_data = self.calculate_mts_time_target_compliance()
        
        summary = {
            'priorities': {},
            'overall_compliance': compliance_data.get('overall_mts_compliance', 0.0),
            'total_patients': compliance_data.get('total_patients_assessed', 0),
            'total_compliant': compliance_data.get('total_compliant_patients', 0)
        }
        
        priorities = ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE']
        for priority in priorities:
            key = priority.lower()
            summary['priorities'][priority] = {
                'compliance_rate': compliance_data.get(f'{key}_mts_compliance', 0.0),
                'target_time': compliance_data.get(f'{key}_target_time', 0),
                'total_patients': compliance_data.get(f'{key}_total_patients', 0),
                'compliant_patients': compliance_data.get(f'{key}_compliant_patients', 0),
                'breaches': compliance_data.get(f'{key}_mts_breaches', 0),
                'avg_wait_time': compliance_data.get(f'{key}_avg_wait_time', 0.0)
            }
        
        return summary
    
    def _calculate_median_wait_time(self) -> float:
        """Calculate median wait time for completed patients"""
        if not self.simulation_state.completed_patients:
            return 0.0
        
        wait_times = [patient.wait_time for patient in self.simulation_state.completed_patients]
        wait_times.sort()
        n = len(wait_times)
        
        if n % 2 == 0:
            return (wait_times[n//2 - 1] + wait_times[n//2]) / 2
        else:
            return wait_times[n//2]
    
    def calculate_wait_times_by_priority(self) -> Dict[str, float]:
        """Calculate current average wait times by priority"""
        from ..enums.Triage import Priority
        wait_times_by_priority = {}
        
        for priority in Priority:
            priority_name = priority.name
            priority_patients = [p for p in self.simulation_state.completed_patients 
                               if p.priority and p.priority == priority]
            
            if priority_patients:
                avg_wait_time = sum(p.wait_time for p in priority_patients) / len(priority_patients)
                wait_times_by_priority[f'{priority_name.lower()}_wait_time'] = avg_wait_time
            else:
                wait_times_by_priority[f'{priority_name.lower()}_wait_time'] = 0.0
                
        return wait_times_by_priority
    
    def calculate_treatment_times_by_priority(self) -> Dict[str, float]:
        """Calculate current average treatment times by priority"""
        from ..enums.Triage import Priority
        treatment_times_by_priority = {}
        
        for priority in Priority:
            priority_name = priority.name
            priority_patients = [p for p in self.simulation_state.completed_patients 
                               if p.priority and p.priority == priority]
            
            if priority_patients:
                avg_treatment_time = sum(p.treatment_time for p in priority_patients) / len(priority_patients)
                treatment_times_by_priority[f'{priority_name.lower()}_treatment_time'] = avg_treatment_time
            else:
                treatment_times_by_priority[f'{priority_name.lower()}_treatment_time'] = 0.0
                
        return treatment_times_by_priority