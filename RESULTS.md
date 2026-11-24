# Results: claimed vs reproduced

What the numbers in the README and dissertation actually are when the dissertation-era code is
re-run properly. Why each number differs is explained in [AUDIT.md](AUDIT.md). Everything here was
produced on 2026-11-24 on an Apple M4 Pro (24 GB) with the commands in section 5; raw per-replication
data is in `results/`.

## Summary

| Claim | Claimed | Reproduced (30 paired replications, 95% CI) |
|---|---|---|
| Doctor wait, MoA vs rule | -58.2% (204.3 -> 85.3 min) | As coded: -63% (325 -> 122 min) with a *coin-flip* "MoA"; real qwen2.5:7b MoA: -95%. In both cases the gain comes from patients who never see a doctor. **With the routing fixed: +0.0 +/- 79 min (coin) and -11 +/- 89 min (qwen2.5:7b). Null.** |
| MRI wait | -40.5% | As coded -37% (from dropped MRI scans); fixed: +0.3 +/- 1.4 min. **Null.** |
| Ultrasound wait | -60.8% | +0.3% as coded; fixed +3.8 +/- 12 min. **Null.** |
| Bed wait | -72.4% | +0.3% as coded; the bed queue is unstable (waits of about 50 h). **Null.** |
| Utilisation | +19.3% (76.2 -> 90.9%) | 76.9% -> 74.2% as coded (lower); fixed 77.0% -> 77.0%. **Contradicted.** |
| MoA beats single agent | 85.3 vs 172.9 min | -0.2 +/- 35 min (coin arms); the real MoA never took the MRI bypass. **Not reproduced.** |
| Accuracy by demographic, parity gap 15.9% -> 1.2%, 94.6% appropriateness | Table 4-1 | No code or data. On the repo's cases every arm scores 100% because every label is "physician". **Cannot be evaluated with the repo's data.** |
| 30 runs, 95% CI; expert review of 237 cases | stated | Not implemented / not performed originally; the 30 runs are done here. |

## 1. Design

- **Simulator**: `edsim/` restored unmodified from `37d31df` (the code behind Chapter 4).
- **Configuration**: the dissertation's lambda = 12 patients/h and 30-day horizon (`--config
  dissertation`). Service times, triage mix and capacities (3 doctors, 1 MRI, 1 ultrasound, 5 beds)
  are the code's, because the dissertation's log-normal times, bed stay of 3 days and imaging hours
  were never implemented and its capacities are not stated. The code's own defaults (lambda = 25/h,
  5,000 min, `--config code`) are reported too.
- **Replications**: N = 30 per arm, seeds 1000-1029, the **same seeds in every arm**, so arms are
  compared as paired differences (paired t, 95% CI). p-values are Holm-adjusted over the 10
  comparisons in each table (2 arms x 5 metrics).
- **Metrics**: "as coded" = the original `edsim/metrics.py` (no warm-up, served patients only,
  utilisation can exceed 100%). "Corrected" = patients arriving after a 24 h warm-up, busy time
  clipped to the horizon, plus the share of requests still waiting at the end (for an unstable queue
  the mean wait of the served patients is a lower bound that grows with the horizon).
- **Arms**: `rule_based`, and the original `single_llm` / `multi_llm`, which are **coin flips, not
  LLMs** (red patients needing an MRI go straight to MRI with p = 0.8 / 0.7). Real LLM arms are in
  section 3.

## 2. Simulation: claimed vs reproduced

### Table 1. Dissertation configuration, metrics as coded (the closest re-run of Chapter 4)

Mean +/- 95% CI over 30 replications. Relative change = paired difference / rule-based mean.

| Metric | Rule-based | Single "LLM" (coin, p=0.8) | MoA "LLM" (coin, p=0.7) | MoA vs rule (paired) | Claimed (rule / single / MoA, change) |
|---|---|---|---|---|---|
| Doctor wait (min) | 325 +/- 60 | 122 +/- 26 | 122 +/- 20 | **-204 +/- 64 (-63%)**, p_Holm = 3e-6 | 204.3 / 172.9 / 85.3 (-58.2%) |
| MRI wait (min) | 12.5 +/- 0.9 | 9.8 +/- 1.1 | 7.9 +/- 0.9 | -4.6 +/- 1.4 (-37%), p_Holm = 1e-6 | 42.2 / 30.2 / 25.1 (-40.5%) |
| Ultrasound wait (min) | 73.7 +/- 6.6 | 80.7 +/- 8.3 | 73.9 +/- 7.4 | +0.2 +/- 10 (+0.3%), p_Holm = 1 | 158.7 / 85.8 / 62.2 (-60.8%) |
| Bed wait (min) | 2,950 +/- 130 | 2,910 +/- 130 | 2,950 +/- 130 | +9.2 +/- 180 (+0.3%), p_Holm = 1 | 166.2 / 77.7 / 45.9 (-72.4%) |
| Bed requests still waiting at day 30 | 58% | 58% | 58% | - | - |
| Mean utilisation, 4 resources | 76.9% +/- 0.3 | 75.2% +/- 0.4 | 74.2% +/- 0.4 | -2.8 +/- 0.5 pp, p_Holm = 9e-12 | 76.2% -> 90.9% (+19.3%) |
| Doctor / MRI / ultrasound / bed utilisation | 99 / 30 / 79 / 100% | 96 / 24 / 80 / 100% | 96 / 21 / 80 / 100% | - | 95/30/45/82, 65/92/85/75, 88/95/90/89% |
| Patients who never see a doctor | 0% | 4.0% | 3.5% | - | - |
| MoA minus single-agent, doctor wait | | | | -0.2 +/- 35 min, p = 0.99 | -87.6 min (172.9 -> 85.3) |

Reading it:

- The **direction** of the doctor-wait effect matches the dissertation, and the size (-63% +/- 20 pp)
  is compatible with -58.2%. But the rule-based doctor wait varies from **104 to 683 min** across
  the 30 seeds (the doctor station runs at rho = 1.00), so a single unseeded run (which is what
  the original script produces) can land almost anywhere; the dissertation's 204.3 is well inside
  that spread.
- **Single-agent and MoA are indistinguishable on doctor wait** (difference -0.2 +/- 35 min). The
  claimed MoA advantage over single-agent (85.3 vs 172.9 min) is not reproduced; in the code the MoA
  arm is the *less* accurate coin (0.7 vs 0.8). Only 47% of seeds even give the claimed ordering
  MoA < single < rule.
- **Ultrasound and bed waits do not change**, as expected: no arm changes ultrasound or bed routing.
  The claimed -60.8% and -72.4% are not reproduced. Bed waits are about 50 hours because the bed
  stage is overloaded (rho = 2.4), not 2-3 hours.
- **Utilisation goes down, not up**, because the coin-flip arms delete work (next table). The
  rule-based baseline of 76.9% happens to be close to the claimed 76.2%; the claimed 90.9% for MoA is
  contradicted.
- The MRI-wait reduction is real in the code but comes from dropping 30% (MoA) / 20% (single) of the
  MRI scans that patients need (AUDIT.md section 1, item 2), which also explains why MoA "beats"
  single-agent on MRI (-1.9 +/- 1.4 min).

### Table 2. Same, corrected metrics

Warm-up 24 h, horizon clipping. Practically identical to Table 1 for this configuration, so the
missing warm-up is not what moves the numbers; the instability and the routing bugs are.

| Metric | Rule-based | Single (coin) | MoA (coin) | MoA vs rule (paired) |
|---|---|---|---|---|
| Doctor wait (min) | 335 +/- 62 | 124 +/- 27 | 124 +/- 21 | -211 +/- 66 (-63%) |
| MRI wait (min) | 12.6 +/- 0.9 | 9.9 +/- 1.0 | 7.9 +/- 0.9 | -4.6 +/- 1.4 (-37%) |
| Ultrasound wait (min) | 74.2 +/- 6.9 | 80.9 +/- 8.2 | 73.9 +/- 7.6 | -0.3 +/- 10 |
| Bed wait (min) | 3,070 +/- 140 | 3,030 +/- 130 | 3,070 +/- 140 | +7.6 +/- 180 |
| Mean utilisation | 77.0% | 75.2% | 74.2% | -2.8 +/- 0.5 pp |

### Table 3. Routing bugs fixed (`--fix-routing`): the effect disappears

Nobody loses a service they need; a bypassed patient has the MRI first and then sees the doctor;
a non-bypassed patient keeps the MRI. Same seeds, same coin flips.

| Metric | Rule-based | Single (coin) | MoA (coin) | MoA vs rule (paired) |
|---|---|---|---|---|
| Doctor wait (min) | 335 +/- 62 | 385 +/- 75 | 335 +/- 65 | **+0.0 +/- 79** (p_Holm = 1) |
| MRI wait (min) | 12.6 +/- 0.9 | 12.3 +/- 1.0 | 12.9 +/- 1.1 | +0.3 +/- 1.4 (p_Holm = 1) |
| Ultrasound wait (min) | 74.2 +/- 6.9 | 79.2 +/- 14 | 77.9 +/- 9.0 | +3.8 +/- 12 (p_Holm = 1) |
| Bed wait (min) | 3,070 +/- 140 | 3,050 +/- 160 | 3,060 +/- 120 | -0.9 +/- 140 (p_Holm = 1) |
| Mean utilisation | 77.0% | 77.0% | 77.0% | -0.05 +/- 0.42 pp (p_Holm = 1) |

All ten comparisons are null. **Within this model, routing red MRI patients to MRI first has no
detectable effect on any wait or on utilisation.** Every reported improvement traces back to the two
bugs that remove doctor visits and MRI scans.

### Table 4. Sensitivity

| Configuration (MoA vs rule, paired, 30 seeds) | Doctor wait | MRI wait | Ultrasound wait | Bed wait | Mean util. |
|---|---|---|---|---|---|
| Code defaults: lambda = 25/h, 5,000 min (`--config code`), as coded | **+20 +/- 28 min (+13%)** | -19 +/- 10 (-46%) | -4 +/- 19 | +30 +/- 54 | -3.4 +/- 1.0 pp |
| Same, corrected (24 h warm-up) | **-73 +/- 36 min (-48%)** | -20 +/- 11 (-49%) | -6 +/- 23 | +32 +/- 59 | -3.7 +/- 1.3 pp |
| Stable staffing: 4 doctors, 15 beds (rho = 0.75 / 0.80), as coded | -1.4 +/- 0.4 min (-18%) on a base of 7.8 min | -5.9 +/- 1.7 (-43%) | -6.1 +/- 8.9 | -0.1 +/- 0.8 | -3.3 +/- 0.4 pp |

With the code defaults (doctor rho = 2.08, bed rho = 5), 53% of doctor requests and 61% of bed
requests are still waiting at the end of the run, and **the sign of the doctor-wait effect flips
with the warm-up choice** (+13% as coded, -48% with a 24 h warm-up): in an unstable queue the
number is not an estimate of anything. With enough staff for the queues to be stable, the as-coded
doctor-wait gain shrinks to about 1.4 minutes, and it still comes from deleting doctor visits.

## 3. Real LLM arms

Models: only models already installed locally were used (no pulls). **qwen2.5:7b** (Q4_K_M) through
Ollama, temperature 0, seed 0, `num_predict` 200, JSON output. `num_ctx` was 4096 for the first 26 of
the 72 decision-table rows and 12288 for the rest; 12288 is the context the shared Ollama server kept
loaded, and the prompts are far shorter than either, so the two settings see identical input. Prompts:
the dissertation's appendix (single agent; neurological specialist; aggregator); the cardiac and
abdominal specialists use the appendix's general specialist template because their prompts are not
printed. MoA = 3 specialists in parallel + 1 aggregator, one layer. Every answer and its
justification is in `results/llm/*.jsonl`; 0 of 72 x 5 table answers were unparseable.

The dissertation's GPT-OSS-20B and Mistral-7B are not installed and were **not** pulled. Running them
is `ollama pull gpt-oss:20b` (about 14 GB on disk, needs roughly 16 GB free RAM, tight on this 24 GB
machine with other workloads) and `ollama pull mistral:7b` (about 4.4 GB), then the same three
commands with `--model`. qwen2.5:14b is installed but was not run: the shared Ollama server was
already congested (median 9 s per single-agent call and 37 s per MoA case with the 7B model, up to
9 minutes under contention).

### 3a. Decision table: every input the simulator can produce

A simulated patient only has a triage colour, an MRI flag (red only) and an ultrasound flag, so
there are 12 clinical inputs. Each was sent under 6 demographic variants (male/female x
White/Black/Asian) = 72 prompts per arm.

| Clinical input (all 6 demographic variants) | Single agent | MoA final decision | Dissertation protocol says |
|---|---|---|---|
| red, MRI indicated (with or without ultrasound) | **MRI** (12/12) | **physician** (12/12) | MRI direct |
| red, ultrasound indicated, no MRI | ultrasound (6/6) | ultrasound (6/6) | ultrasound direct only if abdominal |
| orange / yellow / green / blue, ultrasound indicated | **ultrasound** (24/24) | **ultrasound** (24/24) | physician first (rule 2 is red/orange abdominal only) |
| any colour, no imaging indicated | physician (30/30) | physician (30/30) | physician first |

- **No final decision changed with gender or ethnicity**, for either arm (counterfactual test, one
  deterministic answer per cell). One specialist did: the neurological agent recommended MRI for
  5 of the 6 variants of "red, MRI indicated" but physician for the Asian female variant, and its
  answer for "red, MRI and ultrasound indicated" also varied by group. The aggregator overrode both.
  With one answer per cell this is an observation, not an estimate of bias.
- **The MoA aggregator never takes the MRI bypass** that the protocol prescribes: the cardiac and
  abdominal specialists say "physician" and the aggregator follows the prompt's "most conservative
  recommendation" rule. So the MoA arm does not do what the dissertation's MoA is credited with.
- **Both arms send every ultrasound-flagged patient straight to ultrasound, including blue
  (non-urgent) patients**, contrary to the protocol's rule 2. That is about 20% of all arrivals.

### 3b. Simulation driven by the real LLM decisions

The decision table replaces the coin flips (`--llm-table`); each simulated patient is given one of the
6 demographic variants at random. Dissertation configuration, 30 paired replications.

| Metric (as coded) | Rule-based | Single agent (qwen2.5:7b) | MoA (qwen2.5:7b) | Single vs rule | MoA vs rule |
|---|---|---|---|---|---|
| Patients who never see a doctor | 0% | **23.9%** | **18.9%** | | |
| Doctor wait (min) | 325 +/- 60 | 12.1 +/- 0.7 | 18.1 +/- 1.2 | -322 +/- 62 (-96%) | -316 +/- 62 (-95%) |
| MRI wait (min) | 12.5 +/- 0.9 | 12.7 +/- 1.0 | 12.7 +/- 1.2 | +0.3 +/- 1.3 | -0.0 +/- 1.5 |
| Ultrasound wait (min) | 73.7 +/- 6.6 | 75.8 +/- 5.6 | 79.4 +/- 7.5 | +1.6 +/- 8.1 | +5.3 +/- 10 |
| Bed wait (min) | 2,950 +/- 130 | 2,790 +/- 150 | 2,970 +/- 120 | -168 +/- 170 | +23 +/- 140 |
| Mean utilisation | 76.9% | 71.3% | 72.8% | -5.7 +/- 0.5 pp | -4.2 +/- 0.5 pp |

(Paired differences use the corrected metrics; Holm-adjusted p < 1e-9 for doctor wait and
utilisation, all others p_Holm >= 0.34.)

The near-elimination of doctor waits is **not a benefit**: under the original code's semantics a
bypassed patient never sees a doctor, so the LLMs' over-use of direct ultrasound simply removes a
fifth of the patients from the doctor queue. With `--fix-routing` (the bypassed patients still see
a doctor afterwards):

| Metric, `--fix-routing` | Rule-based | Single agent | MoA | Single vs rule | MoA vs rule |
|---|---|---|---|---|---|
| Doctor wait (min) | 335 +/- 62 | 346 +/- 78 | 324 +/- 63 | +12 +/- 99 | -11 +/- 89 |
| MRI wait (min) | 12.6 +/- 0.9 | 12.9 +/- 0.9 | 12.7 +/- 1.1 | +0.3 +/- 1.4 | +0.2 +/- 1.7 |
| Ultrasound wait (min) | 74.2 +/- 6.9 | 75.4 +/- 8.3 | 81.0 +/- 8.3 | +1.2 +/- 9.0 | +6.8 +/- 10 |
| Bed wait (min) | 3,070 +/- 140 | 2,920 +/- 140 | 2,940 +/- 120 | -149 +/- 220 | -122 +/- 160 |
| Mean utilisation | 77.0% | 77.2% | 77.3% | +0.2 +/- 0.4 pp | +0.3 +/- 0.5 pp |

All ten comparisons null (p_Holm = 1). **With real LLM routers and correct bookkeeping, neither the
single agent nor the MoA changes any wait or utilisation in this model.**

### 3c. The repository's 237 cases

Stratified fixed-seed sample of **5 cases per gender x ethnicity group (n = 30 of 237)**, because
the shared Ollama server was congested; `--per-group` can be dropped to run all 237. The case
vignettes contain only what the file has: triage colour, age, sex, ethnicity, condition-severity
flags, chronic-condition count and frailty score. There is no presenting complaint in the data.

| Group | n | Rule-based | Single agent | MoA |
|---|---|---|---|---|
| All | 30 | 100% [88.6, 100] | 100% [88.6, 100] | 100% [88.6, 100] |
| Each of the 6 groups | 5 | 100% [56.6, 100] | 100% [56.6, 100] | 100% [56.6, 100] |

Accuracy against the file's `ground_truth_route`, Wilson 95% CI. Both LLM arms routed all 30 cases
to the physician (0 unparseable). The parity gap is 0 pp for every arm.

This does **not** reproduce, or test, the dissertation's Table 4-1 (rule-based 76.8-84.3%, MoA
92.4-95.2%, 94.6% overall). Every case in the file is labelled "physician" (the cleaning bug in
AUDIT.md section 1, item 6), so a router that always says "physician", including the rule-based
baseline, is 100% "accurate". A meaningful accuracy and bias evaluation needs cases with real
presenting complaints and clinician-assigned routes, which the repository does not contain.

## 4. Claims with no reproducible basis

| Claim | Status |
|---|---|
| 94.6% clinical appropriateness | No code, data or output. Section 3c: all arms score 100% on the repo's cases because every label is "physician". |
| Accuracy by demographic (Table 4-1) and parity gap 15.9% -> 1.2% | No code. 1.2% does not appear in the dissertation. Measured values in section 3. |
| Expert review of 237 cases | Not performed in anything in the repo; the 237 cases carry one auto-generated label. Needs real clinicians. |
| 30 runs with 95% CI | Not implemented originally; done here (N = 30, paired). |
| 10,000+ FHIR R4 UK Core patients | Not supported (100-patient US Synthea run, CSV export, not used by the simulator). |
| GPT-OSS-20B / Mistral-7B routers | Never implemented or run; neither model was available here (section 3). |
| Cost of about £0.04 per consultation, EKS | No code or data. |

## 5. Commands

```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python test_reproduce.py                                   # traced sim == original sim

# Tables 1-2 (about 2 min), Table 4 rows, Table 3
.venv/bin/python reproduce.py sim --config dissertation --reps 30
.venv/bin/python reproduce.py sim --config code --reps 30
.venv/bin/python reproduce.py sim --config dissertation --reps 30 --doctors 4 --beds 15 --tag sim_dissertation_stable_4doctors_15beds
.venv/bin/python reproduce.py sim --config dissertation --reps 30 --fix-routing --tag sim_dissertation_fixed_routing

# Section 3 (needs Ollama with the model pulled; OLLAMA_HOST defaults to http://127.0.0.1:11434)
.venv/bin/python reproduce.py llm-table --model qwen2.5:7b
.venv/bin/python reproduce.py sim --config dissertation --reps 30 --llm-table results/llm/table_qwen2.5-7b.json
.venv/bin/python reproduce.py sim --config dissertation --reps 30 --llm-table results/llm/table_qwen2.5-7b.json --fix-routing --tag sim_dissertation_table_qwen2.5-7b_fixed_routing
.venv/bin/python reproduce.py llm-cases --model qwen2.5:7b --per-group 5   # 30 cases; drop --per-group for all 237

# The original single, unseeded run (writes output/), for comparison
MPLBACKEND=Agg .venv/bin/python run_simulation.py
```

Outputs: `results/<tag>/reps.csv` (one row per arm and replication) and `results/<tag>/summary.md`
(every metric, as coded and corrected, plus the paired tests); `results/llm/*.jsonl` (every LLM
answer with its justification and timing).
