# NHS Triage Simulation Framework

## Reducing Patient Wait Times in NHS Triage Using a Mixture-of-Agents Simulation Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![SimPy](https://img.shields.io/badge/SimPy-4.0+-green.svg)](https://simpy.readthedocs.io/)

**Research Repository for MSc Dissertation - University of Surrey**  
**Author:** Raunak Burrows  
**Supervisor:** Dr. Xiatian Zhu  
**September 2025**

---

## 📖 Abstract

This repository contains the complete implementation of a novel Mixture-of-Agents (MoA) framework for optimizing patient routing in NHS emergency departments following initial triage assessment. The research addresses a critical gap in healthcare operations by focusing on post-triage routing optimization, demonstrating **58% reduction in doctor wait times** while maintaining **94.6% clinical appropriateness** and reducing demographic bias.

### Key Achievements
- **58.2% reduction** in doctor wait times (204.3 → 85.3 minutes)
- **40.5% reduction** in MRI wait times  
- **60.8% reduction** in ultrasound wait times
- **19.3% improvement** in resource utilization
- **Bias reduction**: Demographic parity gap from 15.9% to 1.2%
- **Clinical safety maintained** at 94.6% appropriateness

---

## 🎯 Problem Statement

Emergency departments across the NHS face unprecedented pressure:
- Only **76.4%** of A&E patients seen within 4 hours (Q4 2023-24)
- Over **35,000** patients wait more than 12 hours
- Manchester Triage System (MTS) used in **90%** of UK EDs focuses only on initial classification
- **Critical gap**: No intelligent post-triage routing optimization

---

## 🧠 Methodology Overview

### Three-Approach Comparison
1. **Rule-based (Baseline)**: Traditional MTS sequential physician-first protocol
2. **Single-agent**: GPT-OSS-20B model with clinical prompting  
3. **Multi-agent (MoA)**: Specialized domain agents with collaborative decision-making

### Technical Architecture
- **Simulation Framework**: SimPy discrete-event simulation
- **Dataset**: 10,000 synthetic FHIR R4 HL7 UK Core compliant patient journeys
- **Validation**: 30 independent simulation runs, 95% confidence intervals
- **Bias Analysis**: Intersectional demographic evaluation across gender-ethnicity combinations

---

## 🚀 Getting Started

### Prerequisites
```bash
Python 3.8+
SimPy 4.0+
NumPy
Pandas
Matplotlib
Seaborn
FHIR-py
Synthea (for dataset generation)
```

### Installation
```bash
git clone https://github.com/burrows99/nhs-triage-simulation.git
cd nhs-triage-simulation
pip install -r requirements.txt
```

### Quick Start
```bash
# Run basic simulation comparison
python main_simulation.py

# Generate synthetic dataset
python scripts/generate_synthetic_data.py

# Run bias analysis
python analysis/bias_evaluation.py

# Generate performance reports
python analysis/performance_metrics.py
```

---

## 📁 Repository Structure

```
nhs-triage-simulation/
├── README.md
├── requirements.txt
├── main_simulation.py              # Main simulation runner
├── config/
│   ├── simulation_params.yml      # Simulation parameters
│   └── nhs_demographics.yml       # NHS demographic distributions
├── src/
│   ├── simulation/
│   │   ├── simpy_environment.py    # Core SimPy simulation
│   │   ├── patient_generator.py    # Patient arrival modeling
│   │   ├── triage_module.py        # MTS implementation
│   │   └── resource_manager.py     # Resource allocation logic
│   ├── routing/
│   │   ├── rule_based.py          # Traditional routing
│   │   ├── single_agent.py        # Single LLM routing
│   │   └── multi_agent.py         # MoA routing framework
│   ├── agents/
│   │   ├── neurological_agent.py  # Neurology specialist
│   │   ├── cardiac_agent.py       # Cardiology specialist
│   │   ├── abdominal_agent.py     # Abdominal specialist
│   │   └── aggregator.py          # Decision aggregator
│   └── utils/
│       ├── fhir_parser.py         # FHIR data handling
│       └── metrics_calculator.py  # Performance metrics
├── data/
│   ├── synthetic/                 # Generated synthetic data
│   └── validation/               # Expert validation data
├── analysis/
│   ├── bias_evaluation.py        # Demographic bias analysis
│   ├── performance_metrics.py    # Wait time & utilization analysis
│   └── clinical_validation.py    # Expert review validation
├── scripts/
│   ├── generate_synthetic_data.py # Synthea data generation
│   └── run_experiments.py        # Batch experiment runner
├── results/
│   ├── figures/                  # Generated visualizations
│   └── reports/                  # Performance analysis reports
├── tests/
│   ├── test_simulation.py        # Unit tests
│   └── test_routing.py           # Routing algorithm tests
└── docs/
    ├── methodology.md            # Detailed methodology
    ├── api_reference.md          # Code documentation
    └── deployment_guide.md       # NHS deployment guidelines
```

---

## 🧪 Core Components

### 1. Simulation Environment (`src/simulation/`)
- **SimPy-based** discrete-event simulation
- **Poisson arrival process** (λ=12 patients/hour)
- **M/M/c and M/G/1** queuing models
- **Resource contention** modeling

### 2. Routing Strategies (`src/routing/`)
- **Rule-based**: Traditional sequential consultation pathway
- **Single-agent**: LLM-powered routing decisions
- **Multi-agent**: Collaborative specialist agents with aggregator

### 3. Agent Framework (`src/agents/`)
- **Neurological Agent**: Stroke assessment, MRI indications
- **Cardiac Agent**: Chest pain protocols, coronary syndromes
- **Abdominal Agent**: Ultrasound requirements, surgical evaluation
- **Aggregator**: Synthesizes recommendations, applies safety thresholds

### 4. Bias Analysis (`analysis/bias_evaluation.py`)
- **Intersectional analysis** across demographic combinations
- **Demographic parity difference** calculation: δ_g = |α_g - α_avg|
- **Counterfactual testing** methodology

---

## 📊 Key Results

### Performance Improvements (MoA vs Rule-based)
| Metric | Rule-based | MoA | Improvement |
|--------|------------|-----|-------------|
| Doctor Wait Time | 204.3 min | 85.3 min | **-58.2%** |
| MRI Wait Time | 42.2 min | 25.1 min | **-40.5%** |
| Ultrasound Wait Time | 158.7 min | 62.2 min | **-60.8%** |
| Bed Wait Time | 166.2 min | 45.9 min | **-72.4%** |
| Resource Utilization | 76% | 91% | **+19.3%** |

### Clinical Accuracy by Demographics
| Demographic | Rule-based | Single-agent | MoA |
|-------------|------------|--------------|-----|
| White Male | 84.3% | 87.6% | **94.2%** |
| Black Male | 78.2% | 76.5% | **92.4%** |
| Asian Female | 79.1% | 78.6% | **95.2%** |

### Bias Reduction
- **MoA demographic parity gap**: 1.2%
- **Single-agent demographic parity gap**: 15.9%
- **Overall clinical appropriateness**: 94.6% maintained

---

## 🔬 Experiments and Validation

### Running Full Experiments
```bash
# Complete experimental suite (30 runs per scenario)
python scripts/run_experiments.py --all

# Specific routing comparison
python scripts/run_experiments.py --routing moa --runs 30

# Bias analysis across demographics
python analysis/bias_evaluation.py --intersectional

# Generate performance visualizations
python analysis/performance_metrics.py --visualize
```

### Validation Protocol
1. **Statistical Validation**: 30 independent runs, 95% confidence intervals
2. **Clinical Validation**: Expert review of 237 diverse cases
3. **Bias Validation**: Intersectional analysis across all demographic combinations
4. **Safety Validation**: Confidence thresholds and audit trail verification

---

## 📈 Usage Examples

### Basic Simulation Run
```python
from src.simulation.simpy_environment import NHSEmergencySimulation
from src.routing.multi_agent import MoARoutingSystem

# Initialize simulation
sim = NHSEmergencySimulation(duration=30*24*60)  # 30 days
routing = MoARoutingSystem()

# Run simulation
results = sim.run(routing_system=routing)

# Analyze results
print(f"Average doctor wait: {results.avg_doctor_wait:.1f} minutes")
print(f"Resource utilization: {results.resource_utilization:.1%}")
```

### Demographic Bias Analysis
```python
from analysis.bias_evaluation import BiasAnalyzer

# Initialize bias analyzer
analyzer = BiasAnalyzer()

# Run intersectional analysis
bias_results = analyzer.evaluate_demographic_parity(
    routing_systems=['rule_based', 'single_agent', 'moa'],
    demographics=['gender', 'ethnicity']
)

# Generate bias report
analyzer.generate_report(bias_results)
```

### Custom Agent Configuration
```python
from src.agents.neurological_agent import NeurologicalAgent
from src.agents.aggregator import DecisionAggregator

# Configure specialist agents
neuro_agent = NeurologicalAgent(confidence_threshold=0.7)
cardiac_agent = CardiacAgent(confidence_threshold=0.7)

# Initialize aggregator
aggregator = DecisionAggregator(
    agents=[neuro_agent, cardiac_agent],
    safety_threshold=0.7
)
```

---

## 📋 Configuration

### Simulation Parameters (`config/simulation_params.yml`)
```yaml
simulation:
  duration_days: 30
  patient_arrival_rate: 12  # patients per hour
  random_seed: 42

resources:
  doctors: 10
  mri_machines: 2
  ultrasound_devices: 3
  beds: 50

service_times:
  triage: 
    distribution: lognormal
    mu: 8
    sigma: 2
  physician_consultation:
    distribution: lognormal
    mu: 15
    sigma: 5
```

### NHS Demographics (`config/nhs_demographics.yml`)
```yaml
demographics:
  ethnicity:
    white: 0.805
    asian: 0.087
    black: 0.032
    mixed: 0.029
    other: 0.047
  gender:
    male: 0.488
    female: 0.512
  age_distribution:
    mean: 43.1
    std: 18.0
```

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/

# Specific test suites
python -m pytest tests/test_simulation.py -v
python -m pytest tests/test_routing.py -v

# Coverage report
python -m pytest --cov=src tests/
```

---

## 🚀 Deployment Considerations

### NHS Compatibility Requirements
- **GDPR Compliance**: Local deployment, no external data transmission
- **FHIR Integration**: Complete HL7 FHIR R4 UK Core compatibility
- **Audit Trails**: Comprehensive decision logging for clinical governance
- **Clinical Safety**: Multiple validation layers and confidence thresholds

### Cost-Effectiveness
- **Computational Cost**: £0.04 per consultation
- **Infrastructure**: Compatible with existing NHS IT systems
- **Scalability**: Cloud-ready architecture for trust-wide deployment

---

## 📚 Academic Publications

**Primary Publication:**
- Burrows, R. (2025). "Reducing Patient Wait Times in NHS Triage Using a Mixture-of-Agents Simulation Framework." *MSc Dissertation, University of Surrey.*

**Related Work:**
- Manchester Triage System implementation studies
- Healthcare operations research methodologies  
- AI bias evaluation in clinical settings
- Mixture-of-Agents collaborative decision-making

---

## 🤝 Contributing

We welcome contributions to improve the simulation framework:

1. **Fork the repository**
2. **Create feature branch** (`git checkout -b feature/improvement`)  
3. **Commit changes** (`git commit -am 'Add new feature'`)
4. **Push to branch** (`git push origin feature/improvement`)
5. **Create Pull Request**

### Contribution Areas
- Additional specialist agents (pediatric, orthopedic, etc.)
- Enhanced bias mitigation techniques
- Real-world data integration capabilities
- Performance optimization
- Documentation improvements

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Contact

**Raunak Burrows**  
MSc Artificial Intelligence, University of Surrey  
📧 Email: [Contact Information]  
🔗 LinkedIn: [LinkedIn Profile]  
🐙 GitHub: [@burrows99](https://github.com/burrows99)

**Supervisor:**  
Dr. Xiatian Zhu  
University of Surrey

---

## 🙏 Acknowledgments

- **University of Surrey** - Academic supervision and resources
- **NHS England** - Operational data and statistics for validation
- **SimPy Community** - Discrete-event simulation framework
- **Synthea Project** - FHIR-compliant synthetic data generation
- **Manchester Triage Group** - Established triage protocols

---

## 📊 Performance Monitoring

Track the latest simulation results and performance metrics:

- **Real-time Dashboard**: [Link to visualization dashboard]
- **Performance Reports**: Generated in `results/reports/`
- **Bias Analysis**: Updated intersectional analysis in `analysis/`

---

## 🔍 Citation

If you use this code or methodology in your research, please cite:

```bibtex
@mastersthesis{burrows2025nhs,
  title={Reducing Patient Wait Times in NHS Triage Using a Mixture-of-Agents Simulation Framework},
  author={Burrows, Raunak},
  year={2025},
  school={University of Surrey},
  type={MSc Dissertation},
  note={Available at: \url{https://github.com/burrows99/nhs-triage-simulation}}
}
```

---

*This research contributes to the growing field of AI-enhanced healthcare operations, demonstrating how collaborative AI systems can improve both efficiency and equity in emergency medical care.*
