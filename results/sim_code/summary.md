## sim_code: {'duration': 5000, 'arrival_rate': 25, 'num_doctors': 3, 'num_mri': 1, 'num_ultrasound': 1, 'num_beds': 5}, warm-up 1440 min

N = 30 replications per arm, same seeds across arms; mean +/- 95% t half-width across replications.

| metric | rule_based | single_llm | multi_llm |
|---|---|---|---|
| patients | 2.06e+03 +/- 14 | 2.07e+03 +/- 19 | 2.07e+03 +/- 17 |
| never_see_doctor | 0 +/- 0 | 0.0399 +/- 0.0016 | 0.0355 +/- 0.0013 |
| urgent_mri_bypass_rate | 0 +/- 0 | 80.5 +/- 1.5 | 70.8 +/- 1.6 |
| doctor_wait_ascoded | 156 +/- 21 | 175 +/- 23 | 176 +/- 22 |
| mri_wait_ascoded | 41.2 +/- 8.5 | 27.2 +/- 6.4 | 22.4 +/- 4.3 |
| ultrasound_wait_ascoded | 73.5 +/- 17 | 104 +/- 32 | 69.5 +/- 8.5 |
| bed_wait_ascoded | 405 +/- 41 | 442 +/- 40 | 436 +/- 37 |
| doctor_wait | 153 +/- 31 | 86.1 +/- 21 | 80.1 +/- 19 |
| mri_wait | 41.2 +/- 9.1 | 28.1 +/- 6.6 | 21 +/- 5.6 |
| ultrasound_wait | 68.5 +/- 20 | 96.9 +/- 32 | 62.2 +/- 9.4 |
| bed_wait | 503 +/- 46 | 557 +/- 44 | 534 +/- 40 |
| doctor_still_waiting | 0.532 +/- 0.0072 | 0.53 +/- 0.0041 | 0.532 +/- 0.0054 |
| mri_still_waiting | 0.0128 +/- 0.0077 | 0.00801 +/- 0.0057 | 0.00657 +/- 0.008 |
| ultrasound_still_waiting | 0.0273 +/- 0.017 | 0.0277 +/- 0.013 | 0.0211 +/- 0.01 |
| bed_still_waiting | 0.61 +/- 0.012 | 0.64 +/- 0.013 | 0.636 +/- 0.015 |
| doctor_util_ascoded | 100 +/- 0.077 | 100 +/- 0.055 | 100 +/- 0.065 |
| mri_util_ascoded | 59.8 +/- 2.5 | 49.3 +/- 3.1 | 42.8 +/- 2.4 |
| ultrasound_util_ascoded | 78.6 +/- 3.4 | 84.3 +/- 3.2 | 82.2 +/- 2.5 |
| bed_util_ascoded | 101 +/- 0.23 | 101 +/- 0.22 | 101 +/- 0.24 |
| doctor_util | 100 +/- 0 | 100 +/- 0 | 100 +/- 0 |
| mri_util | 61 +/- 3.1 | 49.5 +/- 3.3 | 42.4 +/- 3.2 |
| ultrasound_util | 80.2 +/- 4 | 84.9 +/- 3.5 | 83.9 +/- 3 |
| bed_util | 100 +/- 0 | 100 +/- 0 | 100 +/- 0 |
| mean_util_ascoded | 84.8 +/- 0.88 | 83.6 +/- 1.2 | 81.5 +/- 0.88 |
| mean_util | 85.3 +/- 1.1 | 83.6 +/- 1.3 | 81.6 +/- 1.1 |

Paired differences vs rule_based (arm minus baseline; Holm-adjusted over the 10 tests):

| arm | metric | diff +/- 95% CI | relative | p | p (Holm) |
|---|---|---|---|---|---|
| single_llm | doctor_wait | -67.1 +/- 40 | -43.8% | 0.0017 | 0.012 |
| single_llm | mri_wait | -13.1 +/- 11 | -31.8% | 0.024 | 0.15 |
| single_llm | ultrasound_wait | 28.4 +/- 35 | +41.4% | 0.1 | 0.31 |
| single_llm | bed_wait | 54.8 +/- 61 | +10.9% | 0.075 | 0.3 |
| single_llm | mean_util | -1.69 +/- 1.6 | -2.0% | 0.034 | 0.17 |
| multi_llm | doctor_wait | -73.1 +/- 36 | -47.7% | 0.00029 | 0.0026 |
| multi_llm | mri_wait | -20.3 +/- 11 | -49.2% | 0.00078 | 0.0063 |
| multi_llm | ultrasound_wait | -6.31 +/- 23 | -9.2% | 0.58 | 0.58 |
| multi_llm | bed_wait | 31.9 +/- 59 | +6.3% | 0.28 | 0.56 |
| multi_llm | mean_util | -3.72 +/- 1.3 | -4.4% | 2.2e-06 | 2.2e-05 |
