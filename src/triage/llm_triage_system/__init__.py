"""LLM Triage System Package

This package provides LLM-based triage systems with support for:
- Single-agent triage (SingleLLMTriage)
- Multi-agent triage with LangGraph (MixtureLLMTriage) - placeholder
- Base class for custom implementations (BaseLLMTriageSystem)
"""

from .single_llm_triage import SingleLLMTriage
from .mixture_llm_triage import MixtureLLMTriage
from .base_llm_triage import BaseLLMTriageSystem

# Backward compatibility (deprecated)
from .llm_triage_system import LLMTriageSystem

__all__ = ['SingleLLMTriage', 'MixtureLLMTriage', 'BaseLLMTriageSystem', 'LLMTriageSystem']