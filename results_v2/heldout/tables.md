# v2 results (heldout seeds)

## Scenario: base

Replications per arm: {'load_aware': 30, 'moa_load': 30, 'moa_static': 30, 'rule_mts': 30}

### Primary metrics (mean ± 95% CI over replications)

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Doctor wait, mean (min) | 88.5 ± 4.4 | 86.4 ± 3.9 | 83.7 ± 3.5 | 82.4 ± 3.5 |
| Doctor wait, P90 (min) | 222.5 ± 9.4 | 214.8 ± 10.1 | 200.5 ± 12.7 | 201.2 ± 11.4 |
| Time to needed imaging, mean (min) | 78.5 ± 4.5 | 79.9 ± 4.5 | 26.0 ± 2.5 | 24.9 ± 2.6 |
| Length of stay, mean (min) | 216.9 ± 6.6 | 216.1 ± 6.2 | 206.8 ± 5.7 | 203.6 ± 5.7 |
| Protocol-violation rate (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Never seen by a doctor (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |

### Secondary metrics

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Never seen by a doctor (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Fallback rate (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| censored_rate | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Re-streamed UTC to ED (%) | 1.38 ± 0.09 | 1.34 ± 0.09 | 1.38 ± 0.09 | 1.38 ± 0.09 |
| Unnecessary scans (% of patients) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.38 ± 0.06 | 0.38 ± 0.06 |
| Imaging first (%) | 14.47 ± 0.25 | 14.47 ± 0.25 | 31.77 ± 0.29 | 33.65 ± 0.36 |
| Streamed to UTC (%) | 42.02 ± 0.34 | 39.95 ± 0.28 | 33.15 ± 0.28 | 33.89 ± 0.39 |
| Doctor contacts per patient | 1.24 ± 0.00 | 1.24 ± 0.00 | 1.07 ± 0.00 | 1.05 ± 0.00 |
| Length of stay, P90 (min) | 402.8 ± 16.6 | 421.1 ± 16.7 | 422.5 ± 15.8 | 411.0 ± 15.5 |
| Doctor-wait gap across groups (min) | 36.2 ± 3.6 | 42.0 ± 3.8 | 66.3 ± 4.9 | 64.2 ± 3.9 |
| LOS gap across groups (min) | 66.7 ± 6.5 | 69.4 ± 7.1 | 106.0 ± 6.7 | 107.7 ± 6.4 |

### Utilisation (fraction of capacity, measurement window)

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| util_ed_doctor | 0.79 ± 0.01 | 0.81 ± 0.01 | 0.81 ± 0.01 | 0.80 ± 0.01 |
| util_utc_doctor | 0.77 ± 0.01 | 0.73 ± 0.01 | 0.61 ± 0.01 | 0.62 ± 0.01 |
| util_xray | 0.55 ± 0.01 | 0.55 ± 0.01 | 0.55 ± 0.01 | 0.55 ± 0.01 |
| util_ct | 0.30 ± 0.01 | 0.30 ± 0.01 | 0.32 ± 0.01 | 0.32 ± 0.01 |
| util_us | 0.19 ± 0.01 | 0.19 ± 0.01 | 0.19 ± 0.01 | 0.19 ± 0.01 |
| util_specialist | 0.65 ± 0.01 | 0.65 ± 0.01 | 0.65 ± 0.01 | 0.65 ± 0.01 |
| util_bed | 0.82 ± 0.02 | 0.82 ± 0.02 | 0.82 ± 0.02 | 0.82 ± 0.02 |
## Scenario: stress

Replications per arm: {'load_aware': 30, 'moa_load': 30, 'moa_static': 30, 'rule_mts': 30}

### Primary metrics (mean ± 95% CI over replications)

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Doctor wait, mean (min) | 195.9 ± 9.5 | 190.7 ± 9.5 | 194.5 ± 18.5 | 192.2 ± 21.4 |
| Doctor wait, P90 (min) | 430.3 ± 19.9 | 415.4 ± 20.8 | 397.5 ± 15.8 | 398.1 ± 21.7 |
| Time to needed imaging, mean (min) | 151.8 ± 11.0 | 153.6 ± 10.7 | 49.7 ± 3.7 | 47.8 ± 3.5 |
| Length of stay, mean (min) | 438.4 ± 38.2 | 437.3 ± 39.7 | 415.2 ± 41.9 | 407.8 ± 43.1 |
| Protocol-violation rate (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Never seen by a doctor (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |

### Secondary metrics

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Never seen by a doctor (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Fallback rate (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| censored_rate | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Re-streamed UTC to ED (%) | 1.40 ± 0.09 | 1.37 ± 0.08 | 1.47 ± 0.09 | 1.40 ± 0.09 |
| Unnecessary scans (% of patients) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.38 ± 0.05 | 0.38 ± 0.05 |
| Imaging first (%) | 14.26 ± 0.27 | 14.26 ± 0.27 | 31.18 ± 0.25 | 33.66 ± 0.34 |
| Streamed to UTC (%) | 41.76 ± 0.45 | 40.67 ± 0.36 | 33.96 ± 0.32 | 33.64 ± 0.46 |
| Doctor contacts per patient | 1.25 ± 0.00 | 1.24 ± 0.00 | 1.08 ± 0.00 | 1.05 ± 0.00 |
| Length of stay, P90 (min) | 741.0 ± 48.8 | 766.0 ± 50.3 | 864.7 ± 69.9 | 842.7 ± 77.2 |
| Doctor-wait gap across groups (min) | 76.7 ± 7.7 | 76.3 ± 8.4 | 159.7 ± 29.9 | 159.6 ± 34.8 |
| LOS gap across groups (min) | 273.6 ± 86.1 | 287.6 ± 90.0 | 348.6 ± 90.7 | 355.6 ± 91.2 |

### Utilisation (fraction of capacity, measurement window)

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| util_ed_doctor | 0.95 ± 0.01 | 0.97 ± 0.01 | 0.97 ± 0.01 | 0.96 ± 0.01 |
| util_utc_doctor | 0.93 ± 0.01 | 0.90 ± 0.01 | 0.75 ± 0.01 | 0.75 ± 0.01 |
| util_xray | 0.66 ± 0.01 | 0.66 ± 0.01 | 0.67 ± 0.01 | 0.67 ± 0.01 |
| util_ct | 0.37 ± 0.01 | 0.37 ± 0.01 | 0.38 ± 0.01 | 0.38 ± 0.01 |
| util_us | 0.23 ± 0.01 | 0.23 ± 0.01 | 0.23 ± 0.01 | 0.23 ± 0.01 |
| util_specialist | 0.78 ± 0.01 | 0.78 ± 0.01 | 0.78 ± 0.01 | 0.78 ± 0.01 |
| util_bed | 0.96 ± 0.01 | 0.96 ± 0.01 | 0.96 ± 0.01 | 0.96 ± 0.01 |
## Scenario: base_review

Replications per arm: {'load_aware': 30, 'moa_load': 30, 'moa_static': 30, 'rule_mts': 30}

### Primary metrics (mean ± 95% CI over replications)

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Doctor wait, mean (min) | 99.4 ± 4.4 | 99.3 ± 4.0 | 129.1 ± 5.3 | 148.6 ± 10.6 |
| Doctor wait, P90 (min) | 244.6 ± 9.2 | 242.0 ± 9.2 | 293.5 ± 13.9 | 317.2 ± 16.5 |
| Time to needed imaging, mean (min) | 90.7 ± 4.4 | 91.9 ± 4.3 | 26.4 ± 2.6 | 27.0 ± 2.5 |
| Length of stay, mean (min) | 240.6 ± 6.8 | 241.5 ± 6.5 | 272.1 ± 8.3 | 291.2 ± 13.7 |
| Protocol-violation rate (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Never seen by a doctor (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |

### Secondary metrics

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Never seen by a doctor (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Fallback rate (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| censored_rate | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Re-streamed UTC to ED (%) | 1.38 ± 0.09 | 1.35 ± 0.09 | 1.41 ± 0.09 | 1.38 ± 0.09 |
| Unnecessary scans (% of patients) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.38 ± 0.06 | 0.38 ± 0.06 |
| Imaging first (%) | 14.47 ± 0.25 | 14.47 ± 0.25 | 32.80 ± 0.32 | 33.65 ± 0.36 |
| Streamed to UTC (%) | 42.02 ± 0.34 | 40.68 ± 0.27 | 34.97 ± 0.29 | 33.89 ± 0.39 |
| Doctor contacts per patient | 1.37 ± 0.00 | 1.37 ± 0.00 | 1.37 ± 0.00 | 1.37 ± 0.00 |
| Length of stay, P90 (min) | 483.5 ± 20.8 | 500.5 ± 20.5 | 601.7 ± 22.5 | 628.7 ± 25.2 |
| Doctor-wait gap across groups (min) | 42.0 ± 3.9 | 47.3 ± 4.7 | 107.7 ± 6.4 | 137.3 ± 14.4 |
| LOS gap across groups (min) | 90.5 ± 8.4 | 89.8 ± 9.9 | 153.6 ± 7.5 | 185.8 ± 16.7 |

### Utilisation (fraction of capacity, measurement window)

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| util_ed_doctor | 0.85 ± 0.01 | 0.86 ± 0.01 | 0.93 ± 0.01 | 0.94 ± 0.01 |
| util_utc_doctor | 0.77 ± 0.01 | 0.75 ± 0.01 | 0.64 ± 0.01 | 0.62 ± 0.01 |
| util_xray | 0.55 ± 0.01 | 0.55 ± 0.01 | 0.55 ± 0.01 | 0.55 ± 0.01 |
| util_ct | 0.30 ± 0.01 | 0.30 ± 0.01 | 0.32 ± 0.01 | 0.32 ± 0.01 |
| util_us | 0.19 ± 0.01 | 0.19 ± 0.01 | 0.19 ± 0.01 | 0.19 ± 0.01 |
| util_specialist | 0.65 ± 0.01 | 0.65 ± 0.01 | 0.65 ± 0.01 | 0.65 ± 0.01 |
| util_bed | 0.82 ± 0.02 | 0.82 ± 0.02 | 0.82 ± 0.02 | 0.82 ± 0.02 |

## Primary family: moa_load vs each baseline (Holm over all 20 tests)

| Scenario | Comparison | Metric | Difference (95% CI) | Relative | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|---|
| base | moa_load − rule_mts | Doctor wait, mean (min) | -4.85 ± 2.12 | -5.5% | 6.1e-05 | 0.00061 | AI better |
| base | moa_load − rule_mts | Doctor wait, P90 (min) | -22.0 ± 7.9 | -9.9% | 3.8e-06 | 5.3e-05 | AI better |
| base | moa_load − rule_mts | Time to needed imaging, mean (min) | -52.5 ± 3.1 | -66.9% | 3.7e-25 | 7e-24 | AI better |
| base | moa_load − rule_mts | Length of stay, mean (min) | -10.1 ± 2.3 | -4.7% | 8.9e-10 | 1.3e-08 | AI better |
| base | moa_load − rule_mts | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| base | moa_load − load_aware | Doctor wait, mean (min) | -2.73 ± 1.63 | -3.2% | 0.0018 | 0.014 | AI better |
| base | moa_load − load_aware | Doctor wait, P90 (min) | -14.4 ± 6.1 | -6.7% | 4e-05 | 0.00044 | AI better |
| base | moa_load − load_aware | Time to needed imaging, mean (min) | -53.9 ± 3.0 | -67.5% | 1.1e-25 | 2.1e-24 | AI better |
| base | moa_load − load_aware | Length of stay, mean (min) | -9.24 ± 1.92 | -4.3% | 9.5e-11 | 1.5e-09 | AI better |
| base | moa_load − load_aware | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| stress | moa_load − rule_mts | Doctor wait, mean (min) | -1.45 ± 13.27 | -0.7% | 0.83 | 1 | no detectable difference |
| stress | moa_load − rule_mts | Doctor wait, P90 (min) | -32.8 ± 14.5 | -7.6% | 7.2e-05 | 0.00065 | AI better |
| stress | moa_load − rule_mts | Time to needed imaging, mean (min) | -102.1 ± 9.4 | -67.3% | 1e-19 | 1.8e-18 | AI better |
| stress | moa_load − rule_mts | Length of stay, mean (min) | -23.2 ± 9.4 | -5.3% | 2.3e-05 | 0.00028 | AI better |
| stress | moa_load − rule_mts | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| stress | moa_load − load_aware | Doctor wait, mean (min) | 3.78 ± 11.43 | +2.0% | 0.5 | 1 | no detectable difference |
| stress | moa_load − load_aware | Doctor wait, P90 (min) | -17.9 ± 10.7 | -4.3% | 0.0019 | 0.014 | AI better |
| stress | moa_load − load_aware | Time to needed imaging, mean (min) | -103.9 ± 9.2 | -67.7% | 2.8e-20 | 5.1e-19 | AI better |
| stress | moa_load − load_aware | Length of stay, mean (min) | -22.1 ± 8.7 | -5.1% | 1.6e-05 | 0.00021 | AI better |
| stress | moa_load − load_aware | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |

## Secondary: state-blind MoA (moa_static) (Holm within this family)

| Scenario | Comparison | Metric | Difference (95% CI) | Relative | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|---|
| base | moa_static − rule_mts | Doctor wait, mean (min) | -6.09 ± 2.42 | -6.9% | 1.7e-05 | 0.00033 | AI better |
| base | moa_static − rule_mts | Doctor wait, P90 (min) | -21.3 ± 7.9 | -9.6% | 6.4e-06 | 0.00013 | AI better |
| base | moa_static − rule_mts | Time to needed imaging, mean (min) | -53.5 ± 3.1 | -68.2% | 2e-25 | 5.9e-24 | AI better |
| base | moa_static − rule_mts | Length of stay, mean (min) | -13.3 ± 2.7 | -6.1% | 4.7e-11 | 1.2e-09 | AI better |
| base | moa_static − rule_mts | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| base | moa_static − load_aware | Doctor wait, mean (min) | -3.97 ± 1.96 | -4.6% | 0.00027 | 0.0044 | AI better |
| base | moa_static − load_aware | Doctor wait, P90 (min) | -13.6 ± 5.9 | -6.4% | 5.1e-05 | 0.00092 | AI better |
| base | moa_static − load_aware | Time to needed imaging, mean (min) | -55.0 ± 3.1 | -68.8% | 6.4e-26 | 1.9e-24 | AI better |
| base | moa_static − load_aware | Length of stay, mean (min) | -12.5 ± 2.3 | -5.8% | 8.4e-12 | 2.2e-10 | AI better |
| base | moa_static − load_aware | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| base | moa_static − moa_load | Doctor wait, mean (min) | -1.24 ± 0.76 | -1.5% | 0.0023 | 0.03 | AI better |
| base | moa_static − moa_load | Doctor wait, P90 (min) | 0.72 ± 3.23 | +0.4% | 0.65 | 1 | no detectable difference |
| base | moa_static − moa_load | Time to needed imaging, mean (min) | -1.07 ± 0.38 | -4.1% | 3.1e-06 | 7.2e-05 | AI better |
| base | moa_static − moa_load | Length of stay, mean (min) | -3.22 ± 0.86 | -1.6% | 1.8e-08 | 4.4e-07 | AI better |
| base | moa_static − moa_load | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| stress | moa_static − rule_mts | Doctor wait, mean (min) | -3.71 ± 16.12 | -1.9% | 0.64 | 1 | no detectable difference |
| stress | moa_static − rule_mts | Doctor wait, P90 (min) | -32.2 ± 16.7 | -7.5% | 0.00045 | 0.0068 | AI better |
| stress | moa_static − rule_mts | Time to needed imaging, mean (min) | -104.0 ± 9.6 | -68.5% | 1e-19 | 2.8e-18 | AI better |
| stress | moa_static − rule_mts | Length of stay, mean (min) | -30.6 ± 11.1 | -7.0% | 4.2e-06 | 9.2e-05 | AI better |
| stress | moa_static − rule_mts | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| stress | moa_static − load_aware | Doctor wait, mean (min) | 1.52 ± 14.57 | +0.8% | 0.83 | 1 | no detectable difference |
| stress | moa_static − load_aware | Doctor wait, P90 (min) | -17.3 ± 10.4 | -4.2% | 0.0019 | 0.027 | AI better |
| stress | moa_static − load_aware | Time to needed imaging, mean (min) | -105.8 ± 9.3 | -68.9% | 2.8e-20 | 7.8e-19 | AI better |
| stress | moa_static − load_aware | Length of stay, mean (min) | -29.5 ± 10.7 | -6.8% | 4.2e-06 | 9.2e-05 | AI better |
| stress | moa_static − load_aware | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| stress | moa_static − moa_load | Doctor wait, mean (min) | -2.26 ± 5.10 | -1.2% | 0.37 | 1 | no detectable difference |
| stress | moa_static − moa_load | Doctor wait, P90 (min) | 0.61 ± 9.54 | +0.2% | 0.9 | 1 | no detectable difference |
| stress | moa_static − moa_load | Time to needed imaging, mean (min) | -1.91 ± 0.88 | -3.8% | 0.00013 | 0.0022 | AI better |
| stress | moa_static − moa_load | Length of stay, mean (min) | -7.45 ± 5.51 | -1.8% | 0.0098 | 0.12 | no detectable difference |
| stress | moa_static − moa_load | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |

## Fairness: group gaps (max − min across sex × ethnicity groups) (Holm within this family)

| Scenario | Comparison | Metric | Difference (95% CI) | Relative | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|---|
| base | moa_load − rule_mts | Doctor-wait gap across groups (min) | 30.2 ± 4.8 | +83.4% | 2e-13 | 1.4e-12 | AI worse |
| base | moa_load − rule_mts | LOS gap across groups (min) | 39.3 ± 5.2 | +59.0% | 1.6e-15 | 1.3e-14 | AI worse |
| base | moa_load − load_aware | Doctor-wait gap across groups (min) | 24.4 ± 5.3 | +58.1% | 2.9e-10 | 1.4e-09 | AI worse |
| base | moa_load − load_aware | LOS gap across groups (min) | 36.7 ± 6.5 | +52.9% | 2.1e-12 | 1.2e-11 | AI worse |
| stress | moa_load − rule_mts | Doctor-wait gap across groups (min) | 83.0 ± 25.5 | +108.2% | 2.6e-07 | 7.9e-07 | AI worse |
| stress | moa_load − rule_mts | LOS gap across groups (min) | 75.0 ± 19.2 | +27.4% | 8.6e-09 | 3.5e-08 | AI worse |
| stress | moa_load − load_aware | Doctor-wait gap across groups (min) | 83.4 ± 25.6 | +109.2% | 2.7e-07 | 7.9e-07 | AI worse |
| stress | moa_load − load_aware | LOS gap across groups (min) | 61.0 ± 24.5 | +21.2% | 1.9e-05 | 1.9e-05 | AI worse |

## Sensitivity: imaging-first does not save the review contact (Holm within this family)

| Scenario | Comparison | Metric | Difference (95% CI) | Relative | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|---|
| base_review | moa_load − rule_mts | Doctor wait, mean (min) | 29.6 ± 2.6 | +29.8% | 3.8e-20 | 2.7e-19 | AI worse |
| base_review | moa_load − rule_mts | Doctor wait, P90 (min) | 48.9 ± 7.5 | +20.0% | 6.8e-14 | 2.2e-13 | AI worse |
| base_review | moa_load − rule_mts | Time to needed imaging, mean (min) | -64.2 ± 3.3 | -70.8% | 5.6e-27 | 5e-26 | AI better |
| base_review | moa_load − rule_mts | Length of stay, mean (min) | 31.5 ± 2.8 | +13.1% | 5e-20 | 3e-19 | AI worse |
| base_review | moa_load − rule_mts | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| base_review | moa_load − load_aware | Doctor wait, mean (min) | 29.8 ± 2.6 | +30.0% | 2.1e-20 | 1.7e-19 | AI worse |
| base_review | moa_load − load_aware | Doctor wait, P90 (min) | 51.5 ± 7.8 | +21.3% | 5.6e-14 | 2.2e-13 | AI worse |
| base_review | moa_load − load_aware | Time to needed imaging, mean (min) | -65.4 ± 3.2 | -71.2% | 2e-27 | 2e-26 | AI better |
| base_review | moa_load − load_aware | Length of stay, mean (min) | 30.5 ± 2.9 | +12.6% | 1.6e-19 | 8.1e-19 | AI worse |
| base_review | moa_load − load_aware | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |

## Fairness: counterfactual demographic swaps (MoA, state-blind)

| Swap | Decisions | Route changed | Rate (Wilson 95% CI) |
|---|---|---|---|
| any of the 5 other descriptions | 115 | 5 | 4.3% [1.9, 9.8] |
| sex only (ethnicity as recorded) | 23 | 1 | 4.3% [0.8, 21.0] |
| ethnicity only (sex as recorded) | 46 | 2 | 4.3% [1.2, 14.5] |
| both changed | 46 | 2 | 4.3% [1.2, 14.5] |

Route changes by presentation:

- cardiac_arrest: ED -> CT_FIRST: 2
- head_injury_loc: CT_FIRST -> ED: 1
- lung_mass: XRAY_FIRST -> ED: 2
