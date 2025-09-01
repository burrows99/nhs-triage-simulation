import simpy
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
from ..entities.patient import Patient, Priority, PatientStatus
from ..triage.base_triage import BaseTriage
from ..triage.manchester_triage import ManchesterTriage


class EmergencyDepartment:
    """Main Emergency Department simulation class based on research paper methodology <mcreference link="https://www.researchgate.net/publication/365839940_Patient_Flow_Optimization_in_an_Emergency_Department_Using_SimPy-Based_Simulation_Modeling_and_Analysis_A_Case_Study" index="0">0</mcreference>"""
    
    def __init__(self, 
                 env: simpy.Environment,
                 num_triage_nurses: int = 2,
                 num_doctors: int = 4,
                 num_cubicles: int = 8,
                 num_admission_beds: int = 20,
                 triage_system: Optional[BaseTriage] = None):
        """
        Initialize Emergency Department simulation
        
        Args:
            env: SimPy environment
            num_triage_nurses: Number of triage nurses
            num_doctors: Number of doctors available
            num_cubicles: Number of consultation cubicles
            num_admission_beds: Number of admission beds
            triage_system: Triage system to use (defaults to Manchester)
        """
        self.env = env
        
        # Resources based on research paper resource allocation methodology
        self.doctors = simpy.Resource(env, capacity=num_doctors)
        self.cubicles = simpy.Resource(env, capacity=num_cubicles)
        self.admission_beds = simpy.Resource(env, capacity=num_admission_beds)
        
        # Triage system
        if triage_system is None:
            self.triage_system = ManchesterTriage()
        else:
            self.triage_system = triage_system
        
        # Patient tracking
        self.patients_in_system: List[Patient] = []
        self.completed_patients: List[Patient] = []
        self.priority_queues: Dict[Priority, deque] = {
            priority: deque() for priority in Priority
        }
        
        # Metrics collection
        self.metrics = {
            'total_arrivals': 0,
            'total_departures': 0,
            'total_admissions': 0,
            'total_discharges': 0,
            'lwbs_count': 0,  # Left without being seen
            'wait_times_by_priority': defaultdict(list),
            'consultation_times': [],
            'total_system_times': [],
            'resource_utilization': defaultdict(list),
            'queue_lengths': defaultdict(list)
        }
        
        # Configuration parameters
        self.consultation_time_params = {
            Priority.IMMEDIATE: {'mean': 45, 'std': 15},
            Priority.VERY_URGENT: {'mean': 35, 'std': 12},
            Priority.URGENT: {'mean': 25, 'std': 10},
            Priority.STANDARD: {'mean': 20, 'std': 8},
            Priority.NON_URGENT: {'mean': 15, 'std': 5}
        }
        
        self.admission_probability = {
            Priority.IMMEDIATE: 0.8,
            Priority.VERY_URGENT: 0.4,
            Priority.URGENT: 0.2,
            Priority.STANDARD: 0.1,
            Priority.NON_URGENT: 0.05
        }
        
        # Performance monitoring
        self.monitoring_interval = 60  # Monitor every hour
        self.env.process(self._monitor_performance())
    
    def patient_arrival(self, patient: Patient):
        """Handle patient arrival and initiate ED journey"""
        return self._patient_journey(patient)
    
    def _patient_journey(self, patient: Patient):
        """Complete patient journey through ED based on research methodology"""
        self.patients_in_system.append(patient)
        self.metrics['total_arrivals'] += 1
        
        print(f"Time {self.env.now:.1f}: Patient {patient.patient_id[:8]} arrived with complaint: {patient.chief_complaint}")
        
        try:
            # Step 1: Triage Process
            yield from self._triage_process(patient)
            
            # Step 2: Queue for consultation based on priority
            yield from self._queue_for_consultation(patient)
            
            # Step 3: Consultation process
            yield from self._consultation_process(patient)
            
            # Step 4: Admission or discharge decision
            yield from self._disposition_process(patient)
            
        except simpy.Interrupt:
            # Handle patient leaving without being seen
            patient.update_status(PatientStatus.LEFT_WITHOUT_BEING_SEEN, self.env.now)
            self.metrics['lwbs_count'] += 1
            print(f"Time {self.env.now:.1f}: Patient {patient.patient_id[:8]} left without being seen")
        
        finally:
            # Remove from active patients and add to completed
            if patient in self.patients_in_system:
                self.patients_in_system.remove(patient)
            self.completed_patients.append(patient)
            self._record_patient_metrics(patient)
    
    def _triage_process(self, patient: Patient):
        """Triage process using the configured triage system"""
        # Update patient status to waiting for triage
        patient.update_status(PatientStatus.WAITING_TRIAGE, self.env.now)
        
        # Simulate triage nurse availability (simplified)
        triage_time = max(1.0, np.random.normal(5.0, 2.0))  # Ensure positive triage time
        yield self.env.timeout(triage_time)
        
        # Update status to in triage
        patient.update_status(PatientStatus.IN_TRIAGE, self.env.now)
        
        # Use triage system to assess patient
        triage_result = self.triage_system.assess_single_patient(patient)
        
        # Set patient priority and estimated consultation time
        patient.set_priority(triage_result.priority, triage_result.confidence_score, triage_result.reason)
        patient.estimated_consultation_time = triage_result.service_time
        
        print(f"Time {self.env.now:.1f}: Patient {patient.patient_id[:8]} triaged as {triage_result.priority.name} "
              f"(Service time: {triage_result.service_time:.1f}min) - {triage_result.reason}")
        
        # Update status to waiting for consultation
        patient.update_status(PatientStatus.WAITING_CONSULTATION, self.env.now)
    
    def _queue_for_consultation(self, patient: Patient):
        """Queue patient for consultation based on priority"""
        if patient.priority:
            self.priority_queues[patient.priority].append(patient)
            print(f"Time {self.env.now:.1f}: Patient {patient.patient_id[:8]} queued for consultation (Priority {patient.priority.value})")
        # Make this a generator function
        yield self.env.timeout(0)
    
    def _consultation_process(self, patient: Patient):
        """Consultation process with priority-based resource allocation"""
        # Wait for doctor and cubicle (priority handled by queue order)
        doctor_request = self.doctors.request()
        cubicle_request = self.cubicles.request()
        
        # Wait for both resources
        yield doctor_request & cubicle_request
        
        try:
            # Update status to in consultation
            patient.update_status(PatientStatus.IN_CONSULTATION, self.env.now)
            
            # Remove from priority queue
            if patient.priority and patient in self.priority_queues[patient.priority]:
                self.priority_queues[patient.priority].remove(patient)
            
            # Use service time from triage assessment
            consultation_time = patient.estimated_consultation_time or self._estimate_consultation_time(patient)
            
            print(f"Time {self.env.now:.1f}: Patient {patient.patient_id[:8]} started consultation (estimated {consultation_time:.1f} min)")
            
            # Perform consultation
            yield self.env.timeout(consultation_time)
            
            self.metrics['consultation_times'].append(consultation_time)
            
            print(f"Time {self.env.now:.1f}: Patient {patient.patient_id[:8]} completed consultation")
            
        finally:
            # Release resources
            self.doctors.release(doctor_request)
            self.cubicles.release(cubicle_request)
    
    def _disposition_process(self, patient: Patient):
        """Determine patient disposition (admission or discharge)"""
        if patient.priority:
            admission_prob = self.admission_probability[patient.priority]
            requires_admission = np.random.random() < admission_prob
            patient.requires_admission = requires_admission
            
            if requires_admission:
                yield from self._admission_process(patient)
            else:
                yield from self._discharge_process(patient)
    
    def _admission_process(self, patient: Patient):
        """Handle patient admission process"""
        patient.update_status(PatientStatus.WAITING_ADMISSION, self.env.now)
        
        # Request admission bed
        with self.admission_beds.request() as bed_request:
            yield bed_request
            
            patient.update_status(PatientStatus.ADMITTED, self.env.now)
            patient.discharge_disposition = "Admitted"
            
            self.metrics['total_admissions'] += 1
            self.metrics['total_departures'] += 1
            
            print(f"Time {self.env.now:.1f}: Patient {patient.patient_id[:8]} admitted")
    
    def _discharge_process(self, patient: Patient):
        """Handle patient discharge process"""
        patient.update_status(PatientStatus.DISCHARGED, self.env.now)
        patient.discharge_disposition = "Discharged"
        
        self.metrics['total_discharges'] += 1
        self.metrics['total_departures'] += 1
        
        print(f"Time {self.env.now:.1f}: Patient {patient.patient_id[:8]} discharged")
        
        # Make this a generator function
        yield self.env.timeout(0)
    
    def _estimate_consultation_time(self, patient: Patient) -> float:
        """Estimate consultation time based on priority and patient factors"""
        if not patient.priority:
            return np.random.normal(20, 8)  # Default time
        
        params = self.consultation_time_params[patient.priority]
        base_time = np.random.normal(params['mean'], params['std'])
        
        # Adjust for patient complexity
        complexity_factor = 1.0
        
        # Age adjustments
        if patient.age is not None:
            if patient.age < 2:
                complexity_factor += 0.3  # Pediatric cases take longer
            elif patient.age > 75:
                complexity_factor += 0.2  # Elderly cases may be more complex
        
        # Medical history complexity
        if patient.medical_history:
            complexity_factor += 0.1
        
        # Chief complaint complexity
        if patient.chief_complaint:
            complex_complaints = ['chest pain', 'difficulty breathing', 'abdominal pain', 'head injury']
            if any(term in patient.chief_complaint.lower() for term in complex_complaints):
                complexity_factor += 0.2
        
        final_time = max(5.0, base_time * complexity_factor)
        return final_time
    
    def _record_patient_metrics(self, patient: Patient):
        """Record patient journey metrics for analysis"""
        if patient.metrics.total_time_in_system:
            self.metrics['total_system_times'].append(patient.metrics.total_time_in_system)
        
        if patient.priority and patient.metrics.consultation_wait_time:
            self.metrics['wait_times_by_priority'][patient.priority].append(patient.metrics.consultation_wait_time)
    
    def _monitor_performance(self):
        """Monitor ED performance metrics periodically"""
        while True:
            yield self.env.timeout(self.monitoring_interval)
            
            # Record resource utilization
            doctor_utilization = (self.doctors.capacity - len(self.doctors.users)) / self.doctors.capacity
            cubicle_utilization = (self.cubicles.capacity - len(self.cubicles.users)) / self.cubicles.capacity
            
            self.metrics['resource_utilization']['doctors'].append((self.env.now, 1 - doctor_utilization))
            self.metrics['resource_utilization']['cubicles'].append((self.env.now, 1 - cubicle_utilization))
            
            # Record queue lengths
            for priority, queue in self.priority_queues.items():
                self.metrics['queue_lengths'][priority].append((self.env.now, len(queue)))
            
            # Check for wait time breaches
            breached_patients = self.triage_system.check_wait_time_breaches(self.patients_in_system)
            if breached_patients:
                print(f"Time {self.env.now:.1f}: {len(breached_patients)} patients exceeded maximum wait times")
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current ED status snapshot"""
        status_counts = defaultdict(int)
        for patient in self.patients_in_system:
            status_counts[patient.status.value] += 1
        
        priority_counts = defaultdict(int)
        for patient in self.patients_in_system:
            if patient.priority:
                priority_counts[patient.priority.name] += 1
        
        return {
            'current_time': self.env.now,
            'patients_in_system': len(self.patients_in_system),
            'completed_patients': len(self.completed_patients),
            'status_distribution': dict(status_counts),
            'priority_distribution': dict(priority_counts),
            'resource_availability': {
                'doctors': len(self.doctors.users),
                'cubicles': len(self.cubicles.users),
                'admission_beds': len(self.admission_beds.users)
            },
            'queue_lengths': {priority.name: len(queue) for priority, queue in self.priority_queues.items()}
        }
    
    def get_simulation_results(self) -> Dict[str, Any]:
        """Get comprehensive simulation results for analysis"""
        results = {
            'summary_statistics': {
                'total_arrivals': self.metrics['total_arrivals'],
                'total_departures': self.metrics['total_departures'],
                'total_admissions': self.metrics['total_admissions'],
                'total_discharges': self.metrics['total_discharges'],
                'lwbs_count': self.metrics['lwbs_count'],
                'admission_rate': self.metrics['total_admissions'] / max(1, self.metrics['total_departures']),
                'lwbs_rate': self.metrics['lwbs_count'] / max(1, self.metrics['total_arrivals'])
            },
            'wait_time_statistics': {},
            'consultation_statistics': {},
            'system_time_statistics': {},
            'triage_statistics': self.triage_system.get_triage_statistics(),
            'resource_utilization': dict(self.metrics['resource_utilization']),
            'patient_data': [patient.to_dict() for patient in self.completed_patients]
        }
        
        # Calculate wait time statistics by priority
        for priority, wait_times in self.metrics['wait_times_by_priority'].items():
            if wait_times:
                results['wait_time_statistics'][priority.name] = {
                    'mean': np.mean(wait_times),
                    'median': np.median(wait_times),
                    'std': np.std(wait_times),
                    'min': np.min(wait_times),
                    'max': np.max(wait_times),
                    'count': len(wait_times)
                }
        
        # Calculate consultation time statistics
        if self.metrics['consultation_times']:
            consultation_times = self.metrics['consultation_times']
            results['consultation_statistics'] = {
                'mean': np.mean(consultation_times),
                'median': np.median(consultation_times),
                'std': np.std(consultation_times),
                'min': np.min(consultation_times),
                'max': np.max(consultation_times)
            }
        
        # Calculate total system time statistics
        if self.metrics['total_system_times']:
            system_times = self.metrics['total_system_times']
            results['system_time_statistics'] = {
                'mean': np.mean(system_times),
                'median': np.median(system_times),
                'std': np.std(system_times),
                'min': np.min(system_times),
                'max': np.max(system_times)
            }
        
        return results
    
    def optimize_resources(self, target_wait_time: float = 60.0) -> Dict[str, int]:
        """Suggest resource optimization based on current performance"""
        current_wait_times = []
        for wait_times in self.metrics['wait_times_by_priority'].values():
            current_wait_times.extend(wait_times)
        
        if not current_wait_times:
            return {'doctors': self.doctors.capacity, 'cubicles': self.cubicles.capacity}
        
        avg_wait_time = np.mean(current_wait_times)
        
        suggestions = {
            'doctors': self.doctors.capacity,
            'cubicles': self.cubicles.capacity,
            'triage_nurses': self.triage_system.nurses.capacity
        }
        
        # Simple optimization logic based on research paper methodology
        if avg_wait_time > target_wait_time * 1.5:
            # Significant wait time breach - increase resources
            suggestions['doctors'] = min(self.doctors.capacity + 2, 10)
            suggestions['cubicles'] = min(self.cubicles.capacity + 2, 12)
        elif avg_wait_time > target_wait_time:
            # Moderate wait time breach - slight increase
            suggestions['doctors'] = min(self.doctors.capacity + 1, 8)
            suggestions['cubicles'] = min(self.cubicles.capacity + 1, 10)
        
        return suggestions