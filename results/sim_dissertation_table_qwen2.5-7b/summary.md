## sim_dissertation_table_qwen2.5-7b: {'duration': 43200, 'arrival_rate': 12, 'num_doctors': 3, 'num_mri': 1, 'num_ultrasound': 1, 'num_beds': 5}, warm-up 1440 min

N = 30 replications per arm, same seeds across arms; mean +/- 95% t half-width across replications.

| metric | rule_based | llm_single | llm_moa |
|---|---|---|---|
| patients | 8.63e+03 +/- 30 | 8.63e+03 +/- 46 | 8.66e+03 +/- 49 |
| never_see_doctor | 0 +/- 0 | 0.239 +/- 0.0017 | 0.189 +/- 0.0012 |
| urgent_mri_bypass_rate | 0 +/- 0 | 100 +/- 0 | 0 +/- 0 |
| doctor_wait_ascoded | 325 +/- 60 | 12.1 +/- 0.68 | 18.1 +/- 1.2 |
| mri_wait_ascoded | 12.5 +/- 0.89 | 12.7 +/- 1 | 12.7 +/- 1.2 |
| ultrasound_wait_ascoded | 73.7 +/- 6.6 | 75.8 +/- 5.6 | 79.4 +/- 7.5 |
| bed_wait_ascoded | 2.95e+03 +/- 1.3e+02 | 2.79e+03 +/- 1.5e+02 | 2.97e+03 +/- 1.2e+02 |
| doctor_wait | 335 +/- 62 | 12.2 +/- 0.71 | 18.1 +/- 1.2 |
| mri_wait | 12.6 +/- 0.92 | 12.8 +/- 1.1 | 12.6 +/- 1.2 |
| ultrasound_wait | 74.2 +/- 6.9 | 75.8 +/- 5.6 | 79.5 +/- 7.8 |
| bed_wait | 3.07e+03 +/- 1.4e+02 | 2.9e+03 +/- 1.6e+02 | 3.09e+03 +/- 1.3e+02 |
| doctor_still_waiting | 0.0114 +/- 0.0031 | 0.000168 +/- 0.00012 | 0.00028 +/- 0.00015 |
| mri_still_waiting | 0.000563 +/- 0.00039 | 0 +/- 0 | 0.000532 +/- 0.00059 |
| ultrasound_still_waiting | 0.00152 +/- 0.00064 | 0.00278 +/- 0.00086 | 0.00147 +/- 0.00072 |
| bed_still_waiting | 0.583 +/- 0.0025 | 0.585 +/- 0.0038 | 0.588 +/- 0.0032 |
| doctor_util_ascoded | 98.9 +/- 0.34 | 76.1 +/- 0.52 | 81.3 +/- 0.68 |
| mri_util_ascoded | 29.9 +/- 0.66 | 29.6 +/- 0.73 | 29.6 +/- 1.2 |
| ultrasound_util_ascoded | 78.9 +/- 0.93 | 79.5 +/- 1 | 80.3 +/- 1 |
| bed_util_ascoded | 100 +/- 0.027 | 100 +/- 0.027 | 100 +/- 0.026 |
| doctor_util | 99.1 +/- 0.34 | 76.1 +/- 0.53 | 81.4 +/- 0.67 |
| mri_util | 30 +/- 0.64 | 29.6 +/- 0.74 | 29.5 +/- 1.2 |
| ultrasound_util | 79.1 +/- 0.93 | 79.5 +/- 1 | 80.3 +/- 1.1 |
| bed_util | 100 +/- 0 | 100 +/- 0 | 100 +/- 0 |
| mean_util_ascoded | 76.9 +/- 0.33 | 71.3 +/- 0.37 | 72.8 +/- 0.5 |
| mean_util | 77 +/- 0.33 | 71.3 +/- 0.36 | 72.8 +/- 0.5 |

Paired differences vs rule_based (arm minus baseline; Holm-adjusted over the 10 tests):

| arm | metric | diff +/- 95% CI | relative | p | p (Holm) |
|---|---|---|---|---|---|
| llm_single | doctor_wait | -322 +/- 62 | -96.4% | 1.4e-11 | 1.1e-10 |
| llm_single | mri_wait | 0.258 +/- 1.3 | +2.1% | 0.69 | 1 |
| llm_single | ultrasound_wait | 1.62 +/- 8.1 | +2.2% | 0.69 | 1 |
| llm_single | bed_wait | -168 +/- 1.7e+02 | -5.5% | 0.056 | 0.34 |
| llm_single | mean_util | -5.72 +/- 0.48 | -7.4% | 8.9e-21 | 8.9e-20 |
| llm_moa | doctor_wait | -316 +/- 62 | -94.6% | 2.3e-11 | 1.6e-10 |
| llm_moa | mri_wait | -0.0147 +/- 1.5 | -0.1% | 0.98 | 1 |
| llm_moa | ultrasound_wait | 5.34 +/- 10 | +7.2% | 0.29 | 1 |
| llm_moa | bed_wait | 23.4 +/- 1.4e+02 | +0.8% | 0.74 | 1 |
| llm_moa | mean_util | -4.21 +/- 0.51 | -5.5% | 1.7e-16 | 1.5e-15 |
