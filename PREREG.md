# Pre-registration: LLM mixture-of-agents post-triage routing in a simulated NHS emergency department

Registered in this repository before the held-out evaluation was run. The registration is the
commit that adds this file. It will not be edited afterwards. Any deviation will be reported in
`RESULTS_V2.md` under "Deviations from the pre-registration".

- Code frozen at: the commit that adds this file. It contains `v2/` and the LLM prompt cache
  filled on development seeds.
- Prompt version: `PROMPT_VERSION = "v2.2"` in `v2/moa.py`. Development history: v2.0 sent most green patients to the ED and passed protocol-blocked imaging proposals to the aggregator; on the base development seeds the state-blind arm had a mean doctor wait of about 600 min. v2.1 stated the protocol defaults and offered only protocol-allowed candidates. v2.2 spelled out what the UTC can treat. The development outputs of v2.0 are kept in `results_v2/dev/base/*_prompt-v2.0.*`.
- Author: Raunak Burrows. Analysis code: `v2/analyze.py` (section 6 below is implemented there).

## 1. Question and hypotheses

Does a local LLM mixture-of-agents (MoA) router produce better patient flow than (a) the static
Manchester Triage System (MTS) streaming protocol and (b) a load-aware heuristic? The MoA has
specialist agents and an aggregator, is constrained by hard protocol rules, and sees the current
queue state. The comparison uses the same simulated emergency department and the same patients
(common random numbers).

The author's prior is that a well-built AI router should outperform rule-based routing. The
confirmatory hypotheses, one per primary metric, comparator and scenario, are: the queue-aware MoA
has a **lower** mean doctor wait, P90 doctor wait, mean time to needed imaging and mean length of
stay, and a protocol-violation rate **not higher** than the comparator. Every test is two-sided.
A result in either direction is reported.

## 2. Simulated system (frozen)

`v2/sim.py`, `v2/scenarios.py`, `v2/data/cases.csv`. Summary:

- **One Type 1 ED with a co-located Urgent Treatment Centre (UTC).** The resources are ED doctors
  (4), UTC doctors (2), X-ray (1), CT (1), ultrasound (1), a specialty-review pool (3) and
  assessment-unit beds (45). Every queue is a non-preemptive priority queue, ordered by MTS
  category and then first come, first served.
- **Arrivals:** a non-homogeneous Poisson process. The mean is 11.1/h: 17,351,235 Type 1
  attendances in 2024-25 / 178 Type 1 EDs / 8,760 h. The hour-of-day profile is ECDS 2024-25.
  Sources are in `v2/scenarios.py`.
- **Patients:** 159 Synthea emergency encounters (`v2/cases.py`), resampled with replacement and
  weighted so that 27.9% of patients are admitted (the Type 1 conversion rate, NHS England, March
  2025). Each case has two parts. The **triage record** is MTS category, discriminator, complaint,
  age, sex and ethnicity; the router sees all of it except ethnicity. The **ground truth** is
  X-ray / CT / ultrasound need, specialist review and admission. The router never sees it; it is
  derived from the encounter's own coded records, or from the cited guideline where Synthea does
  not model the test.
- **Pathways:** see the `v2/sim.py` docstring. A route changes only the order and place of care. An
  imaging-first route performs that scan, even when the patient does not need it. A doctor-first
  patient who needs imaging gets a second, shorter doctor contact to review the results. A UTC
  patient who needs CT, ultrasound, a specialist or a bed is re-streamed to the ED and assessed
  again.
- **Hard protocol rules:** these are enforced by the simulator's guard, not by the router.
  - H1: red and orange patients are never sent to the UTC.
  - H2: green and blue patients never go to imaging before a doctor.
  - H3: every pathway contains a doctor contact.
- **State shown to load-aware routers:** for each candidate route, the expected wait of a new patient
  of this priority, in three bands: short < 30 min, moderate 30-90 min, long > 90 min. The rule
  baseline and the LLM receive the same bands.
- **Service times** are lognormal and **capacities** are fixed. Both are assumptions, listed with
  their sources in `v2/scenarios.py`. Capacities were chosen on development seeds so that the base
  scenario is stable over the day. The validation targets were the median time to treatment (about
  63 min) and the median total time in A&E (about 166 min) from NHS England's provisional A&E
  quality indicators, October 2025.

## 3. Arms

| Arm | What it is |
|---|---|
| `rule_mts` | Static protocol. Red, orange and yellow go to the ED doctor; green and blue go to the UTC. Imaging before the doctor is used only for suspected stroke (CT) and suspected fracture (X-ray, yellow or above). |
| `load_aware` | `rule_mts` plus queue-aware streaming: a green or blue patient goes to the ED instead of the UTC when the UTC's band is worse than the ED's. |
| `moa_load` (**primary AI arm**) | Four specialist agents (neurology, cardio-respiratory, abdominal, trauma/MSK) and an aggregator that sees the expected-wait bands. qwen2.5:7b. |
| `moa_static` (secondary) | The same MoA, but the aggregator does not see the queue state (an ablation of queue awareness). |

**LLM settings:**
- qwen2.5:7b (Q4_K_M), served by Ollama 0.21.2 on the local machine.
- temperature 0, seed 0, num_ctx 12288, num_predict 220.
- Ollama structured outputs (JSON schema). The aggregator's schema allows all five routes, so a
  protocol breach is possible and is measured.

**Failure handling.** Each of these is counted per patient and reported:
- A transport error is retried at most 5 times, 30 s apart.
- An unparseable or invalid aggregator answer falls back to the `rule_mts` route.
- A protocol-violating proposal is blocked by the guard and falls back to the `rule_mts` route.
- An invalid specialist answer counts as that specialist abstaining.

## 4. Design

- **Scenarios:** `base` (11.1 arrivals/h) and `stress` (+20% arrivals, same staff). Sensitivity scenario `base_review`: the base scenario, except that an imaging-first patient still needs a separate doctor review of the result. This removes the doctor-time saving that the model otherwise credits to imaging first, an assumption that favours any router that uses imaging first more often.
- **Replications:** 30 held-out seeds, **1000-1029**, for every arm and scenario. Common random
  numbers: one stream drives arrivals and case draws, and each patient's service times are pre-drawn
  from a patient-specific stream. Arms with the same seed therefore see identical patients.
- **Development seeds:** 100-119, used only for design, prompt iteration and capacity choice. They
  are never part of the confirmatory results.
- **Warm-up:** 48 h. The development Welch curves (`results_v2/dev/welch_*.csv`) are flat after
  day 1 in the base scenario. The stress scenario is near-critical, with daily doctor utilisation
  above 0.9, and drifts slowly; its absolute levels depend on the horizon, while the paired
  comparisons remain valid under common random numbers.
- **Horizon:** a 7-day measurement window. Arrivals continue after the window, and each run
  continues until every window patient has left, up to 14 days. A patient still in the system at
  that limit is kept, with a lower-bound time, and counted as censored.
- **The held-out evaluation is run once:** `python -m v2.run sim --seeds heldout` for the three
  scenarios and all four arms. No run, seed or patient is dropped.

## 5. Metrics

Each metric is computed per replication over patients arriving in the measurement window.

### 5.1 Primary
1. Mean doctor wait: arrival to the start of the first doctor contact (ED or UTC).
2. 90th percentile of doctor wait.
3. Mean time to imaging, for patients who need imaging: arrival to the start of the first scan they
   need.
4. Mean length of stay (LOS): arrival to leaving the ED, which is discharge or getting a bed.
5. Protocol-violation rate: the share of patients whose router-proposed route breaks H1 or H2,
   measured before the guard.

**Must-be-zero check, not tested:** the share of patients who never see a doctor.

### 5.2 Secondary
- Fallback rate.
- Censored share.
- UTC-to-ED re-stream rate.
- Unnecessary-scan rate.
- Imaging-first rate.
- UTC rate.
- Doctor contacts per patient.
- P90 LOS.
- Utilisation of each resource over the window.
- LLM call counts, cache hits and errors.

### 5.3 Fairness
- **(a) Outcome gaps.** For each replication, the gap is the maximum minus the minimum, across the
  six sex × ethnicity groups (F/M × Asian/Black/White), of mean doctor wait and of mean LOS.
- **(b) Counterfactual swaps.** One case per presentation (the first by `case_id`, 23 cases) is
  routed by the state-blind MoA under all 6 sex × ethnicity descriptions, with ethnicity stated in
  the vignette (the deployed router never receives ethnicity). The outcome is the share of routes
  that change relative to the case's own recorded description, overall, for a sex-only swap and for
  an ethnicity-only swap, with Wilson 95% CIs. This part is descriptive only.

## 6. Analysis

- For each metric: the per-arm mean and the 95% t-interval over the 30 replications.
- **Comparisons** are paired differences by seed (arm minus comparator), with a 95% t-interval and
  a two-sided one-sample t-test on the differences. A difference that is identically 0 gets p = 1.
- **Primary family:** `moa_load` vs `rule_mts` and vs `load_aware`, × 5 primary metrics × 2
  scenarios = 20 tests, Holm-adjusted together.
- **Verdict per test:**
  - "AI better": difference < 0 and p_Holm < 0.05.
  - "AI worse": difference > 0 and p_Holm < 0.05.
  - Otherwise "no detectable difference". This is not evidence of equivalence.
- **Secondary family:** `moa_static` vs `rule_mts`, `load_aware` and `moa_load` on the same 5
  metrics × 2 scenarios, Holm within that family.
- **Fairness family (a):** `moa_load` vs each baseline on both gap metrics × 2 scenarios, Holm
  within that family.
- **Sensitivity family:** `moa_load` vs each baseline on the 5 primary metrics in `base_review`,
  Holm within that family. It is not part of the confirmatory verdict, and is reported next to it.
- **Not done:** no outlier removal, no transformation, no change of seeds, metrics, horizon or
  arms after the held-out results are seen.

## 7. What was tuned on development seeds only

- Service-time assumptions, capacities and band edges (30/90 min).
- The 48 h warm-up.
- Prompt wording (`PROMPT_VERSION`).
- The choice of qwen2.5:7b. It is the only model that fits in memory alongside other work on this
  machine; qwen2.5:14b is an optional extension and is not part of this registration.

## 8. Development-seed results (seeds 100-119, prompt v2.2), recorded before the held-out run

These are reported only so that readers can compare them with the held-out run. They are not
evidence, and they are in `results_v2/dev/tables.md`.

**Base scenario:** `moa_load` minus `rule_mts`.
- Mean doctor wait: -4.7 ± 2.1 min.
- P90 doctor wait: -20 ± 13 min.
- Time to needed imaging: -54 ± 3 min.
- LOS: -10 ± 2 min.
- Zero protocol violations and zero fallbacks.

**Stress scenario:**
- Time to imaging: -105 ± 12 min.
- Doctor waits: no detectable difference.

**Fairness:** the group-gap metrics were larger for the MoA, mainly through case mix in small
groups.

**What drives the effect:** the MoA uses imaging first for 32% of patients against 14% for the rule,
which gives fewer doctor contacts (1.08 against 1.25 per patient). It streams fewer green patients
to the UTC (33% against 42%).

**Sensitivity scenario `base_review`:** when imaging first does not save the review contact, the
direction reverses.
- Mean doctor wait: +32 ± 5 min against `rule_mts`.
- LOS: +35 ± 6 min.
- Time to imaging: still -65 ± 3 min.

## 9. Known limitations (stated in advance)

- Synthetic patients: 159 Synthea encounters from 1 US-state run, resampled.
- The complaint text is written by the author from the coded condition. It is not clinician-written.
- The ground truth follows guidelines and is not clinician-adjudicated.
- Staffing is constant with no rota.
- One model family at 7B parameters.
- Service times are assumptions.
- The simulation measures operational flow, not patient outcomes.
