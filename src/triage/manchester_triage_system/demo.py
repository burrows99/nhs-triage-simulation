#!/usr/bin/env python3
"""FMTS Demonstration - Complete Implementation of Research Paper

This demonstration shows the complete FMTS system following the exact approach
described in the research paper by Cremeens & Khorasani (2014).

Usage:
    python demo.py

Reference: https://www.researchgate.net/publication/286737453_FMTS_A_fuzzy_implementation_of_the_Manchester_triage_system
"""

from manchester_triage_system import (
    ManchesterTriageSystem,
    ZMouseFuzzyInterface,
    KnowledgeAcquisitionSystem,
    PAPER_INFO,
    CAPABILITIES
)


def main():
    """Main demonstration function following the exact FMTS paper approach"""
    
    # Initialize complete FMTS system as described in the paper
    # Reference: Paper describes both decision aid and knowledge acquisition components
    mts = ManchesterTriageSystem()
    knowledge_system = KnowledgeAcquisitionSystem()
    
    print("FMTS - Fuzzy Manchester Triage System")
    print("Complete Implementation of Research Paper (2014)")
    print(f"Authors: {', '.join(PAPER_INFO['authors'])}")
    print(f"Institution: {PAPER_INFO['institution']}")
    print("=" * 60)
    print("\n📋 FMTS Paper Components Implemented:")
    for feature in CAPABILITIES['features']:
        print(f"✅ {feature}")
    print("=" * 60)
    
    # Test cases based on FMTS paper examples and methodology
    # Reference: Paper Figure 1 shows shortness of breath flowchart example
    test_cases = [
        {
            'reason': 'chest_pain',
            'symptoms': {
                'severe_pain': 'very_severe',
                'crushing_sensation': 'severe',
                'radiation': 'moderate',
                'breathless': 'mild',
                'sweating': 'severe'
            }
        },
        {
            'reason': 'shortness_of_breath', 
            'symptoms': {
                'difficulty_breathing': 'moderate',
                'wheeze': 'mild',
                'unable_to_speak': 'none',
                'cyanosis': 'none',
                'exhaustion': 'moderate'
            }
        },
        {
            'reason': 'headache',
            'symptoms': {
                'pain_severity': 'mild',
                'sudden_onset': 'none', 
                'neck_stiffness': 'none',
                'photophobia': 'mild',
                'confusion': 'none'
            }
        }
    ]
    
    # Process each case using FMTS decision aid system
    # Reference: Paper describes "decision aid system for the ER nurses to properly 
    # categorize patients based on their symptoms"
    for i, case in enumerate(test_cases, 1):
        print(f"\n🏥 Patient {i} - Presenting with: {case['reason'].replace('_', ' ').title()}")
        print("-" * 50)
        
        # Use the FMTS triage function (Paper: decision aid interface)
        result = mts.triage_patient(case['reason'], case['symptoms'])
        
        print(f"📊 Flowchart Used: {result['flowchart_used']}")
        print(f"🚨 Triage Category: {result['triage_category']}")
        print(f"⏰ Wait Time: {result['wait_time']}")
        print(f"🔢 Fuzzy Score: {result['fuzzy_score']:.2f}")
        print(f"💊 Symptoms Processed: {result['symptoms_processed']}")
    
    # System Statistics
    print(f"\n📈 System Statistics:")
    print(f"Available Flowcharts: {len(mts.flowcharts)} total")
    available_flowcharts = mts.flowcharts['flowchart_id'].tolist()
    print(f"Sample flowcharts: {available_flowcharts[:10]}...")  # Show first 10
    
    # Demonstrate Knowledge Acquisition Component (Paper Section I)
    print("\n🔬 Knowledge Acquisition Component Demo:")
    print("Reference: FMTS paper Section I - Expert configuration interface")
    
    # Start expert session
    session_id = knowledge_system.start_expert_session("Dr_Smith_001")
    print(f"✅ Expert session started: {session_id}")
    
    # Demonstrate Z-mouse interface
    zmouse_result = knowledge_system.zmouse.z_mouse_input("chest_pain", "severe", confidence=0.9)
    print(f"🖱️  Z-mouse input recorded: {zmouse_result['symptom']} = {zmouse_result['linguistic_value']} (confidence: {zmouse_result['confidence']})")
    
    # Create fuzzy mark
    fuzzy_mark = knowledge_system.zmouse.create_fuzzy_mark("critical", (0, 10), [(0, 0), (8, 1), (10, 1)])
    print(f"📍 Fuzzy mark created for term: {fuzzy_mark['term']}")
    
    # Add expert rule
    rule_added = knowledge_system.add_expert_rule(
        session_id,
        "Emergency cardiac condition rule",
        [
            {"symptom": "severe_pain", "value": "very_severe"},
            {"symptom": "crushing_sensation", "value": "severe"}
        ],
        "red"
    )
    print(f"📝 Expert rule added: {rule_added}")
    
    # End expert session
    session_summary = knowledge_system.end_expert_session(session_id)
    print(f"📋 Expert session completed. Summary: {session_summary}")
    
    # Show knowledge system statistics
    knowledge_stats = knowledge_system.get_system_statistics()
    print(f"\n🧠 Knowledge System Statistics:")
    print(f"Total Expert Sessions: {knowledge_stats['total_sessions']}")
    print(f"Expert Rules Created: {knowledge_stats['total_rules']}")
    print(f"Configured Terms: {knowledge_stats['configured_terms']}")
    print(f"Fuzzy Marks: {knowledge_stats['fuzzy_marks']}")
    
    print("\n🎯 FMTS Implementation Complete!")
    print("All major components from the research paper have been implemented.")
    print(f"\nPaper Reference: {PAPER_INFO['url']}")
    
    # Export system configuration for demonstration
    print("\n💾 Exporting system configuration...")
    config = knowledge_system.export_expert_knowledge()
    print(f"Configuration exported with {len(mts.flowcharts)} flowcharts")
    print(f"Expert knowledge includes {len(config['rule_base'])} rules")


def demonstrate_individual_components():
    """Demonstrate individual components of the FMTS system"""
    
    print("\n" + "=" * 60)
    print("🔧 Individual Component Demonstration")
    print("=" * 60)
    
    # Import individual components
    from manchester_triage_system import (
        ManchesterTriageSystem,
        ZMouseFuzzyInterface,
        KnowledgeAcquisitionSystem
    )
    
    # Demonstrate ManchesterTriageSystem
    print("\n1️⃣ Manchester Triage System (Core)")
    mts = ManchesterTriageSystem()
    print(f"   Flowcharts loaded: {len(mts.flowcharts)}")
    print(f"   Fuzzy rules created: {len(mts.fuzzy_rules)}")
    
    # Demonstrate ZMouseFuzzyInterface
    print("\n2️⃣ Z-Mouse Fuzzy Interface")
    zmouse = ZMouseFuzzyInterface()
    mark = zmouse.create_fuzzy_mark("test_term", (0, 10), [(0, 0), (5, 1), (10, 0)])
    print(f"   Fuzzy mark created: {mark['term']}")
    print(f"   Available terms: {len(zmouse.get_linguistic_terms())}")
    
    # Demonstrate KnowledgeAcquisitionSystem
    print("\n3️⃣ Knowledge Acquisition System")
    kas = KnowledgeAcquisitionSystem()
    session = kas.start_expert_session("demo_expert")
    print(f"   Expert session started: {session}")
    
    rule_added = kas.add_expert_rule(
        session,
        "Demo rule",
        [{"symptom": "pain", "value": "severe"}],
        "yellow"
    )
    print(f"   Expert rule added: {rule_added}")
    
    stats = kas.get_system_statistics()
    print(f"   System statistics: {stats}")


if __name__ == "__main__":
    """Run the complete FMTS demonstration"""
    try:
        main()
        demonstrate_individual_components()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demonstration interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error during demonstration: {e}")
        print("Please ensure all dependencies are installed:")
        print("pip install pandas numpy scikit-fuzzy scikit-learn")
    else:
        print("\n\n✨ Demonstration completed successfully!")