from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from ..patient.patient import Patient
from ...enums.priority import Priority

@dataclass
class RoutingAgent:
    """Enhanced rule-based routing agent for patient resource assignment with decision logging"""
    
    # Store routing decisions for analysis and UI display
    routing_decisions: List[Dict[str, Any]] = field(default_factory=list)
    
    def should_assign_to_doctor(self, patient: Patient, priority: Priority) -> bool:
        """Determine if patient should be assigned to doctor (default: always true)"""
        return True
    
    def should_assign_urgent_bed(self, patient: Patient, priority: Priority) -> bool:
        """Determine if urgent patient should also get a bed"""
        return priority in [Priority.RED, Priority.ORANGE]
    
    def make_routing_decision(self, patient: Patient, priority: Priority) -> Dict[str, Any]:
        """Make comprehensive routing decision and log it for UI display"""
        assign_doctor = self.should_assign_to_doctor(patient, priority)
        assign_bed = self.should_assign_urgent_bed(patient, priority)
        
        # Generate routing logic explanation
        logic_parts = []
        if assign_doctor:
            logic_parts.append(f"Doctor consultation required for {priority.name_display} priority")
        if assign_bed:
            logic_parts.append(f"Urgent bed needed for {priority.name_display} priority")
        elif priority in [Priority.YELLOW, Priority.GREEN, Priority.BLUE]:
            logic_parts.append("Outpatient treatment - no bed required")
        
        routing_logic = "; ".join(logic_parts) if logic_parts else "Standard routing protocol"
        
        # Create decision record
        decision = {
            "patient_name": patient.name,
            "priority": priority.value,
            "priority_display": priority.name_display,
            "assign_doctor": assign_doctor,
            "assign_bed": assign_bed,
            "routing_logic": routing_logic,
            "symptoms": patient.symptoms.symptoms if hasattr(patient.symptoms, 'symptoms') else [],
            "timestamp": None  # Will be set by simulation
        }
        
        # Store decision for UI access
        self.routing_decisions.append(decision)
        
        # Keep only last 50 decisions to prevent memory issues
        if len(self.routing_decisions) > 50:
            self.routing_decisions = self.routing_decisions[-50:]
        
        return decision
    
    def get_latest_decision(self) -> Optional[Dict[str, Any]]:
        """Get the most recent routing decision for UI display"""
        return self.routing_decisions[-1] if self.routing_decisions else None
    
    def get_decisions_for_patient(self, patient_name: str) -> List[Dict[str, Any]]:
        """Get all routing decisions for a specific patient"""
        return [d for d in self.routing_decisions if d["patient_name"] == patient_name]
    
    def get_decision_statistics(self) -> Dict[str, Any]:
        """Get routing decision statistics for analysis"""
        if not self.routing_decisions:
            return {"total_decisions": 0}
        
        total = len(self.routing_decisions)
        doctor_assignments = sum(1 for d in self.routing_decisions if d["assign_doctor"])
        bed_assignments = sum(1 for d in self.routing_decisions if d["assign_bed"])
        
        priority_counts = {}
        for decision in self.routing_decisions:
            priority = decision["priority"]
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        return {
            "total_decisions": total,
            "doctor_assignment_rate": doctor_assignments / total if total > 0 else 0,
            "bed_assignment_rate": bed_assignments / total if total > 0 else 0,
            "priority_distribution": priority_counts
        }