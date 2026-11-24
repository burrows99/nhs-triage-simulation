## sim_dissertation: {'duration': 43200, 'arrival_rate': 12, 'num_doctors': 3, 'num_mri': 1, 'num_ultrasound': 1, 'num_beds': 5}, warm-up 1440 min

N = 30 replications per arm, same seeds across arms; mean +/- 95% t half-width across replications.

| metric | rule_based | single_llm | multi_llm |
|---|---|---|---|
| patients | 8.63e+03 +/- 30 | 8.65e+03 +/- 42 | 8.62e+03 +/- 38 |
| never_see_doctor | 0 +/- 0 | 0.04 +/- 0.00076 | 0.035 +/- 0.0008 |
| urgent_mri_bypass_rate | 0 +/- 0 | 80.1 +/- 0.8 | 70.2 +/- 0.73 |
| doctor_wait_ascoded | 325 +/- 60 | 122 +/- 26 | 122 +/- 20 |
| mri_wait_ascoded | 12.5 +/- 0.89 | 9.84 +/- 1.1 | 7.9 +/- 0.86 |
| ultrasound_wait_ascoded | 73.7 +/- 6.6 | 80.7 +/- 8.3 | 73.9 +/- 7.4 |
| bed_wait_ascoded | 2.95e+03 +/- 1.3e+02 | 2.91e+03 +/- 1.3e+02 | 2.95e+03 +/- 1.3e+02 |
| doctor_wait | 335 +/- 62 | 124 +/- 27 | 124 +/- 21 |
| mri_wait | 12.6 +/- 0.92 | 9.92 +/- 1 | 7.94 +/- 0.91 |
| ultrasound_wait | 74.2 +/- 6.9 | 80.9 +/- 8.2 | 73.9 +/- 7.6 |
| bed_wait | 3.07e+03 +/- 1.4e+02 | 3.03e+03 +/- 1.3e+02 | 3.07e+03 +/- 1.4e+02 |
| doctor_still_waiting | 0.0114 +/- 0.0031 | 0.00324 +/- 0.0012 | 0.00388 +/- 0.0011 |
| mri_still_waiting | 0.000563 +/- 0.00039 | 0 +/- 0 | 0.000119 +/- 0.00024 |
| ultrasound_still_waiting | 0.00152 +/- 0.00064 | 0.00186 +/- 0.00091 | 0.0016 +/- 0.00068 |
| bed_still_waiting | 0.583 +/- 0.0025 | 0.584 +/- 0.0029 | 0.584 +/- 0.003 |
| doctor_util_ascoded | 98.9 +/- 0.34 | 96.2 +/- 0.58 | 96.2 +/- 0.57 |
| mri_util_ascoded | 29.9 +/- 0.66 | 24.1 +/- 0.71 | 20.7 +/- 0.66 |
| ultrasound_util_ascoded | 78.9 +/- 0.93 | 80.3 +/- 1 | 79.7 +/- 1.1 |
| bed_util_ascoded | 100 +/- 0.027 | 100 +/- 0.032 | 100 +/- 0.029 |
| doctor_util | 99.1 +/- 0.34 | 96.3 +/- 0.58 | 96.3 +/- 0.58 |
| mri_util | 30 +/- 0.64 | 24.2 +/- 0.7 | 20.7 +/- 0.66 |
| ultrasound_util | 79.1 +/- 0.93 | 80.4 +/- 1 | 79.8 +/- 1.1 |
| bed_util | 100 +/- 0 | 100 +/- 0 | 100 +/- 0 |
| mean_util_ascoded | 76.9 +/- 0.33 | 75.2 +/- 0.4 | 74.2 +/- 0.37 |
| mean_util | 77 +/- 0.33 | 75.2 +/- 0.38 | 74.2 +/- 0.38 |

Paired differences vs rule_based (arm minus baseline; Holm-adjusted over the 10 tests):

| arm | metric | diff +/- 95% CI | relative | p | p (Holm) |
|---|---|---|---|---|---|
| single_llm | doctor_wait | -211 +/- 68 | -63.0% | 6.7e-07 | 4e-06 |
| single_llm | mri_wait | -2.65 +/- 1.5 | -21.1% | 0.00083 | 0.0042 |
| single_llm | ultrasound_wait | 6.71 +/- 11 | +9.1% | 0.23 | 0.9 |
| single_llm | bed_wait | -38.8 +/- 1.7e+02 | -1.3% | 0.65 | 1 |
| single_llm | mean_util | -1.79 +/- 0.46 | -2.3% | 1.1e-08 | 9.7e-08 |
| multi_llm | doctor_wait | -211 +/- 66 | -63.0% | 3.6e-07 | 2.5e-06 |
| multi_llm | mri_wait | -4.63 +/- 1.4 | -36.8% | 2.5e-07 | 2e-06 |
| multi_llm | ultrasound_wait | -0.264 +/- 10 | -0.4% | 0.96 | 1 |
| multi_llm | bed_wait | 7.55 +/- 1.8e+02 | +0.2% | 0.93 | 1 |
| multi_llm | mean_util | -2.82 +/- 0.47 | -3.7% | 6.1e-13 | 6.1e-12 |
