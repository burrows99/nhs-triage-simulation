## sim_dissertation_fixed_routing: {'duration': 43200, 'arrival_rate': 12, 'num_doctors': 3, 'num_mri': 1, 'num_ultrasound': 1, 'num_beds': 5}, warm-up 1440 min, --fix-routing

N = 30 replications per arm, same seeds across arms; mean +/- 95% t half-width across replications.

| metric | rule_based | single_llm | multi_llm |
|---|---|---|---|
| patients | 8.63e+03 +/- 30 | 8.63e+03 +/- 37 | 8.63e+03 +/- 42 |
| never_see_doctor | 0 +/- 0 | 0 +/- 0 | 0 +/- 0 |
| urgent_mri_bypass_rate | 0 +/- 0 | 80 +/- 0.81 | 70.1 +/- 0.73 |
| doctor_wait_ascoded | 325 +/- 60 | 374 +/- 73 | 325 +/- 62 |
| mri_wait_ascoded | 12.5 +/- 0.89 | 12.3 +/- 0.96 | 12.7 +/- 1.1 |
| ultrasound_wait_ascoded | 73.7 +/- 6.6 | 78.3 +/- 14 | 77 +/- 8.5 |
| bed_wait_ascoded | 2.95e+03 +/- 1.3e+02 | 2.93e+03 +/- 1.6e+02 | 2.94e+03 +/- 1.1e+02 |
| doctor_wait | 335 +/- 62 | 385 +/- 75 | 335 +/- 65 |
| mri_wait | 12.6 +/- 0.92 | 12.3 +/- 0.96 | 12.9 +/- 1.1 |
| ultrasound_wait | 74.2 +/- 6.9 | 79.2 +/- 14 | 77.9 +/- 9 |
| bed_wait | 3.07e+03 +/- 1.4e+02 | 3.05e+03 +/- 1.6e+02 | 3.06e+03 +/- 1.2e+02 |
| doctor_still_waiting | 0.0114 +/- 0.0031 | 0.0116 +/- 0.0034 | 0.0119 +/- 0.0035 |
| mri_still_waiting | 0.000563 +/- 0.00039 | 0.000246 +/- 0.00028 | 0.000311 +/- 0.0003 |
| ultrasound_still_waiting | 0.00152 +/- 0.00064 | 0.00254 +/- 0.0012 | 0.00157 +/- 0.0008 |
| bed_still_waiting | 0.583 +/- 0.0025 | 0.582 +/- 0.0028 | 0.583 +/- 0.0036 |
| doctor_util_ascoded | 98.9 +/- 0.34 | 99 +/- 0.37 | 98.9 +/- 0.34 |
| mri_util_ascoded | 29.9 +/- 0.66 | 30 +/- 0.83 | 29.9 +/- 0.89 |
| ultrasound_util_ascoded | 78.9 +/- 0.93 | 78.6 +/- 1.2 | 78.6 +/- 0.91 |
| bed_util_ascoded | 100 +/- 0.027 | 100 +/- 0.028 | 100 +/- 0.025 |
| doctor_util | 99.1 +/- 0.34 | 99.2 +/- 0.36 | 99.1 +/- 0.32 |
| mri_util | 30 +/- 0.64 | 30.1 +/- 0.79 | 30 +/- 0.84 |
| ultrasound_util | 79.1 +/- 0.93 | 78.8 +/- 1.1 | 78.8 +/- 0.95 |
| bed_util | 100 +/- 0 | 100 +/- 0 | 100 +/- 0 |
| mean_util_ascoded | 76.9 +/- 0.33 | 76.9 +/- 0.38 | 76.9 +/- 0.34 |
| mean_util | 77 +/- 0.33 | 77 +/- 0.38 | 77 +/- 0.34 |

Paired differences vs rule_based (arm minus baseline; Holm-adjusted over the 10 tests):

| arm | metric | diff +/- 95% CI | relative | p | p (Holm) |
|---|---|---|---|---|---|
| single_llm | doctor_wait | 50.1 +/- 1e+02 | +15.0% | 0.33 | 1 |
| single_llm | mri_wait | -0.263 +/- 1.1 | -2.1% | 0.62 | 1 |
| single_llm | ultrasound_wait | 5.08 +/- 17 | +6.9% | 0.54 | 1 |
| single_llm | bed_wait | -13.3 +/- 2e+02 | -0.4% | 0.89 | 1 |
| single_llm | mean_util | -0.0224 +/- 0.48 | -0.0% | 0.92 | 1 |
| multi_llm | doctor_wait | 0.0322 +/- 79 | +0.0% | 1 | 1 |
| multi_llm | mri_wait | 0.295 +/- 1.4 | +2.3% | 0.68 | 1 |
| multi_llm | ultrasound_wait | 3.76 +/- 12 | +5.1% | 0.53 | 1 |
| multi_llm | bed_wait | -0.942 +/- 1.4e+02 | -0.0% | 0.99 | 1 |
| multi_llm | mean_util | -0.0505 +/- 0.42 | -0.1% | 0.81 | 1 |
