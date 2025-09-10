import simpy
import json
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..entities.hospital.hospital import Hospital
from ..entities.patient.patient import Patient
from ..services.patient_factory import PatientFactory
from ..enums.priority import Priority

class HospitalSimulation:
    """SimPy-based hospital simulation that tracks patient journeys and generates JSON events"""
    
    def __init__(self, hospital: Hospital, simulation_time: int = 480):
        self.env = simpy.Environment()
        self.hospital = hospital
        self.hospital.env = self.env  # Give hospital access to environment
        self.simulation_time = simulation_time
        self.events: List[Dict[str, Any]] = []
        self.patient_factory = PatientFactory()
        self.start_time = datetime.now()
        
    def log_event(self, event_type: str, patient_name: str, resource_name: Optional[str] = None, 
                  priority: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        """Log simulation events for JSON export"""
        event = {
            "timestamp": self.env.now,
            "real_time": (self.start_time + timedelta(minutes=self.env.now)).isoformat(),
            "event_type": event_type,
            "patient_name": patient_name,
            "resource_name": resource_name,
            "priority": priority,
            "details": details or {}
        }
        self.events.append(event)
        print(f"[{self.env.now:6.1f}] {event_type}: {patient_name} {details or ''}")
    
    def patient_arrival_process(self):
        """Generate patient arrivals throughout the simulation"""
        patient_id = 1
        
        while True:
            # Create patient with random priority
            patient: Patient = self.patient_factory.create_patient()
            patient.id = patient_id
            patient_id += 1
            
            # Start patient journey
            self.env.process(self.patient_journey(patient))
            
            # Wait for next arrival (exponential distribution)
            inter_arrival_time = random.expovariate(1.0 / 15)  # Average 15 minutes
            yield self.env.timeout(inter_arrival_time)
    
    def patient_journey(self, patient: Patient):
        """Simulate complete patient journey through hospital"""
        # 1. Patient arrives
        arrival_time = self.env.now
        self.log_event("PATIENT_ARRIVAL", patient.name, details={
            "symptoms": patient.symptoms.symptoms,
            "history": patient.history
        })
        
        # 2. Triage process
        yield self.env.timeout(2)  # 2 minutes for triage
        priority = self.hospital.triage_system.determine_priority(patient)
        triage_info = self.hospital.triage_system.get_triage_info(patient)
        
        self.log_event("TRIAGE_COMPLETE", patient.name, priority=priority.value, details={
            "priority_name": priority.name_display,
            "max_wait_time": priority.max_wait_time,
            "triage_scores": triage_info["final_scores"]
        })
        
        # 3. Routing decision using enhanced routing agent
        routing_decision = self.hospital.routing_agent.make_routing_decision(patient, priority)
        routing_decision["timestamp"] = self.env.now  # Add timestamp
        
        self.log_event("ROUTING_DECISION", patient.name, priority=priority.value, details={
            "assign_doctor": routing_decision["assign_doctor"],
            "assign_bed": routing_decision["assign_bed"],
            "routing_logic": routing_decision["routing_logic"]
        })
        
        # 4. Doctor consultation
        if routing_decision["assign_doctor"]:
            available_doctors = self.hospital.get_available_doctors()
            if available_doctors:
                # Choose doctor with least patients in queue for load balancing
                doctor = min(available_doctors, key=lambda d: d.get_total_patients_in_queue())
                
                # Add to doctor's queue
                doctor.add_patient_to_queue(patient, priority.value)
                self.log_event("QUEUE_JOIN", patient.name, doctor.name, priority.value, details={
                    "queue_position": len([p for p in doctor.patient_queue[priority.value]]),
                    "total_in_queue": doctor.get_total_patients_in_queue()
                })
                
                # Wait for doctor availability based on priority
                wait_time = self._calculate_wait_time(priority, doctor)
                yield self.env.timeout(wait_time)
                
                # Start consultation
                self.log_event("CONSULTATION_START", patient.name, doctor.name, priority.value)
                
                # Consultation duration based on priority
                consultation_time = self._calculate_consultation_time(priority)
                yield self.env.timeout(consultation_time)
                
                # Remove from queue
                doctor.remove_patient_from_queue(patient)
                self.log_event("CONSULTATION_END", patient.name, doctor.name, priority.value, details={
                    "duration": consultation_time
                })
        
        # 5. Bed assignment for urgent patients
        if routing_decision["assign_bed"]:
            available_beds = self.hospital.get_available_beds()
            if available_beds:
                bed = available_beds[0]
                bed.add_patient_to_queue(patient, priority.value)
                
                self.log_event("BED_ASSIGNMENT", patient.name, bed.name, priority.value)
                
                # Stay in bed based on priority
                bed_time = self._calculate_bed_time(priority)
                yield self.env.timeout(bed_time)
                
                bed.remove_patient_from_queue(patient)
                self.log_event("BED_DISCHARGE", patient.name, bed.name, priority.value, details={
                    "duration": bed_time
                })
        
        # 6. Patient discharge
        total_time = self.env.now - arrival_time
        self.hospital.discharge_patient(patient)
        
        self.log_event("PATIENT_DISCHARGE", patient.name, details={
            "total_time_in_hospital": total_time,
            "priority": priority.value
        })
    
    def _calculate_wait_time(self, priority: Priority, doctor) -> float:
        """Calculate expected wait time based on priority and doctor queue"""
        base_wait_times = {
            Priority.RED: 0,      # Immediate
            Priority.ORANGE: 2,   # 2 minutes
            Priority.YELLOW: 5,   # 5 minutes
            Priority.GREEN: 10,   # 10 minutes
            Priority.BLUE: 15     # 15 minutes
        }
        
        base_wait = base_wait_times.get(priority, 10)
        queue_factor = doctor.get_total_patients_in_queue() * 2  # 2 minutes per patient in queue
        
        return base_wait + queue_factor
    
    def _calculate_consultation_time(self, priority: Priority) -> float:
        """Calculate consultation duration based on priority"""
        consultation_times = {
            Priority.RED: 45,     # 45 minutes for critical
            Priority.ORANGE: 30,  # 30 minutes for very urgent
            Priority.YELLOW: 20,  # 20 minutes for urgent
            Priority.GREEN: 15,   # 15 minutes for standard
            Priority.BLUE: 10     # 10 minutes for non-urgent
        }
        
        return consultation_times.get(priority, 15)
    
    def _calculate_bed_time(self, priority: Priority) -> float:
        """Calculate bed occupancy duration based on priority"""
        bed_times = {
            Priority.RED: 120,    # 2 hours for critical
            Priority.ORANGE: 90,  # 1.5 hours for very urgent
            Priority.YELLOW: 60,  # 1 hour for urgent
            Priority.GREEN: 30,   # 30 minutes for standard
            Priority.BLUE: 15     # 15 minutes for non-urgent
        }
        
        return bed_times.get(priority, 60)
    
    def hospital_status_monitor(self):
        """Monitor and log hospital status periodically"""
        while True:
            yield self.env.timeout(60)  # Every hour
            
            stats = self.hospital.get_hospital_stats()
            queue_summary = self.hospital.get_queue_summary()
            
            self.log_event("HOSPITAL_STATUS", "SYSTEM", details={
                "statistics": stats,
                "queue_summary": queue_summary,
                "simulation_time": self.env.now
            })
    
    def run_simulation(self) -> List[Dict[str, Any]]:
        """Run the complete simulation and return events"""
        print(f"Starting hospital simulation for {self.simulation_time} minutes...")
        
        # Start processes
        self.env.process(self.patient_arrival_process())
        self.env.process(self.hospital_status_monitor())
        
        # Run simulation
        self.env.run(until=self.simulation_time)
        
        print(f"\nSimulation completed. Generated {len(self.events)} events.")
        return self.events
    
    def export_events_to_json(self, filename: Optional[str] = None) -> str:
        """Export simulation events to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hospital_simulation_{timestamp}.json"
        
        simulation_data = {
            "simulation_info": {
                "start_time": self.start_time.isoformat(),
                "duration_minutes": self.simulation_time,
                "total_events": len(self.events),
                "hospital_name": self.hospital.name
            },
            "events": self.events
        }
        
        with open(filename, 'w') as f:
            json.dump(simulation_data, f, indent=2, default=str)
        
        print(f"Events exported to {filename}")
        return filename