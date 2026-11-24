## sim_dissertation_stable_4doctors_15beds: {'duration': 43200, 'arrival_rate': 12, 'num_doctors': 4, 'num_mri': 1, 'num_ultrasound': 1, 'num_beds': 15}, warm-up 1440 min

N = 30 replications per arm, same seeds across arms; mean +/- 95% t half-width across replications.

| metric | rule_based | single_llm | multi_llm |
|---|---|---|---|
| patients | 8.66e+03 +/- 39 | 8.62e+03 +/- 29 | 8.63e+03 +/- 35 |
| never_see_doctor | 0 +/- 0 | 0.0403 +/- 0.00081 | 0.0345 +/- 0.00085 |
| urgent_mri_bypass_rate | 0 +/- 0 | 80 +/- 0.8 | 70.2 +/- 0.74 |
| doctor_wait_ascoded | 7.81 +/- 0.33 | 6.02 +/- 0.22 | 6.38 +/- 0.29 |
| mri_wait_ascoded | 13.8 +/- 1.4 | 8.7 +/- 0.79 | 7.89 +/- 0.78 |
| ultrasound_wait_ascoded | 81.3 +/- 6.4 | 76.5 +/- 6.5 | 75.1 +/- 6.4 |
| bed_wait_ascoded | 6.48 +/- 0.62 | 5.97 +/- 0.45 | 6.39 +/- 0.59 |
| doctor_wait | 7.81 +/- 0.33 | 6.07 +/- 0.23 | 6.4 +/- 0.3 |
| mri_wait | 14 +/- 1.5 | 8.71 +/- 0.81 | 7.98 +/- 0.78 |
| ultrasound_wait | 80.9 +/- 6.5 | 77.1 +/- 6.5 | 75.5 +/- 6.4 |
| bed_wait | 6.54 +/- 0.64 | 6.06 +/- 0.45 | 6.44 +/- 0.61 |
| doctor_still_waiting | 0.000124 +/- 0.00011 | 0.00015 +/- 0.00011 | 0.000149 +/- 9.6e-05 |
| mri_still_waiting | 0.000307 +/- 0.0003 | 0.000288 +/- 0.00044 | 0.000336 +/- 0.0005 |
| ultrasound_still_waiting | 0.00201 +/- 0.00083 | 0.00162 +/- 0.00098 | 0.00162 +/- 0.00094 |
| bed_still_waiting | 0.000195 +/- 0.00014 | 0.000301 +/- 0.00019 | 0.000244 +/- 0.00019 |
| doctor_util_ascoded | 75.2 +/- 0.46 | 71.9 +/- 0.37 | 72.4 +/- 0.35 |
| mri_util_ascoded | 30.5 +/- 0.91 | 23.9 +/- 0.74 | 20.7 +/- 0.73 |
| ultrasound_util_ascoded | 79.8 +/- 1 | 79.9 +/- 1.1 | 79.4 +/- 0.85 |
| bed_util_ascoded | 80.1 +/- 0.45 | 79.8 +/- 0.42 | 79.9 +/- 0.37 |
| doctor_util | 75.2 +/- 0.44 | 72 +/- 0.37 | 72.5 +/- 0.38 |
| mri_util | 30.6 +/- 0.94 | 23.8 +/- 0.75 | 20.7 +/- 0.76 |
| ultrasound_util | 79.9 +/- 1 | 80.1 +/- 1.1 | 79.6 +/- 0.85 |
| bed_util | 80.2 +/- 0.44 | 79.9 +/- 0.41 | 80 +/- 0.39 |
| mean_util_ascoded | 66.4 +/- 0.43 | 63.9 +/- 0.42 | 63.1 +/- 0.42 |
| mean_util | 66.5 +/- 0.43 | 63.9 +/- 0.43 | 63.2 +/- 0.45 |

Paired differences vs rule_based (arm minus baseline; Holm-adjusted over the 10 tests):

| arm | metric | diff +/- 95% CI | relative | p | p (Holm) |
|---|---|---|---|---|---|
| single_llm | doctor_wait | -1.74 +/- 0.4 | -22.3% | 8.5e-10 | 6.8e-09 |
| single_llm | mri_wait | -5.28 +/- 1.7 | -37.8% | 3.6e-07 | 2.2e-06 |
| single_llm | ultrasound_wait | -3.79 +/- 9.1 | -4.7% | 0.4 | 0.8 |
| single_llm | bed_wait | -0.483 +/- 0.75 | -7.4% | 0.2 | 0.79 |
| single_llm | mean_util | -2.53 +/- 0.5 | -3.8% | 3.2e-11 | 2.9e-10 |
| multi_llm | doctor_wait | -1.4 +/- 0.45 | -18.0% | 5e-07 | 2.5e-06 |
| multi_llm | mri_wait | -6.01 +/- 1.8 | -43.0% | 1.7e-07 | 1.2e-06 |
| multi_llm | ultrasound_wait | -5.39 +/- 9.3 | -6.7% | 0.24 | 0.79 |
| multi_llm | bed_wait | -0.104 +/- 0.81 | -1.6% | 0.8 | 0.8 |
| multi_llm | mean_util | -3.28 +/- 0.39 | -4.9% | 1.3e-16 | 1.3e-15 |
