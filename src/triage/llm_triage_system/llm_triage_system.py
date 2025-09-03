"""LLM Triage System - Deprecated

This module is deprecated. Use SingleLLMTriage or MixtureLLMTriage directly.
"""

# Re-export new classes for migration
from .single_llm_triage import SingleLLMTriage
from .mixture_llm_triage import MixtureLLMTriage
from .base_llm_triage import BaseLLMTriageSystem

# Deprecated - use SingleLLMTriage instead
LLMTriageSystem = SingleLLMTriage

__all__ = ['SingleLLMTriage', 'MixtureLLMTriage', 'BaseLLMTriageSystem', 'LLMTriageSystem']
    