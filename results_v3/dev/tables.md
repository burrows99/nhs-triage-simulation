# v3 results (dev seeds)

## Scenario: base

Replications per arm: {'load_aware': 20, 'moa_load': 20, 'moa_static': 20, 'rule_mts': 20}

### Primary metrics (mean ± 95% CI over replications)

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Doctor wait, mean (min) | 104.3 ± 6.1 | 104.2 ± 5.8 | 114.3 ± 6.0 | 114.8 ± 6.0 |
| Doctor wait, P90 (min) | 259.0 ± 14.6 | 259.1 ± 14.5 | 289.3 ± 14.1 | 287.7 ± 14.6 |
| Time to needed imaging, mean (min) | 97.7 ± 5.2 | 98.7 ± 5.2 | 25.6 ± 2.9 | 26.4 ± 2.5 |
| Length of stay, mean (min) | 240.5 ± 8.4 | 241.7 ± 8.5 | 238.6 ± 7.7 | 237.7 ± 7.3 |
| Protocol-violation rate (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Never seen by a doctor (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |

### Secondary metrics

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Never seen by a doctor (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Fallback rate (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| censored_rate | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Re-streamed UTC to ED (%) | 1.50 ± 0.09 | 1.45 ± 0.10 | 1.46 ± 0.09 | 1.50 ± 0.09 |
| Unnecessary scans (% of patients) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Imaging first (%) | 14.33 ± 0.35 | 14.33 ± 0.35 | 32.94 ± 0.43 | 33.83 ± 0.57 |
| Streamed to UTC (%) | 41.79 ± 0.65 | 40.33 ± 0.58 | 40.20 ± 0.57 | 40.78 ± 0.59 |
| Doctor contacts per patient | 1.25 ± 0.01 | 1.25 ± 0.01 | 1.06 ± 0.00 | 1.05 ± 0.00 |
| Length of stay, P90 (min) | 474.3 ± 21.3 | 491.3 ± 20.6 | 471.0 ± 17.9 | 464.9 ± 17.3 |
| Doctor-wait gap across groups (min) | 43.7 ± 5.3 | 48.2 ± 6.5 | 56.6 ± 5.9 | 60.7 ± 5.8 |
| LOS gap across groups (min) | 81.2 ± 8.6 | 82.5 ± 8.2 | 77.5 ± 8.5 | 82.5 ± 8.0 |

### Utilisation (fraction of capacity, measurement window)

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| util_ed_doctor | 0.86 ± 0.01 | 0.87 ± 0.01 | 0.88 ± 0.01 | 0.87 ± 0.01 |
| util_utc_doctor | 0.77 ± 0.02 | 0.74 ± 0.01 | 0.74 ± 0.01 | 0.75 ± 0.01 |
| util_xray | 0.55 ± 0.01 | 0.55 ± 0.01 | 0.54 ± 0.01 | 0.54 ± 0.01 |
| util_ct | 0.32 ± 0.01 | 0.32 ± 0.01 | 0.32 ± 0.01 | 0.32 ± 0.01 |
| util_us | 0.20 ± 0.01 | 0.20 ± 0.01 | 0.20 ± 0.01 | 0.20 ± 0.01 |
| util_specialist | 0.65 ± 0.01 | 0.65 ± 0.01 | 0.65 ± 0.01 | 0.65 ± 0.01 |
| util_bed | 0.82 ± 0.02 | 0.82 ± 0.02 | 0.82 ± 0.02 | 0.82 ± 0.02 |
## Scenario: stress

Replications per arm: {'load_aware': 20, 'moa_load': 20, 'moa_static': 20, 'rule_mts': 20}

### Primary metrics (mean ± 95% CI over replications)

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Doctor wait, mean (min) | 305.9 ± 39.5 | 314.5 ± 37.5 | 344.1 ± 42.2 | 339.8 ± 43.8 |
| Doctor wait, P90 (min) | 691.9 ± 99.9 | 693.3 ± 99.5 | 769.8 ± 116.0 | 777.5 ± 119.1 |
| Time to needed imaging, mean (min) | 288.2 ± 44.0 | 288.7 ± 43.7 | 71.0 ± 12.8 | 62.5 ± 6.4 |
| Length of stay, mean (min) | 803.8 ± 105.2 | 824.2 ± 100.1 | 786.1 ± 91.8 | 766.2 ± 90.2 |
| Protocol-violation rate (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Never seen by a doctor (%) | 0.00 ± 0.00 | 0.02 ± 0.02 | 0.03 ± 0.03 | 0.02 ± 0.02 |

### Secondary metrics

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Never seen by a doctor (%) | 0.00 ± 0.00 | 0.02 ± 0.02 | 0.03 ± 0.03 | 0.02 ± 0.02 |
| Fallback rate (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| censored_rate | 0.01 ± 0.00 | 0.01 ± 0.00 | 0.01 ± 0.00 | 0.01 ± 0.00 |
| Re-streamed UTC to ED (%) | 1.46 ± 0.12 | 1.46 ± 0.12 | 1.58 ± 0.13 | 1.46 ± 0.12 |
| Unnecessary scans (% of patients) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Imaging first (%) | 14.39 ± 0.47 | 14.39 ± 0.47 | 32.60 ± 0.48 | 33.96 ± 0.38 |
| Streamed to UTC (%) | 41.60 ± 0.43 | 41.46 ± 0.44 | 41.57 ± 0.46 | 41.51 ± 0.44 |
| Doctor contacts per patient | 1.24 ± 0.01 | 1.24 ± 0.01 | 1.06 ± 0.00 | 1.04 ± 0.00 |
| Length of stay, P90 (min) | 1307.7 ± 205.3 | 1312.4 ± 203.5 | 1029.5 ± 137.3 | 1017.4 ± 133.7 |
| Doctor-wait gap across groups (min) | 155.5 ± 30.4 | 172.4 ± 29.9 | 201.4 ± 36.6 | 192.8 ± 32.8 |
| LOS gap across groups (min) | 987.1 ± 184.0 | 1037.8 ± 173.4 | 1033.8 ± 173.2 | 1029.7 ± 180.0 |

### Utilisation (fraction of capacity, measurement window)

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| util_ed_doctor | 0.99 ± 0.00 | 1.00 ± 0.00 | 1.00 ± 0.00 | 1.00 ± 0.00 |
| util_utc_doctor | 0.93 ± 0.01 | 0.92 ± 0.01 | 0.93 ± 0.01 | 0.92 ± 0.01 |
| util_xray | 0.66 ± 0.01 | 0.66 ± 0.01 | 0.67 ± 0.01 | 0.67 ± 0.02 |
| util_ct | 0.38 ± 0.02 | 0.38 ± 0.02 | 0.38 ± 0.02 | 0.38 ± 0.02 |
| util_us | 0.24 ± 0.01 | 0.24 ± 0.01 | 0.24 ± 0.01 | 0.24 ± 0.01 |
| util_specialist | 0.78 ± 0.01 | 0.78 ± 0.01 | 0.79 ± 0.01 | 0.79 ± 0.01 |
| util_bed | 0.95 ± 0.02 | 0.94 ± 0.02 | 0.95 ± 0.02 | 0.95 ± 0.02 |
## Scenario: base_review

Replications per arm: {'load_aware': 20, 'moa_load': 20, 'moa_static': 20, 'rule_mts': 20}

### Primary metrics (mean ± 95% CI over replications)

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Doctor wait, mean (min) | 99.4 ± 5.9 | 99.0 ± 5.6 | 102.6 ± 5.8 | 103.2 ± 5.7 |
| Doctor wait, P90 (min) | 244.1 ± 13.6 | 242.4 ± 14.2 | 251.7 ± 14.3 | 252.1 ± 14.3 |
| Time to needed imaging, mean (min) | 92.1 ± 4.8 | 93.2 ± 4.8 | 24.5 ± 2.9 | 25.5 ± 2.5 |
| Length of stay, mean (min) | 242.3 ± 8.9 | 243.5 ± 9.1 | 242.6 ± 8.9 | 241.8 ± 8.4 |
| Protocol-violation rate (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Never seen by a doctor (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |

### Secondary metrics

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| Never seen by a doctor (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Fallback rate (%) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| censored_rate | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Re-streamed UTC to ED (%) | 1.50 ± 0.09 | 1.46 ± 0.10 | 1.47 ± 0.09 | 1.50 ± 0.09 |
| Unnecessary scans (% of patients) | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 | 0.00 ± 0.00 |
| Imaging first (%) | 14.33 ± 0.35 | 14.33 ± 0.35 | 33.00 ± 0.42 | 33.83 ± 0.57 |
| Streamed to UTC (%) | 41.79 ± 0.65 | 40.42 ± 0.58 | 40.44 ± 0.58 | 40.98 ± 0.61 |
| Doctor contacts per patient | 1.38 ± 0.01 | 1.38 ± 0.01 | 1.38 ± 0.01 | 1.38 ± 0.01 |
| Length of stay, P90 (min) | 493.7 ± 25.0 | 511.9 ± 25.0 | 507.8 ± 24.5 | 499.8 ± 22.3 |
| Doctor-wait gap across groups (min) | 41.1 ± 4.8 | 44.5 ± 7.5 | 49.2 ± 5.4 | 52.7 ± 4.9 |
| LOS gap across groups (min) | 91.2 ± 9.5 | 92.7 ± 8.9 | 98.6 ± 9.2 | 102.9 ± 9.7 |

### Utilisation (fraction of capacity, measurement window)

| Metric | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| util_ed_doctor | 0.86 ± 0.01 | 0.87 ± 0.01 | 0.87 ± 0.01 | 0.87 ± 0.01 |
| util_utc_doctor | 0.77 ± 0.02 | 0.74 ± 0.01 | 0.74 ± 0.01 | 0.75 ± 0.02 |
| util_xray | 0.55 ± 0.01 | 0.55 ± 0.01 | 0.54 ± 0.01 | 0.54 ± 0.01 |
| util_ct | 0.32 ± 0.01 | 0.32 ± 0.01 | 0.32 ± 0.01 | 0.32 ± 0.01 |
| util_us | 0.20 ± 0.01 | 0.20 ± 0.01 | 0.20 ± 0.01 | 0.20 ± 0.01 |
| util_specialist | 0.65 ± 0.01 | 0.65 ± 0.01 | 0.65 ± 0.01 | 0.65 ± 0.01 |
| util_bed | 0.82 ± 0.02 | 0.82 ± 0.02 | 0.82 ± 0.02 | 0.82 ± 0.02 |

## Primary family: moa_load vs each baseline (Holm over all 20 tests)

| Scenario | Comparison | Metric | Difference (95% CI) | Relative | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|---|
| base | moa_load − rule_mts | Doctor wait, mean (min) | 10.0 ± 1.3 | +9.6% | 8e-13 | 1.3e-11 | AI worse |
| base | moa_load − rule_mts | Doctor wait, P90 (min) | 30.2 ± 5.7 | +11.7% | 9.1e-10 | 1.2e-08 | AI worse |
| base | moa_load − rule_mts | Time to needed imaging, mean (min) | -72.1 ± 3.6 | -73.8% | 2.7e-20 | 5.1e-19 | AI better |
| base | moa_load − rule_mts | Length of stay, mean (min) | -1.90 ± 1.38 | -0.8% | 0.0095 | 0.057 | no detectable difference |
| base | moa_load − rule_mts | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| base | moa_load − load_aware | Doctor wait, mean (min) | 10.1 ± 0.9 | +9.7% | 6.2e-16 | 1.1e-14 | AI worse |
| base | moa_load − load_aware | Doctor wait, P90 (min) | 30.1 ± 3.0 | +11.6% | 1e-14 | 1.8e-13 | AI worse |
| base | moa_load − load_aware | Time to needed imaging, mean (min) | -73.1 ± 3.6 | -74.1% | 2.2e-20 | 4.4e-19 | AI better |
| base | moa_load − load_aware | Length of stay, mean (min) | -3.12 ± 1.20 | -1.3% | 3.1e-05 | 0.00022 | AI better |
| base | moa_load − load_aware | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| stress | moa_load − rule_mts | Doctor wait, mean (min) | 38.2 ± 9.7 | +12.5% | 1e-07 | 9e-07 | AI worse |
| stress | moa_load − rule_mts | Doctor wait, P90 (min) | 78.0 ± 16.9 | +11.3% | 9.2e-09 | 1e-07 | AI worse |
| stress | moa_load − rule_mts | Time to needed imaging, mean (min) | -217.2 ± 34.1 | -75.4% | 4.3e-11 | 6e-10 | AI better |
| stress | moa_load − rule_mts | Length of stay, mean (min) | -17.6 ± 20.8 | -2.2% | 0.092 | 0.46 | no detectable difference |
| stress | moa_load − rule_mts | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| stress | moa_load − load_aware | Doctor wait, mean (min) | 29.6 ± 6.0 | +9.4% | 3.5e-09 | 4.2e-08 | AI worse |
| stress | moa_load − load_aware | Doctor wait, P90 (min) | 76.5 ± 17.4 | +11.0% | 2e-08 | 2e-07 | AI worse |
| stress | moa_load − load_aware | Time to needed imaging, mean (min) | -217.8 ± 33.8 | -75.4% | 3.5e-11 | 5.3e-10 | AI better |
| stress | moa_load − load_aware | Length of stay, mean (min) | -38.1 ± 11.2 | -4.6% | 9.1e-07 | 7.3e-06 | AI better |
| stress | moa_load − load_aware | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |

## Secondary: state-blind MoA (moa_static) (Holm within this family)

| Scenario | Comparison | Metric | Difference (95% CI) | Relative | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|---|
| base | moa_static − rule_mts | Doctor wait, mean (min) | 10.5 ± 1.0 | +10.1% | 3.7e-15 | 1e-13 | AI worse |
| base | moa_static − rule_mts | Doctor wait, P90 (min) | 28.7 ± 6.1 | +11.1% | 7.6e-09 | 1.7e-07 | AI worse |
| base | moa_static − rule_mts | Time to needed imaging, mean (min) | -71.3 ± 3.5 | -73.0% | 2.6e-20 | 7.5e-19 | AI better |
| base | moa_static − rule_mts | Length of stay, mean (min) | -2.81 ± 1.38 | -1.2% | 0.00042 | 0.0064 | AI better |
| base | moa_static − rule_mts | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| base | moa_static − load_aware | Doctor wait, mean (min) | 10.6 ± 1.0 | +10.2% | 2.8e-15 | 8e-14 | AI worse |
| base | moa_static − load_aware | Doctor wait, P90 (min) | 28.6 ± 4.3 | +11.0% | 2.1e-11 | 5.5e-10 | AI worse |
| base | moa_static − load_aware | Time to needed imaging, mean (min) | -72.4 ± 3.5 | -73.3% | 2e-20 | 6e-19 | AI better |
| base | moa_static − load_aware | Length of stay, mean (min) | -4.03 ± 1.66 | -1.7% | 6.5e-05 | 0.001 | AI better |
| base | moa_static − load_aware | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| base | moa_static − moa_load | Doctor wait, mean (min) | 0.50 ± 0.66 | +0.4% | 0.13 | 1 | no detectable difference |
| base | moa_static − moa_load | Doctor wait, P90 (min) | -1.53 ± 2.83 | -0.5% | 0.27 | 1 | no detectable difference |
| base | moa_static − moa_load | Time to needed imaging, mean (min) | 0.77 ± 0.89 | +3.0% | 0.086 | 0.95 | no detectable difference |
| base | moa_static − moa_load | Length of stay, mean (min) | -0.90 ± 1.13 | -0.4% | 0.11 | 1 | no detectable difference |
| base | moa_static − moa_load | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| stress | moa_static − rule_mts | Doctor wait, mean (min) | 33.9 ± 6.8 | +11.1% | 2.5e-09 | 5.7e-08 | AI worse |
| stress | moa_static − rule_mts | Doctor wait, P90 (min) | 85.6 ± 20.4 | +12.4% | 4.2e-08 | 8.4e-07 | AI worse |
| stress | moa_static − rule_mts | Time to needed imaging, mean (min) | -225.7 ± 39.2 | -78.3% | 2.5e-10 | 5.9e-09 | AI better |
| stress | moa_static − rule_mts | Length of stay, mean (min) | -37.5 ± 18.6 | -4.7% | 0.00047 | 0.0066 | AI better |
| stress | moa_static − rule_mts | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| stress | moa_static − load_aware | Doctor wait, mean (min) | 25.3 ± 9.2 | +8.0% | 1.5e-05 | 0.00026 | AI worse |
| stress | moa_static − load_aware | Doctor wait, P90 (min) | 84.2 ± 21.0 | +12.1% | 8.3e-08 | 1.6e-06 | AI worse |
| stress | moa_static − load_aware | Time to needed imaging, mean (min) | -226.2 ± 38.9 | -78.3% | 2.1e-10 | 5.2e-09 | AI better |
| stress | moa_static − load_aware | Length of stay, mean (min) | -57.9 ± 12.4 | -7.0% | 8e-09 | 1.7e-07 | AI better |
| stress | moa_static − load_aware | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| stress | moa_static − moa_load | Doctor wait, mean (min) | -4.29 ± 5.88 | -1.2% | 0.14 | 1 | no detectable difference |
| stress | moa_static − moa_load | Doctor wait, P90 (min) | 7.63 ± 5.99 | +1.0% | 0.015 | 0.2 | no detectable difference |
| stress | moa_static − moa_load | Time to needed imaging, mean (min) | -8.45 ± 7.47 | -11.9% | 0.029 | 0.34 | no detectable difference |
| stress | moa_static − moa_load | Length of stay, mean (min) | -19.9 ± 6.6 | -2.5% | 4.6e-06 | 8.2e-05 | AI better |
| stress | moa_static − moa_load | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |

## Fairness: group gaps (max − min across sex × ethnicity groups) (Holm within this family)

| Scenario | Comparison | Metric | Difference (95% CI) | Relative | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|---|
| base | moa_load − rule_mts | Doctor-wait gap across groups (min) | 12.9 ± 4.1 | +29.4% | 2.9e-06 | 2.3e-05 | AI worse |
| base | moa_load − rule_mts | LOS gap across groups (min) | -3.67 ± 5.71 | -4.5% | 0.19 | 0.39 | no detectable difference |
| base | moa_load − load_aware | Doctor-wait gap across groups (min) | 8.42 ± 5.00 | +17.5% | 0.0023 | 0.011 | AI worse |
| base | moa_load − load_aware | LOS gap across groups (min) | -5.00 ± 4.61 | -6.1% | 0.035 | 0.1 | no detectable difference |
| stress | moa_load − rule_mts | Doctor-wait gap across groups (min) | 45.9 ± 24.7 | +29.5% | 0.00097 | 0.0058 | AI worse |
| stress | moa_load − rule_mts | LOS gap across groups (min) | 46.6 ± 39.4 | +4.7% | 0.023 | 0.091 | no detectable difference |
| stress | moa_load − load_aware | Doctor-wait gap across groups (min) | 29.0 ± 14.1 | +16.8% | 0.00037 | 0.0026 | AI worse |
| stress | moa_load − load_aware | LOS gap across groups (min) | -4.05 ± 16.56 | -0.4% | 0.61 | 0.61 | no detectable difference |

## Sensitivity: imaging-first does not save the review contact (Holm within this family)

| Scenario | Comparison | Metric | Difference (95% CI) | Relative | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|---|
| base_review | moa_load − rule_mts | Doctor wait, mean (min) | 3.27 ± 0.98 | +3.3% | 1.2e-06 | 6.9e-06 | AI worse |
| base_review | moa_load − rule_mts | Doctor wait, P90 (min) | 7.63 ± 4.42 | +3.1% | 0.0019 | 0.0093 | AI worse |
| base_review | moa_load − rule_mts | Time to needed imaging, mean (min) | -67.6 ± 3.2 | -73.4% | 1.7e-20 | 1.5e-19 | AI better |
| base_review | moa_load − rule_mts | Length of stay, mean (min) | 0.34 ± 1.04 | +0.1% | 0.5 | 1 | no detectable difference |
| base_review | moa_load − rule_mts | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |
| base_review | moa_load − load_aware | Doctor wait, mean (min) | 3.66 ± 0.65 | +3.7% | 3.2e-10 | 2.6e-09 | AI worse |
| base_review | moa_load − load_aware | Doctor wait, P90 (min) | 9.31 ± 2.65 | +3.8% | 5.6e-07 | 3.9e-06 | AI worse |
| base_review | moa_load − load_aware | Time to needed imaging, mean (min) | -68.7 ± 3.3 | -73.7% | 1.5e-20 | 1.5e-19 | AI better |
| base_review | moa_load − load_aware | Length of stay, mean (min) | -0.82 ± 0.65 | -0.3% | 0.016 | 0.065 | no detectable difference |
| base_review | moa_load − load_aware | Protocol-violation rate (%) | 0.00 ± 0.00 | +nan% | 1 | 1 | no detectable difference |

## Fairness: counterfactual demographic swaps (MoA, state-blind)

(counterfactual probe not run)

## Harm family (PREREG_V3 5.4): moa_load vs rule_mts in the v2 harm subgroups (Holm within this family; removed = upper 95% limit < +10 min)

| Scenario | Comparison | Metric | Difference (95% CI) | Relative | p | p (Holm) | Verdict |
|---|---|---|---|---|---|---|---|
| base | moa_load − rule_mts | Whiplash (green): doctor wait (min) | 3.35 ± 6.29 | +3.5% | 0.28 | 0.28 | no detectable difference |
| base | moa_load − rule_mts | Gunshot/TBI/appendicitis (red/orange): doctor wait (min) | 1.25 ± 0.42 | +21.3% | 4.9e-06 | 2.4e-05 | AI worse |
| base | moa_load − rule_mts | Suspected hip fracture: LOS (min) | 22.0 ± 15.7 | +5.3% | 0.0083 | 0.033 | AI worse |
| stress | moa_load − rule_mts | Whiplash (green): doctor wait (min) | 37.5 ± 37.7 | +17.9% | 0.051 | 0.1 | no detectable difference |
| stress | moa_load − rule_mts | Gunshot/TBI/appendicitis (red/orange): doctor wait (min) | 1.43 ± 0.43 | +21.3% | 1.3e-06 | 8e-06 | AI worse |
| stress | moa_load − rule_mts | Suspected hip fracture: LOS (min) | 143.2 ± 106.5 | +14.2% | 0.011 | 0.033 | AI worse |

Removed: base/harm_whiplash_dw (n=20)=yes, base/harm_ro_imaging_dw (n=20)=yes, base/harm_hip_los (n=20)=NO, stress/harm_whiplash_dw (n=20)=NO, stress/harm_ro_imaging_dw (n=20)=yes, stress/harm_hip_los (n=20)=NO
