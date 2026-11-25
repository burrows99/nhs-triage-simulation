# Results: LLM mixture-of-agents post-triage routing (held-out, pre-registered)

This is the evaluation registered in [PREREG.md](PREREG.md).

- **Registration commit:** `ffefd6a`.
- **Held-out run:** seeds 1000-1029, run once at that commit (`results_v2/logs/heldout_commit.txt`).
- **Results committed:** `6eeded0`.
- **Model:** qwen2.5:7b (Q4_K_M), served locally by Ollama 0.21.2.
- **Prompts:** v2.2.

Every number here comes from `results_v2/heldout/tables.md` and `paired_tests.csv`, which
`python -m v2.run analyze` writes. Exploratory breakdowns that were not pre-registered are in
`results_v2/heldout/exploratory.md` and are labelled as exploratory below.

## Summary

Comparison: the queue-aware LLM MoA (`moa_load`) minus each baseline. Values are paired differences
over 30 seeds with 95% CIs, Holm-adjusted over the 20 primary tests. Negative means the MoA is
better.

| Scenario | Metric | vs static MTS protocol | vs load-aware heuristic |
|---|---|---|---|
| base | Mean doctor wait | **-4.9 ± 2.1 min (-5.5%), AI better** | **-2.7 ± 1.6 min (-3.2%), AI better** |
| base | P90 doctor wait | **-22.0 ± 7.9 min (-9.9%), AI better** | **-14.4 ± 6.1 min (-6.7%), AI better** |
| base | Time to needed imaging | **-52.5 ± 3.1 min (-67%), AI better** | **-53.9 ± 3.0 min (-68%), AI better** |
| base | Mean length of stay | **-10.1 ± 2.3 min (-4.7%), AI better** | **-9.2 ± 1.9 min (-4.3%), AI better** |
| base | Protocol-violation rate | 0 vs 0, no difference | 0 vs 0, no difference |
| stress | Mean doctor wait | -1.5 ± 13.3 min, no detectable difference | +3.8 ± 11.4 min, no detectable difference |
| stress | P90 doctor wait | **-32.8 ± 14.5 min (-7.6%), AI better** | **-17.9 ± 10.7 min (-4.3%), AI better** |
| stress | Time to needed imaging | **-102.1 ± 9.4 min (-67%), AI better** | **-103.9 ± 9.2 min (-68%), AI better** |
| stress | Mean length of stay | **-23.2 ± 9.4 min (-5.3%), AI better** | **-22.1 ± 8.7 min (-5.1%), AI better** |
| stress | Protocol-violation rate | 0 vs 0, no difference | 0 vs 0, no difference |

**Primary verdict.**
- The MoA is better than both baselines on 14 of the 16 testable comparisons.
- It shows no detectable difference on mean doctor wait under stress.
- It is worse on none.
- No patient in any arm went unseen by a doctor (0 of 179,028 patients per arm across the three
  scenarios).
- No LLM call needed a fallback (0 of 2,454 cached calls returned invalid output).

**Results that qualify the verdict, all reported in full below:**
1. **The gain depends on one modelling assumption.** The model assumes that a patient imaged before
   the doctor needs no separate doctor review of the result. In the pre-registered sensitivity
   scenario, where that review still happens, the direction reverses on three metrics:
   - mean doctor wait **+29.6 ± 2.6 min**;
   - P90 doctor wait +48.9 ± 7.5 min;
   - LOS **+31.5 ± 2.8 min**.

   Time to imaging is still 64 min shorter.
2. **Queue awareness added nothing.** The state-blind MoA was as good as or slightly better than the
   queue-aware MoA, for example base LOS -3.2 ± 0.9 min. The gain comes from the specialists'
   clinical imaging-first decisions, not from load balancing. The load-aware heuristic was also
   within a few minutes of the static protocol.
3. **The pre-registered fairness metric is worse for the MoA.** The gap between the best- and
   worst-served sex × ethnicity group is +30 ± 5 min in doctor wait (base) and +83 ± 26 min (stress)
   larger than under the static protocol. The router never receives ethnicity. The exploratory
   analysis attributes the gap to case mix in very small groups, not to the router's use of
   demographics (see Fairness).
4. **There are clinically important local harms that the averages hide** (exploratory,
   per presentation):
   - Low-risk whiplash (green) is sent to the ED instead of the UTC. Its patients wait **+262 min**
     (base) and **+768 min** (stress) for a doctor.
   - Red and orange patients sent to CT or ultrasound first (gunshot wound, traumatic brain injury,
     appendicitis) see a doctor about 25-30 min later. In practice a trauma team would meet them in
     CT.
   - Suspected hip fractures get an unnecessary CT before the needed X-ray (LOS +34 min).

## 1. Design (as registered)

- **Department:** one simulated English Type 1 ED with a co-located UTC.
  - Arrivals: 11.1/h with the ECDS 2024-25 hour-of-day profile.
  - Case mix: 159 Synthea encounters, with admissions weighted to 27.9%.
  - Staff and resources: 4 ED doctors, 2 UTC doctors, 1 X-ray, 1 CT, 1 ultrasound, a specialty
    pool of 3 and 45 assessment-unit beds.
  - Hard protocol rules are enforced by a guard.
- **Scenarios:**
  - `base`.
  - `stress`: +20% arrivals with the same staff.
  - `base_review`: sensitivity scenario in which imaging first does not save the review contact.
- **Runs:** 48 h warm-up, a 7-day window, every window patient followed to departure (0% censored),
  common random numbers, 30 held-out seeds.
- **Patients per replication:** 1,862 on average in base (range 1,796-1,935) and 2,244 in stress.
- **Arms:**
  - `rule_mts`: static protocol.
  - `load_aware`: static protocol plus streaming of green/blue patients by wait band.
  - `moa_load`: four specialist agents and a queue-aware aggregator.
  - `moa_static`: the same MoA without queue state.

### Operating point (base, static protocol)

| | Model | NHS England, October 2025 |
|---|---|---|
| Median time to first doctor | 62 min | 63 min |
| Median length of stay | 191 min | 166 min |

The NHS figures are the median time to treatment and the median total time in A&E, across all
department types. Utilisation in base: ED doctors 0.79, UTC doctors 0.77, beds 0.82. In stress:
0.95, 0.93 and 0.96.

## 2. Primary metrics (mean ± 95% CI over 30 replications)

**Base**

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Doctor wait, mean (min) | 88.5 ± 4.4 | 86.4 ± 3.9 | 83.7 ± 3.5 | 82.4 ± 3.5 |
| Doctor wait, P90 (min) | 222.5 ± 9.4 | 214.8 ± 10.1 | 200.5 ± 12.7 | 201.2 ± 11.4 |
| Time to needed imaging (min) | 78.5 ± 4.5 | 79.9 ± 4.5 | 26.0 ± 2.5 | 24.9 ± 2.6 |
| Length of stay, mean (min) | 216.9 ± 6.6 | 216.1 ± 6.2 | 206.8 ± 5.7 | 203.6 ± 5.7 |
| Protocol-violation rate | 0 | 0 | 0 | 0 |
| Never seen by a doctor | 0 | 0 | 0 | 0 |

**Stress**

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Doctor wait, mean (min) | 195.9 ± 9.5 | 190.7 ± 9.5 | 194.5 ± 18.5 | 192.2 ± 21.4 |
| Doctor wait, P90 (min) | 430.3 ± 19.9 | 415.4 ± 20.8 | 397.5 ± 15.8 | 398.1 ± 21.7 |
| Time to needed imaging (min) | 151.8 ± 11.0 | 153.6 ± 10.7 | 49.7 ± 3.7 | 47.8 ± 3.5 |
| Length of stay, mean (min) | 438.4 ± 38.2 | 437.3 ± 39.7 | 415.2 ± 41.9 | 407.8 ± 43.1 |
| Protocol-violation rate | 0 | 0 | 0 | 0 |
| Never seen by a doctor | 0 | 0 | 0 | 0 |

**Sensitivity: `base_review`, imaging first still needs a review**

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Doctor wait, mean (min) | 99.4 ± 4.4 | 99.3 ± 4.0 | 129.1 ± 5.3 | 148.6 ± 10.6 |
| Doctor wait, P90 (min) | 244.6 ± 9.2 | 242.0 ± 9.2 | 293.5 ± 13.9 | 317.2 ± 16.5 |
| Time to needed imaging (min) | 90.7 ± 4.4 | 91.9 ± 4.3 | 26.4 ± 2.6 | 27.0 ± 2.5 |
| Length of stay, mean (min) | 240.6 ± 6.8 | 241.5 ± 6.5 | 272.1 ± 8.3 | 291.2 ± 13.7 |

All paired differences with p-values and Holm-adjusted p-values are in
`results_v2/heldout/tables.md` and `results_v2/heldout/paired_tests.csv`.

**Sensitivity family (Holm within the family), `moa_load` minus `rule_mts`:**
- mean doctor wait +29.6 ± 2.6;
- P90 doctor wait +48.9 ± 7.5;
- time to imaging -64.2 ± 3.3;
- LOS +31.5 ± 2.8.

All are significant, with p_Holm < 1e-12. The comparison with `load_aware` is nearly identical. In
this scenario queue awareness did help: `moa_static` was 19.5 min worse than `moa_load` on mean
doctor wait.

## 3. Where the AI wins and where it loses

All of this section is exploratory: per presentation, pooled over replications, in
`results_v2/heldout/exploratory.md`.

The MoA changes routing in three ways.

1. **Imaging first for 32% of patients, against 14% under the static protocol.** It sends heart
   failure, suspected lung mass and knee injuries to X-ray first, head injury with loss of
   consciousness to CT first, and appendicitis to ultrasound first. This cuts doctor contacts from
   1.24 to 1.07 per patient and time to imaging by about two-thirds. Per presentation in base:
   - head injury with loss of consciousness: LOS -72 min;
   - knee injury: -67 min;
   - lung mass: -67 min;
   - heart failure: -47 min.
2. **Fewer patients streamed to the UTC: 33% against 42%.** This comes almost entirely from sending
   low-risk whiplash to the ED. The UTC empties (utilisation 0.61 against 0.77), so every other green
   patient waits about 60 min less in base and about 120 min less in stress. Whiplash patients,
   however, enter the ED as the lowest priority and wait 361 min (base) and 982 min (stress) for a
   doctor.
3. **Clinically questionable imaging first for some high-acuity patients.** These are gunshot
   wounds and traumatic brain injury (CT), appendicitis (ultrasound), and hip fracture (CT, which is
   unnecessary; the X-ray is still needed afterwards). The time to first doctor for these patients
   rises by 25-30 min. Unnecessary scans affect 0.38% of patients.

Queue awareness made no measurable difference in base or stress. The aggregator's wait-band
instruction rarely changed a decision that the clinical rules had already settled.

## 4. LLM operation, fallbacks and violations

| | Count |
|---|---|
| Unique LLM calls, all cached, all prompt versions and the fairness probe | 2,454 (1,267 specialist, 1,187 aggregator) |
| Invalid / unparseable outputs | **0** |
| Transport errors after retries | **0** |
| Fallbacks to the static protocol | **0** in every held-out arm and scenario |
| Protocol-violating proposals blocked by the guard | **0** in every held-out arm and scenario |
| Routing decisions, `moa_load`, base | 55,851: 47,883 by the aggregator; 7,968 had a single protocol-allowed candidate (ED) |
| New LLM calls during the held-out run | 20; everything else was a cache hit on calls made on development seeds |
| Median call latency (shared local server, Apple M4 Pro) | 4.6 s per specialist, 2.8 s per aggregator |

The zero violation rate reflects a design choice made on development seeds (prompt v2.1): the
aggregator is offered only protocol-allowed candidates, and a blocked specialist proposal is shown
as blocked. The output schema still accepts any of the five routes. With prompt v2.0, which offered
blocked proposals as candidates, 7-9% of patients had a protocol-violating proposal blocked by the
guard (`results_v2/logs/dev_base_moa_prompt-v2.0.log`). v2.0 also sent most green patients to the
ED; the state-blind mean doctor wait was about 600 min. These are development seeds only.

## 5. Fairness

**(a) Pre-registered: group gaps.** The gap is the maximum minus the minimum, across the six
sex × ethnicity groups, of the mean per replication. Holm is applied within the family.

| Scenario | Gap | rule_mts | load_aware | moa_load | moa_load − rule_mts | moa_load − load_aware |
|---|---|---|---|---|---|---|
| base | doctor wait (min) | 36.2 ± 3.6 | 42.0 ± 3.8 | 66.3 ± 4.9 | **+30.2 ± 4.8, AI worse** | **+24.4 ± 5.3, AI worse** |
| base | LOS (min) | 66.7 ± 6.5 | 69.4 ± 7.1 | 106.0 ± 6.7 | **+39.3 ± 5.2, AI worse** | **+36.7 ± 6.5, AI worse** |
| stress | doctor wait (min) | 76.7 ± 7.7 | 76.3 ± 8.4 | 159.7 ± 29.9 | **+83.0 ± 25.5, AI worse** | **+83.4 ± 25.6, AI worse** |
| stress | LOS (min) | 273.6 ± 86.1 | 287.6 ± 90.0 | 348.6 ± 90.7 | **+75.0 ± 19.2, AI worse** | **+61.0 ± 24.5, AI worse** |

**(b) Pre-registered, descriptive: counterfactual swaps.** One case per presentation (23 cases) was
routed by the state-blind MoA under all six sex × ethnicity descriptions, with ethnicity stated in
the vignette.

| Swap | Decisions | Route changed | Rate (Wilson 95% CI) |
|---|---|---|---|
| any other description | 115 | 5 | 4.3% [1.9, 9.8] |
| sex only | 23 | 1 | 4.3% [0.8, 21.0] |
| ethnicity only | 46 | 2 | 4.3% [1.2, 14.5] |
| both | 46 | 2 | 4.3% [1.2, 14.5] |

The changes were:
- cardiac arrest, ED to CT first (2);
- lung mass, X-ray first to ED (2);
- head injury with loss of consciousness, CT first to ED (1).

So the model's decisions are not fully invariant to stated demographics. The deployed router never
receives ethnicity, so in the simulation only the age and sex wording can act.

**Exploratory interpretation of (a).**
- The groups are small: 7 to 12 Synthea cases each, except White patients (51 and 71).
- Each group's mean is driven by which presentations it happens to contain. For example, the only
  whiplash case among Black women is sent to the ED by the MoA.
- The router does not receive ethnicity, and its routes are consistent across cases of the same
  presentation; the one exception is head injury with loss of consciousness, where one 12-year-old's
  route differs.
- The widened gap is therefore a consequence of presentation-level routing changes falling unevenly
  on small groups, not of the router using demographics.
- Even so, the effect on patients is real: the pre-registered metric registers it, and the case
  pool is too small to separate the two explanations cleanly.

## 6. Deviations from the pre-registration

**None in design, seeds, metrics or analysis.**

Notes:
- `v2/figures.py` (plot layout only) and `v2/explore.py` (exploratory breakdowns) were changed or
  added after the registration commit and before the held-out results were seen. Neither affects
  any registered number.
- The registration describes the stress scenario as near-critical with slow drift. This was
  confirmed: bed utilisation is 0.96 and LOS drifts upward over the window (Welch curve), so
  absolute stress levels depend on the horizon.

## 7. Figures

These are generated by `python -m v2.figures heldout` and saved in `results_v2/heldout/figures/`:
- `fig_primary_forest`: paired differences for the primary and sensitivity families.
- `fig_hourly`: arrival profile and doctor wait by arrival hour.
- `fig_routes`: route mix by MTS category for each arm.
- `fig_warmup`: Welch warm-up curves on development seeds.

## 8. Limitations

- The data are synthetic.
- The case pool is small, and the complaint text was written by the author.
- The ground truth follows guidelines and has not been reviewed by clinicians.
- One 7B model family was used.
- Staffing is constant.
- The result depends on the assumption that imaging first saves a review contact. This assumption
  is plausible but unmeasured; the sensitivity scenario shows its weight.

## 9. Optional follow-ups (not run)

- **qwen2.5:14b.** It is installed, but did not fit in memory alongside other work at the time.
- **GPT-OSS-20B and Mistral-7B.** These would need `ollama pull` and the owner's approval.
- **Clinician review.** Clinicians should review the vignettes, the ground-truth labels and the
  MoA's rationales before any claim of clinical appropriateness is made.
