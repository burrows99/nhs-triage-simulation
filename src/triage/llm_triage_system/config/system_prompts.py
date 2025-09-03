"""NHS UK Triage Guidelines System Prompts for LLM Triage System

This module contains comprehensive NHS triage guidelines and system prompts
for use in the LLM-based triage system to ensure clinical accuracy and
compliance with UK medical standards.
"""

# Simplified NHS Triage Categories for NHS-trained model
NHS_TRIAGE_CATEGORIES = """
MTS Categories (Priority 1-5):
- RED (1): Immediate - Life-threatening
- ORANGE (2): Very Urgent - 1-2 hours  
- YELLOW (3): Urgent - 2-4 hours
- GREEN (4): Standard - 4-6 hours
- BLUE (5): Non-urgent - Self-care/routine
"""

# Optimized Clinical Assessment Prompt for NHS-trained model
CLINICAL_ASSESSMENT_PROMPT = """
You are a UK medical triage assistant. Apply your NHS training to assess patients using Manchester Triage System protocols.

Prioritize patient safety and use clinical judgment for uncertain cases.
"""

# Wait Time Estimation Guidelines
WAIT_TIME_GUIDELINES = {
    "RED": "Immediate (0 min)",
    "ORANGE": "1-2 hours", 
    "YELLOW": "2-4 hours",
    "GREEN": "4-6 hours",
    "BLUE": "Self-care or routine appointment"
}

# Simplified Confidence Guidelines
CONFIDENCE_GUIDELINES = """
Confidence (0.0-1.0): Rate your certainty in the triage decision.
High (0.8-1.0) for clear cases, Low (0.0-0.4) for uncertain cases.
"""

def get_system_prompt() -> str:
    """Get the optimized system prompt for NHS-trained model.
    
    Returns:
        str: Concise system prompt focusing on output format
    """
    return f"""{CLINICAL_ASSESSMENT_PROMPT}

{NHS_TRIAGE_CATEGORIES}

{CONFIDENCE_GUIDELINES}

Provide accurate triage assessments using your NHS training.
"""

def get_triage_categories() -> list:
    """Get valid NHS triage categories.
    
    Returns:
        list: Valid triage category strings
    """
    return ["RED", "ORANGE", "YELLOW", "GREEN", "BLUE"]

def get_wait_time_for_category(category: str) -> str:
    """Get expected wait time for triage category.
    
    Args:
        category (str): Triage category
        
    Returns:
        str: Expected wait time description
    """
    return WAIT_TIME_GUIDELINES.get(category, "Unknown category")