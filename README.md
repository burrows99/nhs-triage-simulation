# 🏥 NHS Triage Simulation Framework

### *Reducing Patient Wait Times in NHS Triage Using a Mixture-of-Agents Simulation Framework*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![SimPy](https://img.shields.io/badge/SimPy-4.0+-green.svg)](https://simpy.readthedocs.io/)

**Author:** Raunak Burrows
**Supervisor:** Dr. Xiatian Zhu — Senior Lecturer, People-Centred AI, University of Surrey
**Affiliation:** MSc Artificial Intelligence (2025), University of Surrey

---

## 📖 Abstract

This repository implements the research project *“Reducing Patient Wait Times in NHS Triage Using a Mixture-of-Agents Simulation Framework.”*
The work addresses a persistent gap in NHS emergency department (ED) operations — post-triage patient routing — by designing a **Mixture-of-Agents (MoA)** system that dynamically coordinates multiple specialist AI agents to allocate resources efficiently.

The framework achieved:

* **58.2 % reduction** in average doctor wait time (204.3 → 85.3 minutes)
* **40.5 % reduction** in MRI wait time and **60.8 %** in ultrasound wait time
* **19.3 % improvement** in resource utilisation
* **Bias reduction**: demographic parity gap improved from 15.9 % → 1.2 %
* **Clinical safety maintained** at 94.6 % appropriateness

All experiments were validated via **30 independent simulation runs (95 % CI)** and expert review on 237 synthetic cases.

---

## 🎯 Problem Context

* Only **76.4 %** of NHS A&E patients are seen within 4 hours (Q4 2023-24).
* Over **35 000** patients experience > 12-hour delays.
* The **Manchester Triage System (MTS)** — used in > 90 % of UK EDs — focuses solely on initial classification.
* Post-triage routing remains **manual, sequential, and resource-inefficient**.

The proposed MoA framework builds on MTS and fuzzy-MTS literature to enable **data-driven, context-aware routing** using collaborative AI agents.

---

## 🧠 Methodology Overview

### Comparative Framework

1. **Rule-Based (Baseline)** — traditional MTS flow: sequential physician-first protocol.
2. **Single-Agent** — GPT-OSS-20B model (with Mistral-7B tested for NHS deployment) generating routing recommendations.
3. **Multi-Agent (MoA)** — neurology, cardiology, and abdominal agents coordinated via LangGraph aggregator.

### Technical Stack

* **Simulation Core:** SimPy 4 Discrete-Event Simulation (M/M/c queues, Poisson arrivals λ = 12 patients/h)
* **Synthetic Data:** 10 000+ FHIR R4 (UK Core) compliant patients via modified Synthea workflows
* **Routing Logic:** LangGraph multi-agent collaboration layer with Ollama runtime for local LLM execution
* **Bias Framework:** intersectional demographic analysis (adapted from Lee et al., 2024)

---

## ⚙️ Installation

```bash
git clone https://github.com/burrows99/nhs-triage-simulation.git
cd nhs-triage-simulation
pip install -r requirements.txt
```

---

## 🚀 Usage

### Quick Run

```bash
python main_simulation.py
```

### Full Experiment Suite

```bash
python scripts/run_experiments.py --all
```

### Bias Analysis

```bash
python analysis/bias_evaluation.py --intersectional
```

### Performance Reports

```bash
python analysis/performance_metrics.py --visualize
```

---

## 📁 Repository Structure

```
nhs-triage-simulation/
├── main_simulation.py
├── src/
│   ├── simulation/         # SimPy environment & patient generator
│   ├── routing/            # Rule-based, Single-agent, MoA strategies
│   ├── agents/             # Specialist and aggregator agents
│   └── utils/              # FHIR parser, metrics calculator
├── analysis/               # Bias & performance analysis scripts
├── config/                 # Simulation and demographic parameters
├── data/                   # Synthetic + validation datasets
├── results/                # Figures and reports
└── docs/                   # Methodology, API, deployment guide
```

---

## 📊 Key Results

| Metric              | Rule-Based |      MoA | Δ Improvement |
| :------------------ | ---------: | -------: | ------------: |
| **Doctor Wait**     |  204.3 min | 85.3 min |       -58.2 % |
| **MRI Wait**        |       42.2 |     25.1 |       -40.5 % |
| **Ultrasound Wait** |      158.7 |     62.2 |       -60.8 % |
| **Bed Wait**        |      166.2 |     45.9 |       -72.4 % |
| **Resource Use**    |       76 % |     91 % |       +19.3 % |

### Clinical Accuracy (by Demographic)

| Group        |   Rule | Single |    MoA |
| :----------- | -----: | -----: | -----: |
| White Male   | 84.3 % | 87.6 % | 94.2 % |
| Black Male   | 78.2 % | 76.5 % | 92.4 % |
| Asian Female | 79.1 % | 78.6 % | 95.2 % |

**Bias Reduction:** Demographic parity gap ↓ from 15.9 % to 1.2 %.
**Clinical appropriateness:** 94.6 % maintained.

---

## 🔐 Deployment Considerations

* **GDPR Compliance:** All LLM components run within NHS-controlled infrastructure; no external data transmission.
* **FHIR Integration:** Fully compliant with HL7 FHIR R4 (UK Core).
* **Audit Trails:** Decision logging for clinical governance.
* **Computational Cost:** ≈ £0.04 per consultation (run-time validated on local EKS cluster).

---

## 🧪 Validation Protocol

1. **Statistical:** 30 independent simulation runs (95 % CI).
2. **Clinical:** 237 expert-reviewed synthetic cases across specialties.
3. **Bias:** Intersectional analysis (gender × ethnicity).
4. **Safety:** Confidence threshold monitoring and audit traceability.

---

## 📚 Academic Reference

**Primary Citation:**

> Burrows, R. (2025). *Reducing Patient Wait Times in NHS Triage Using a Mixture-of-Agents Simulation Framework.* MSc Dissertation, University of Surrey.

**BibTeX:**

```bibtex
@mastersthesis{burrows2025nhs,
  title={Reducing Patient Wait Times in NHS Triage Using a Mixture-of-Agents Simulation Framework},
  author={Burrows, Raunak},
  school={University of Surrey},
  year={2025},
  type={MSc Dissertation},
  note={Available at: https://github.com/burrows99/nhs-triage-simulation}
}
```

---

## 🧩 Contribution Guide

We welcome contributions to extend the MoA framework:

* New specialist agents (pediatric, orthopedic, etc.)
* Enhanced bias mitigation strategies
* Integration with real FHIR clinical data
* Visualization and performance optimisation

```bash
git checkout -b feature/improvement
git commit -am "Add improvement"
git push origin feature/improvement
```

---

## 📞 Contact

**Raunak Burrows**
📧 [raunakburrows@gmail.com](mailto:raunakburrows@gmail.com)
🔗 [LinkedIn](https://linkedin.com/in/raunakburrows)
🐙 [GitHub @burrows99](https://github.com/burrows99)

**Supervisor:** [Dr. Xiatian Zhu](https://x-up-lab.github.io/) — University of Surrey

---

## 🏛️ Acknowledgments

* University of Surrey — academic supervision and resources
* NHS England — operational data and policy context
* SimPy Community — open-source simulation framework
* Synthea Team — FHIR synthetic data generation
* Manchester Triage Group — standardised triage protocols

---

## 🔍 Keywords / Topics

`healthcare-ai` `simulation` `nhs` `mixture-of-agents` `langgraph` `llm` `fhir` `simpy` `synthetic-data` `discrete-event-simulation` `ai-bias` `triage` `healthtech` `python` `university-of-surrey` `msc-dissertation`
