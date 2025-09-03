"""Mixture LLM Triage System

Multi-agent LLM triage system using LangGraph for orchestrating multiple
specialized agents in the triage decision process.

This system uses parallel agents to analyze different aspects of triage:
- Symptom Analyzer: Analyzes patient symptoms and clinical presentation
- History Evaluator: Reviews patient medical history and risk factors
- Guidelines Checker: Validates against NHS triage guidelines
- Operations Analyst: Considers current hospital operational metrics
- Trends Analyzer: Analyzes patterns and trends in patient flow
- Finalizer: Combines all agent outputs into final triage decision
"""

import json
import asyncio
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from concurrent.futures import ThreadPoolExecutor

try:
    from langgraph.graph import StateGraph, END
    from langgraph.graph.message import add_messages
    LANGGRAPH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"LangGraph import failed: {e}")
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = None
    add_messages = None

from src.logger import logger
from .base_llm_triage import BaseLLMTriageSystem
from .json_handler import TriageJSONHandler, ResponseQuality
from src.models.triage_result import TriageResult
from .config.system_prompts import get_triage_categories


# Custom reducer function for agent analysis results
def agent_analysis_reducer(left: List[Dict[str, Any]], right: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Reducer function to handle multiple agent updates to analysis fields.
    
    Args:
        left: Current list of analysis results
        right: New analysis result to add
        
    Returns:
        Updated list with new analysis result appended
    """
    if left is None:
        left = []
    if right is not None:
        return left + [right]
    return left

# Custom reducer for dictionary fields that might be updated by multiple agents
def dict_reducer(left: Optional[Dict[str, Any]], right: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Reducer function for dictionary fields - takes the latest non-null value."""
    return right if right is not None else left


# State definition for LangGraph workflow
# Custom reducer for string fields that might be updated by multiple agents
def string_reducer(left: Optional[str], right: Optional[str]) -> Optional[str]:
    """Reducer function for string fields - takes the latest non-null value."""
    return right if right is not None else left

class TriageState(TypedDict):
    """State object for the multi-agent triage workflow."""
    # Use reducer for symptoms to handle potential concurrent updates
    symptoms: Annotated[str, string_reducer]
    operational_context: Annotated[str, string_reducer]
    patient_history: Annotated[str, string_reducer]
    
    # Agent analysis results - using custom reducer to handle concurrent updates
    symptom_analysis: Annotated[List[Dict[str, Any]], agent_analysis_reducer]
    history_evaluation: Annotated[List[Dict[str, Any]], agent_analysis_reducer]
    guidelines_check: Annotated[List[Dict[str, Any]], agent_analysis_reducer]
    operations_analysis: Annotated[List[Dict[str, Any]], agent_analysis_reducer]
    trends_analysis: Annotated[List[Dict[str, Any]], agent_analysis_reducer]
    
    # Final result - using dict reducer to handle concurrent updates
    final_decision: Annotated[Optional[Dict[str, Any]], dict_reducer]
    
    # Workflow control - using string reducer to handle concurrent updates
    next_step: Annotated[Optional[str], string_reducer]
    error: Annotated[Optional[str], string_reducer]


class MixtureLLMTriage(BaseLLMTriageSystem):
    """
    Multi-agent LLM triage system using LangGraph.
    
    This system orchestrates multiple specialized agents:
    - SymptomAnalyzer: Analyzes clinical symptoms and presentation
    - HistoryEvaluator: Reviews patient medical history and risk factors
    - GuidelinesChecker: Validates against NHS triage guidelines
    - OperationsAnalyst: Considers current hospital operational metrics
    - TrendsAnalyzer: Analyzes patterns and trends in patient flow
    - Finalizer: Combines all agent outputs into final triage decision
    
    Uses LangGraph for parallel execution and workflow orchestration.
    """
    
    def __init__(self, model_name: str = None, operation_metrics=None, nhs_metrics=None, 
                 agent_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the mixture LLM triage system.
        
        Args:
            model_name (str): Primary model identifier
            operation_metrics: OperationMetrics instance
            nhs_metrics: NHSMetrics instance
            agent_config (Dict): Configuration for specialized agents
        """
        # Import HF_MODEL here to ensure environment is loaded
        from .base_llm_triage import HF_MODEL
        if model_name is None:
            model_name = HF_MODEL
        super().__init__(model_name, operation_metrics, nhs_metrics)
        
        self.agent_config = agent_config or self._get_default_agent_config()
        self.workflow = None
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.json_handler = TriageJSONHandler(strict_mode=True)
        
        logger.info(f"🤖 Initializing Mixture LLM Triage System (Multi-Agent)")
        
        if not LANGGRAPH_AVAILABLE:
            logger.warning(f"⚠️ LangGraph not available - falling back to single agent")
        else:
            logger.info(f"✅ LangGraph available - initializing multi-agent workflow")
            self._initialize_workflow()
    
    def _get_default_agent_config(self) -> Dict[str, Any]:
        """
        Get default configuration for specialized agents.
        
        Returns:
            Dict containing agent specifications
        """
        return {
            "symptom_analyzer": {
                "role": "Analyze and categorize patient symptoms",
                "model": self.model_name,
                "temperature": 0.1
            },
            "context_evaluator": {
                "role": "Evaluate operational context and resource constraints",
                "model": self.model_name,
                "temperature": 0.0
            },
            "triage_specialist": {
                "role": "Make final triage category decisions",
                "model": self.model_name,
                "temperature": 0.0
            },
            "validator": {
                "role": "Validate and quality-check triage decisions",
                "model": self.model_name,
                "temperature": 0.0
            }
        }
    
    def triage_patient(self, symptoms: str) -> TriageResult:
        """
        Triage a patient using multi-agent system.
        
        Args:
            symptoms (str): Patient symptoms description
            
        Returns:
            TriageResult: Triage result from multi-agent consensus
        """
        logger.info(f"🔄 DATA_TRANSFER_START: MixtureLLMTriage.triage_patient() initiated")
        logger.info(f"📊 TRANSFER_SOURCE: Symptoms text - {symptoms}")
        logger.info(f"📍 TRANSFER_DESTINATION: Multi-agent workflow system")
        logger.info(f"🤖 Starting Multi-Agent Triage Assessment")
        logger.info(f"📋 Patient Symptoms: {symptoms[:80]}{'...' if len(symptoms) > 80 else ''}")
        
        # Validate input
        logger.info(f"🔄 DATA_TRANSFER: Validating symptoms input...")
        self._validate_symptoms(symptoms)
        logger.info(f"📊 TRANSFER_RESULT: Symptoms validation completed")
        
        if not LANGGRAPH_AVAILABLE or self.workflow is None:
            logger.warning(f"⚠️ SYSTEM_FALLBACK: Multi-agent workflow not available - falling back to single agent")
            return self._fallback_single_agent_triage(symptoms)
        
        try:
            # Execute multi-agent workflow
            logger.info(f"🔄 DATA_TRANSFER: Executing Multi-Agent Workflow")
            logger.info(f"📊 TRANSFER_PAYLOAD: Symptoms length: {len(symptoms)} chars")
            result = self._execute_multi_agent_workflow(symptoms)
            logger.info(f"📊 TRANSFER_RESULT: Workflow result - {str(result.__dict__)[:300]}...")
            logger.info(f"✅ DATA_TRANSFER_SUCCESS: Multi-Agent Triage Assessment Complete")
            return result
            
        except Exception as e:
            logger.error(f"❌ DATA_TRANSFER_ERROR: Multi-agent workflow failed: {e}")
            logger.info(f"🔄 SYSTEM_FALLBACK: Falling back to single agent")
            return self._fallback_single_agent_triage(symptoms)
    
    def _fallback_single_agent_triage(self, symptoms: str) -> TriageResult:
        """
        Fallback to single-agent triage when multi-agent is not available.
        
        Args:
            symptoms (str): Patient symptoms
            
        Returns:
            TriageResult: Single-agent triage result
        """
        from .single_llm_triage import SingleLLMTriage
        
        # Create single agent instance with same configuration
        single_agent = SingleLLMTriage(
            model_name=self.model_name,
            operation_metrics=self.operation_metrics,
            nhs_metrics=self.nhs_metrics
        )
        
        return single_agent.triage_patient(symptoms)
    
    def _initialize_workflow(self) -> None:
        """
        Initialize the LangGraph workflow for multi-agent triage.
        """
        if not LANGGRAPH_AVAILABLE:
            return
        
        try:
            # Create the workflow graph
            workflow = StateGraph(TriageState)
            
            # Add agent nodes
            workflow.add_node("symptom_analyzer", self._symptom_analyzer_agent)
            workflow.add_node("history_evaluator", self._history_evaluator_agent)
            workflow.add_node("guidelines_checker", self._guidelines_checker_agent)
            workflow.add_node("operations_analyst", self._operations_analyst_agent)
            workflow.add_node("trends_analyzer", self._trends_analyzer_agent)
            workflow.add_node("finalizer", self._finalizer_agent)
            
            # Set entry point
            workflow.set_entry_point("symptom_analyzer")
            
            # Add parallel edges for concurrent execution
            workflow.add_edge("symptom_analyzer", "history_evaluator")
            workflow.add_edge("symptom_analyzer", "guidelines_checker")
            workflow.add_edge("symptom_analyzer", "operations_analyst")
            workflow.add_edge("symptom_analyzer", "trends_analyzer")
            
            # All agents feed into finalizer
            workflow.add_edge("history_evaluator", "finalizer")
            workflow.add_edge("guidelines_checker", "finalizer")
            workflow.add_edge("operations_analyst", "finalizer")
            workflow.add_edge("trends_analyzer", "finalizer")
            
            # Finalizer ends the workflow
            workflow.add_edge("finalizer", END)
            
            # Compile the workflow
            self.workflow = workflow.compile()
            logger.info(f"✅ Multi-agent workflow initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize workflow: {e}")
            self.workflow = None
    
    def _execute_multi_agent_workflow(self, symptoms: str) -> TriageResult:
        """
        Execute the multi-agent workflow for triage decision.
        
        Args:
            symptoms (str): Patient symptoms
            
        Returns:
            TriageResult: Final triage decision from multi-agent consensus
        """
        # Prepare operational context
        operational_context = ""
        if self.operation_metrics and self.nhs_metrics:
            current_time = 0.0
            if self.operation_metrics.system_snapshots:
                current_time = self.operation_metrics.system_snapshots[-1].timestamp
            operational_context = self._generate_operational_context(current_time)
        
        # Initialize state
        initial_state: TriageState = {
            "symptoms": symptoms,
            "operational_context": operational_context,
            "patient_history": self._extract_patient_history(symptoms),
            "symptom_analysis": [],
            "history_evaluation": [],
            "guidelines_check": [],
            "operations_analysis": [],
            "trends_analysis": [],
            "final_decision": None,
            "next_step": None,
            "error": None
        }
        
        # Execute workflow
        logger.info(f"🔄 Executing parallel agent analysis")
        final_state = self.workflow.invoke(initial_state)
        
        if final_state.get("error"):
            raise RuntimeError(f"Workflow error: {final_state['error']}")
        
        if not final_state.get("final_decision"):
            raise RuntimeError("No final decision produced by workflow")
        
        # Convert to TriageResult
        return TriageResult.from_llm_result(final_state["final_decision"])
    
    def _extract_patient_history(self, symptoms: str) -> str:
        """
        Extract or infer patient history from symptoms description.
        
        Args:
            symptoms (str): Patient symptoms
            
        Returns:
            str: Patient history context
        """
        # For now, extract basic history indicators from symptoms
        # In a real system, this would access patient records
        history_indicators = []
        
        if "previous" in symptoms.lower() or "history of" in symptoms.lower():
            history_indicators.append("Previous medical history mentioned")
        if "medication" in symptoms.lower() or "taking" in symptoms.lower():
            history_indicators.append("Current medications indicated")
        if "allergy" in symptoms.lower() or "allergic" in symptoms.lower():
            history_indicators.append("Allergy information present")
        
        return "; ".join(history_indicators) if history_indicators else "No specific history indicators found"
    
    # Individual Agent Methods
    
    def _symptom_analyzer_agent(self, state: TriageState) -> TriageState:
        """
        Analyze patient symptoms and clinical presentation.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with symptom analysis
        """
        logger.info(f"🔍 Symptom Analyzer: Analyzing clinical presentation")
        
        try:
            prompt = f"""
            You are a clinical symptom analyzer. Analyze the following patient symptoms and provide a structured assessment.
            
            Patient Symptoms: {state['symptoms']}
            
            CRITICAL: You MUST respond with ONLY valid JSON. No explanations, no markdown, no additional text.
            
            Required JSON format (copy exactly, replacing values):
            {{
              "severity_assessment": "high",
              "primary_symptoms": ["symptom1", "symptom2"],
              "red_flags": ["flag1", "flag2"],
              "differential_diagnosis": ["condition1", "condition2"],
              "urgency_indicators": ["indicator1", "indicator2"]
            }}
            
            Rules:
            - severity_assessment: Must be exactly one of: low, moderate, high, critical
            - All arrays must contain strings
            - Use proper JSON syntax with double quotes
            
            Respond with JSON only - no other text.
            """
            
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            analysis = json.loads(completion.choices[0].message.content)
            # Update state using the custom reducer
            state["symptom_analysis"] = analysis
            logger.info(f"✅ Symptom analysis complete: {analysis.get('severity_assessment', 'unknown')} severity")
            
        except Exception as e:
            logger.error(f"❌ Symptom analyzer failed: {e}")
            state["symptom_analysis"] = {"error": str(e), "severity_assessment": "moderate"}
        
        return state
    
    def _history_evaluator_agent(self, state: TriageState) -> TriageState:
        """
        Evaluate patient medical history and risk factors.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with history evaluation
        """
        logger.info(f"🔍 History Evaluator: Analyzing patient history")
        
        try:
            prompt = f"""
            You are a medical history evaluator. Analyze the patient's medical history and risk factors.
            
            Patient Symptoms: {state['symptoms']}
            Patient History: {state['patient_history']}
            
            CRITICAL: You MUST respond with ONLY valid JSON. No explanations, no markdown, no additional text.
            
            Required JSON format (copy exactly, replacing values):
            {{
              "risk_factors": ["factor1", "factor2"],
              "comorbidities": ["condition1", "condition2"],
              "medication_interactions": ["interaction1", "interaction2"],
              "historical_patterns": ["pattern1", "pattern2"],
              "risk_stratification": "moderate"
            }}
            
            Rules:
            - risk_stratification: Must be exactly one of: low, moderate, high, unknown
            - All arrays must contain strings
            - Use proper JSON syntax with double quotes
            
            Respond with JSON only - no other text.
            """
            
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            evaluation = json.loads(completion.choices[0].message.content)
            # Update state using the custom reducer
            state["history_evaluation"] = evaluation
            logger.info(f"✅ History evaluation complete: {evaluation.get('risk_stratification', 'unknown')} risk")
            
        except Exception as e:
            logger.error(f"❌ History evaluator failed: {e}")
            state["history_evaluation"] = {"error": str(e), "risk_stratification": "moderate"}
        
        return state
    
    def _guidelines_checker_agent(self, state: TriageState) -> TriageState:
        """
        Check against NHS triage guidelines and protocols.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with guidelines check
        """
        logger.info(f"🔍 Guidelines Checker: Validating against NHS protocols")
        
        try:
            prompt = f"""
            You are an NHS triage guidelines specialist. Evaluate the case against NHS triage protocols.
            
            Patient Symptoms: {state['symptoms']}
            Symptom Analysis: {state.get('symptom_analysis', {})}
            
            CRITICAL: You MUST respond with ONLY valid JSON. No explanations, no markdown, no additional text.
            
            Required JSON format (copy exactly, replacing values):
            {{
              "nhs_category_recommendation": "ORANGE",
              "protocol_compliance": true,
              "guideline_references": ["guideline1", "guideline2"],
              "special_considerations": ["consideration1", "consideration2"],
              "escalation_criteria": ["criteria1", "criteria2"]
            }}
            
            Rules:
            - nhs_category_recommendation: Must be exactly one of: RED, ORANGE, YELLOW, GREEN, BLUE
            - protocol_compliance: Must be boolean true or false
            - All arrays must contain strings
            - Use proper JSON syntax with double quotes
            
            Respond with JSON only - no other text.
            """
            
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            
            guidelines = json.loads(completion.choices[0].message.content)
            # Update state using the custom reducer
            state["guidelines_check"] = guidelines
            logger.info(f"✅ Guidelines check complete: {guidelines.get('nhs_category_recommendation', 'unknown')} recommended")
            
        except Exception as e:
            logger.error(f"❌ Guidelines checker failed: {e}")
            state["guidelines_check"] = {"error": str(e), "nhs_category_recommendation": "YELLOW"}
        
        return state
    
    def _operations_analyst_agent(self, state: TriageState) -> TriageState:
        """
        Analyze current hospital operational metrics and capacity.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with operations analysis
        """
        logger.info(f"🔍 Operations Analyst: Analyzing hospital capacity")
        
        try:
            prompt = f"""
            You are a hospital operations analyst. Analyze current operational conditions and their impact on triage decisions.
            
            Operational Context: {state['operational_context']}
            Patient Symptoms: {state['symptoms']}
            
            CRITICAL: You MUST respond with ONLY valid JSON. No explanations, no markdown, no additional text.
            
            Required JSON format (copy exactly, replacing values):
            {{
              "capacity_status": "moderate",
              "resource_availability": ["resource1", "resource2"],
              "wait_time_impact": "minimal",
              "throughput_considerations": ["consideration1", "consideration2"],
              "operational_recommendations": ["recommendation1", "recommendation2"]
            }}
            
            Rules:
            - capacity_status: Must be one of: low, moderate, high, critical
            - wait_time_impact: Must be one of: minimal, moderate, significant, severe
            - All arrays must contain strings
            - Use proper JSON syntax with double quotes
            
            Respond with JSON only - no other text.
            """
            
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            operations = json.loads(completion.choices[0].message.content)
            # Update state using the custom reducer
            state["operations_analysis"] = operations
            logger.info(f"✅ Operations analysis complete: {operations.get('capacity_status', 'unknown')} capacity")
            
        except Exception as e:
            logger.error(f"❌ Operations analyst failed: {e}")
            state["operations_analysis"] = {"error": str(e), "capacity_status": "normal"}
        
        return state
    
    def _trends_analyzer_agent(self, state: TriageState) -> TriageState:
        """
        Analyze patterns and trends in patient flow and outcomes.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with trends analysis
        """
        logger.info(f"🔍 Trends Analyzer: Analyzing patient flow patterns")
        
        try:
            # Get recent triage data if available
            recent_trends = "No trend data available"
            if self.nhs_metrics:
                try:
                    metrics = self.nhs_metrics.calculate_metrics()
                    triage_dist = metrics.get('triage_category_distribution', {})
                    recent_trends = f"Recent triage distribution: {triage_dist}"
                except:
                    pass
            
            prompt = f"""
            You are a healthcare trends analyst. Analyze patterns and trends relevant to this triage case.
            
            Patient Symptoms: {state['symptoms']}
            Recent Trends: {recent_trends}
            Operational Context: {state['operational_context']}
            
            CRITICAL: You MUST respond with ONLY valid JSON. No explanations, no markdown, no additional text.
            
            Required JSON format (copy exactly, replacing values):
            {{
              "pattern_recognition": ["pattern1", "pattern2"],
              "seasonal_factors": ["factor1", "factor2"],
              "population_trends": ["trend1", "trend2"],
              "outcome_predictions": ["prediction1", "prediction2"],
              "trend_based_recommendations": ["recommendation1", "recommendation2"]
            }}
            
            Rules:
            - All fields must be arrays containing strings
            - Use proper JSON syntax with double quotes
            - If no data available, use empty arrays []
            
            Respond with JSON only - no other text.
            """
            
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            trends = json.loads(completion.choices[0].message.content)
            # Update state using the custom reducer
            state["trends_analysis"] = trends
            logger.info(f"✅ Trends analysis complete")
            
        except Exception as e:
            logger.error(f"❌ Trends analyzer failed: {e}")
            state["trends_analysis"] = {"error": str(e), "pattern_recognition": "no patterns identified"}
        
        return state
    
    def _finalizer_agent(self, state: TriageState) -> TriageState:
        """
        Combine all agent outputs into final triage decision.
        
        Args:
            state: Current workflow state with all agent analyses
            
        Returns:
            Updated state with final decision
        """
        logger.info(f"🔍 Finalizer: Combining all agent analyses")
        
        # 🔍 DEBUG: Log all agent inputs and outputs
        logger.info(f"🔍 DEBUG: === AGENT INPUT/OUTPUT VALIDATION ===")
        logger.info(f"🔍 DEBUG: Patient symptoms: {state['symptoms'][:100]}...")
        logger.info(f"🔍 DEBUG: Operational context: {state['operational_context'][:100]}...")
        logger.info(f"🔍 DEBUG: Patient history: {state['patient_history'][:100]}...")
        
        try:
            # Compile all agent outputs - handle list format from Annotated fields
            agent_outputs = {}
            
            # Safely extract the latest analysis from each agent's results list
            for field_name in ["symptom_analysis", "history_evaluation", "guidelines_check", "operations_analysis", "trends_analysis"]:
                field_data = state.get(field_name, [])
                if isinstance(field_data, list) and len(field_data) > 0:
                    agent_outputs[field_name] = field_data[-1]
                elif isinstance(field_data, dict):
                    agent_outputs[field_name] = field_data
                else:
                    agent_outputs[field_name] = {"error": "No analysis available", "status": "missing"}
                
                # 🔍 DEBUG: Log each agent's output
                logger.info(f"🔍 DEBUG: {field_name} output: {json.dumps(agent_outputs[field_name], indent=2)[:200]}...")
            
            prompt = f"""
            You are the final decision maker for a multi-agent triage system. Combine all agent analyses into a final triage decision.
            
            Patient Symptoms: {state['symptoms']}
            
            Agent Analyses:
            {json.dumps(agent_outputs, indent=2)}
            
            Based on all agent inputs, provide your final triage decision in JSON format with:
            - triage_category: Final NHS triage category (RED/ORANGE/YELLOW/GREEN/BLUE)
            - priority_score: Priority score (1-5, where 1 is highest priority)
            - confidence: Confidence level (0.0-1.0)
            - reasoning: Detailed reasoning combining all agent inputs
            - wait_time: Expected wait time description
            - consensus_factors: Key factors that led to consensus
            - dissenting_opinions: Any conflicting agent recommendations
            
            Ensure the triage_category is one of: RED, ORANGE, YELLOW, GREEN, BLUE
            Respond only with valid JSON.
            """
            
            # Use strict JSON formatting
            api_params = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "max_tokens": 800
            }
            
            # Add JSON mode for supported models
            if "gpt" in self.model_name.lower() or "claude" in self.model_name.lower():
                api_params["response_format"] = {"type": "json_object"}
            
            completion = self.client.chat.completions.create(**api_params)
            response_content = completion.choices[0].message.content
            
            # Use JSON handler for parsing and validation
            json_result = self.json_handler.process_response(response_content)
            
            if json_result.quality == ResponseQuality.FAILED or json_result.data is None:
                error_msg = f"Multi-agent JSON processing failed: {'; '.join(json_result.errors)}"
                logger.error(f"❌ {error_msg}")
                logger.error(f"🚨 STRICT MODE: No fallback - failing fast for debugging")
                logger.error(f"Raw response: {response_content[:300]}...")
                raise ValueError(error_msg)
            
            logger.info(f"✅ Multi-agent JSON processed (Quality: {json_result.quality.value}, Time: {json_result.processing_time_ms:.1f}ms)")
            if json_result.warnings:
                for warning in json_result.warnings:
                    logger.warning(f"⚠️  {warning}")
            
            final_decision = json_result.data
            
            # Ensure all required fields are present with defaults
            final_decision.setdefault("priority_score", self._category_to_priority(final_decision["triage_category"]))
            final_decision.setdefault("confidence", 0.8)
            final_decision.setdefault("reasoning", "Multi-agent consensus decision")
            final_decision.setdefault("wait_time", "Based on current capacity")
            final_decision.setdefault("consensus_factors", "Agent consensus analysis")
            final_decision.setdefault("dissenting_opinions", "None identified")
            
            state["final_decision"] = final_decision
            
            # 🔍 DEBUG: Log final decision details
            logger.info(f"🔍 DEBUG: === FINAL AGENT DECISION ===")
            logger.info(f"🔍 DEBUG: Triage category: {final_decision['triage_category']}")
            logger.info(f"🔍 DEBUG: Priority score: {final_decision['priority_score']}")
            logger.info(f"🔍 DEBUG: Confidence: {final_decision['confidence']}")
            logger.info(f"🔍 DEBUG: Wait time: '{final_decision['wait_time']}'")
            logger.info(f"🔍 DEBUG: Reasoning: {final_decision['reasoning'][:150]}...")
            logger.info(f"🔍 DEBUG: Consensus factors: {final_decision.get('consensus_factors', 'N/A')}")
            
            logger.info(f"✅ Final decision: {final_decision['triage_category']} (Priority {final_decision['priority_score']})")
            
        except Exception as e:
            logger.error(f"❌ Finalizer failed: {e}")
            # Fallback decision
            state["final_decision"] = {
                "triage_category": "YELLOW",
                "priority_score": 3,
                "confidence": 0.5,
                "reasoning": f"Multi-agent system error, fallback decision: {str(e)}",
                "wait_time": "Standard wait time"
            }
        
        return state
    
    def _category_to_priority(self, category: str) -> int:
        """
        Convert triage category to priority score.
        
        Args:
            category: Triage category
            
        Returns:
            Priority score (1-5)
        """
        mapping = {
            "RED": 1,
            "ORANGE": 2,
            "YELLOW": 3,
            "GREEN": 4,
            "BLUE": 5
        }
        return mapping.get(category, 3)
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about configured agents.
        
        Returns:
            Dict containing agent configuration and status
        """
        return {
            "system_type": "Multi-Agent LLM Triage",
            "implementation_status": "Fully Implemented" if LANGGRAPH_AVAILABLE else "LangGraph Not Available",
            "agent_config": self.agent_config,
            "langgraph_enabled": LANGGRAPH_AVAILABLE,
            "workflow_initialized": self.workflow is not None,
            "agents": [
                "SymptomAnalyzer",
                "HistoryEvaluator", 
                "GuidelinesChecker",
                "OperationsAnalyst",
                "TrendsAnalyzer",
                "Finalizer"
            ],
            "fallback_mode": "Single Agent" if not LANGGRAPH_AVAILABLE else "None"
        }
    
    # JSON validation now handled by TriageJSONHandler