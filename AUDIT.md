# Reproducibility audit

Audit of the claims in `README.md` and `MScDissertation2025.pdf` ("Reducing Patient Wait Times in
NHS Emergency Department Triage Using a Mixture-of-Agents Simulation Framework", MSc dissertation,
University of Surrey, 2025) against the code and data in this repository, including its full git
history. Audited on 2026-11-24. The re-run numbers are in [RESULTS.md](RESULTS.md).

Everything below can be checked with `git show <commit>:<path>`. Line numbers refer to the files
as restored on this branch (identical to commit `37d31df`).

## 0. Which code produced the dissertation?

The PDF's creation date is 2025-09-09. The git history has three unrelated code bases:

| Period | Commit(s) | What it is | Relation to the dissertation |
|---|---|---|---|
| 2025-08-30 to 09-04 | `fbf52ad` to `ebf771c` (branch `clean`) | A SimPy hospital with LLM *triage classification* (Ollama / Hugging Face, LangGraph listed in requirements), Synthea data | A different experiment (it classifies triage level, it does not route after triage). Its own report (`output/comparison_all_systems_1week/comparison_report.md` on `clean`) shows the "Multi-Agent LLM" system putting **100% of patients in YELLOW**, i.e. the LLM output had collapsed to one class. |
| 2025-09-08 | `37d31df` | `edsim/` + `run_simulation.py`: post-triage routing with arms `rule_based`, `single_llm`, `multi_llm`; doctor / MRI / ultrasound / bed; `data/` with the 237-row case file | **The dissertation's experiment.** Same arms, resources and metrics as Chapter 4, and the last commit before the PDF. |
| 2025-09-10 onward (HEAD) | `77be695` to `7cc62fb` | `backend/` + `streamlit_app.py`: an event-log demo for a visualiser | Written after the dissertation; it computes none of the reported metrics (section 4). |

`edsim/`, `run_simulation.py` and the case file were deleted from `main` on 2025-09-10 (`77be695`),
so before this branch no commit of `main` could reproduce any number in the dissertation. This branch
restores them verbatim.

## 1. Top gaps (most important first)

1. **There is no LLM in the simulation.** In `edsim/agents.py` the `single_llm` and `multi_llm` arms
   are a coin flip: a red patient who needs an MRI is sent straight to MRI with probability 0.8
   (`single_llm`, line 35) or 0.7 (`multi_llm`, line 44); every other patient is routed exactly as
   in `rule_based`. Nothing calls a model. `ai/mixture_of_agents.py` and `ai/agents/base.py` at
   `37d31df` are **empty files**. The code's own README calls this "mock LLM evaluation", and the
   earlier version of the same model (`mathematical_modeling.py`, `f1a37f6`) uses the same coin flip. The
   dissertation hints at it ("probabilistic agent behavior to emulate AI decision-making", "if-else
   structures rather than opaque AI systems") but its Chapter 3 describes GPT-OSS-20B specialist
   agents and an aggregator as if they had been run. No code anywhere in the history runs a routing
   LLM, GPT-OSS-20B or Mistral-7B, and there is no Langflow artefact.
2. **The "LLM" arms win because two routing bugs delete work from the queues.** In
   `edsim/agents.py`:
   - a bypassed patient's task list is `mri, [ultrasound], bed`: they **never see a doctor at all**
     (not "imaging first, then doctor"). This removes about 3.5-4% of the doctor workload, at a
     doctor utilisation of rho = 1.0 (below).
   - a red patient who needs an MRI but is *not* bypassed gets `doctor, [ultrasound], bed`: the
     `if patient.needs_mri: tasks.append('mri')` line exists only in the `rule_based` branch, so
     **their MRI is silently dropped** (20% of needed MRIs in `single_llm`, 30% in `multi_llm`).
     This is the whole "MRI wait reduction" and the MRI utilisation drop.

   With both bugs fixed (`--fix-routing`: nobody loses a service they need, a bypass only reorders
   it), every difference between arms disappears: doctor wait MoA vs rule-based **+0.0 min
   (95% CI +/-79)**, MRI **+0.3 +/- 1.4**, ultrasound **+3.8 +/- 12**, bed **-0.9 +/- 140**,
   utilisation **-0.05 +/- 0.42 pp** (RESULTS.md, table 3). The reported gains are an artefact of the
   bugs, not of the routing.
3. **The doctor and bed queues are unstable, so the waits are not well defined.** With the
   dissertation's lambda = 12/h and the code's service times (doctor 15 min, 3 doctors; bed 60 min,
   5 beds), the offered load is rho = 12 x 15/60 / 3 = **1.00** for doctors and rho = 12 x 1 / 5 =
   **2.4** for beds. A queue at rho >= 1 has no steady state: the mean wait grows with the run
   length. In 30 days, 58% of bed requests are still waiting at the end, and across 30 seeds the
   rule-based mean doctor wait ranges from **104 to 683 minutes**. The code defaults
   (`run_simulation.py`: lambda = 25/h) are worse still (doctor rho = 2.08, bed rho = 5). Any
   single-run number taken from this model is mostly noise plus a horizon effect.
4. **"30 independent runs (95% CI)" is not implemented.** `run_simulation.py` runs each arm once.
   No code anywhere in the history loops over replications, computes a confidence interval, or sets
   a seed (`random` and `np.random` are never seeded in `edsim`). No CI appears in the dissertation's
   results either. Re-running the unmodified script twice gives different rankings: the committed
   output at `37d31df` has `multi_llm` *worst* for doctor wait (287 min vs 174 rule-based); a re-run
   in this audit had `single_llm` best (84 min) and `multi_llm` worst (213 min).
5. **The committed result contradicts the dissertation.** `output/comparison/inferences.txt` at
   `37d31df` (the run the dissertation would have come from) reports doctor waits of rule 173.9 /
   single 117.9 / MoA **287.1** min and bed waits up to 491 min. None of the Chapter 4 numbers
   (204.3 / 172.9 / 85.3 etc.) appear in any file, log or output in the history.
6. **The "237 expert-reviewed cases" are 237 Synthea encounters with a script-generated label, and
   the label is the same for all 237.** `data/cleaned/nhs_ecds_aligned_routing_dataset.csv` has 237
   rows from 99 Synthea Massachusetts patients; `ground_truth_route` is `doctor` for **every** row,
   `needs_mri` and `needs_ultrasound` are `False` for every row, and triage is only blue (202) or
   orange (35). The cause is a bug in `data/clean.py` (`37d31df`): `condition_keywords` is built
   from the *severity names* (`"orange, "`, `"red, "`), so the regexes that look for `stroke`,
   `head injury`, `abdominal pain` etc. in it can never match. No expert review, review sheet,
   inter-rater data or accuracy computation exists. Consequences: a rule-based router scores 100%
   on these cases by construction (the dissertation reports 76.8-84.3%), and the cases cannot test
   MRI or ultrasound routing at all.
7. **No code computes clinical accuracy, demographic parity, or the 94.6%.** The only demographic
   code (`data/analysis.py`) tabulates the case file by gender and ethnicity; it has no routing
   decisions and no accuracy. Table 4-1, Figure 4-2, the 94.6% appropriateness, the "15.2% fewer
   safety incidents" and the "89% vs 76% plausibility" have no code, data or output behind them.
   The README's "demographic parity gap 15.9% -> 1.2%" is not in the dissertation in that form:
   15.9 pp is the single-agent vs MoA gap for *Black male* patients only, and 1.2% appears nowhere
   in the dissertation. From Table 4-1 itself the max-min parity gaps are 7.5 pp (rule),
   12.4 pp (single) and 2.8 pp (MoA).
8. **"10 000+ FHIR R4 (UK Core) patients" is not what the repository generated.** The Synthea
   config (`docker-compose.yml` at `37d31df`) is `-p 100 ... --exporter.fhir.export false ...
   Massachusetts`: 100 living US patients, CSV export, no FHIR patient bundles, no UK Core profile.
   `output/csv/patients.csv` has 135 rows; the case file has 99 patients. The dissertation itself
   says both 10,000 (section 3.2) and 5,000 (Appendix A-2). The simulator does not read the Synthea
   data at all: `PatientFactory.create_patient` is called without `patient_data`, so every simulated
   patient's triage colour is a weighted coin (`TRIAGE_WEIGHTS`) and MRI / ultrasound need are
   Bernoulli(0.5 for red only) and Bernoulli(0.2).
9. **The model in the code is not the model in the dissertation.** Dissertation: log-normal service
   times (doctor 15+/-5, MRI 25+/-8, ultrasound 18+/-6, triage 8+/-2 min), bed stay 3 days, MRI and
   ultrasound "with limited availability hours", lambda = 12/h, 30 days, 10,000 patients per run.
   Code: exponential service (doctor 15, MRI 30, ultrasound 20, bed 60 min), no triage stage, no
   availability hours, lambda = 25/h, 5,000 min (3.5 days). 30 days at lambda = 12/h is about 8,640
   patients, not 10,000. Capacities (3 doctors, 1 MRI, 1 ultrasound, 5 beds) are not stated in
   the dissertation. The dissertation's second routing rule (red/orange abdominal -> direct
   ultrasound) is not implemented: no patient is ever sent straight to ultrasound.
10. **MRI, ultrasound and bed demand are identical across arms by construction** (the arms only
    change the order of tasks for red+MRI patients, plus the two bugs above). So the reported MRI
    utilisation of 30% / 92% / 95%, ultrasound 45% / 85% / 90% and the 72% bed-wait reduction cannot
    come from this model. Re-run as coded, the MoA arm *lowers* mean utilisation (77.0% -> 74.2%,
    because it deletes work), the opposite of the claimed 76.2% -> 90.9%.

## 2. Claim by claim

"Code" = code exists that computes the number; "Data" = data in the repo supports it; "Script" =
a command reproduces it. Reproduced values: RESULTS.md.

| Claim (README / dissertation) | Code | Data | Script | Verdict |
|---|---|---|---|---|
| Doctor wait 204.3 -> 85.3 min (-58.2%) | metric yes (`edsim/metrics.py`) | no output contains it | no (unseeded, single run) | **Not reproduced.** As coded: 325 +/- 60 -> 122 +/- 20 min (-63%), entirely due to bug 2; with the bug fixed: 0 change. Single-agent and MoA are identical (MoA - single = -0.2 +/- 35 min). |
| MRI wait -40.5% (42.2 -> 25.1) | metric yes | no | no | **Not reproduced as a routing effect.** As coded 12.6 -> 7.9 min, caused by dropping 30% of MRIs (bug 2). Fixed: +0.3 +/- 1.4 min. |
| Ultrasound wait -60.8% (158.7 -> 62.2) | metric yes | no | no | **Not reproduced.** No arm changes ultrasound routing; as coded -0.3 +/- 10 min. |
| Bed wait -72.4% (166.2 -> 45.9) | metric yes | no | no | **Not reproduced.** Bed queue is unstable (rho = 2.4); waits ~3,070 min, no arm difference (+7.6 +/- 180). |
| Resource utilisation +19.3% (76.2% -> 90.9%) | metric yes (biased, section 3) | no | no | **Contradicted.** Baseline 77.0% matches; MoA gives 74.2% (lower). Per-resource figures in Ch. 4 average to 63% / 90.5%, not 76.2 / 90.9. |
| Clinical appropriateness 94.6% | no | no | no | **No supporting code or data.** Table 4-1's MoA rows average 93.9%, not 94.6%. |
| Accuracy by demographic (Table 4-1, README table) | no | case file has a single-valued label | no | **No supporting code.** Rule-based scores 100% on the repo's cases by construction. Real-LLM figures in RESULTS.md. |
| Demographic parity gap 15.9% -> 1.2% | no | no | no | **Not in the dissertation in this form; 1.2% appears nowhere.** |
| "30 independent runs (95% CI)" | no | no | no | **Not implemented** (single unseeded run per arm). Implemented on this branch. |
| "Expert review on 237 synthetic cases" | no | 237 auto-labelled Synthea rows | no | **Not performed in anything in the repo.** The 237 is the row count of the case file. |
| 10,000+ FHIR R4 UK Core patients via modified Synthea | no | 100-135 US patients, CSV | `docker-compose.yml` (`-p 100`) | **Not supported.** |
| lambda = 12/h, Poisson, M/M/c | partly: Poisson arrivals and exponential service exist | - | - | Code default is 25/h; dissertation says log-normal (so not M/M/c); at 12/h the doctor station is critically loaded. |
| GPT-OSS-20B single agent; MoA of neuro / cardiac / abdominal agents + aggregator via LangGraph and Ollama | no (coin flips; empty `ai/` files) | - | - | **Not implemented.** Implemented on this branch with locally available models (RESULTS.md). |
| Mistral-7B "tested for NHS deployment" | no | - | - | No code mentions Mistral. The dissertation also names DeepSeek-7B for the single agent (Appendix A.3) and calls GPT-OSS-20B a "7B parameter configuration" (section 3.3.2). |
| Single agent beats rule-based by 16% on doctor wait | - | - | - | 204.3 -> 172.9 is 15.4%; the dissertation's 49.5% (MoA vs single) is 50.7% by its own numbers. |
| "validation against NHS Digital operational data" | no | no | no | No such data or comparison in the repo. |
| About £0.04 per consultation, EKS cluster | no | no | no | No code, cost log or infrastructure in the repo. |
| Demographic table 3-1 (Synthea matches NHS: Black 3.2%, ...) | no | case file: Black 10.1%, Asian 8.9%, White 81.0% | no | **Contradicted by the repo's data** for Black; Appendix A-2 also disagrees with 3-1 (Other 4.7% vs 6.3%). |
| README usage: `pip install -r requirements.txt`, `python main_simulation.py`, `scripts/run_experiments.py --all`, `analysis/bias_evaluation.py`, `analysis/performance_metrics.py`, `src/routing`, `config/`, `docs/` | - | - | - | **None of these paths have ever existed** in any commit. `backend/requirements.txt` lists FastAPI / mypy but not `simpy`, `faker` or `streamlit`, which the code imports. |

## 3. Defects in the dissertation-era simulator (`edsim`, `37d31df`)

Left unmodified on this branch so the original behaviour can be reproduced; `reproduce.py` measures
around them.

- **Routing bugs** (section 1, item 2): `edsim/agents.py` lines 33-50.
- **No seeds**: `edsim` draws from the global `random` (routing) and `np.random` (everything else),
  never seeded.
- **No warm-up**: statistics start at t = 0 with an empty department.
- **Censoring**: `wait_times` only records patients whose request was granted. In an overloaded
  queue the patients still waiting at the end, who have the longest waits, are dropped, so the
  mean is biased low and depends on the run length (58% of bed requests are still waiting at the
  end of a 30-day run).
- **Utilisation can exceed 100%**: `services.py` line 114 adds the *full* sampled service time when
  the service starts, even if it ends after the horizon (the committed output reports 100.2-101.5%).
- **"Queue length" is not queue length**: `services.py` line 94 records `resource.count`, which in
  SimPy is the number of patients *in service* (at most the capacity), not the number waiting
  (`len(resource.queue)`). The queue plots and the "max queue" inferences are therefore wrong.
- **"Accuracy" is the input parameter read back**: `mock_llm_evaluation` measures how often the coin
  flip came up heads and compares it with the probability that was fed in (`SCENARIO_FACTOR`).
- **The MoA arm is parameterised as the worse router** (0.7 vs 0.8), yet the dissertation reports
  MoA better than single-agent on every metric.
- **Comparison design**: arms run once each with unrelated random streams (no common random
  numbers), no paired test, no correction for the 8+ comparisons, and the "overall ranking" in
  `edsim/utils/inference.py` is an ad-hoc point score.

## 4. Current `main` code (`backend/`, `streamlit_app.py`)

Written after the dissertation (2025-09-10/11). It cannot produce any reported metric:

- No capacity constraints: a doctor or bed is a Python list, not a SimPy resource; any number of
  patients are "in consultation" at once. "Wait" is a formula (`base_wait + 2 min x queue length`,
  `routing_service.py` `calculate_wait_time`), not a simulated queue.
- No MRI or ultrasound in the simulated hospital (`HospitalFactory.create_sample_hospital`).
- One routing policy only (all patients to a doctor, red/orange to a bed); no LLM, no arms.
- Arrivals 1 per 15 min (4/h), 120-minute runs, symptoms drawn with Faker / `random`, no seeds,
  no metric aggregation. `main.py` prompts with `input()`.
- The two top-level `hospital_simulation_*.json` files (and the six in `backend/`) are event logs of
  2-hour runs with 7-8 patients, written 2025-09-10/11, i.e. after the dissertation; they support no
  claimed number.

## 5. Citations that could not be located

A quick search did not find these two references as cited; the owner should check them against the
original sources:

- [16] Wang, Y., et al. (2024). "Rethinking Mixture-of-Agents for complex clinical decision making."
  AAAI 38(1), 123-131. The Mixture-of-Agents paper usually cited is Wang, J. et al. (2024),
  "Mixture-of-Agents Enhances Large Language Model Capabilities", arXiv:2406.04692.
- [5] Lee, C., et al. (2024). "Evaluating intersectional bias in clinical AI systems: A counterfactual
  analysis framework." J. Biomed. Inform. 152, 104628. (Cited for the bias methodology and in the
  README.)

The remaining references were not checked.

## 6. What this branch changes

- Restores `edsim/`, `run_simulation.py` and the case file
  (`data/nhs_ecds_aligned_routing_dataset.csv`) from `37d31df`, unmodified.
- `requirements.txt` (pinned, Python 3.12) at the top level.
- `reproduce.py`: one entry point. Seeds every replication, runs each arm N times with the same
  seeds (paired), reports the original metrics and corrected ones (warm-up, horizon clipping,
  share still waiting), 95% t-intervals, paired differences with Holm-adjusted p-values, and the
  `--fix-routing` sensitivity. `test_reproduce.py` checks that the traced simulator reproduces the
  original one exactly for a given seed.
- `llm_router.py`: real single-agent and MoA routers (Ollama, the appendix prompts) for the arms the
  code only mocked; every answer is logged, unparseable answers are counted, never replaced by rules.
- `results/`: the raw per-replication CSVs, summaries and LLM logs behind RESULTS.md.
- README: the unsupported numbers are replaced with the reproduced ones, and the dissertation's
  figures are kept only as clearly labelled, unreproduced claims.

The dissertation PDF is unchanged.
