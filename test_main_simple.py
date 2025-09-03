#!/usr/bin/env python3
"""
Simple test of the main simulation with LLM triage system using Hugging Face API.
This bypasses file logging to avoid disk space issues.
"""

import sys
import os
import logging

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Set up simple console logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('hospital_simulation')

from src.triage.llm_triage_system.llm_triage_system import LLMTriageSystem

def test_llm_integration():
    """Test the LLM triage system integration"""
    logger.info("🚀 Testing LLM Triage System Integration")
    logger.info("=" * 50)
    
    try:
        # Initialize LLM triage system
        logger.info("🤖 Initializing LLM Triage System with Hugging Face API...")
        llm_triage = LLMTriageSystem()
        logger.info("✅ LLM Triage System initialized successfully")
        
        # Test with a sample patient
        test_symptoms = "Patient presents with severe chest pain, shortness of breath, and nausea. Pain started 20 minutes ago."
        logger.info(f"🏥 Testing triage with sample patient: {test_symptoms[:60]}...")
        
        result = llm_triage.triage_patient(test_symptoms)
        
        logger.info("📊 Triage Result:")
        logger.info(f"  Category: {result.triage_category}")
        logger.info(f"  Priority: {result.priority_score}")
        logger.info(f"  Confidence: {result.confidence:.2f}")
        logger.info(f"  Wait Time: {result.wait_time}")
        logger.info(f"  Reasoning: {result.reasoning[:100]}...")
        
        logger.info("✅ LLM Triage System integration test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_llm_integration()
    sys.exit(0 if success else 1)