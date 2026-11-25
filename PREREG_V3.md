# Pre-registration v3: harm guards for LLM mixture-of-agents post-triage routing

This file registers the confirmatory v3 evaluation. It is committed **before** any v3 held-out run.
The registration is the commit that adds this file; the commit hash is recorded in
`results_v3/logs/heldout_commit.txt` when the held-out run starts. This file will not be edited after
that commit. Any deviation will be reported in `RESULTS_V3.md` under "Deviations from the
pre-registration".

- Author: Raunak Burrows. The design, code and analysis were produced by an AI coding agent (Claude,
  Anthropic) under the author's direction; see the paper's acknowledgments.
- Code: the `v2/` package run with `STUDY=v3` (`v2/scenarios.py`). `STUDY=v2` (the default) still
  reproduces the v2 study bit for bit; this was checked on held-out seeds 1000 and 1001 for
  `rule_mts`, `load_aware` and `moa_load` in `base` and `base_review` after the v3 changes.
- Prompts: **unchanged** from v2 (`PROMPT_VERSION = "v2.2"` in `v2/moa.py`). No prompt was edited
  for v3. The model, options, schemas and cache are those of v2.
- Analysis code: `v2/analyze.py` (sections 6-7 below), `v2/explore.py` (exploratory).

## 0. Why v3 exists, and what was known when it was designed

v3 was designed **after** the v2 held-out results were seen (`RESULTS_V2.md`; seeds 1000-1029, used
once). It is therefore not independent of v2: v2 is the development history, v3 is the confirmatory
study of the guarded design. The v2 held-out seeds are never used for v3 claims; v3 uses fresh
held-out seeds (section 4).

The v2 study found that the MoA beat both baselines on 14 of 16 primary comparisons. The result
depended on the assumption that imaging first saves a doctor contact: it reversed in the
`base_review` sensitivity scenario. Exploratory per-presentation analysis showed three clinical harms:

1. **Low-risk whiplash (green) sent to the ED instead of the UTC.** These patients then waited
   +262 min (base) and +768 min (stress) longer for a doctor.
2. **Red/orange patients sent to CT or ultrasound before the doctor** (gunshot wound, traumatic brain
   injury, appendicitis). They saw a doctor about 25-30 min later.
3. **Suspected hip fracture given a CT before the X-ray it needed.** LOS rose by +34 min.

## 1. Changes from v2 (everything else is identical)

### 1.1 Guard and pathway rules (apply to every arm; enforced by the simulator, not the router)

| Rule | What it does | Clinical basis (verified source) |
|---|---|---|
| **R1** UTC eligibility | A green or blue patient is streamed to the UTC. The ED is an allowed route only when the UTC's expected-wait band is worse than the ED's (the overflow rule the `load_aware` baseline already uses). | NHS England, *Urgent treatment centres - principles and standards* (2023): UTCs see minor injuries and minor ailments and should act as the front door to a co-located ED. NICE NG41 rec. 1.1.5 (Canadian C-spine rule): a minor rear-end collision and being ambulatory are low-risk factors, and a low-risk patient who can rotate the neck has no risk (no imaging); Stiell et al., JAMA 2001. |
| **R2** Team at the scanner | For red and orange patients, an imaging-first route no longer delays the doctor. The doctor contact starts in parallel with the scan (the team meets the patient in imaging); treatment starts when the doctor contact ends, and disposition waits for the scan. | MTS target times: red immediate, orange 10 min (Manchester Triage Group). NICE NG39 rec. 1.4.3-1.4.4 (major trauma: imaging is part of the primary survey and is interpreted immediately). NICE NG128 rec. 1.3.2 (suspected stroke: brain imaging immediately). NICE NG232 rec. 1.5.8 (head injury: CT within 1 h of risk factors being identified). |
| **R3** X-ray first for suspected fracture | A yellow patient whose triage record matches the static protocol's suspected-fracture pattern (deformity, unable to weight-bear, unable to stand, shortened leg) goes X-ray first. No CT first; the X-ray is not deferred until after the doctor. | NICE CG124 rec. 1.1.1 (hip fracture: MRI if fracture is suspected despite negative X-rays; CT only if MRI is unavailable within 24 h or contraindicated). NICE NG38 (suspected fractures: X-ray, decided with the Ottawa rules). Nurse-requested radiographs: Thurston & Field, J Accid Emerg Med 1996. |

The H1-H3 rules of v2 are unchanged. As in v2, the MoA aggregator is offered only the routes the
guard allows; a route outside that set is still possible under the output schema, is blocked by the
guard, falls back to the static protocol route, and is counted as a protocol violation. With R1 and
R3, many patients have a single allowed route. The MoA then returns it without an aggregator call
(`source = moa_single_candidate`). In v2 the single route was always "ED".

R1 and R3 restrict the routers. In practice they leave `rule_mts` and `load_aware` unchanged, because
those baselines already follow them. R2 is a pathway change and affects every arm that routes
red/orange patients to imaging first, including `rule_mts`, which sends suspected stroke to CT first.

### 1.2 The review-contact assumption (decided, with reason)

In v2 base, a patient imaged before the doctor needed no separate review contact, and no doctor
time was spent on the result. That credited imaging first with a free saving of doctor time.
`base_review` (separate, queued review contact) reversed the v2 result.

**v3 base and stress use a middle assumption, "folded" review.** When the scan precedes the doctor,
the result is read in the same contact. The contact therefore lasts the assessment time **plus** the
review time (doctor time is not saved), but there is no second wait in the queue. The reasons:
- Reading and explaining a result is real doctor work, so it is not treated as free.
- With the result available at the first contact, the patient does not have to queue a second time.
  This is the stated aim of nurse-initiated imaging (Thurston & Field 1996). NHS England's UTC
  standards ask for post-X-ray review protocols that avoid duplication.
- It is conservative relative to v2: it removes the doctor-time saving that drove the v2 gain.

If a patient imaged first also needs another scan, a separate review still follows, as in v2.
`base_review` is kept unchanged as the pre-registered pessimistic sensitivity scenario: imaging first
still needs a separate, queued review contact.

### 1.3 Unchanged

Arrivals (11.1/h, ECDS 2024-25 hourly profile), the case pool (159 Synthea encounters, 27.9%
admitted), capacities (ED doctors 4, UTC doctors 2, X-ray/CT/US 1 each, specialty pool 3, beds 45),
service-time assumptions, wait bands (30/90 min), warm-up (48 h), window (7 days), drain limit (14
days), the four arms, prompts, model and LLM options.

Capacities were **not** re-tuned for v3. With the folded review, the static protocol's base
operating point on development seeds is:
- median time to first doctor 77 min (national median time to treatment: 63 min);
- median LOS 202 min (national median total time in A&E: 166 min);
- ED-doctor utilisation 0.86 (v2: 0.80).

The **stress** scenario (+20% arrivals, same staff) is now **overloaded**: ED-doctor utilisation is
about 0.995 on development seeds and queues grow through the week. Stress results are therefore those
of a finite one-week overload episode. Their absolute levels depend on the horizon, and a small share
of patients (about 1% on development seeds) is still present at the 14-day drain limit. Such patients
are kept with lower-bound times and counted as censored, as registered in v2. Comparisons stay paired
under common random numbers.

## 2. Hypotheses

The author's prior, stated in advance, is that the guarded AI router should still beat rule-based
routing. The development-seed results in section 8 already point the other way on doctor wait. The
hypotheses are registered as in v2, and every test is two-sided.

- **Primary (confirmatory).** Compared with each baseline (`rule_mts`, `load_aware`), the queue-aware
  MoA (`moa_load`) has a lower mean doctor wait, P90 doctor wait, mean time to needed imaging and mean
  LOS, and a protocol-violation rate that is not higher. Scenarios: `base` and `stress`.
- **Harm (confirmatory, new in v3).** In each of the three v2 harm subgroups, `moa_load` is no worse
  than `rule_mts` by more than a margin of 10 min (section 6.4).

## 3. Arms

These are unchanged from v2: `rule_mts`, `load_aware`, `moa_load` (primary AI arm), `moa_static`
(state-blind ablation). The model is qwen2.5:7b (Q4_K_M), Ollama 0.21.2, temperature 0, seed 0,
num_ctx 12288, num_predict 220, JSON-schema structured outputs, served locally.

## 4. Design

- **Scenarios:** `base`, `stress`. Sensitivity: `base_review`.
- **Development seeds:** 100-119 (as v2). Used for every v3 design decision.
- **Held-out seeds:** **2000-2029**, never run before this registration. Run once:
  `STUDY=v3 python -m v2.run sim --scenario <s> --seeds heldout` for the three scenarios, all four
  arms. No run, seed or patient is dropped.
- Common random numbers, warm-up, window and drain are as in v2. The v3 Welch curves
  (`results_v3/dev/welch_*.csv`, static protocol, 20 development seeds, empty start) were checked:
  - base: the daily mean doctor wait is 96-110 min over days 0-9, a mild upward drift at ED-doctor
    utilisation 0.86;
  - stress: it climbs from day 1 (overload, section 1.3).

  The 48 h warm-up is kept.

## 5. Metrics (per replication, patients arriving in the window)

### 5.1 Primary
These are as in v2: mean doctor wait, P90 doctor wait, mean time to needed imaging, mean LOS,
protocol-violation rate (proposal outside the allowed set, measured before the guard). The share
never seen by a doctor is a must-be-zero check.

The violation rate now counts breaches of R1 and R3 as well as H1 and H2.

### 5.2 Secondary
These are as in v2: fallback rate, censored share, re-stream rate, unnecessary-scan rate,
imaging-first rate, UTC rate, doctor contacts per patient, P90 LOS, utilisation, LLM call counts.

### 5.3 Fairness
These are as in v2:
- (a) The gaps across the six sex x ethnicity groups (max - min) in mean doctor wait and mean LOS.
- (b) The counterfactual swap probe: 23 cases (the first case of each presentation by `case_id`) x
  6 descriptions, routed by the state-blind MoA with the v3 guard sets
  (`STUDY=v3 python -m v2.run fairness`). Descriptive only.

### 5.4 Harm subgroups (new)
These are per-replication means within subgroups defined on the triage record, so they do not depend
on the route:
- `harm_whiplash_dw`: mean doctor wait of whiplash (green) patients.
- `harm_ro_imaging_dw`: mean doctor wait of gunshot, traumatic brain injury and appendicitis
  patients (red/orange).
- `harm_hip_los`: mean LOS of suspected hip fracture patients.

A replication in which a subgroup is empty is left out of that comparison only. The number of seeds
used is reported.

## 6. Analysis (implemented in `v2/analyze.py`)

The method is unchanged from v2:
- per-arm mean and 95% t-interval over 30 replications;
- paired differences by seed (arm minus comparator), each with a 95% t-interval and a two-sided
  one-sample t-test;
- an identically zero difference gets p = 1;
- Holm adjustment within each family.

Verdicts:
- "AI better": difference < 0 and p_Holm < 0.05.
- "AI worse": difference > 0 and p_Holm < 0.05.
- Otherwise "no detectable difference", which is not evidence of equivalence.

1. **Primary family (confirmatory):** `moa_load` vs `rule_mts` and vs `load_aware`, x 5 primary
   metrics x {base, stress} = 20 tests, Holm together.
2. **Secondary family:** `moa_static` vs `rule_mts`, `load_aware` and `moa_load`, same 5 metrics x 2
   scenarios, Holm within the family.
3. **Fairness family (a):** `moa_load` vs each baseline, 2 gap metrics x 2 scenarios = 8 tests, Holm
   within the family.
4. **Harm family (confirmatory, new):** `moa_load` vs `rule_mts`, 3 harm metrics x {base, stress} =
   6 tests, Holm within the family. A harm is called **removed** if the upper limit of the 95%
   t-interval of the paired difference is **below +10 min**. It is called **still present** if the
   difference is > 0 with p_Holm < 0.05. Anything else is called **inconclusive**.
5. **Sensitivity family:** `moa_load` vs each baseline on the 5 primary metrics in `base_review`,
   Holm within the family. It is reported next to the primary verdict, not as part of it.

**Not done:** no outlier removal, no transformation, and no change of seeds, metrics, horizon, arms,
rules or prompts after held-out results are seen.

## 7. Exploratory (labelled as such when reported)

- The per-presentation table (all replications pooled; `v2/explore.py`) for base and stress.
  Presentations where `moa_load - rule_mts` exceeds +15 min in mean doctor wait or mean LOS are listed
  as possible new harms.
- The case-mix-standardised group gaps (`v2/explore.py`), as in v2.
- A descriptive v2-vs-v3 comparison of the harm subgroups. v2 and v3 use different seeds and
  different pathway rules, so this comparison is not paired and is not tested.

## 8. What was decided on development seeds (100-119), before this registration

- **R2 timing (implementation fix).** In the first implementation, treatment started only after
  both the scan and the parallel doctor contact had ended. A doctor-first patient starts treatment
  when the contact ends. The fix makes R2 consistent with that, and it was found because gunshot/TBI
  LOS rose about 11-13 min on development seeds.
- **R3 (rule change).** R3 first only removed CT-first for a suspected fracture. On development
  seeds the MoA then chose ED-first for hip fracture, and hip-fracture LOS rose +79 min against the
  static protocol. NICE CG124 and NG38 put the X-ray first, so R3 was tightened to "X-ray first".
- **Capacities.** Kept at the v2 values (section 1.3). Raising ED doctors to 5 was tried on 10
  development seeds: the median time to first doctor fell to 30 min, far below the 63 min target, so
  4 was kept.
- **Prompts.** Not changed.

### Development-seed results (prompt v2.2, v3 rules), recorded before the held-out run

Paired differences `moa_load - rule_mts`, mean ± 95% CI half-width over 20 development seeds:

| Metric | base | stress | base_review (sensitivity) |
|---|---|---|---|
| Mean doctor wait (min) | +10.0 ± 1.3 | +38.2 ± 9.7 | +3.3 ± 1.0 |
| P90 doctor wait (min) | +30.2 ± 5.7 | +78.0 ± 16.9 | +7.6 ± 4.4 |
| Time to needed imaging (min) | -72.1 ± 3.6 | -217.2 ± 34.1 | -67.6 ± 3.3 |
| Mean LOS (min) | -1.9 ± 1.4 | -17.6 ± 20.8 | +0.3 ± 1.0 |
| Protocol violations | 0 vs 0 | 0 vs 0 | 0 vs 0 |

Development seeds therefore show that once imaging first no longer saves doctor time, the MoA's
imaging-first routing gives much faster imaging but **longer** waits for a doctor, and LOS changes
little. The MoA sends 33% of patients to imaging first, against 14% under the static protocol.

Harm subgroups (`moa_load - rule_mts`):
- whiplash doctor wait: +3.4 ± 6.3 (base), +37.5 ± 37.7 (stress);
- gunshot/TBI/appendicitis doctor wait: +1.3 ± 0.4 (base), +1.4 ± 0.4 (stress);
- hip-fracture LOS: +22.0 ± 15.7 (base), +143 ± 107 (stress).

All three harms are gone at the level of the route: whiplash stays in the UTC, red/orange imaging no
longer delays the doctor, and hip fracture gets the X-ray first in both arms. Hip-fracture LOS is still
longer, however. The pooled per-presentation table shows the same +22 min for every X-ray-first
fracture presentation. The MoA's extra X-ray-first patients (heart failure, lung mass, knee injury)
lengthen the queue for the single X-ray room. This spill-over is a property of the guarded design and
is left in. Nothing was changed to remove it.

Gunshot and TBI LOS remains about +10-12 min (pooled, base): under the folded review, treatment starts
when the longer combined contact ends. A change that would start treatment at the end of the
assessment part was considered and **not** made. It would favour the AI arm and was suggested only by
development results.

Fairness (a), development seeds: the doctor-wait gap is wider for `moa_load` (+12.9 ± 4.1 base,
+45.9 ± 24.7 stress, against `rule_mts`). The LOS gap shows no detectable difference.

No fallbacks, no protocol violations and no LLM errors occurred. The v3 development runs needed 178
new LLM calls in total; all other calls were cache hits on v2 calls.

These are not evidence. They are in `results_v3/dev/tables.md` and `results_v3/dev/exploratory.md`.

## 9. Known limitations (stated in advance)

These are as in v2: synthetic patients (159 Synthea encounters), author-written complaint text,
guideline-derived ground truth not adjudicated by clinicians, constant staffing, one 7B model,
assumed service times, and flow outcomes rather than patient outcomes. In addition:
- **v3 was designed after seeing v2's held-out harms.** Fresh seeds protect against seed-level
  overfitting, but not against design choices made in response to v2. The harm family tests exactly
  the harms v2 exposed, so harms of a different kind would only show up in the exploratory sweep.
- **R1 and R3 remove LLM discretion** for green/blue patients (outside UTC overflow) and for yellow
  suspected fractures. Part of any improvement on those subgroups is therefore true by construction;
  the confirmatory question is what the guarded router does to the department as a whole.
- **Overloaded stress scenario** (section 1.3).
