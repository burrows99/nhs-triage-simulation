# v2 results (dev seeds)

## Scenario: base

Replications per arm: {'load_aware': 20, 'moa_load': 20, 'moa_static': 20, 'rule_mts': 20}

### Primary metrics (mean ± 95% CI over replications)

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Doctor wait, mean (min) | 89.2 ± 5.8 | 87.1 ± 5.5 | 84.5 ± 5.5 | 83.5 ± 5.2 |
| Doctor wait, P90 (min) | 218.3 ± 12.6 | 211.6 ± 13.8 | 198.2 ± 17.6 | 202.4 ± 18.3 |
| Time to needed imaging, mean (min) | 79.9 ± 4.8 | 81.2 ± 4.7 | 25.8 ± 2.8 | 25.1 ± 2.6 |
| Length of stay, mean (min) | 219.1 ± 8.0 | 218.1 ± 7.9 | 208.8 ± 7.5 | 206.2 ± 7.5 |
| Protocol-violation rate (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Never seen by a doctor (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |

### Secondary metrics

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Never seen by a doctor (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Fallback rate (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| censored_rate | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Re-streamed UTC to ED (%) | 1.50 ± 0.09 | 1.44 ± 0.10 | 1.50 ± 0.09 | 1.50 ± 0.09 |
| Unnecessary scans (% of patients) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.44 ± 0.07 | 0.44 ± 0.07 |
| Imaging first (%) | 14.33 ± 0.35 | 14.33 ± 0.35 | 32.02 ± 0.41 | 33.83 ± 0.57 |
| Streamed to UTC (%) | 41.79 ± 0.65 | 39.80 ± 0.57 | 32.98 ± 0.44 | 33.42 ± 0.54 |
| Doctor contacts per patient | 1.25 ± 0.01 | 1.25 ± 0.01 | 1.08 ± 0.00 | 1.06 ± 0.00 |
| Length of stay, P90 (min) | 409.7 ± 19.5 | 426.6 ± 19.2 | 429.7 ± 20.7 | 421.1 ± 21.8 |
| Doctor-wait gap across groups (min) | 35.5 ± 4.6 | 39.2 ± 5.3 | 68.6 ± 5.5 | 68.8 ± 5.3 |
| LOS gap across groups (min) | 69.6 ± 7.2 | 70.1 ± 7.1 | 111.8 ± 7.2 | 115.0 ± 6.7 |

### Utilisation (fraction of capacity, measurement window)

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| util_ed_doctor | 0.80 ± 0.01 | 0.82 ± 0.01 | 0.82 ± 0.01 | 0.80 ± 0.01 |
| util_utc_doctor | 0.77 ± 0.02 | 0.73 ± 0.01 | 0.61 ± 0.01 | 0.62 ± 0.01 |
| util_xray | 0.55 ± 0.01 | 0.55 ± 0.01 | 0.54 ± 0.01 | 0.54 ± 0.01 |
| util_ct | 0.32 ± 0.01 | 0.32 ± 0.01 | 0.34 ± 0.01 | 0.34 ± 0.01 |
| util_us | 0.20 ± 0.01 | 0.20 ± 0.01 | 0.20 ± 0.01 | 0.20 ± 0.01 |
| util_specialist | 0.65 ± 0.01 | 0.65 ± 0.01 | 0.65 ± 0.01 | 0.65 ± 0.01 |
| util_bed | 0.82 ± 0.02 | 0.82 ± 0.02 | 0.82 ± 0.02 | 0.82 ± 0.02 |
## Scenario: stress

Replications per arm: {'load_aware': 20, 'moa_load': 20, 'moa_static': 20, 'rule_mts': 20}

### Primary metrics (mean ± 95% CI over replications)

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Doctor wait, mean (min) | 201.1 ± 15.4 | 198.9 ± 15.5 | 205.4 ± 20.5 | 200.5 ± 18.9 |
| Doctor wait, P90 (min) | 427.6 ± 27.0 | 423.3 ± 25.4 | 422.4 ± 22.1 | 426.9 ± 27.4 |
| Time to needed imaging, mean (min) | 161.5 ± 14.5 | 163.3 ± 14.2 | 56.2 ± 5.0 | 53.5 ± 5.0 |
| Length of stay, mean (min) | 463.6 ± 55.3 | 463.8 ± 55.0 | 445.5 ± 56.2 | 436.2 ± 54.3 |
| Protocol-violation rate (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Never seen by a doctor (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |

### Secondary metrics

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Never seen by a doctor (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Fallback rate (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| censored_rate | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Re-streamed UTC to ED (%) | 1.46 ± 0.12 | 1.43 ± 0.12 | 1.57 ± 0.12 | 1.46 ± 0.12 |
| Unnecessary scans (% of patients) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.38 ± 0.05 | 0.38 ± 0.05 |
| Imaging first (%) | 14.39 ± 0.47 | 14.39 ± 0.47 | 31.36 ± 0.43 | 33.96 ± 0.38 |
| Streamed to UTC (%) | 41.60 ± 0.43 | 40.77 ± 0.46 | 34.06 ± 0.42 | 33.40 ± 0.47 |
| Doctor contacts per patient | 1.25 ± 0.00 | 1.25 ± 0.00 | 1.08 ± 0.00 | 1.06 ± 0.00 |
| Length of stay, P90 (min) | 782.4 ± 62.4 | 803.3 ± 58.5 | 974.1 ± 146.1 | 958.3 ± 146.4 |
| Doctor-wait gap across groups (min) | 85.9 ± 10.2 | 85.8 ± 8.8 | 170.2 ± 26.5 | 173.3 ± 27.1 |
| LOS gap across groups (min) | 305.1 ± 108.5 | 312.3 ± 104.9 | 392.1 ± 113.1 | 404.0 ± 114.1 |

### Utilisation (fraction of capacity, measurement window)

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| util_ed_doctor | 0.96 ± 0.01 | 0.97 ± 0.01 | 0.98 ± 0.01 | 0.97 ± 0.01 |
| util_utc_doctor | 0.93 ± 0.01 | 0.91 ± 0.01 | 0.76 ± 0.01 | 0.75 ± 0.01 |
| util_xray | 0.67 ± 0.02 | 0.67 ± 0.02 | 0.67 ± 0.02 | 0.67 ± 0.02 |
| util_ct | 0.38 ± 0.02 | 0.38 ± 0.02 | 0.40 ± 0.02 | 0.40 ± 0.02 |
| util_us | 0.24 ± 0.01 | 0.24 ± 0.01 | 0.24 ± 0.01 | 0.24 ± 0.01 |
| util_specialist | 0.79 ± 0.01 | 0.79 ± 0.01 | 0.79 ± 0.01 | 0.79 ± 0.01 |
| util_bed | 0.97 ± 0.01 | 0.97 ± 0.01 | 0.97 ± 0.01 | 0.97 ± 0.01 |
## Scenario: base_review

Replications per arm: {'load_aware': 20, 'moa_load': 20, 'moa_static': 20, 'rule_mts': 20}

### Primary metrics (mean ± 95% CI over replications)

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Doctor wait, mean (min) | 99.9 ± 5.9 | 99.6 ± 5.6 | 132.2 ± 9.0 | 151.6 ± 13.1 |
| Doctor wait, P90 (min) | 244.4 ± 13.6 | 242.1 ± 14.1 | 298.5 ± 15.9 | 320.8 ± 19.3 |
| Time to needed imaging, mean (min) | 92.0 ± 4.9 | 93.2 ± 4.8 | 26.9 ± 3.1 | 27.6 ± 2.6 |
| Length of stay, mean (min) | 242.8 ± 8.8 | 244.0 ± 9.0 | 277.8 ± 12.8 | 296.7 ± 17.5 |
| Protocol-violation rate (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Never seen by a doctor (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |

### Secondary metrics

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Never seen by a doctor (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Fallback rate (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| censored_rate | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Re-streamed UTC to ED (%) | 1.50 ± 0.09 | 1.46 ± 0.09 | 1.51 ± 0.09 | 1.50 ± 0.09 |
| Unnecessary scans (% of patients) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.44 ± 0.07 | 0.44 ± 0.07 |
| Imaging first (%) | 14.33 ± 0.35 | 14.33 ± 0.35 | 32.96 ± 0.42 | 33.83 ± 0.57 |
| Streamed to UTC (%) | 41.79 ± 0.65 | 40.39 ± 0.58 | 34.60 ± 0.45 | 33.42 ± 0.54 |
| Doctor contacts per patient | 1.38 ± 0.01 | 1.38 ± 0.01 | 1.38 ± 0.01 | 1.38 ± 0.01 |
| Length of stay, P90 (min) | 493.9 ± 24.8 | 513.4 ± 24.8 | 606.5 ± 28.9 | 639.7 ± 32.2 |
| Doctor-wait gap across groups (min) | 41.7 ± 4.8 | 46.1 ± 7.0 | 113.9 ± 9.3 | 143.4 ± 18.0 |
| LOS gap across groups (min) | 91.3 ± 9.7 | 92.4 ± 8.8 | 164.6 ± 11.9 | 196.2 ± 20.3 |

### Utilisation (fraction of capacity, measurement window)

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| util_ed_doctor | 0.86 ± 0.01 | 0.87 ± 0.01 | 0.94 ± 0.01 | 0.95 ± 0.01 |
| util_utc_doctor | 0.77 ± 0.02 | 0.74 ± 0.01 | 0.64 ± 0.01 | 0.62 ± 0.01 |
| util_xray | 0.55 ± 0.01 | 0.55 ± 0.01 | 0.54 ± 0.01 | 0.54 ± 0.01 |
| util_ct | 0.32 ± 0.01 | 0.32 ± 0.01 | 0.34 ± 0.01 | 0.34 ± 0.01 |
| util_us | 0.20 ± 0.01 | 0.20 ± 0.01 | 0.20 ± 0.01 | 0.20 ± 0.01 |
| util_specialist | 0.65 ± 0.01 | 0.65 ± 0.01 | 0.65 ± 0.01 | 0.65 ± 0.01 |
| util_bed | 0.82 ± 0.02 | 0.82 ± 0.02 | 0.82 ± 0.02 | 0.82 ± 0.02 |

## Primary family: moa_load vs each baseline (Holm over all 20 tests)

| Scenario | Comparison | Metric | Difference (95% CI) | Relative | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|---|
| base | moa_load − rule_mts | Doctor wait, mean (min) | -4.74 ± 2.06 | -5.3% | 0.00012 | 0.0017 | AI better |
| base | moa_load − rule_mts | Doctor wait, P90 (min) | -20.1 ± 12.7 | -9.2% | 0.0036 | 0.043 | AI better |
| base | moa_load − rule_mts | Time to needed imaging, mean (min) | -54.1 ± 3.4 | -67.7% | 2.2e-18 | 4.1e-17 | AI better |
| base | moa_load − rule_mts | Length of stay, mean (min) | -10.2 ± 2.0 | -4.7% | 1.2e-09 | 1.8e-08 | AI better |
| base | moa_load − rule_mts | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| base | moa_load − load_aware | Doctor wait, mean (min) | -2.59 ± 1.30 | -3.0% | 0.00052 | 0.0068 | AI better |
| base | moa_load − load_aware | Doctor wait, P90 (min) | -13.3 ± 9.7 | -6.3% | 0.0097 | 0.087 | no detectable difference |
| base | moa_load − load_aware | Time to needed imaging, mean (min) | -55.4 ± 3.3 | -68.2% | 1.1e-18 | 2.2e-17 | AI better |
| base | moa_load − load_aware | Length of stay, mean (min) | -9.30 ± 1.43 | -4.3% | 2.9e-11 | 4.6e-10 | AI better |
| base | moa_load − load_aware | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| stress | moa_load − rule_mts | Doctor wait, mean (min) | 4.27 ± 9.89 | +2.1% | 0.38 | 1 | no detectable difference |
| stress | moa_load − rule_mts | Doctor wait, P90 (min) | -5.27 ± 18.08 | -1.2% | 0.55 | 1 | no detectable difference |
| stress | moa_load − rule_mts | Time to needed imaging, mean (min) | -105.3 ± 12.2 | -65.2% | 2.1e-13 | 3.6e-12 | AI better |
| stress | moa_load − rule_mts | Length of stay, mean (min) | -18.1 ± 12.4 | -3.9% | 0.0066 | 0.066 | no detectable difference |
| stress | moa_load − rule_mts | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| stress | moa_load − load_aware | Doctor wait, mean (min) | 6.50 ± 8.99 | +3.3% | 0.15 | 1 | no detectable difference |
| stress | moa_load − load_aware | Doctor wait, P90 (min) | -0.97 ± 18.48 | -0.2% | 0.91 | 1 | no detectable difference |
| stress | moa_load − load_aware | Time to needed imaging, mean (min) | -107.1 ± 11.9 | -65.6% | 8.9e-14 | 1.6e-12 | AI better |
| stress | moa_load − load_aware | Length of stay, mean (min) | -18.3 ± 12.3 | -4.0% | 0.0056 | 0.062 | no detectable difference |
| stress | moa_load − load_aware | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |

## Secondary: state-blind MoA (moa_static) (Holm within this family)

| Scenario | Comparison | Metric | Difference (95% CI) | Relative | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|---|
| base | moa_static − rule_mts | Doctor wait, mean (min) | -5.71 ± 2.59 | -6.4% | 0.00019 | 0.0043 | AI better |
| base | moa_static − rule_mts | Doctor wait, P90 (min) | -16.0 ± 13.4 | -7.3% | 0.022 | 0.4 | no detectable difference |
| base | moa_static − rule_mts | Time to needed imaging, mean (min) | -54.7 ± 3.2 | -68.5% | 7.8e-19 | 2.3e-17 | AI better |
| base | moa_static − rule_mts | Length of stay, mean (min) | -12.8 ± 2.5 | -5.9% | 1.9e-09 | 4.8e-08 | AI better |
| base | moa_static − rule_mts | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| base | moa_static − load_aware | Doctor wait, mean (min) | -3.56 ± 2.04 | -4.1% | 0.0017 | 0.036 | AI better |
| base | moa_static − load_aware | Doctor wait, P90 (min) | -9.20 ± 10.16 | -4.3% | 0.073 | 1 | no detectable difference |
| base | moa_static − load_aware | Time to needed imaging, mean (min) | -56.1 ± 3.2 | -69.1% | 3.7e-19 | 1.1e-17 | AI better |
| base | moa_static − load_aware | Length of stay, mean (min) | -11.9 ± 2.2 | -5.5% | 5e-10 | 1.3e-08 | AI better |
| base | moa_static − load_aware | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| base | moa_static − moa_load | Doctor wait, mean (min) | -0.97 ± 1.57 | -1.1% | 0.21 | 1 | no detectable difference |
| base | moa_static − moa_load | Doctor wait, P90 (min) | 4.11 ± 4.18 | +2.1% | 0.054 | 0.86 | no detectable difference |
| base | moa_static − moa_load | Time to needed imaging, mean (min) | -0.65 ± 0.60 | -2.5% | 0.034 | 0.57 | no detectable difference |
| base | moa_static − moa_load | Length of stay, mean (min) | -2.60 ± 1.64 | -1.2% | 0.0036 | 0.068 | no detectable difference |
| base | moa_static − moa_load | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| stress | moa_static − rule_mts | Doctor wait, mean (min) | -0.60 ± 12.55 | -0.3% | 0.92 | 1 | no detectable difference |
| stress | moa_static − rule_mts | Doctor wait, P90 (min) | -0.71 ± 21.26 | -0.2% | 0.95 | 1 | no detectable difference |
| stress | moa_static − rule_mts | Time to needed imaging, mean (min) | -108.0 ± 12.2 | -66.9% | 1.3e-13 | 3.5e-12 | AI better |
| stress | moa_static − rule_mts | Length of stay, mean (min) | -27.4 ± 15.7 | -5.9% | 0.0017 | 0.036 | AI better |
| stress | moa_static − rule_mts | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| stress | moa_static − load_aware | Doctor wait, mean (min) | 1.63 ± 11.75 | +0.8% | 0.77 | 1 | no detectable difference |
| stress | moa_static − load_aware | Doctor wait, P90 (min) | 3.60 ± 20.91 | +0.8% | 0.72 | 1 | no detectable difference |
| stress | moa_static − load_aware | Time to needed imaging, mean (min) | -109.8 ± 11.9 | -67.2% | 5.6e-14 | 1.6e-12 | AI better |
| stress | moa_static − load_aware | Length of stay, mean (min) | -27.6 ± 15.6 | -5.9% | 0.0015 | 0.034 | AI better |
| stress | moa_static − load_aware | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| stress | moa_static − moa_load | Doctor wait, mean (min) | -4.87 ± 7.79 | -2.4% | 0.21 | 1 | no detectable difference |
| stress | moa_static − moa_load | Doctor wait, P90 (min) | 4.56 ± 12.97 | +1.1% | 0.47 | 1 | no detectable difference |
| stress | moa_static − moa_load | Time to needed imaging, mean (min) | -2.68 ± 1.08 | -4.8% | 5.3e-05 | 0.0013 | AI better |
| stress | moa_static − moa_load | Length of stay, mean (min) | -9.25 ± 9.68 | -2.1% | 0.06 | 0.9 | no detectable difference |
| stress | moa_static − moa_load | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |

## Fairness: group gaps (max − min across sex × ethnicity groups) (Holm within this family)

| Scenario | Comparison | Metric | Difference (95% CI) | Relative | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|---|
| base | moa_load − rule_mts | Doctor-wait gap across groups (min) | 33.1 ± 3.8 | +93.5% | 1.3e-13 | 1.1e-12 | AI worse |
| base | moa_load − rule_mts | LOS gap across groups (min) | 42.2 ± 5.6 | +60.6% | 2.3e-12 | 1.6e-11 | AI worse |
| base | moa_load − load_aware | Doctor-wait gap across groups (min) | 29.4 ± 5.2 | +74.9% | 3.3e-10 | 1.6e-09 | AI worse |
| base | moa_load − load_aware | LOS gap across groups (min) | 41.6 ± 6.7 | +59.3% | 6.1e-11 | 3.6e-10 | AI worse |
| stress | moa_load − rule_mts | Doctor-wait gap across groups (min) | 84.2 ± 22.9 | +98.0% | 3e-07 | 9.8e-07 | AI worse |
| stress | moa_load − rule_mts | LOS gap across groups (min) | 87.0 ± 29.1 | +28.5% | 5.2e-06 | 1e-05 | AI worse |
| stress | moa_load − load_aware | Doctor-wait gap across groups (min) | 84.3 ± 22.6 | +98.2% | 2.5e-07 | 9.8e-07 | AI worse |
| stress | moa_load − load_aware | LOS gap across groups (min) | 79.8 ± 29.0 | +25.6% | 1.5e-05 | 1.5e-05 | AI worse |

## Sensitivity: imaging-first does not save the review contact (Holm within this family)

| Scenario | Comparison | Metric | Difference (95% CI) | Relative | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|---|
| base_review | moa_load − rule_mts | Doctor wait, mean (min) | 32.3 ± 4.8 | +32.3% | 1.5e-11 | 9e-11 | AI worse |
| base_review | moa_load − rule_mts | Doctor wait, P90 (min) | 54.0 ± 10.3 | +22.1% | 1.2e-09 | 3.5e-09 | AI worse |
| base_review | moa_load − rule_mts | Time to needed imaging, mean (min) | -65.1 ± 3.3 | -70.7% | 4.6e-20 | 4.1e-19 | AI better |
| base_review | moa_load − rule_mts | Length of stay, mean (min) | 35.0 ± 5.5 | +14.4% | 4.1e-11 | 2.1e-10 | AI worse |
| base_review | moa_load − rule_mts | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| base_review | moa_load − load_aware | Doctor wait, mean (min) | 32.6 ± 4.5 | +32.7% | 5.3e-12 | 4.2e-11 | AI worse |
| base_review | moa_load − load_aware | Doctor wait, P90 (min) | 56.3 ± 9.3 | +23.3% | 9.5e-11 | 3.8e-10 | AI worse |
| base_review | moa_load − load_aware | Time to needed imaging, mean (min) | -66.3 ± 3.3 | -71.1% | 2.9e-20 | 2.9e-19 | AI better |
| base_review | moa_load − load_aware | Length of stay, mean (min) | 33.8 ± 4.9 | +13.8% | 1.3e-11 | 9e-11 | AI worse |
| base_review | moa_load − load_aware | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |

## Fairness: counterfactual demographic swaps (MoA, state-blind)

(counterfactual probe not run)
