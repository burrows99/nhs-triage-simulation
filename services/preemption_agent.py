from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import random
import time
from enum import Enum

try:
    from ..entities.patient import Patient
    from ..enums.resource_type import ResourceType
    from ..enums.priority import TriagePriority
except ImportError:
    from entities.patient import Patient
    from enums.resource_type import ResourceType
    from enums.priority import TriagePriority


class PreemptionDecision(Enum):
    """Possible preemption decisions."""
    NO_PREEMPTION = "no_preemption"
    PREEMPT_RESOURCE = "preempt_resource"
    QUEUE_PATIENT = "queue_patient"


@dataclass(frozen=True)
class ResourceState:
    """
    Current state of a hospital resource.
    
    Immutable representation ensuring data integrity during decision making.
    """
    resource_id: str
    resource_type: ResourceType
    is_available: bool
    current_patient_id: Optional[str]
    current_patient_priority: Optional[TriagePriority]
    estimated_remaining_time: float
    queue_length: int
    
    def __post_init__(self) -> None:
        """Validate resource state data."""
        if not self.resource_id:
            raise ValueError("Resource ID cannot be empty")
        if self.estimated_remaining_time < 0:
            raise ValueError("Estimated remaining time cannot be negative")
        if self.queue_length < 0:
            raise ValueError("Queue length cannot be negative")


@dataclass(frozen=True)
class HospitalOperationsState:
    """
    Immutable snapshot of hospital operations state.
    
    Contains all resource states and system metrics needed for
    preemption decision making. Immutability ensures consistency
    during analysis and prevents accidental state modification.
    """
    timestamp: float
    total_patients_in_system: int
    average_wait_time: float
    resource_states: Dict[str, ResourceState]
    queue_states: Dict[ResourceType, List[str]]  # Resource type -> patient IDs in queue
    system_load: float  # Overall system utilization (0.0 to 1.0)
    
    def __post_init__(self) -> None:
        """Validate hospital operations state."""
        if self.timestamp < 0:
            raise ValueError("Timestamp cannot be negative")
        if self.total_patients_in_system < 0:
            raise ValueError("Total patients cannot be negative")
        if self.average_wait_time < 0:
            raise ValueError("Average wait time cannot be negative")
        if not 0.0 <= self.system_load <= 1.0:
            raise ValueError("System load must be between 0.0 and 1.0")
    
    def get_available_resources(self, resource_type: ResourceType) -> List[ResourceState]:
        """Get all available resources of specified type."""
        return [
            state for state in self.resource_states.values()
            if state.resource_type == resource_type and state.is_available
        ]
    
    def get_preemptible_resources(self, resource_type: ResourceType, incoming_priority: TriagePriority) -> List[ResourceState]:
        """Get resources that can be preempted by incoming patient."""
        preemptible: List[ResourceState] = []
        for state in self.resource_states.values():
            if (state.resource_type == resource_type and
                not state.is_available and
                state.current_patient_priority is not None and
                incoming_priority.value < state.current_patient_priority.value and
                resource_type.is_preemptive):
                preemptible.append(state)
        return preemptible


@dataclass(frozen=True)
class PreemptionResponse:
    """
    Response from preemption agent containing decision and rationale.
    
    Immutable to ensure decision integrity and provide audit trail.
    """
    decision: PreemptionDecision
    resource_id_to_preempt: Optional[str]
    target_queue_position: Optional[int]  # Position in queue (0 = front)
    confidence_score: float  # 0.0 to 1.0
    reasoning: str
    estimated_wait_time_reduction: float  # Minutes saved
    system_impact_score: float  # -1.0 to 1.0 (negative = harmful, positive = beneficial)
    
    def __post_init__(self) -> None:
        """Validate preemption response."""
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        if not -1.0 <= self.system_impact_score <= 1.0:
            raise ValueError("System impact score must be between -1.0 and 1.0")
        if self.estimated_wait_time_reduction < 0:
            raise ValueError("Estimated wait time reduction cannot be negative")
        if self.decision == PreemptionDecision.PREEMPT_RESOURCE and not self.resource_id_to_preempt:
            raise ValueError("Resource ID must be provided for preemption decision")
        if self.decision == PreemptionDecision.QUEUE_PATIENT and self.target_queue_position is None:
            raise ValueError("Queue position must be provided for queue decision")


class MockAPIClient:
    """
    Mock API client for simulating external preemption decision service.
    
    In production, this would connect to an AI/ML service that analyzes
    hospital operations data and provides intelligent preemption recommendations.
    """
    
    def __init__(self, base_url: str = "https://api.hospital-ai.example.com", api_key: str = "mock_key") -> None:
        """Initialize mock API client."""
        self.base_url = base_url
        self.api_key = api_key
        self.request_count = 0
        self.response_time_ms = 150  # Simulate API latency
    
    def make_preemption_request(self, patient_data: Dict[str, Any], operations_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make mock API request for preemption decision.
        
        Args:
            patient_data: Patient information
            operations_state: Current hospital state
            
        Returns:
            Mock API response
        """
        self.request_count += 1
        
        # Simulate API latency
        time.sleep(self.response_time_ms / 1000.0)
        
        # Mock response generation
        mock_response = {
            "request_id": f"req_{self.request_count}_{int(time.time())}",
            "status": "success",
            "decision": self._generate_mock_decision(patient_data, operations_state),
            "confidence": random.uniform(0.6, 0.95),
            "processing_time_ms": self.response_time_ms,
            "model_version": "v2.1.0",
            "timestamp": time.time()
        }
        
        return mock_response
    
    def _generate_mock_decision(self, patient_data: Dict[str, Any], operations_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate mock preemption decision based on simple heuristics.
        
        In production, this would be replaced by sophisticated ML models.
        """
        patient_priority = patient_data.get("priority", 3)
        system_load = operations_state.get("system_load", 0.5)
        
        # Simple decision logic for demonstration
        if patient_priority <= 2 and system_load > 0.8:
            # High priority patient in overloaded system - likely preemption
            decision_type = "preempt_resource"
            resource_id = self._select_mock_resource_to_preempt(operations_state)
            impact_score = random.uniform(0.3, 0.8)
            wait_reduction = random.uniform(15.0, 45.0)
        elif patient_priority <= 3 and system_load > 0.6:
            # Medium priority - might get queue priority
            decision_type = "queue_patient"
            resource_id = None
            impact_score = random.uniform(0.1, 0.4)
            wait_reduction = random.uniform(5.0, 20.0)
        else:
            # Low priority or low system load - no preemption
            decision_type = "no_preemption"
            resource_id = None
            impact_score = random.uniform(-0.1, 0.2)
            wait_reduction = 0.0
        
        return {
            "decision_type": decision_type,
            "resource_id": resource_id,
            "queue_position": random.randint(0, 2) if decision_type == "queue_patient" else None,
            "impact_score": impact_score,
            "wait_time_reduction": wait_reduction,
            "reasoning": self._generate_mock_reasoning(decision_type, patient_priority, system_load)
        }
    
    def _select_mock_resource_to_preempt(self, operations_state: Dict[str, Any]) -> Optional[str]:
        """Select a mock resource ID for preemption."""
        # In practice, this would analyze actual resource states
        mock_resource_ids = ["doc_001", "doc_002", "mri_001", "mri_002"]
        return random.choice(mock_resource_ids)
    
    def _generate_mock_reasoning(self, decision_type: str, priority: int, system_load: float) -> str:
        """Generate mock reasoning for the decision."""
        if decision_type == "preempt_resource":
            return f"High priority patient (P{priority}) in overloaded system ({system_load:.1%}). Preemption recommended to minimize critical wait time."
        elif decision_type == "queue_patient":
            return f"Medium priority patient (P{priority}) with moderate system load ({system_load:.1%}). Queue optimization recommended."
        else:
            return f"Standard priority patient (P{priority}) with acceptable system load ({system_load:.1%}). No intervention required."


class PreemptionAgent:
    """
    Intelligent preemption decision agent for hospital resource optimization.
    
    Makes data-driven decisions about when to preempt current services
    for higher priority patients, considering system-wide impact and
    patient outcomes. Uses external AI service (mocked) for complex
    decision making.
    
    Key capabilities:
    - Analyzes patient priority and system state
    - Evaluates preemption opportunities
    - Provides confidence-scored recommendations
    - Tracks decision outcomes for learning
    
    Future enhancements would include:
    - Machine learning model integration
    - Historical outcome analysis
    - Real-time system optimization
    - Multi-objective decision making
    """
    
    def __init__(self, api_client: Optional[MockAPIClient] = None, enable_learning: bool = False) -> None:
        """Initialize preemption agent."""
        self.api_client = api_client or MockAPIClient()
        self.enable_learning = enable_learning
        self.decision_history: List[tuple[float, PreemptionResponse, Dict[str, Any]]] = []
        self.performance_metrics = {
            "total_decisions": 0,
            "preemptions_recommended": 0,
            "preemptions_successful": 0,
            "average_confidence": 0.0,
            "average_impact_score": 0.0
        }
    
    def make_preemption_decision(self, patient: Patient, operations_state: HospitalOperationsState) -> PreemptionResponse:
        """
        Make preemption decision for incoming patient.
        
        Args:
            patient: Incoming patient requiring service
            operations_state: Current hospital operations state
            
        Returns:
            Preemption decision with rationale
            
        Raises:
            ValueError: If patient or operations state is invalid
        """
        if not patient:
            raise ValueError("Patient cannot be None")
        if not operations_state:
            raise ValueError("Operations state cannot be None")
        
        # Prepare data for API call
        patient_data = self._serialize_patient_data(patient)
        state_data = self._serialize_operations_state(operations_state)
        
        try:
            # Make API call to decision service
            api_response = self.api_client.make_preemption_request(patient_data, state_data)
            
            # Parse response into structured decision
            decision = self._parse_api_response(api_response, patient, operations_state)
            
            # Record decision for learning
            if self.enable_learning:
                self._record_decision(decision, {"patient": patient_data, "state": state_data})
            
            # Update performance metrics
            self._update_metrics(decision)
            
            return decision
            
        except Exception as e:
            # Fallback to simple heuristic if API fails
            return self._fallback_decision(patient, operations_state, str(e))
    
    def _serialize_patient_data(self, patient: Patient) -> Dict[str, Any]:
        """Serialize patient data for API call."""
        return {
            "patient_id": patient.patient_id,
            "priority": patient.priority.value,
            "priority_name": patient.priority.name,
            "required_resource": patient.required_resource.value,
            "estimated_service_time": patient.estimated_service_time,
            "arrival_time": patient.arrival_time,
            "current_status": patient.status.value,
            "is_high_priority": patient.is_high_priority
        }
    
    def _serialize_operations_state(self, state: HospitalOperationsState) -> Dict[str, Any]:
        """Serialize operations state for API call."""
        return {
            "timestamp": state.timestamp,
            "total_patients": state.total_patients_in_system,
            "average_wait_time": state.average_wait_time,
            "system_load": state.system_load,
            "resource_count": len(state.resource_states),
            "available_resources": {
                resource_type.value: len(state.get_available_resources(resource_type))
                for resource_type in ResourceType
            },
            "queue_lengths": {
                resource_type.value: len(queue)
                for resource_type, queue in state.queue_states.items()
            }
        }
    
    def _parse_api_response(self, api_response: Dict[str, Any], patient: Patient, operations_state: HospitalOperationsState) -> PreemptionResponse:
        """Parse API response into structured preemption decision."""
        decision_data = api_response.get("decision", {})
        
        # Map API decision type to enum
        decision_type_map = {
            "no_preemption": PreemptionDecision.NO_PREEMPTION,
            "preempt_resource": PreemptionDecision.PREEMPT_RESOURCE,
            "queue_patient": PreemptionDecision.QUEUE_PATIENT
        }
        
        decision_type = decision_type_map.get(
            decision_data.get("decision_type", "no_preemption"),
            PreemptionDecision.NO_PREEMPTION
        )
        
        return PreemptionResponse(
            decision=decision_type,
            resource_id_to_preempt=decision_data.get("resource_id"),
            target_queue_position=decision_data.get("queue_position"),
            confidence_score=api_response.get("confidence", 0.5),
            reasoning=decision_data.get("reasoning", "API decision"),
            estimated_wait_time_reduction=decision_data.get("wait_time_reduction", 0.0),
            system_impact_score=decision_data.get("impact_score", 0.0)
        )
    
    def _fallback_decision(self, patient: Patient, operations_state: HospitalOperationsState, error_reason: str) -> PreemptionResponse:
        """Generate fallback decision when API fails."""
        # Simple heuristic: only preempt for immediate priority patients
        if patient.priority == TriagePriority.IMMEDIATE:
            # Look for preemptible resources
            preemptible = operations_state.get_preemptible_resources(
                patient.required_resource, patient.priority
            )
            
            if preemptible:
                # Select resource with lowest priority current patient
                target_resource = min(preemptible, 
                                    key=lambda r: r.current_patient_priority.value if r.current_patient_priority else 5)
                
                return PreemptionResponse(
                    decision=PreemptionDecision.PREEMPT_RESOURCE,
                    resource_id_to_preempt=target_resource.resource_id,
                    target_queue_position=None,
                    confidence_score=0.7,
                    reasoning=f"Fallback decision for immediate priority patient. API error: {error_reason}",
                    estimated_wait_time_reduction=target_resource.estimated_remaining_time,
                    system_impact_score=0.5
                )
        
        # Default: no preemption
        return PreemptionResponse(
            decision=PreemptionDecision.NO_PREEMPTION,
            resource_id_to_preempt=None,
            target_queue_position=None,
            confidence_score=0.8,
            reasoning=f"Fallback: no preemption recommended. API error: {error_reason}",
            estimated_wait_time_reduction=0.0,
            system_impact_score=0.0
        )
    
    def _record_decision(self, decision: PreemptionResponse, context: Dict[str, Any]) -> None:
        """Record decision for learning and analysis."""
        self.decision_history.append((time.time(), decision, context))
        
        # Keep only recent decisions to prevent memory bloat
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-500:]
    
    def _update_metrics(self, decision: PreemptionResponse) -> None:
        """Update performance metrics."""
        self.performance_metrics["total_decisions"] += 1
        
        if decision.decision == PreemptionDecision.PREEMPT_RESOURCE:
            self.performance_metrics["preemptions_recommended"] += 1
        
        # Update running averages
        total = self.performance_metrics["total_decisions"]
        self.performance_metrics["average_confidence"] = (
            (self.performance_metrics["average_confidence"] * (total - 1) + decision.confidence_score) / total
        )
        self.performance_metrics["average_impact_score"] = (
            (self.performance_metrics["average_impact_score"] * (total - 1) + decision.system_impact_score) / total
        )
    
    def get_performance_summary(self) -> Dict[str, float]:
        """Get agent performance summary."""
        total_decisions = self.performance_metrics["total_decisions"]
        if total_decisions == 0:
            return {key: 0.0 for key in self.performance_metrics}
        
        summary = dict(self.performance_metrics)
        summary["preemption_rate"] = (
            self.performance_metrics["preemptions_recommended"] / total_decisions
        )
        
        return summary
    
    def __str__(self) -> str:
        return f"PreemptionAgent(decisions={self.performance_metrics['total_decisions']}, preemption_rate={self.get_performance_summary().get('preemption_rate', 0.0):.1%})"