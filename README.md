# NHS ED triage simulation: post-triage routing with an LLM mixture-of-agents

A discrete-event simulation (SimPy) of an English Type 1 emergency department (ED) with a co-located
Urgent Treatment Centre (UTC). It compares four post-triage routers in a pre-registered experiment:

- a static Manchester Triage System (MTS) protocol;
- a load-aware heuristic;
- a local LLM mixture-of-agents (MoA) router: four specialist agents and a queue-aware aggregator,
  running qwen2.5:7b through Ollama;
- the same MoA without queue state.

| Document | Contents |
|---|---|
| [PREREG.md](PREREG.md) | the pre-registration, committed before the held-out run |
| [RESULTS_V2.md](RESULTS_V2.md) | the results, with confidence intervals, fallback and violation counts, and fairness |
| `v2/` | the simulator, routers, MoA, analysis and figures |
| `results_v2/` | every per-replication and per-patient output |
| `v2/cache/llm_cache.sqlite` | every LLM request and response, for exact replay |

## Result in brief (held-out, pre-registered; details in RESULTS_V2.md)

**Primary comparisons.** The queue-aware LLM MoA was compared with both baselines on 16 testable
comparisons (4 metrics, 2 scenarios, 2 baselines). It was better on 14 and worse on none.
- Base scenario: mean doctor wait -4.9 min (-5.5%), P90 doctor wait -22 min, time to needed
  imaging -53 min (-67%), and length of stay -10 min against the static protocol.
- No patient went unseen by a doctor.
- No fallback was needed and no protocol-violating proposal was made.

**Caveats, all reported in full:**
- The gain comes from more imaging-first decisions, which save a doctor review. When that saving is
  removed (the pre-registered sensitivity scenario), the MoA is worse: +30 min doctor wait and
  +32 min length of stay.
- Queue awareness added nothing.
- The pre-registered sex × ethnicity outcome gap widened. The router never sees ethnicity; the
  exploratory analysis points to case mix in small groups.
- Some local decisions are clinically poor: low-risk whiplash is sent to the ED, and some red and
  orange patients go to a scan before the doctor.

## What the model contains

- **Arrivals.** 11.1 per hour on average: 2024-25 Type 1 attendances divided by 178 Type 1 EDs. The
  hour-of-day profile comes from ECDS 2024-25. The stress scenario adds 20% to arrivals.
- **Patients.** 159 Synthea emergency encounters, resampled so that 27.9% of patients are admitted.
  Each encounter carries:
  - a triage record that the router sees: MTS category and discriminator, complaint, age and sex;
  - a separate ground truth that the router never sees: X-ray, CT and ultrasound need, specialist
    review and admission. It is derived from the encounter's own coded records, or from guideline
    indications. See `v2/cases.py`.
- **Resources.** ED doctors, UTC doctors, X-ray, CT, ultrasound, specialty review and assessment-unit
  beds. All are MTS-priority queues.
- **Routes.** Each patient gets one of five routes: ED doctor first, UTC, or CT, ultrasound or X-ray
  before the doctor. A route only reorders or relocates care; every needed service is still
  delivered.
- **Hard rules,** enforced by the simulator rather than the router:
  - red and orange patients are never sent to the UTC;
  - green and blue patients never go to imaging first;
  - every patient sees a doctor.

  A breached proposal is blocked, replaced with the protocol route, and counted.
- **Statistics.** 48 h warm-up, 7-day measurement window, and every window patient is followed until
  they leave (no censoring). Arms use common random numbers. There are 30 held-out seeds, with paired
  differences and Holm correction.

## Run

```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python -m v2.test_v2                       # self-checks
.venv/bin/python -m v2.run cases                     # rebuild v2/data/cases.csv from the Synthea CSVs in git history
.venv/bin/python -m v2.run welch --scenario base     # warm-up check (development seeds)
# LLM arms need Ollama with qwen2.5:7b. OLLAMA_HOST defaults to http://127.0.0.1:11435.
# Every response is cached, so a re-run with the shipped cache makes no model calls.
for sc in base stress; do .venv/bin/python -m v2.run sim --scenario $sc --seeds heldout; done
.venv/bin/python -m v2.run fairness
.venv/bin/python -m v2.run analyze --seeds heldout   # -> results_v2/heldout/tables.md, paired_tests.csv
.venv/bin/python -m v2.figures heldout               # -> results_v2/heldout/figures/
```

## Repository layout

```
v2/                 simulator (sim.py), scenarios (scenarios.py), case pool (cases.py, data/cases.csv),
                    routers (routers.py), LLM MoA (moa.py), CLI (run.py), analysis, figures, self-checks
results_v2/         dev/ and heldout/ outputs, fairness/, logs/
PREREG.md           pre-registration
RESULTS_V2.md       results
edsim/, run_simulation.py, data/   the 2025 prototype simulator, kept unchanged for reference
backend/, streamlit_app.py         an event-log visualiser (separate)
```

Synthetic data only, no patient data. MIT licence.
