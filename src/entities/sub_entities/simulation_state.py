import attr
import os
from typing import Dict, List, Optional
from ..patient import Patient
from ..doctor import Doctor
from ...enums.Triage import Priority

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

@attr.s(auto_attribs=True)
class SimulationState:
    """Centralized simulation state management using attrs"""
    
    # Time tracking
    current_time: float = 0.0
    simulation_duration: float = 480.0
    
    # Patient tracking
    total_arrivals: int = 0
    total_completed: int = 0
    patients_in_system: int = 0
    active_patients: List[Patient] = attr.ib(factory=list)
    completed_patients: List[Patient] = attr.ib(factory=list)
    
    # Queue state
    queue_lengths: Dict[Priority, int] = attr.ib(factory=lambda: {
        Priority.RED: 0,
        Priority.ORANGE: 0, 
        Priority.YELLOW: 0,
        Priority.GREEN: 0,
        Priority.BLUE: 0
    })
    
    # Doctor state
    busy_doctors: List[int] = attr.ib(factory=list)
    available_doctors: List[int] = attr.ib(factory=list)
    doctor_patient_assignments: Dict[int, Optional[int]] = attr.ib(factory=dict)
    
    # MRI machine state
    busy_mri_machines: List[int] = attr.ib(factory=list)
    available_mri_machines: List[int] = attr.ib(factory=list)
    mri_patient_assignments: Dict[int, Optional[int]] = attr.ib(factory=dict)
    
    # Blood test nurse state
    busy_blood_nurses: List[int] = attr.ib(factory=list)
    available_blood_nurses: List[int] = attr.ib(factory=list)
    blood_nurse_patient_assignments: Dict[int, Optional[int]] = attr.ib(factory=dict)
    
    # Bed state
    busy_beds: List[int] = attr.ib(factory=list)
    available_beds: List[int] = attr.ib(factory=list)
    bed_patient_assignments: Dict[int, Optional[int]] = attr.ib(factory=dict)
    
    # Resource utilization
    triage_utilization: float = 0.0
    doctor_utilization: float = 0.0
    mri_utilization: float = 0.0
    blood_nurse_utilization: float = 0.0
    bed_utilization: float = 0.0
    
    # Statistics
    total_wait_time: float = 0.0
    total_treatment_time: float = 0.0
    preemptions_count: int = 0
    
    # History tracking
    state_history: List[Dict] = attr.ib(factory=list)
    
    def __attrs_post_init__(self):
        """Initialize metrics service after attrs initialization"""
        from ...services.metrics import MetricsService
        self.metrics_service = MetricsService(self)
    
    def record_history(self) -> None:
        """Record current simulation state in history before any updates"""
        snapshot = self.get_log_summary().copy()
        snapshot['recorded_at'] = self.current_time
        self.state_history.append(snapshot)
    
    def update_time(self, new_time: float) -> None:
        """Update simulation time"""
        self.record_history()  # Record state before update
        self.current_time = new_time
    
    def register_patient_arrival(self, patient: Patient) -> None:
        """Register a new patient arrival"""
        self.record_history()  # Record state before update
        self.total_arrivals += 1
        self.patients_in_system += 1
        self.active_patients.append(patient)
    
    def register_patient_completion(self, patient: Patient) -> None:
        """Register patient completion"""
        self.record_history()  # Record state before update
        self.total_completed += 1
        self.patients_in_system -= 1
        if patient in self.active_patients:
            self.active_patients.remove(patient)
        self.completed_patients.append(patient)
        
        # Update statistics (Patient is attr-based, these attributes are always present)
        self.total_wait_time += patient.wait_time
        self.total_treatment_time += patient.treatment_time
    
    def update_queue_length(self, priority: Priority, length: int) -> None:
        """Update queue length for a specific priority"""
        self.queue_lengths[priority] = length
    
    def update_all_queue_lengths(self, queue_lengths: Dict[Priority, int]) -> None:
        """Update all queue lengths at once"""
        for priority, length in queue_lengths.items():
            self.queue_lengths[priority] = length
    
    def assign_doctor_to_patient(self, doctor_id: int, patient_id: int) -> None:
        """Assign doctor to patient"""
        self.record_history()  # Record state before update
        if doctor_id in self.available_doctors:
            self.available_doctors.remove(doctor_id)
        if doctor_id not in self.busy_doctors:
            self.busy_doctors.append(doctor_id)
        self.doctor_patient_assignments[doctor_id] = patient_id
    
    def release_doctor(self, doctor_id: int) -> None:
        """Release doctor from patient assignment"""
        self.record_history()  # Record state before update
        if doctor_id in self.busy_doctors:
            self.busy_doctors.remove(doctor_id)
        if doctor_id not in self.available_doctors:
            self.available_doctors.append(doctor_id)
        self.doctor_patient_assignments[doctor_id] = None
    
    def assign_mri_to_patient(self, mri_id: int, patient_id: int) -> None:
        """Assign MRI machine to patient"""
        self.record_history()  # Record state before update
        if mri_id in self.available_mri_machines:
            self.available_mri_machines.remove(mri_id)
        if mri_id not in self.busy_mri_machines:
            self.busy_mri_machines.append(mri_id)
        self.mri_patient_assignments[mri_id] = patient_id
    
    def release_mri(self, mri_id: int) -> None:
        """Release MRI machine from patient assignment"""
        self.record_history()  # Record state before update
        if mri_id in self.busy_mri_machines:
            self.busy_mri_machines.remove(mri_id)
        if mri_id not in self.available_mri_machines:
            self.available_mri_machines.append(mri_id)
        self.mri_patient_assignments[mri_id] = None
    
    def assign_blood_nurse_to_patient(self, nurse_id: int, patient_id: int) -> None:
        """Assign blood test nurse to patient"""
        self.record_history()  # Record state before update
        if nurse_id in self.available_blood_nurses:
            self.available_blood_nurses.remove(nurse_id)
        if nurse_id not in self.busy_blood_nurses:
            self.busy_blood_nurses.append(nurse_id)
        self.blood_nurse_patient_assignments[nurse_id] = patient_id
    
    def release_blood_nurse(self, nurse_id: int) -> None:
        """Release blood test nurse from patient assignment"""
        self.record_history()  # Record state before update
        if nurse_id in self.busy_blood_nurses:
            self.busy_blood_nurses.remove(nurse_id)
        if nurse_id not in self.available_blood_nurses:
            self.available_blood_nurses.append(nurse_id)
        self.blood_nurse_patient_assignments[nurse_id] = None
    
    def assign_bed_to_patient(self, bed_id: int, patient_id: int) -> None:
        """Assign bed to patient"""
        self.record_history()  # Record state before update
        if bed_id in self.available_beds:
            self.available_beds.remove(bed_id)
        if bed_id not in self.busy_beds:
            self.busy_beds.append(bed_id)
        self.bed_patient_assignments[bed_id] = patient_id
    
    def release_bed(self, bed_id: int) -> None:
        """Release bed from patient assignment"""
        self.record_history()  # Record state before update
        if bed_id in self.busy_beds:
            self.busy_beds.remove(bed_id)
        if bed_id not in self.available_beds:
            self.available_beds.append(bed_id)
        self.bed_patient_assignments[bed_id] = None
    
    def record_preemption(self) -> None:
        """Record a preemption event"""
        self.record_history()  # Record state before update
        self.preemptions_count += 1
    
    def update_resource_utilization(self, triage_util: float, doctor_util: float, 
                                   mri_util: float = 0.0, blood_nurse_util: float = 0.0, 
                                   bed_util: float = 0.0) -> None:
        """Update resource utilization metrics"""
        self.triage_utilization = triage_util
        self.doctor_utilization = doctor_util
        self.mri_utilization = mri_util
        self.blood_nurse_utilization = blood_nurse_util
        self.bed_utilization = bed_util
    

    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        return {
            'current_time': self.current_time,
            'total_arrivals': self.total_arrivals,
            'total_completed': self.total_completed,
            'patients_in_system': self.patients_in_system,
            'queue_lengths': dict(self.queue_lengths),
            'busy_doctors': len(self.busy_doctors),
            'available_doctors': len(self.available_doctors),
            'busy_mri_machines': len(self.busy_mri_machines),
            'available_mri_machines': len(self.available_mri_machines),
            'busy_blood_nurses': len(self.busy_blood_nurses),
            'available_blood_nurses': len(self.available_blood_nurses),
            'busy_beds': len(self.busy_beds),
            'available_beds': len(self.available_beds),
            'triage_utilization': self.triage_utilization,
            'doctor_utilization': self.doctor_utilization,
            'mri_utilization': self.mri_utilization,
            'blood_nurse_utilization': self.blood_nurse_utilization,
            'bed_utilization': self.bed_utilization,
            'average_wait_time': self.metrics_service.get_average_wait_time(),
            'average_treatment_time': self.metrics_service.get_average_treatment_time(),
            'preemptions_count': self.preemptions_count
        }
    
    def get_log_summary(self) -> Dict:
        """Get compact simulation state summary for logging"""
        return {
            "simulation_time": self.current_time,
            "total_arrivals": self.total_arrivals,
            "total_completed": self.total_completed,
            "patients_in_system": self.patients_in_system,
            "busy_doctors": len(self.busy_doctors),
            "available_doctors": len(self.available_doctors),
            "busy_mri_machines": len(self.busy_mri_machines),
            "available_mri_machines": len(self.available_mri_machines),
            "busy_blood_nurses": len(self.busy_blood_nurses),
            "available_blood_nurses": len(self.available_blood_nurses),
            "busy_beds": len(self.busy_beds),
            "available_beds": len(self.available_beds),
            "preemptions_count": self.preemptions_count,
            "queue_lengths": {priority.name: length for priority, length in self.queue_lengths.items()}
        }
    
    def get_state_history(self) -> List[Dict]:
        """Get the complete state history"""
        return self.state_history.copy()
    

    

    
    def _plot_mts_analysis(self, nhs_metrics: Dict, output_dir: str) -> str:
        """Generate MTS compliance analysis chart"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle('Manchester Triage System Performance Analysis', fontsize=16, fontweight='bold')
        
        # Get MTS data
        mts_data = self._get_mts_chart_data(nhs_metrics)
        
        # Plot compliance chart
        self._plot_mts_compliance_chart(ax1, mts_data)
        
        # Plot queue status chart
        self._plot_mts_queue_status_chart(ax2, mts_data)
        
        # Save chart
        plt.tight_layout()
        mts_file = os.path.join(output_dir, 'mts_compliance_analysis.png')
        plt.savefig(mts_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return mts_file
    
    def _get_mts_chart_data(self, nhs_metrics: Dict) -> Dict:
        """Prepare MTS chart data"""
        mts_priorities = ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE']
        mts_targets = [0, 10, 60, 120, 240]  # Official MTS target times in minutes
        priority_colors = ['red', 'orange', 'yellow', 'green', 'blue']
        
        # Get compliance rates
        compliance_rates = [nhs_metrics.get(f'{p.lower()}_mts_compliance', 0) for p in mts_priorities]
        
        # Get current queue lengths
        current_queue_lengths = []
        for priority_name in mts_priorities:
            try:
                priority_enum = Priority[priority_name]
                queue_length = self.queue_lengths.get(priority_enum, 0)
                current_queue_lengths.append(queue_length)
            except KeyError:
                current_queue_lengths.append(0)
        
        return {
            'priorities': mts_priorities,
            'targets': mts_targets,
            'colors': priority_colors,
            'compliance_rates': compliance_rates,
            'queue_lengths': current_queue_lengths
        }
    
    def _plot_mts_compliance_chart(self, ax, mts_data: Dict) -> None:
        """Plot MTS compliance by priority chart"""
        priorities = mts_data['priorities']
        compliance_rates = mts_data['compliance_rates']
        colors = mts_data['colors']
        
        # Create bars
        bars = ax.bar(priorities, compliance_rates, color=colors, alpha=0.7)
        
        # Add target line
        ax.axhline(y=95, color='black', linestyle='--', label='95% Target')
        
        # Configure chart
        ax.set_ylabel('Compliance Rate (%)')
        ax.set_title('MTS Time Target Compliance by Priority')
        ax.set_ylim(0, 100)
        ax.legend()
        
        # Add data labels or no data message
        if any(rate > 0 for rate in compliance_rates):
            for bar, rate in zip(bars, compliance_rates):
                if rate > 0:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                            f'{rate:.1f}%', ha='center', fontweight='bold')
        else:
            ax.text(0.5, 0.5, 'No completed patients\nfor compliance calculation', 
                    transform=ax.transAxes, ha='center', va='center', 
                    fontsize=12, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    def _plot_mts_queue_status_chart(self, ax, mts_data: Dict) -> None:
        """Plot MTS target times vs actual wait times chart"""
        priorities = mts_data['priorities']
        targets = mts_data['targets']
        colors = mts_data['colors']
        
        # Create labels with target times
        labels = [f'{p}\n({t}min)' for p, t in zip(priorities, targets)]
        
        # Plot target times (gray bars)
        ax.bar(labels, targets, alpha=0.5, color='gray', label='MTS Target Times')
        
        # Calculate actual wait times by priority from completed patients
        actual_wait_times = self._calculate_actual_wait_times_by_priority(priorities)
        
        # Plot actual wait times if any patients completed
        if any(wait_time > 0 for wait_time in actual_wait_times):
            bars2 = ax.bar(labels, actual_wait_times, alpha=0.7, 
                          color=colors, label='Actual Average Wait Times', width=0.6)
            
            # Add wait time labels
            for bar, wait_time in zip(bars2, actual_wait_times):
                if wait_time > 0:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                           f'{wait_time:.1f}min', ha='center', fontweight='bold', color='navy')
        else:
            # Show message when no completed patients
            ax.text(0.5, 0.5, 'No completed patients\nfor wait time analysis', 
                   transform=ax.transAxes, ha='center', va='center', 
                   fontsize=12, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # Configure main axis
        ax.set_ylabel('Time (minutes)')
        ax.set_title('MTS Target Times vs Actual Wait Times')
        ax.legend(loc='upper left')
    
    def _calculate_actual_wait_times_by_priority(self, priorities: List[str]) -> List[float]:
        """Calculate average wait times by priority from completed patients"""
        wait_times_by_priority = {}
        
        # Group completed patients by priority and calculate average wait times
        for priority_name in priorities:
            priority_patients = [p for p in self.completed_patients 
                               if p.priority and p.priority.name == priority_name]
            
            if priority_patients:
                avg_wait_time = sum(p.wait_time for p in priority_patients) / len(priority_patients)
                wait_times_by_priority[priority_name] = avg_wait_time
            else:
                wait_times_by_priority[priority_name] = 0.0
        
        return [wait_times_by_priority[priority] for priority in priorities]
    
    def _calculate_median_wait_time(self) -> float:
        """Calculate median wait time for completed patients"""
        if not self.completed_patients:
            return 0.0
        
        wait_times = [patient.wait_time for patient in self.completed_patients]
        wait_times.sort()
        n = len(wait_times)
        
        if n % 2 == 0:
            return (wait_times[n//2 - 1] + wait_times[n//2]) / 2
        else:
            return wait_times[n//2]
    
    def plot_results(self, system_name: str = "default", base_output_dir: str = "output") -> Dict[str, str]:
        """Generate comprehensive plots of simulation results and save to system-specific output directory"""
        # Create system-specific output directory
        output_dir = os.path.join(base_output_dir, system_name)
        os.makedirs(output_dir, exist_ok=True)
        
        plot_files = {}
        
        # Set up the plotting style
        plt.style.use('default')
        fig_size = (12, 8)
        
        # 1. NHS Performance Dashboard
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('NHS Emergency Department Performance Dashboard', fontsize=16, fontweight='bold')
        
        # Calculate NHS metrics
        nhs_metrics = self.metrics_service.calculate_nhs_metrics()
        
        # 4-Hour Target Compliance
        compliance = nhs_metrics['four_hour_target_compliance']
        target = 95.0  # NHS target
        ax1.bar(['Current Performance', 'NHS Target'], [compliance, target], 
               color=['red' if compliance < target else 'green', 'blue'], alpha=0.7)
        ax1.set_ylabel('Compliance (%)')
        ax1.set_title('4-Hour Target Compliance')
        ax1.set_ylim(0, 100)
        for i, v in enumerate([compliance, target]):
            ax1.text(i, v + 2, f'{v:.1f}%', ha='center', fontweight='bold')
        
        # Queue Lengths by Priority
        priorities = ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE']
        queue_lengths = [self.queue_lengths[Priority[p]] for p in priorities]
        colors = ['red', 'orange', 'yellow', 'green', 'blue']
        bars = ax2.bar(priorities, queue_lengths, color=colors, alpha=0.7)
        ax2.set_ylabel('Queue Length')
        ax2.set_title('Current Queue Lengths by Priority')
        for bar, length in zip(bars, queue_lengths):
            if length > 0:
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                        str(length), ha='center', fontweight='bold')
        
        # Resource Utilization
        utilization_data = {
            'Busy Doctors': max(1, len(self.busy_doctors)),
            'Available Doctors': max(1, len(self.available_doctors)),
            'Busy MRI Machines': max(1, len(self.busy_mri_machines)),
            'Available MRI Machines': max(1, len(self.available_mri_machines)),
            'Busy Blood Nurses': max(1, len(self.busy_blood_nurses)),
            'Available Blood Nurses': max(1, len(self.available_blood_nurses)),
            'Busy Beds': max(1, len(self.busy_beds)),
            'Available Beds': max(1, len(self.available_beds))
        }
        # Only create pie chart if we have meaningful data
        if sum(utilization_data.values()) > 0:
            colors = ['#ff4444', '#44ff44', '#4444ff', '#44ffff', '#ff44ff', '#ffff44', '#ff8844', '#88ff44']
            wedges, texts, autotexts = ax3.pie(utilization_data.values(), labels=utilization_data.keys(), 
                                              autopct='%1.1f%%', colors=colors[:len(utilization_data)], 
                                              startangle=90, textprops={'fontsize': 8})
            # Add legend with better positioning
            ax3.legend(wedges, utilization_data.keys(), title="Resources", 
                      loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), fontsize=8)
        else:
            ax3.text(0.5, 0.5, 'No Data Available', ha='center', va='center', transform=ax3.transAxes)
        ax3.set_title('Resource Utilization')
        
        # Performance Metrics Summary
        metrics_text = f"""Simulation Summary:
• Total Arrivals: {self.total_arrivals}
• Completed Treatments: {self.total_completed}
• Average Wait Time: {self.metrics_service.get_average_wait_time():.1f} min
• Average Treatment Time: {self.metrics_service.get_average_treatment_time():.1f} min
• Preemption Events: {self.preemptions_count}
• ED Conversion Rate: {nhs_metrics['ed_conversion_rate']:.1f}%
• Simulation Duration: {self.current_time:.1f} / {self.simulation_duration} min"""
        ax4.text(0.05, 0.95, metrics_text, transform=ax4.transAxes, fontsize=11,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        ax4.set_xlim(0, 1)
        ax4.set_ylim(0, 1)
        ax4.axis('off')
        ax4.set_title('Key Performance Indicators')
        
        plt.tight_layout()
        dashboard_file = os.path.join(output_dir, 'nhs_performance_dashboard.png')
        plt.savefig(dashboard_file, dpi=300, bbox_inches='tight')
        plt.close()
        plot_files['dashboard'] = dashboard_file
        
        # 2. State History Timeline (if available)
        if self.state_history:
            fig, ((ax1, ax2), (ax3, ax4), (ax5, ax6), (ax7, ax8)) = plt.subplots(4, 2, figsize=(20, 20))
            fig.suptitle('Simulation State History Timeline', fontsize=16, fontweight='bold')
            
            times = [entry['recorded_at'] for entry in self.state_history]
            arrivals = [entry['total_arrivals'] for entry in self.state_history]
            completed = [entry['total_completed'] for entry in self.state_history]
            in_system = [entry['patients_in_system'] for entry in self.state_history]
            preemptions = [entry['preemptions_count'] for entry in self.state_history]
            
            # Patient Flow Over Time
            ax1.plot(times, arrivals, 'b-', label='Total Arrivals', linewidth=2)
            ax1.plot(times, completed, 'g-', label='Completed', linewidth=2)
            ax1.plot(times, in_system, 'r-', label='In System', linewidth=2)
            ax1.set_ylabel('Patient Count')
            ax1.set_title('Patient Flow Over Time')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Doctor Utilization Over Time
            busy_doctors = [entry['busy_doctors'] for entry in self.state_history]
            available_doctors = [entry['available_doctors'] for entry in self.state_history]
            total_doctors = [b+a for b,a in zip(busy_doctors, available_doctors)]
            ax2.fill_between(times, busy_doctors, alpha=0.6, color='#ff4444', label='Busy Doctors')
            ax2.fill_between(times, busy_doctors, total_doctors, 
                           alpha=0.6, color='#44ff44', label='Available Doctors')
            ax2.set_ylabel('Doctor Count')
            ax2.set_title('Doctor Utilization Over Time')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            # MRI Machine Utilization Over Time
            busy_mri = [entry['busy_mri_machines'] for entry in self.state_history]
            available_mri = [entry['available_mri_machines'] for entry in self.state_history]
            total_mri = [b+a for b,a in zip(busy_mri, available_mri)]
            ax3.fill_between(times, busy_mri, alpha=0.6, color='#4444ff', label='Busy MRI Machines')
            ax3.fill_between(times, busy_mri, total_mri, 
                           alpha=0.6, color='#44ffff', label='Available MRI Machines')
            ax3.set_ylabel('MRI Machine Count')
            ax3.set_title('MRI Machine Utilization Over Time')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            
            # Blood Nurse Utilization Over Time
            busy_nurses = [entry['busy_blood_nurses'] for entry in self.state_history]
            available_nurses = [entry['available_blood_nurses'] for entry in self.state_history]
            total_nurses = [b+a for b,a in zip(busy_nurses, available_nurses)]
            ax4.fill_between(times, busy_nurses, alpha=0.6, color='#ff44ff', label='Busy Blood Nurses')
            ax4.fill_between(times, busy_nurses, total_nurses, 
                           alpha=0.6, color='#ffff44', label='Available Blood Nurses')
            ax4.set_ylabel('Blood Nurse Count')
            ax4.set_title('Blood Nurse Utilization Over Time')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
            
            # Bed Utilization Over Time
            busy_beds = [entry['busy_beds'] for entry in self.state_history]
            available_beds = [entry['available_beds'] for entry in self.state_history]
            total_beds = [b+a for b,a in zip(busy_beds, available_beds)]
            ax5.fill_between(times, busy_beds, alpha=0.6, color='#ff8844', label='Busy Beds')
            ax5.fill_between(times, busy_beds, total_beds, 
                           alpha=0.6, color='#88ff44', label='Available Beds')
            ax5.set_ylabel('Bed Count')
            ax5.set_title('Bed Utilization Over Time')
            ax5.legend()
            ax5.grid(True, alpha=0.3)
            
            # Preemption Events Over Time
            ax6.step(times, preemptions, 'purple', linewidth=2, where='post')
            ax6.fill_between(times, preemptions, alpha=0.3, color='purple', step='post')
            ax6.set_ylabel('Cumulative Preemptions')
            ax6.set_title('Preemption Events Over Time')
            ax6.grid(True, alpha=0.3)
            
            # Actual Arrival Rate from Patient History
            # Calculate instantaneous arrival rate using patient arrival times
            arrival_times = [p.arrival_time for p in self.active_patients + self.completed_patients]
            arrival_times.sort()
            
            # Calculate arrival rate in time windows
            window_size = 30  # 30-minute windows
            time_windows = []
            actual_arrival_rates = []
            
            if arrival_times:
                current_window_start = 0
                max_time = max(times) if times else self.current_time
                
                while current_window_start < max_time:
                    window_end = current_window_start + window_size
                    # Count arrivals in this window
                    arrivals_in_window = sum(1 for t in arrival_times 
                                           if current_window_start <= t < window_end)
                    # Convert to rate per minute
                    rate = arrivals_in_window / window_size if window_size > 0 else 0
                    
                    time_windows.append(current_window_start + window_size/2)  # Center of window
                    actual_arrival_rates.append(rate)
                    current_window_start += window_size
                
                ax7.plot(time_windows, actual_arrival_rates, 'orange', linewidth=2, 
                        label='Actual Arrival Rate', marker='o', markersize=4)
                ax7.fill_between(time_windows, actual_arrival_rates, alpha=0.3, color='orange')
            else:
                ax7.text(0.5, 0.5, 'No patient arrival data available', 
                        transform=ax7.transAxes, ha='center', va='center')
            
            ax7.set_xlabel('Simulation Time (minutes)')
            ax7.set_ylabel('Arrival Rate (patients/min)')
            ax7.set_title('Actual Patient Arrival Rate Over Time')
            ax7.legend()
            ax7.grid(True, alpha=0.3)
            
            # Resource Utilization Summary (ax8)
            # Calculate average utilization percentages for each resource
            if times:
                avg_doctor_util = (sum(busy_doctors) / sum(total_doctors)) * 100 if sum(total_doctors) > 0 else 0
                avg_mri_util = (sum(busy_mri) / sum(total_mri)) * 100 if sum(total_mri) > 0 else 0
                avg_nurse_util = (sum(busy_nurses) / sum(total_nurses)) * 100 if sum(total_nurses) > 0 else 0
                avg_bed_util = (sum(busy_beds) / sum(total_beds)) * 100 if sum(total_beds) > 0 else 0
                
                resources = ['Doctors', 'MRI Machines', 'Blood Nurses', 'Beds']
                utilizations = [avg_doctor_util, avg_mri_util, avg_nurse_util, avg_bed_util]
                colors = ['#ff4444', '#4444ff', '#ff44ff', '#ff8844']
                
                bars = ax8.bar(resources, utilizations, color=colors, alpha=0.7)
                ax8.set_ylabel('Average Utilization (%)')
                ax8.set_title('Average Resource Utilization Summary')
                ax8.set_ylim(0, 100)
                
                # Add value labels on bars
                for bar, util in zip(bars, utilizations):
                    ax8.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                            f'{util:.1f}%', ha='center', fontweight='bold')
            else:
                ax8.text(0.5, 0.5, 'No utilization data available', 
                        transform=ax8.transAxes, ha='center', va='center')
            ax8.grid(True, alpha=0.3)
            
            plt.tight_layout()
            timeline_file = os.path.join(output_dir, 'state_history_timeline.png')
            plt.savefig(timeline_file, dpi=300, bbox_inches='tight')
            plt.close()
            plot_files['timeline'] = timeline_file
        
        # 3. Manchester Triage System Compliance
        mts_file = self._plot_mts_analysis(nhs_metrics, output_dir)
        plot_files['mts_analysis'] = mts_file
        
        # 4. Summary Report
        summary_text = f"""HOSPITAL EMERGENCY DEPARTMENT SIMULATION REPORT
{'='*60}

SIMULATION PARAMETERS:
• Duration: {self.simulation_duration} minutes ({self.simulation_duration/60:.1f} hours)
• Current Time: {self.current_time} minutes
• Progress: {(self.current_time/self.simulation_duration)*100:.1f}%

PATIENT STATISTICS:
• Total Arrivals: {self.total_arrivals}
• Completed Treatments: {self.total_completed}
• Patients in System: {self.patients_in_system}
• Conversion Rate: {nhs_metrics['ed_conversion_rate']:.1f}%

PERFORMANCE METRICS:
• Average Wait Time: {self.metrics_service.get_average_wait_time():.1f} minutes
• Average Treatment Time: {self.metrics_service.get_average_treatment_time():.1f} minutes
• Median Wait Time: {self.metrics_service._calculate_median_wait_time():.1f} minutes

NHS TARGETS:
• 4-Hour Target Compliance: {nhs_metrics['four_hour_target_compliance']:.1f}%
• 4-Hour Breaches: {nhs_metrics['four_hour_breaches']}
• Breach Rate: {nhs_metrics['four_hour_breach_rate']:.1f}%

RESOURCE UTILIZATION:
• Busy Doctors: {len(self.busy_doctors)}
• Available Doctors: {len(self.available_doctors)}
• Doctor Utilization: {nhs_metrics['doctor_utilization_percentage']:.1f}%

QUEUE STATUS:
• RED (Immediate): {self.queue_lengths[Priority.RED]}
• ORANGE (Very Urgent): {self.queue_lengths[Priority.ORANGE]}
• YELLOW (Urgent): {self.queue_lengths[Priority.YELLOW]}
• GREEN (Standard): {self.queue_lengths[Priority.GREEN]}
• BLUE (Non-urgent): {self.queue_lengths[Priority.BLUE]}

PREEMPTION ANALYSIS:
• Total Preemptions: {self.preemptions_count}
• Preemption Rate: {nhs_metrics['preemption_rate_per_100_patients']:.1f} per 100 patients

GENERATED PLOTS:
{chr(10).join([f'• {name.title()}: {path}' for name, path in plot_files.items()])}

Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        report_file = os.path.join(output_dir, 'simulation_report.txt')
        with open(report_file, 'w') as f:
            f.write(summary_text)
        plot_files['report'] = report_file
        
        return plot_files
    
    @staticmethod
    def plot_comparison_charts(simulation_states: Dict[str, 'SimulationState'], 
                              output_dir: str = "output/comparison") -> Dict[str, str]:
        """Generate comprehensive comparison charts for multiple simulation states"""
        os.makedirs(output_dir, exist_ok=True)
        
        if len(simulation_states) < 2:
            raise ValueError("At least 2 simulation states required for comparison")
        
        plot_files = {}
        
        # Generate all comparison charts
        plot_files.update(SimulationState._plot_nhs_metrics_comparison(simulation_states, output_dir))
        plot_files.update(SimulationState._plot_wait_times_comparison(simulation_states, output_dir))
        plot_files.update(SimulationState._plot_mts_compliance_comparison(simulation_states, output_dir))
        plot_files.update(SimulationState._plot_resource_utilization_comparison(simulation_states, output_dir))
        plot_files.update(SimulationState._plot_queue_performance_comparison(simulation_states, output_dir))
        plot_files.update(SimulationState._plot_preemption_analysis_comparison(simulation_states, output_dir))
        
        # Generate summary comparison report
        report_file = SimulationState._generate_comparison_report(simulation_states, output_dir, plot_files)
        plot_files['comparison_report'] = report_file
        
        return plot_files
    
    @staticmethod
    def _plot_nhs_metrics_comparison(simulation_states: Dict[str, 'SimulationState'], 
                                   output_dir: str) -> Dict[str, str]:
        """Plot NHS metrics comparison across simulation states"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('NHS Metrics Comparison Across Triage Systems', fontsize=16, fontweight='bold')
        
        systems = list(simulation_states.keys())
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'][:len(systems)]
        
        # 4-Hour Target Compliance
        compliance_rates = []
        for system_name, state in simulation_states.items():
            nhs_metrics = state.metrics_service.calculate_nhs_metrics()
            compliance_rates.append(nhs_metrics['four_hour_target_compliance'])
        
        bars1 = ax1.bar(systems, compliance_rates, color=colors, alpha=0.7)
        ax1.axhline(y=95, color='red', linestyle='--', label='NHS Target (95%)')
        ax1.set_ylabel('Compliance (%)')
        ax1.set_title('4-Hour Target Compliance')
        ax1.set_ylim(0, 100)
        ax1.legend()
        for bar, rate in zip(bars1, compliance_rates):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                    f'{rate:.1f}%', ha='center', fontweight='bold')
        
        # ED Conversion Rate
        conversion_rates = []
        for system_name, state in simulation_states.items():
            nhs_metrics = state.metrics_service.calculate_nhs_metrics()
            conversion_rates.append(nhs_metrics['ed_conversion_rate'])
        
        bars2 = ax2.bar(systems, conversion_rates, color=colors, alpha=0.7)
        ax2.set_ylabel('Conversion Rate (%)')
        ax2.set_title('ED Conversion Rate (Treatment Completion)')
        ax2.set_ylim(0, 100)
        for bar, rate in zip(bars2, conversion_rates):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                    f'{rate:.1f}%', ha='center', fontweight='bold')
        
        # Doctor Utilization
        doctor_util = []
        for system_name, state in simulation_states.items():
            nhs_metrics = state.metrics_service.calculate_nhs_metrics()
            doctor_util.append(nhs_metrics['doctor_utilization_percentage'])
        
        bars3 = ax3.bar(systems, doctor_util, color=colors, alpha=0.7)
        ax3.set_ylabel('Utilization (%)')
        ax3.set_title('Doctor Utilization')
        ax3.set_ylim(0, 100)
        for bar, util in zip(bars3, doctor_util):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                    f'{util:.1f}%', ha='center', fontweight='bold')
        
        # Preemption Rate
        preemption_rates = []
        for system_name, state in simulation_states.items():
            nhs_metrics = state.metrics_service.calculate_nhs_metrics()
            preemption_rates.append(nhs_metrics['preemption_rate_per_100_patients'])
        
        bars4 = ax4.bar(systems, preemption_rates, color=colors, alpha=0.7)
        ax4.set_ylabel('Preemptions per 100 Patients')
        ax4.set_title('Preemption Rate')
        for bar, rate in zip(bars4, preemption_rates):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    f'{rate:.1f}', ha='center', fontweight='bold')
        
        plt.tight_layout()
        nhs_file = os.path.join(output_dir, 'nhs_metrics_comparison.png')
        plt.savefig(nhs_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return {'nhs_metrics_comparison': nhs_file}
    
    @staticmethod
    def _plot_wait_times_comparison(simulation_states: Dict[str, 'SimulationState'], 
                                  output_dir: str) -> Dict[str, str]:
        """Plot wait times comparison across simulation states"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle('Wait Times Comparison Across Triage Systems', fontsize=16, fontweight='bold')
        
        systems = list(simulation_states.keys())
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'][:len(systems)]
        
        # Average Wait Times
        avg_wait_times = [state.metrics_service.get_average_wait_time() for state in simulation_states.values()]
        median_wait_times = [state.metrics_service._calculate_median_wait_time() for state in simulation_states.values()]
        
        x = range(len(systems))
        width = 0.35
        
        bars1 = ax1.bar([i - width/2 for i in x], avg_wait_times, width, 
                       label='Average Wait Time', color=colors, alpha=0.7)
        bars2 = ax1.bar([i + width/2 for i in x], median_wait_times, width, 
                       label='Median Wait Time', color=colors, alpha=0.5)
        
        ax1.set_ylabel('Time (minutes)')
        ax1.set_title('Average vs Median Wait Times')
        ax1.set_xticks(x)
        ax1.set_xticklabels(systems)
        ax1.legend()
        
        # Add value labels
        for bar, time in zip(bars1, avg_wait_times):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    f'{time:.1f}', ha='center', fontweight='bold')
        for bar, time in zip(bars2, median_wait_times):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    f'{time:.1f}', ha='center', fontweight='bold')
        
        # Average Treatment Times
        avg_treatment_times = [state.metrics_service.get_average_treatment_time() for state in simulation_states.values()]
        total_times = [avg_wait_times[i] + avg_treatment_times[i] for i in range(len(systems))]
        
        bars3 = ax2.bar([i - width/2 for i in x], avg_treatment_times, width, 
                       label='Treatment Time', color=colors, alpha=0.7)
        bars4 = ax2.bar([i + width/2 for i in x], total_times, width, 
                       label='Total Time (Wait + Treatment)', color=colors, alpha=0.5)
        
        ax2.set_ylabel('Time (minutes)')
        ax2.set_title('Treatment Times vs Total Times')
        ax2.set_xticks(x)
        ax2.set_xticklabels(systems)
        ax2.legend()
        
        # Add value labels
        for bar, time in zip(bars3, avg_treatment_times):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    f'{time:.1f}', ha='center', fontweight='bold')
        for bar, time in zip(bars4, total_times):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                    f'{time:.1f}', ha='center', fontweight='bold')
        
        plt.tight_layout()
        wait_times_file = os.path.join(output_dir, 'wait_times_comparison.png')
        plt.savefig(wait_times_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return {'wait_times_comparison': wait_times_file}
    
    @staticmethod
    def _plot_mts_compliance_comparison(simulation_states: Dict[str, 'SimulationState'], 
                                      output_dir: str) -> Dict[str, str]:
        """Plot MTS compliance comparison across simulation states"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle('Manchester Triage System Compliance Comparison', fontsize=16, fontweight='bold')
        
        systems = list(simulation_states.keys())
        priorities = ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE']
        colors = ['red', 'orange', 'yellow', 'green', 'blue']
        
        # Overall MTS Compliance
        overall_compliance = []
        for system_name, state in simulation_states.items():
            mts_data = state.metrics_service.calculate_mts_time_target_compliance()
            overall_compliance.append(mts_data.get('overall_mts_compliance', 0.0))
        
        bars1 = ax1.bar(systems, overall_compliance, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'][:len(systems)], alpha=0.7)
        ax1.axhline(y=95, color='red', linestyle='--', label='95% Target')
        ax1.set_ylabel('Compliance (%)')
        ax1.set_title('Overall MTS Compliance')
        ax1.set_ylim(0, 100)
        ax1.legend()
        for bar, rate in zip(bars1, overall_compliance):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                    f'{rate:.1f}%', ha='center', fontweight='bold')
        
        # Priority-specific compliance (stacked bar)
        priority_data = {priority: [] for priority in priorities}
        for system_name, state in simulation_states.items():
            mts_data = state.metrics_service.calculate_mts_time_target_compliance()
            for priority in priorities:
                compliance = mts_data.get(f'{priority.lower()}_mts_compliance', 0.0)
                priority_data[priority].append(compliance)
        
        x = range(len(systems))
        width = 0.15
        for i, priority in enumerate(priorities):
            bars = ax2.bar([pos + i * width for pos in x], priority_data[priority], 
                          width, label=priority, color=colors[i], alpha=0.7)
        
        ax2.set_ylabel('Compliance (%)')
        ax2.set_title('MTS Compliance by Priority')
        ax2.set_xticks([pos + width * 2 for pos in x])
        ax2.set_xticklabels(systems)
        ax2.legend()
        ax2.set_ylim(0, 100)
        
        plt.tight_layout()
        mts_file = os.path.join(output_dir, 'mts_compliance_comparison.png')
        plt.savefig(mts_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return {'mts_compliance_comparison': mts_file}
    
    @staticmethod
    def _plot_resource_utilization_comparison(simulation_states: Dict[str, 'SimulationState'], 
                                            output_dir: str) -> Dict[str, str]:
        """Plot resource utilization comparison across simulation states"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 12))
        fig.suptitle('Resource Utilization Comparison', fontsize=16, fontweight='bold')
        
        systems = list(simulation_states.keys())
        x = range(len(systems))
        width = 0.35
        
        # Doctor Utilization
        busy_doctors = [len(state.busy_doctors) for state in simulation_states.values()]
        available_doctors = [len(state.available_doctors) for state in simulation_states.values()]
        
        bars1 = ax1.bar([i - width/2 for i in x], busy_doctors, width, 
                       label='Busy Doctors', color='#ff4444', alpha=0.7)
        bars2 = ax1.bar([i + width/2 for i in x], available_doctors, width, 
                       label='Available Doctors', color='#44ff44', alpha=0.7)
        
        ax1.set_ylabel('Number of Doctors')
        ax1.set_title('Doctor Resource Allocation')
        ax1.set_xticks(x)
        ax1.set_xticklabels(systems)
        ax1.legend()
        
        for bar, count in zip(bars1, busy_doctors):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(count), ha='center', fontweight='bold')
        for bar, count in zip(bars2, available_doctors):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(count), ha='center', fontweight='bold')
        
        # MRI Machine Utilization
        busy_mri = [len(state.busy_mri_machines) for state in simulation_states.values()]
        available_mri = [len(state.available_mri_machines) for state in simulation_states.values()]
        
        bars3 = ax2.bar([i - width/2 for i in x], busy_mri, width, 
                       label='Busy MRI Machines', color='#4444ff', alpha=0.7)
        bars4 = ax2.bar([i + width/2 for i in x], available_mri, width, 
                       label='Available MRI Machines', color='#44ffff', alpha=0.7)
        
        ax2.set_ylabel('Number of MRI Machines')
        ax2.set_title('MRI Machine Resource Allocation')
        ax2.set_xticks(x)
        ax2.set_xticklabels(systems)
        ax2.legend()
        
        for bar, count in zip(bars3, busy_mri):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(count), ha='center', fontweight='bold')
        for bar, count in zip(bars4, available_mri):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(count), ha='center', fontweight='bold')
        
        # Blood Nurse Utilization
        busy_nurses = [len(state.busy_blood_nurses) for state in simulation_states.values()]
        available_nurses = [len(state.available_blood_nurses) for state in simulation_states.values()]
        
        bars5 = ax3.bar([i - width/2 for i in x], busy_nurses, width, 
                       label='Busy Blood Nurses', color='#ff44ff', alpha=0.7)
        bars6 = ax3.bar([i + width/2 for i in x], available_nurses, width, 
                       label='Available Blood Nurses', color='#ffff44', alpha=0.7)
        
        ax3.set_ylabel('Number of Blood Nurses')
        ax3.set_title('Blood Nurse Resource Allocation')
        ax3.set_xticks(x)
        ax3.set_xticklabels(systems)
        ax3.legend()
        
        for bar, count in zip(bars5, busy_nurses):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(count), ha='center', fontweight='bold')
        for bar, count in zip(bars6, available_nurses):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(count), ha='center', fontweight='bold')
        
        # Bed Utilization
        busy_beds = [len(state.busy_beds) for state in simulation_states.values()]
        available_beds = [len(state.available_beds) for state in simulation_states.values()]
        
        bars7 = ax4.bar([i - width/2 for i in x], busy_beds, width, 
                       label='Busy Beds', color='#ff8844', alpha=0.7)
        bars8 = ax4.bar([i + width/2 for i in x], available_beds, width, 
                       label='Available Beds', color='#88ff44', alpha=0.7)
        
        ax4.set_ylabel('Number of Beds')
        ax4.set_title('Bed Resource Allocation')
        ax4.set_xticks(x)
        ax4.set_xticklabels(systems)
        ax4.legend()
        
        for bar, count in zip(bars7, busy_beds):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(count), ha='center', fontweight='bold')
        for bar, count in zip(bars8, available_beds):
            ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(count), ha='center', fontweight='bold')
        
        plt.tight_layout()
        resource_file = os.path.join(output_dir, 'resource_utilization_comparison.png')
        plt.savefig(resource_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return {'resource_utilization_comparison': resource_file}
    
    @staticmethod
    def _plot_queue_performance_comparison(simulation_states: Dict[str, 'SimulationState'], 
                                         output_dir: str) -> Dict[str, str]:
        """Plot queue performance comparison across simulation states"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle('Queue Performance Comparison', fontsize=16, fontweight='bold')
        
        systems = list(simulation_states.keys())
        priorities = ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE']
        colors = ['red', 'orange', 'yellow', 'green', 'blue']
        
        # Current Queue Lengths by Priority
        queue_data = {priority: [] for priority in priorities}
        for system_name, state in simulation_states.items():
            for priority in priorities:
                queue_length = state.queue_lengths[Priority[priority]]
                queue_data[priority].append(queue_length)
        
        x = range(len(systems))
        width = 0.15
        for i, priority in enumerate(priorities):
            bars = ax1.bar([pos + i * width for pos in x], queue_data[priority], 
                          width, label=priority, color=colors[i], alpha=0.7)
            # Add value labels for non-zero values
            for bar, length in zip(bars, queue_data[priority]):
                if length > 0:
                    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                            str(length), ha='center', fontweight='bold', fontsize=8)
        
        ax1.set_ylabel('Queue Length')
        ax1.set_title('Current Queue Lengths by Priority')
        ax1.set_xticks([pos + width * 2 for pos in x])
        ax1.set_xticklabels(systems)
        ax1.legend()
        
        # Total Queue Load
        total_queue_lengths = []
        for state in simulation_states.values():
            total = sum(state.queue_lengths.values())
            total_queue_lengths.append(total)
        
        bars2 = ax2.bar(systems, total_queue_lengths, 
                       color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'][:len(systems)], alpha=0.7)
        ax2.set_ylabel('Total Queue Length')
        ax2.set_title('Total Queue Load')
        
        for bar, total in zip(bars2, total_queue_lengths):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2, 
                    str(total), ha='center', fontweight='bold')
        
        plt.tight_layout()
        queue_file = os.path.join(output_dir, 'queue_performance_comparison.png')
        plt.savefig(queue_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return {'queue_performance_comparison': queue_file}
    
    @staticmethod
    def _plot_preemption_analysis_comparison(simulation_states: Dict[str, 'SimulationState'], 
                                           output_dir: str) -> Dict[str, str]:
        """Plot preemption analysis comparison across simulation states"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle('Preemption Analysis Comparison', fontsize=16, fontweight='bold')
        
        systems = list(simulation_states.keys())
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'][:len(systems)]
        
        # Total Preemption Events
        preemption_counts = [state.preemptions_count for state in simulation_states.values()]
        
        bars1 = ax1.bar(systems, preemption_counts, color=colors, alpha=0.7)
        ax1.set_ylabel('Total Preemptions')
        ax1.set_title('Total Preemption Events')
        
        for bar, count in zip(bars1, preemption_counts):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(count), ha='center', fontweight='bold')
        
        # Preemption Rate per 100 Patients
        preemption_rates = []
        for state in simulation_states.values():
            if state.total_arrivals > 0:
                rate = (state.preemptions_count / state.total_arrivals) * 100
            else:
                rate = 0.0
            preemption_rates.append(rate)
        
        bars2 = ax2.bar(systems, preemption_rates, color=colors, alpha=0.7)
        ax2.set_ylabel('Preemptions per 100 Patients')
        ax2.set_title('Preemption Rate')
        
        for bar, rate in zip(bars2, preemption_rates):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, 
                    f'{rate:.1f}', ha='center', fontweight='bold')
        
        plt.tight_layout()
        preemption_file = os.path.join(output_dir, 'preemption_analysis_comparison.png')
        plt.savefig(preemption_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return {'preemption_analysis_comparison': preemption_file}
    
    @staticmethod
    def _generate_comparison_report(simulation_states: Dict[str, 'SimulationState'], 
                                  output_dir: str, plot_files: Dict[str, str]) -> str:
        """Generate comprehensive comparison report"""
        report_content = f"""TRIAGE SYSTEMS COMPARISON REPORT
{'='*60}

Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Systems Compared: {', '.join(simulation_states.keys())}

"""
        
        # Summary table
        report_content += "PERFORMANCE SUMMARY\n" + "-"*30 + "\n"
        report_content += f"{'System':<15} {'Arrivals':<10} {'Completed':<10} {'4Hr Comp%':<10} {'Avg Wait':<10} {'Preemptions':<12}\n"
        report_content += "-"*70 + "\n"
        
        for system_name, state in simulation_states.items():
            nhs_metrics = state.metrics_service.calculate_nhs_metrics()
            report_content += f"{system_name:<15} {state.total_arrivals:<10} {state.total_completed:<10} "
            report_content += f"{nhs_metrics['four_hour_target_compliance']:<10.1f} {state.metrics_service.get_average_wait_time():<10.1f} "
            report_content += f"{state.preemptions_count:<12}\n"
        
        # Detailed analysis for each system
        report_content += "\n\nDETAILED SYSTEM ANALYSIS\n" + "="*40 + "\n"
        
        for system_name, state in simulation_states.items():
            nhs_metrics = state.metrics_service.calculate_nhs_metrics()
            mts_summary = state.metrics_service.get_mts_compliance_summary()
            
            report_content += f"\n{system_name.upper()} SYSTEM:\n" + "-"*25 + "\n"
            report_content += f"• Total Arrivals: {state.total_arrivals}\n"
            report_content += f"• Completed Treatments: {state.total_completed}\n"
            report_content += f"• Patients in System: {state.patients_in_system}\n"
            report_content += f"• 4-Hour Target Compliance: {nhs_metrics['four_hour_target_compliance']:.1f}%\n"
            report_content += f"• ED Conversion Rate: {nhs_metrics['ed_conversion_rate']:.1f}%\n"
            report_content += f"• Average Wait Time: {state.metrics_service.get_average_wait_time():.1f} minutes\n"
            report_content += f"• Average Treatment Time: {state.metrics_service.get_average_treatment_time():.1f} minutes\n"
            report_content += f"• Doctor Utilization: {nhs_metrics['doctor_utilization_percentage']:.1f}%\n"
            report_content += f"• Preemption Events: {state.preemptions_count}\n"
            report_content += f"• Overall MTS Compliance: {mts_summary['overall_compliance']:.1f}%\n"
            
            # Queue status
            report_content += "\nQueue Status:\n"
            for priority in ['RED', 'ORANGE', 'YELLOW', 'GREEN', 'BLUE']:
                length = state.queue_lengths[Priority[priority]]
                report_content += f"  - {priority}: {length}\n"
        
        # Best performing system analysis
        report_content += "\n\nPERFORMANCE RANKING\n" + "="*25 + "\n"
        
        # Rank by 4-hour compliance
        compliance_ranking = sorted(simulation_states.items(), 
                                  key=lambda x: x[1].metrics_service.calculate_nhs_metrics()['four_hour_target_compliance'], 
                                  reverse=True)
        report_content += "\nBy 4-Hour Target Compliance:\n"
        for i, (system_name, state) in enumerate(compliance_ranking, 1):
            compliance = state.metrics_service.calculate_nhs_metrics()['four_hour_target_compliance']
            report_content += f"{i}. {system_name}: {compliance:.1f}%\n"
        
        # Rank by average wait time (lower is better)
        wait_time_ranking = sorted(simulation_states.items(), 
                                 key=lambda x: x[1].metrics_service.get_average_wait_time())
        report_content += "\nBy Average Wait Time (lower is better):\n"
        for i, (system_name, state) in enumerate(wait_time_ranking, 1):
            wait_time = state.metrics_service.get_average_wait_time()
            report_content += f"{i}. {system_name}: {wait_time:.1f} minutes\n"
        
        # Generated files
        report_content += "\n\nGENERATED COMPARISON CHARTS\n" + "="*35 + "\n"
        for chart_name, file_path in plot_files.items():
            if chart_name != 'comparison_report':
                report_content += f"• {chart_name.replace('_', ' ').title()}: {file_path}\n"
        
        # Save report
        report_file = os.path.join(output_dir, 'triage_systems_comparison_report.txt')
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        return report_file
     
    def reset(self) -> None:
        """Reset simulation state"""
        self.current_time = 0.0
        self.total_arrivals = 0
        self.total_completed = 0
        self.patients_in_system = 0
        self.active_patients.clear()
        self.completed_patients.clear()
        
        for priority in self.queue_lengths:
            self.queue_lengths[priority] = 0
            
        self.busy_doctors.clear()
        self.available_doctors.clear()
        self.doctor_patient_assignments.clear()
        
        self.busy_mri_machines.clear()
        self.available_mri_machines.clear()
        self.mri_patient_assignments.clear()
        
        self.busy_blood_nurses.clear()
        self.available_blood_nurses.clear()
        self.blood_nurse_patient_assignments.clear()
        
        self.busy_beds.clear()
        self.available_beds.clear()
        self.bed_patient_assignments.clear()
        
        self.triage_utilization = 0.0
        self.doctor_utilization = 0.0
        self.mri_utilization = 0.0
        self.blood_nurse_utilization = 0.0
        self.bed_utilization = 0.0
        self.total_wait_time = 0.0
        self.total_treatment_time = 0.0
        self.preemptions_count = 0
        
        # Clear state history
        self.state_history.clear()