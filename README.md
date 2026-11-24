# 🏥 NHS Triage Simulation Framework

### *Reducing Patient Wait Times in NHS Triage Using a Mixture-of-Agents Simulation Framework*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![SimPy](https://img.shields.io/badge/SimPy-4.0+-green.svg)](https://simpy.readthedocs.io/)

**Author:** Raunak Burrows
**Supervisor:** Dr. Xiatian Zhu — Senior Lecturer, People-Centred AI, University of Surrey
**Affiliation:** MSc Artificial Intelligence (2025), University of Surrey

---

## 📖 Abstract

This repository implements the research project *“Reducing Patient Wait Times in NHS Triage Using a Mixture-of-Agents Simulation Framework.”*
The work addresses a persistent gap in NHS emergency department (ED) operations — post-triage patient routing — by designing a **Mixture-of-Agents (MoA)** system that dynamically coordinates multiple specialist AI agents to allocate resources efficiently.

> **Reproducibility status (audit of 2026-11-24).** The headline numbers previously listed here
> (58.2 % shorter doctor waits, -40.5 % MRI, -60.8 % ultrasound, +19.3 % utilisation, a parity gap of
> 15.9 % -> 1.2 %, 94.6 % appropriateness, "30 runs with 95 % CI", "expert review of 237 cases") are
> **not reproduced** by the code in this repository, and several have no supporting code or data. In
> the dissertation-era simulator the "single-agent" and "MoA" arms are coin flips, not LLMs, and their
> gains come from two routing bugs that delete doctor visits and MRI scans; with those fixed, every
> difference between arms is null. See [AUDIT.md](AUDIT.md) for the gaps and [RESULTS.md](RESULTS.md)
> for the reproduced numbers with confidence intervals. The dissertation PDF is unchanged and still
> contains the original claims.

---

## 🎯 Problem Context

* Only **76.4 %** of NHS A&E patients are seen within 4 hours (Q4 2023-24).
* Over **35 000** patients experience > 12-hour delays.
* The **Manchester Triage System (MTS)** — used in > 90 % of UK EDs — focuses solely on initial classification.
* Post-triage routing remains **manual, sequential, and resource-inefficient**.

The proposed MoA framework builds on MTS and fuzzy-MTS literature to enable **data-driven, context-aware routing** using collaborative AI agents.

---

## 🧠 Methodology Overview

### Comparative Framework (as described in the dissertation)

1. **Rule-Based (Baseline)**: traditional MTS flow, physician-first.
2. **Single-Agent**: an LLM routing recommendation (the dissertation names GPT-OSS-20B, Mistral-7B and DeepSeek-7B).
3. **Multi-Agent (MoA)**: neurological, cardiac and abdominal specialist agents plus an aggregator.

### What the code actually implements

* **Simulation core:** SimPy discrete-event simulation (`edsim/`, restored from commit `37d31df`):
  Poisson arrivals, exponential service times, priority queues for doctors, MRI, ultrasound and beds.
  At the dissertation's lambda = 12 patients/h the doctor station runs at rho = 1.0 and the beds at
  rho = 2.4, i.e. both queues are unstable.
* **Routing arms in `edsim`:** `single_llm` / `multi_llm` send a red patient who needs an MRI straight
  to MRI with probability 0.8 / 0.7. No model is called.
* **Real LLM routers (added in the audit):** `llm_router.py` implements the single-agent and MoA
  routers from the dissertation's appendix prompts against a local Ollama server.
* **Synthetic data:** a 100-patient Synthea (Massachusetts, CSV) run; the cleaned file has 237
  emergency encounters, all labelled `doctor` (`data/nhs_ecds_aligned_routing_dataset.csv`). The
  simulator does not read it. No FHIR / UK Core export, no 10 000-patient dataset.

---

## ⚙️ Installation

```bash
git clone https://github.com/burrows99/nhs-triage-simulation.git
cd nhs-triage-simulation
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.txt
# or: python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

---

## 🚀 Usage

```bash
.venv/bin/python test_reproduce.py                                  # self-check
.venv/bin/python reproduce.py sim --config dissertation --reps 30   # all arms, 30 seeded replications, 95% CIs
.venv/bin/python reproduce.py sim --config dissertation --reps 30 --fix-routing   # routing bugs fixed
.venv/bin/python reproduce.py llm-table --model qwen2.5:7b          # real LLM routers (needs Ollama)
.venv/bin/python reproduce.py sim --config dissertation --reps 30 --llm-table results/llm/table_qwen2.5-7b.json
.venv/bin/python reproduce.py llm-cases --model qwen2.5:7b --per-group 5
MPLBACKEND=Agg .venv/bin/python run_simulation.py                   # the original single unseeded run
```

`backend/` and `streamlit_app.py` are a later (2025-09-10) event-log visualiser; they are not the
dissertation experiment (see AUDIT.md section 4).

---

## 📁 Repository Structure

```
nhs-triage-simulation/
├── edsim/                 # dissertation-era simulator (restored from 37d31df, unmodified)
├── run_simulation.py      # its original entry point (single unseeded run per arm)
├── reproduce.py           # seeded replications, corrected metrics, paired CIs
├── llm_router.py          # real single-agent / MoA routers via Ollama
├── test_reproduce.py
├── data/                  # the 237-encounter case file
├── results/               # raw outputs behind RESULTS.md
├── backend/, streamlit_app.py   # later event-log visualiser
├── AUDIT.md, RESULTS.md
└── MScDissertation2025.pdf
```

---

## 📊 Key Results

Reproduced with the dissertation's lambda = 12/h over 30 days, 30 paired replications, mean +/- 95 % CI
(RESULTS.md tables 1 and 3; original metric code, so as-coded values). "Coin" arms are the original code's mock LLM arms.

| Metric | Rule-based | MoA "coin" arm (as coded) | MoA "coin" arm, routing bugs fixed | Dissertation claim (rule -> MoA) |
| :-- | --: | --: | --: | --: |
| Doctor wait (min) | 325 +/- 60 | 122 +/- 20 | 325 +/- 62 (no change) | 204.3 -> 85.3 |
| MRI wait (min) | 12.5 +/- 0.9 | 7.9 +/- 0.9 | 12.7 +/- 1.1 (no change) | 42.2 -> 25.1 |
| Ultrasound wait (min) | 73.7 +/- 6.6 | 73.9 +/- 7.4 | 77.0 +/- 8.5 (no change) | 158.7 -> 62.2 |
| Bed wait (min, queue unstable) | 2,950 +/- 130 | 2,950 +/- 130 | 2,940 +/- 110 (no change) | 166.2 -> 45.9 |
| Mean utilisation | 76.9 % | 74.2 % | 76.9 % | 76.2 % -> 90.9 % |

With **real LLM routers** (qwen2.5:7b via Ollama, the dissertation's appendix prompts; GPT-OSS-20B and
Mistral-7B were not available) driving the same simulation, the as-coded doctor wait falls by about
95%, but only because 19-24% of patients are sent straight to ultrasound and therefore never see a
doctor. With that bookkeeping fixed, neither the single agent nor the MoA changes any wait or
utilisation (all differences null; RESULTS.md section 3). The MoA aggregator never took the MRI
bypass, and no final routing decision changed with the patient's gender or ethnicity.

The clinical-accuracy-by-demographic table, the 94.6 % appropriateness and the parity-gap figures
that were listed here have no supporting code or data in this repository (AUDIT.md section 2).

---

## 🔐 Deployment Considerations (not implemented)

The dissertation discusses GDPR-compliant local deployment, FHIR R4 (UK Core) integration, audit
trails and a cost of about £0.04 per consultation on an EKS cluster. None of this is implemented or
measured in this repository.

---

## 🧪 Validation

* **Statistical:** `reproduce.py` runs 30 seeded replications per arm with common seeds, paired
  t-intervals and Holm-adjusted p-values. The original code ran each arm once, unseeded.
* **Clinical:** no expert review has been carried out. The 237-case file's labels are generated by
  `data/clean.py` (all `doctor`). A real clinician-labelled case set is still needed.
* **Bias:** `llm-table` routes every simulator input under six gender x ethnicity variants
  (counterfactual test); `llm-cases` reports accuracy and parity gap per group with Wilson CIs.

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
