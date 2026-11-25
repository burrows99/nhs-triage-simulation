# Results v3: guarded LLM mixture-of-agents routing (held-out, pre-registered)

This is the evaluation registered in [PREREG_V3.md](PREREG_V3.md).

- **Registration commit:** `ef136ec` (`ef136eccf01a2d20cbfc0caf732cb1abf8be644b`).
- **Held-out run:** seeds 2000-2029, run once at that commit (`results_v3/logs/heldout_commit.txt`,
  `results_v3/logs/heldout.sh`).
- **Model:** qwen2.5:7b (Q4_K_M), Ollama 0.21.2; prompts v2.2, unchanged from v2.

Every number comes from `results_v3/heldout/tables.md`, `paired_tests.csv` and `exploratory.md`.
These are written by `STUDY=v3 python -m v2.run analyze --seeds heldout` and
`STUDY=v3 python -m v2.explore heldout`. The figures are in `publishing/figures/out/p2j_*`
(`publishing/figures/make_figures.py`).

## Summary

Paired differences `moa_load` minus each baseline over 30 seeds, with 95% CIs, Holm-adjusted over
the 20 primary tests. Negative means the MoA is better.

| Scenario | Metric | vs static MTS protocol | vs load-aware heuristic |
|---|---|---|---|
| base | Mean doctor wait | +9.5 ± 1.2 min (+9.0%), **AI worse** | +10.1 ± 0.7 (+9.5%), **AI worse** |
| base | P90 doctor wait | +29.8 ± 5.1 (+11.3%), **AI worse** | +29.3 ± 3.3 (+11.1%), **AI worse** |
| base | Time to needed imaging | -73.5 ± 3.6 (-75.0%), **AI better** | -74.9 ± 3.7 (-75.4%), **AI better** |
| base | Mean LOS | -2.7 ± 0.9 (-1.1%), **AI better** | -3.3 ± 0.9 (-1.3%), **AI better** |
| base | Protocol violations | 0 vs 0 | 0 vs 0 |
| stress | Mean doctor wait | +34.0 ± 8.5 (+12.0%), **AI worse** | +27.6 ± 4.8 (+9.5%), **AI worse** |
| stress | P90 doctor wait | +69.6 ± 11.1 (+11.5%), **AI worse** | +67.1 ± 10.9 (+11.0%), **AI worse** |
| stress | Time to needed imaging | -197.6 ± 23.8 (-77.6%), **AI better** | -198.6 ± 23.9 (-77.6%), **AI better** |
| stress | Mean LOS | -15.8 ± 14.4 (-2.1%), no detectable difference (p_Holm 0.16) | -30.1 ± 8.8 (-3.9%), **AI better** |
| stress | Protocol violations | 0 vs 0 | 0 vs 0 |

**Primary verdict (16 testable comparisons).**
- AI better on 7: time to imaging 4 of 4, LOS 3 of 4.
- AI worse on 8: mean and P90 doctor wait, both comparators, both scenarios.
- No detectable difference on 1: stress LOS against the static protocol.
- The protocol-violation tests cannot be tested (0 against 0).
- The author's prior, that the guarded AI router would beat rule-based routing, is **not**
  supported on doctor wait. It is supported on imaging, and weakly on LOS.

**Compared with v2.** In v2 the MoA was better on 14 of 16. In v3 the conservative review assumption
removes the doctor time that v2 credited to imaging first, and the doctor-wait advantage turns into a
disadvantage. The imaging advantage stays.

## Harm family (confirmatory; `moa_load` minus `rule_mts`; Holm within 6 tests; margin +10 min)

| Harm subgroup | Scenario | v3 difference | p_Holm | Registered call | v2 (seeds 1000-1029, descriptive) |
|---|---|---|---|---|---|
| Whiplash (green): doctor wait | base | -0.5 ± 3.9 | 0.78 | **removed** | +262.3 ± 14.3 |
| Whiplash (green): doctor wait | stress | +21.0 ± 24.4 | 0.18 | **inconclusive** (upper limit 45 > 10; not significant) | +758.1 ± 176.2 |
| Gunshot/TBI/appendicitis: doctor wait | base | +1.5 ± 0.4 | 9e-8 | **removed** by the margin rule (upper limit 1.9 < 10), though a small worsening is detectable | +27.3 ± 0.7 |
| Gunshot/TBI/appendicitis: doctor wait | stress | +1.8 ± 0.4 | 4e-9 | **removed** by the margin rule, small worsening detectable | +28.6 ± 0.6 |
| Suspected hip fracture: LOS | base | +11.1 ± 10.3 | 0.11 | **inconclusive** (upper limit 21 > 10) | +37.0 ± 17.4 |
| Suspected hip fracture: LOS | stress | +101.4 ± 29.6 | 4e-7 | **still present** | +131.2 ± 35.5 |

The v2 column is recomputed from `results_v2/heldout/*/patients_*.csv.gz` with the same subgroup
definitions. Its seeds and pathway rules differ from v3, so it is descriptive only, not a paired
comparison.

The registered rules are ambiguous for the red/orange subgroup: the difference is both below the
margin and significantly greater than 0. It is reported under both readings.

**Harms at the level of the route.**
- **Whiplash.** In base, 4.3% of whiplash patients went to the ED under `moa_load`, all through the
  R1 overflow exception. In v2 it was every whiplash patient, and under `load_aware` it is 3.3%. The
  state-blind MoA sent 11.6% of whiplash patients to the ED, because R1 opens the ED to it whenever
  the UTC overflows, even though it cannot see the queues.
- **Red/orange imaging.** Imaging first no longer delays the doctor; R2 runs the two in parallel.
- **Hip fracture.** Hip fractures go X-ray first in every arm.

**Harms that remain through spill-over (exploratory).**
- **Fracture patients.** Every X-ray-first fracture presentation waits longer for the doctor
  (ankle +21.0, upper limb +21.6, hip +18.0 min in base; about +65 in stress), though its route is
  the same as under the static protocol. For the three fracture presentations together, about 7 of
  the 21 min in base is a longer X-ray queue (time to X-ray 13.8 to 21.3 min). The rest is a longer
  queue for the ED doctor after the scan. The MoA's extra imaging-first patients enter the yellow
  doctor queue with the review work folded into their first contact.
- **Gunshot, TBI and appendicitis LOS.** These are +10.5 to +12.3 min in base. Under the folded
  review, treatment starts when the longer combined contact ends (PREREG_V3 section 8).

## Primary metrics (mean ± 95% CI over 30 replications)

**base** (1,864 patients per replication on average, range 1,786-1,946)

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Doctor wait, mean (min) | 106.6 ± 4.4 | 106.0 ± 4.6 | 116.1 ± 4.9 | 116.4 ± 4.9 |
| Doctor wait, P90 (min) | 264.4 ± 11.5 | 264.9 ± 12.5 | 294.2 ± 14.0 | 292.6 ± 13.7 |
| Time to needed imaging (min) | 98.0 ± 4.3 | 99.4 ± 4.4 | 24.5 ± 2.3 | 24.4 ± 2.3 |
| LOS, mean (min) | 242.3 ± 6.9 | 242.9 ± 7.2 | 239.6 ± 6.8 | 238.5 ± 6.6 |

**stress** (2,238 per replication, range 2,159-2,324)

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Doctor wait, mean (min) | 282.7 ± 24.5 | 289.1 ± 24.1 | 316.6 ± 27.4 | 313.4 ± 26.8 |
| Doctor wait, P90 (min) | 606.2 ± 55.1 | 608.7 ± 55.1 | 675.8 ± 64.5 | 683.2 ± 65.6 |
| Time to needed imaging (min) | 254.8 ± 27.0 | 255.8 ± 27.0 | 57.2 ± 4.9 | 54.0 ± 3.5 |
| LOS, mean (min) | 760.3 ± 69.9 | 774.6 ± 67.4 | 744.5 ± 62.0 | 735.5 ± 62.6 |

**base_review** (sensitivity: separate, queued review contact after imaging first)

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Doctor wait, mean (min) | 101.7 ± 4.2 | 100.9 ± 4.4 | 104.3 ± 4.4 | 104.7 ± 4.4 |
| Doctor wait, P90 (min) | 250.0 ± 10.8 | 249.1 ± 11.2 | 254.9 ± 11.4 | 254.3 ± 11.3 |
| Time to needed imaging (min) | 92.4 ± 4.1 | 93.6 ± 4.1 | 23.3 ± 2.4 | 23.7 ± 2.3 |
| LOS, mean (min) | 244.3 ± 7.2 | 244.7 ± 7.5 | 244.1 ± 7.4 | 243.2 ± 7.3 |

**Sensitivity family** (`moa_load` minus `rule_mts`):
- mean doctor wait +2.7 ± 1.0 (AI worse, p_Holm 9e-5);
- P90 +4.9 ± 4.0 (no detectable difference);
- imaging -69.1 ± 3.3 (AI better);
- LOS -0.3 ± 1.0 (no detectable difference).

Against `load_aware`: doctor wait +3.4 ± 0.5 and P90 +5.9 ± 1.7 (AI worse), imaging -70.3 ± 3.3
(AI better), LOS -0.7 ± 0.7 (no detectable difference).

When every arm pays a separate review contact, the doctor-wait penalty shrinks from +9.5 to +2.7 min.
Much of the base penalty is therefore the review work moving into the first contact. In the doctor
wait metric, that work counts before the first contact instead of after it.

## Operating point and validation (base, static protocol, held-out)

| | Model | NHS England, October 2025 (all department types) |
|---|---|---|
| Median time to first doctor | 78.0 min | 63 min (median time to treatment) |
| Median LOS | 204.9 min | 166 min (median total time in A&E) |

- Utilisation in base: ED doctors 0.86, UTC doctors 0.78, beds 0.83.
- Utilisation in stress: 0.99, 0.93, 0.94.
- Censored in stress: 634-675 patients per arm over 30 seeds (about 1% of patients). In base and
  `base_review`, none.

**Must-be-zero check, stress.** 14 (`load_aware`), 19 (`moa_load`) and 7 (`moa_static`) of the 67,132
patients per arm had not yet seen a doctor at the 14-day drain limit. All of them are censored patients
still queuing. No completed patient left without a doctor. In base and `base_review` the count is 0 in
every arm.

## Secondary

- **Imaging first:** 33.1% (`moa_load`) against 14.6% (`rule_mts`) in base.
- **Doctor contacts per patient:** 1.06 against 1.25.
- **UTC rate:** 40.3% against 41.8%.
- **Unnecessary scans:** 0 in every arm. In v2 the MoA's rate was 0.38%; R3 removed it.
- **Re-stream rate:** about 1.4-1.5% in every arm.
- **P90 LOS, base:** 469.4 (`moa_load`) against 476.9 (`rule_mts`).
- **P90 LOS, stress:** 914.7 against 1103.0.
- **State-blind MoA:** no different from the queue-aware MoA in base. In stress it was better on LOS
  (-9.0 ± 5.8, p_Holm 0.043) and worse on P90 doctor wait (+7.4 ± 2.6). Queue awareness still adds
  nothing of practical size.

## LLM operation

- **Fallbacks, protocol violations, invalid outputs, transport errors:** 0 in every held-out arm and
  scenario.
- **Routing decisions, `moa_load`, base:** 55,935. Of these, 37,267 (66.6%) had a single allowed
  route and were returned without an aggregator call; 18,668 went through the aggregator.
- **New LLM calls during the held-out run:** 15 (5 base, 7 stress, 3 base_review). Everything else
  was a cache hit.

## Fairness

**(a) Pre-registered group gaps** (Holm within 8 tests), `moa_load` minus each baseline:

| Scenario | Gap | rule_mts | moa_load | vs rule_mts | vs load_aware |
|---|---|---|---|---|---|
| base | doctor wait | 50.3 ± 3.2 | 65.1 ± 4.4 | **+14.8 ± 3.3, AI worse** | **+13.2 ± 4.7, AI worse** |
| base | LOS | 77.5 ± 5.8 | 74.9 ± 5.3 | -2.6 ± 4.2, n.d. | -4.2 ± 4.2, n.d. |
| stress | doctor wait | 137.0 ± 16.7 | 184.5 ± 30.8 | **+47.5 ± 26.5, AI worse** | **+32.8 ± 17.9, AI worse** |
| stress | LOS | 1000.4 ± 149.0 | 1022.0 ± 140.9 | +21.7 ± 27.1, n.d. | -12.8 ± 12.6, n.d. |

The doctor-wait gap still widens, but by about half as much as in v2 (+30.2 base and +83.0 stress in
v2). The LOS gap no longer differs detectably; in v2 it widened by +39.3 and +75.0.

**(b) Counterfactual probe** (state-blind MoA, v3 guard sets): 5 of 115 swapped decisions changed
route, 4.3% (Wilson 95% CI 1.9-9.8):
- sex-only swaps: 1 of 23;
- ethnicity-only swaps: 2 of 46;
- both changed: 2 of 46.

The changes were cardiac arrest ED to CT first (2), lung mass X-ray first to ED (2) and head injury
with loss of consciousness CT first to ED (1). These are the same as v2. The guards fix green and
fracture routes, and those presentations did not flip in v2 either.

## Deviations from the pre-registration

- **None** in seeds, scenarios, arms, metrics, tests or the run itself.
- `publishing/figures/make_figures.py` (plots only) and this file were written after the held-out
  results.
- **Incident.** During the last minutes of the held-out run, `python -m v2.cases` was re-run twice to
  check exclusion counts for the paper. It rewrites `v2/data/cases.csv`, and the rewritten file was
  byte-identical (checked with `cmp`). For every scenario and seed, all four arms have identical
  (pid, case_id, arrival) sequences, which a partially read case file would break. No rerun was made.
- **Prediction in the prereg.** PREREG_V3 section 8 attributed the development-seed hip-fracture LOS
  increase to the X-ray queue alone. The held-out breakdown shows that the X-ray queue is about a third
  of it and the ED-doctor queue the rest.

## Limitations

These are as in PREREG_V3 section 9: synthetic patients, guideline-derived labels, one 7B model,
constant staffing, an overloaded stress scenario, and a design made after seeing the v2 results.
