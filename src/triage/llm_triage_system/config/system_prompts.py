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

def get_full_triage_prompt(symptoms: str, operational_context: str = "") -> str:
    """Generate complete triage prompt with symptoms and operational context.
    
    Args:
        symptoms: Patient symptoms description
        operational_context: Current hospital operational status (optional)
        
    Returns:
        str: Complete prompt for LLM triage assessment
    """
    system_context = get_system_prompt()
    
    # Prepare context-specific text
    reasoning_context = ' and current hospital conditions' if operational_context else ''
    guidelines_context = ' AND the current hospital operational status' if operational_context else ''
    
    prompt = f"""{system_context}{operational_context}

Patient Presentation:
{symptoms}

Based on the NHS UK Triage Guidelines above{guidelines_context}, analyze these symptoms and provide a triage recommendation.

{_get_operational_instructions(operational_context)}

CRITICAL: You MUST respond with ONLY valid JSON. No explanations, no markdown, no additional text.

Required JSON format (copy exactly, replacing values):
{{
  "triage_category": "RED",
  "priority_score": 1,
  "confidence": 0.85,
  "reasoning": "Brief clinical explanation based on NHS guidelines{reasoning_context}",
  "wait_time": "[Calculate based on clinical severity and operational context]"
}}

Rules:
- triage_category: Must be exactly one of: RED, ORANGE, YELLOW, GREEN, BLUE
- priority_score: Must be integer 1-5 (1=RED, 2=ORANGE, 3=YELLOW, 4=GREEN, 5=BLUE)
- confidence: Must be decimal 0.0-1.0 (e.g., 0.85, not 85%)
- reasoning: String under 200 characters
- wait_time: String describing expected wait based on YOUR clinical assessment and operational analysis

Example valid responses:
{{"triage_category": "RED", "priority_score": 1, "confidence": 0.9, "reasoning": "Chest pain with severe symptoms requires immediate assessment", "wait_time": "[Your calculated wait time based on severity]"}}

{{"triage_category": "YELLOW", "priority_score": 3, "confidence": 0.7, "reasoning": "Moderate symptoms requiring urgent but not immediate care", "wait_time": "[Your calculated wait time based on clinical assessment]"}}

Respond with JSON only - no other text."""
    
    return prompt

def _get_operational_instructions(operational_context: str) -> str:
    """Get operational-specific instructions for the prompt.
    
    Args:
        operational_context: Current hospital operational status
        
    Returns:
        str: Operational instructions or empty string
    """
    if operational_context:
        return "IMPORTANT: Consider the current hospital conditions when estimating wait times. If the system is under high pressure, adjust wait time estimates accordingly while maintaining patient safety as the top priority."
    return ""

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