## sim_dissertation_table_qwen2.5-7b_fixed_routing: {'duration': 43200, 'arrival_rate': 12, 'num_doctors': 3, 'num_mri': 1, 'num_ultrasound': 1, 'num_beds': 5}, warm-up 1440 min, --fix-routing

N = 30 replications per arm, same seeds across arms; mean +/- 95% t half-width across replications.

| metric | rule_based | llm_single | llm_moa |
|---|---|---|---|
| patients | 8.63e+03 +/- 30 | 8.64e+03 +/- 27 | 8.64e+03 +/- 32 |
| never_see_doctor | 0 +/- 0 | 0 +/- 0 | 0 +/- 0 |
| urgent_mri_bypass_rate | 0 +/- 0 | 100 +/- 0 | 0 +/- 0 |
| doctor_wait_ascoded | 325 +/- 60 | 337 +/- 76 | 315 +/- 61 |
| mri_wait_ascoded | 12.5 +/- 0.89 | 12.8 +/- 0.86 | 12.9 +/- 1.1 |
| ultrasound_wait_ascoded | 73.7 +/- 6.6 | 74.9 +/- 8 | 80.4 +/- 8.3 |
| bed_wait_ascoded | 2.95e+03 +/- 1.3e+02 | 2.8e+03 +/- 1.4e+02 | 2.83e+03 +/- 1.1e+02 |
| doctor_wait | 335 +/- 62 | 346 +/- 78 | 324 +/- 63 |
| mri_wait | 12.6 +/- 0.92 | 12.9 +/- 0.89 | 12.7 +/- 1.1 |
| ultrasound_wait | 74.2 +/- 6.9 | 75.4 +/- 8.3 | 81 +/- 8.3 |
| bed_wait | 3.07e+03 +/- 1.4e+02 | 2.92e+03 +/- 1.4e+02 | 2.94e+03 +/- 1.2e+02 |
| doctor_still_waiting | 0.0114 +/- 0.0031 | 0.015 +/- 0.0037 | 0.0127 +/- 0.0034 |
| mri_still_waiting | 0.000563 +/- 0.00039 | 0.000476 +/- 0.00054 | 0.000275 +/- 0.00056 |
| ultrasound_still_waiting | 0.00152 +/- 0.00064 | 0.00171 +/- 0.00085 | 0.00194 +/- 0.00096 |
| bed_still_waiting | 0.583 +/- 0.0025 | 0.579 +/- 0.0031 | 0.582 +/- 0.0028 |
| doctor_util_ascoded | 98.9 +/- 0.34 | 98.8 +/- 0.34 | 98.9 +/- 0.27 |
| mri_util_ascoded | 29.9 +/- 0.66 | 29.9 +/- 0.68 | 29.8 +/- 0.91 |
| ultrasound_util_ascoded | 78.9 +/- 0.93 | 79.8 +/- 0.9 | 80.1 +/- 1.2 |
| bed_util_ascoded | 100 +/- 0.027 | 100 +/- 0.026 | 100 +/- 0.025 |
| doctor_util | 99.1 +/- 0.34 | 99 +/- 0.34 | 99.1 +/- 0.26 |
| mri_util | 30 +/- 0.64 | 30 +/- 0.69 | 29.8 +/- 0.94 |
| ultrasound_util | 79.1 +/- 0.93 | 79.9 +/- 0.94 | 80.3 +/- 1.1 |
| bed_util | 100 +/- 0 | 100 +/- 0 | 100 +/- 0 |
| mean_util_ascoded | 76.9 +/- 0.33 | 77.1 +/- 0.25 | 77.2 +/- 0.43 |
| mean_util | 77 +/- 0.33 | 77.2 +/- 0.26 | 77.3 +/- 0.43 |

Paired differences vs rule_based (arm minus baseline; Holm-adjusted over the 10 tests):

| arm | metric | diff +/- 95% CI | relative | p | p (Holm) |
|---|---|---|---|---|---|
| llm_single | doctor_wait | 11.8 +/- 99 | +3.5% | 0.81 | 1 |
| llm_single | mri_wait | 0.308 +/- 1.4 | +2.4% | 0.66 | 1 |
| llm_single | ultrasound_wait | 1.23 +/- 9 | +1.7% | 0.78 | 1 |
| llm_single | bed_wait | -149 +/- 2.2e+02 | -4.9% | 0.17 | 1 |
| llm_single | mean_util | 0.21 +/- 0.38 | +0.3% | 0.27 | 1 |
| llm_moa | doctor_wait | -10.8 +/- 89 | -3.2% | 0.8 | 1 |
| llm_moa | mri_wait | 0.17 +/- 1.7 | +1.4% | 0.84 | 1 |
| llm_moa | ultrasound_wait | 6.83 +/- 10 | +9.2% | 0.19 | 1 |
| llm_moa | bed_wait | -122 +/- 1.6e+02 | -4.0% | 0.14 | 1 |
| llm_moa | mean_util | 0.278 +/- 0.45 | +0.4% | 0.21 | 1 |
