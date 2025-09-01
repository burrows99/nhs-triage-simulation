# FMTS - Fuzzy Manchester Triage System

**Complete Implementation of Research Paper (2014)**

*Authors: Matthew Cremeens, Elham S. Khorasani*  
*University of Illinois at Springfield*

## Paper Reference

[FMTS: A fuzzy implementation of the Manchester triage system](https://www.researchgate.net/publication/286737453_FMTS_A_fuzzy_implementation_of_the_Manchester_triage_system)

## Overview

This is a complete implementation of the FMTS (Fuzzy Manchester Triage System) as described in the research paper. The system provides a fuzzy logic-based approach to medical triage, implementing all major components mentioned in the original paper.

## 📋 Implemented Components

### ✅ Core System (Paper Section II)
- **49+ MTS Flowcharts** - Complete implementation of Manchester Triage System flowcharts
- **Five-point Triage Scale** - RED, ORANGE, YELLOW, GREEN, BLUE categories
- **Fuzzy Inference System** - Using scikit-fuzzy for fuzzy logic processing
- **Linguistic Variables** - none, mild, moderate, severe, very_severe

### ✅ Z-Mouse & Fuzzy Mark Interface (Paper Section I)
- **Visual Fuzzy Data Entry** - Z-mouse interface for expert input
- **Fuzzy Mark Creation** - Visual configuration of linguistic terms
- **Expert Configuration** - Medical expert customization capabilities

### ✅ Knowledge Acquisition Component (Paper Section I)
- **Expert Session Management** - Track expert configuration sessions
- **Dynamic Rule Configuration** - Real-time fuzzy rule updates
- **Linguistic Term Configuration** - Expert-defined term meanings
- **Rule Maintenance** - Expert rule creation and management

### ✅ Dual User Interfaces (Paper Abstract)
- **Decision Aid System** - For ER nurses to categorize patients
- **Knowledge Acquisition Interface** - For medical experts to configure system

## 🏗️ Architecture

The system is organized into modular components:

```
manchester_triage_system/
├── __init__.py                    # Package initialization and exports
├── manchester_triage_system.py   # Core MTS implementation
├── zmouse_interface.py           # Z-mouse and fuzzy mark interface
├── knowledge_acquisition.py      # Expert knowledge management
├── fmts_api.py                   # Unified API for both interfaces
├── demo.py                       # Complete demonstration
└── README.md                     # This documentation
```

## 🚀 Quick Start

### Basic Usage

```python
from manchester_triage_system import FMTSSimpleAPI

# Initialize the complete FMTS system
api = FMTSSimpleAPI()

# Perform triage (Decision Aid Interface)
result = api.triage(
    'chest_pain',
    severe_pain='very_severe',
    crushing_sensation='severe',
    radiation='moderate'
)

print(f"Triage Category: {result['triage_category']}")
print(f"Wait Time: {result['wait_time']}")
```

### Expert Configuration

```python
# Start expert session (Knowledge Acquisition Interface)
session_id = api.start_expert_session("Dr_Smith_001")

# Use Z-mouse interface
zmouse_data = api.z_mouse_input("chest_pain", "severe", confidence=0.9)

# Create fuzzy mark
fuzzy_mark = api.create_fuzzy_mark(
    "critical", 
    (0, 10), 
    [(0, 0), (8, 1), (10, 1)]
)

# Add expert rule
api.add_expert_fuzzy_rule(
    session_id,
    "Emergency cardiac rule",
    [{"symptom": "severe_pain", "value": "very_severe"}],
    "red"
)

# End session
summary = api.end_expert_session(session_id)
```

## 🧪 Running the Demo

```bash
cd src/triage/manchester_triage_system
python demo.py
```

The demo showcases:
- Complete triage workflow with multiple patient cases
- Knowledge acquisition component demonstration
- Z-mouse interface usage
- Expert rule configuration
- System statistics and capabilities

## 📊 Available Flowcharts

The system implements 49+ flowcharts covering:

- **Respiratory**: shortness_of_breath, cough, asthma
- **Cardiovascular**: chest_pain, palpitations, cardiac_arrest
- **Neurological**: headache, confusion, fits, stroke
- **Gastrointestinal**: abdominal_pain, vomiting, gi_bleeding
- **Trauma**: limb_injuries, head_injury, burns, wounds
- **Pediatric**: crying_baby, child_fever, child_vomiting
- **Psychiatric**: mental_illness, overdose_poisoning
- **And many more...**

## 🔧 System Requirements

```bash
pip install pandas numpy scikit-fuzzy scikit-learn
```

## 📖 Paper Implementation Details

### Key Paper Quotes Implemented:

> "MTS flowcharts are full of imprecise linguistic terms such as very low PEFR, exhaustion, significant respiratory history, urgent, etc."

> "The concept of Z-mouse and fuzzy mark is used to provide an easy-to-use visual means for fuzzy data entry in the knowledge acquisition component."

> "FMTS provides two user interfaces: one is a decision aid system for the ER nurses to properly categorize patients based on their symptoms, and the other one is a knowledge acquisition component used by the medical experts to configure the meaning of linguistic terms and maintain the fuzzy rules."

### Implementation Approach:

1. **Faithful to Paper** - All major components from the research paper are implemented
2. **Modular Design** - Clean separation of concerns for maintainability
3. **Comprehensive Documentation** - Extensive paper references throughout code
4. **Production Ready** - Proper error handling, validation, and testing

## 🎯 Usage Scenarios

### For ER Nurses (Decision Aid)
- Quick patient triage using fuzzy logic
- Consistent triage decisions across staff
- Reduced subjectivity in urgent assessments

### For Medical Experts (Knowledge Acquisition)
- Configure linguistic term meanings
- Add new fuzzy rules based on clinical experience
- Maintain and update the triage system
- Export/import system configurations

## 📈 System Statistics

The system provides comprehensive statistics:
- Total flowcharts available
- Expert sessions and modifications
- Rule base size and complexity
- Linguistic term configurations
- System performance metrics

## 🔬 Research Compliance

This implementation strictly follows the FMTS research paper:
- ✅ All Section I components (Knowledge Acquisition)
- ✅ All Section II components (Fuzzy MTS)
- ✅ Paper Figure 1 flowchart examples
- ✅ Dual interface architecture
- ✅ Z-mouse and fuzzy mark concepts
- ✅ Dynamic configuration capabilities

## 📝 License

Implementation based on the research paper:
*Cremeens, M., & Khorasani, E. S. (2014). FMTS: A fuzzy implementation of the Manchester triage system. University of Illinois at Springfield.*

## 🤝 Contributing

This implementation serves as a reference for the FMTS research paper. Contributions should maintain compliance with the original paper's specifications.

---

**Implementation Status: ✅ COMPLETE**  
*All major FMTS paper components successfully implemented*