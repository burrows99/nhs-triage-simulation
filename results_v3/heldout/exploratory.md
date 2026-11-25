# Exploratory: case-mix-standardised group outcomes (not pre-registered)

## base: mean doctor wait by sex x ethnicity (all replications pooled)

| | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| raw gap (min) | 44.8 | 45.0 | 61.9 | 65.5 |
| standardised gap (min) | 24.4 | 23.6 | 32.0 | 33.4 |
| std F_asian | 90.1 | 90.5 | 92.5 | 92.2 |
| std F_black | 105.5 | 103.7 | 111.6 | 121.9 |
| std F_white | 102.9 | 101.9 | 109.4 | 107.1 |
| std M_asian | 103.9 | 101.1 | 112.4 | 110.5 |
| std M_black | 114.5 | 114.1 | 118.6 | 107.3 |
| std M_white | 113.6 | 112.8 | 124.5 | 125.6 |

## stress: mean doctor wait by sex x ethnicity (all replications pooled)

| | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| raw gap (min) | 130.5 | 142.3 | 170.6 | 172.0 |
| standardised gap (min) | 47.3 | 60.0 | 74.8 | 69.7 |
| std F_asian | 250.1 | 249.2 | 266.3 | 267.3 |
| std F_black | 285.4 | 285.0 | 307.3 | 307.5 |
| std F_white | 262.0 | 270.4 | 285.4 | 279.1 |
| std M_asian | 277.8 | 286.8 | 314.0 | 308.2 |
| std M_black | 297.4 | 299.0 | 333.9 | 302.0 |
| std M_white | 297.1 | 309.1 | 341.1 | 337.1 |

## base: per presentation, all replications pooled (min)

| MTS | presentation | rule_mts:route | moa_load:route | rule_mts:dw | moa_load:dw | d_dw(moa_load-rule) | rule_mts:los | moa_load:los | d_los(moa_load-rule) |
|---|---|---|---|---|---|---|---|---|---|
| green | burn | UTC | UTC | 101.8 | 89.7 | -12.0 | 121.8 | 110.4 | -11.4 |
| green | chronic_pain | UTC | UTC | 103.6 | 106.5 | 3.0 | 746.8 | 772.4 | 25.6 |
| green | head_injury_minor | UTC | UTC | 103.1 | 85.6 | -17.5 | 122.9 | 105.8 | -17.1 |
| green | laceration | UTC | UTC | 102.4 | 104.2 | 1.8 | 122.5 | 125.5 | 3.0 |
| green | sprain | UTC | UTC | 100.5 | 95.2 | -5.3 | 120.6 | 116.1 | -4.5 |
| green | whiplash | UTC | UTC | 103.5 | 102.9 | -0.5 | 123.4 | 124.0 | 0.6 |
| orange | allergy | ED | ED | 7.3 | 8.8 | 1.6 | 180.3 | 181.9 | 1.6 |
| orange | appendicitis | ED | US_FIRST | 6.9 | 8.9 | 2.0 | 241.2 | 253.0 | 11.9 |
| orange | asthma | ED | ED | 6.6 | 8.1 | 1.5 | 244.0 | 245.6 | 1.6 |
| orange | mi | ED | ED | 7.1 | 8.9 | 1.7 | 247.4 | 250.8 | 3.3 |
| orange | overdose | ED | ED | 6.8 | 8.2 | 1.4 | 243.6 | 245.8 | 2.1 |
| orange | stroke | CT_FIRST | CT_FIRST | 7.0 | 8.4 | 1.4 | 248.1 | 249.9 | 1.9 |
| orange | tbi | ED | CT_FIRST | 6.7 | 8.6 | 1.9 | 242.8 | 255.2 | 12.3 |
| red | cardiac_arrest | ED | ED | 4.3 | 5.5 | 1.2 | 254.0 | 254.0 | 0.0 |
| red | gunshot | ED | CT_FIRST | 4.5 | 5.5 | 1.0 | 263.3 | 273.8 | 10.5 |
| yellow | fracture_ankle | XRAY_FIRST | XRAY_FIRST | 184.4 | 205.4 | 21.0 | 309.6 | 330.6 | 21.0 |
| yellow | fracture_upper_limb | XRAY_FIRST | XRAY_FIRST | 184.4 | 206.0 | 21.6 | 342.2 | 363.9 | 21.7 |
| yellow | head_injury_loc | ED | CT_FIRST | 153.4 | 189.2 | 35.8 | 375.4 | 334.0 | -41.4 |
| yellow | heart_failure | ED | XRAY_FIRST | 154.6 | 188.5 | 33.9 | 473.5 | 451.9 | -21.6 |
| yellow | hip_fracture | XRAY_FIRST | XRAY_FIRST | 178.6 | 196.6 | 18.0 | 413.8 | 426.6 | 12.9 |
| yellow | knee_injury | ED | XRAY_FIRST | 153.5 | 201.1 | 47.6 | 371.8 | 332.0 | -39.8 |
| yellow | lung_mass | ED | XRAY_FIRST | 151.5 | 203.2 | 51.6 | 373.8 | 328.8 | -45.0 |
| yellow | seizure | ED | ED | 152.6 | 163.1 | 10.6 | 266.7 | 277.3 | 10.6 |

## stress: per presentation, all replications pooled (min)

| MTS | presentation | rule_mts:route | moa_load:route | rule_mts:dw | moa_load:dw | d_dw(moa_load-rule) | rule_mts:los | moa_load:los | d_los(moa_load-rule) |
|---|---|---|---|---|---|---|---|---|---|
| green | burn | UTC | UTC | 226.7 | 228.8 | 2.2 | 246.9 | 249.1 | 2.2 |
| green | chronic_pain | UTC | UTC | 218.7 | 266.6 | 47.9 | 19203.5 | 19758.7 | 555.1 |
| green | head_injury_minor | UTC | UTC | 220.5 | 214.3 | -6.2 | 240.3 | 234.2 | -6.1 |
| green | laceration | UTC | UTC | 225.2 | 259.2 | 33.9 | 245.4 | 279.4 | 34.0 |
| green | sprain | UTC | UTC | 223.8 | 243.2 | 19.4 | 244.0 | 263.5 | 19.5 |
| green | whiplash | UTC | UTC | 225.6 | 247.4 | 21.9 | 245.6 | 267.5 | 21.9 |
| orange | allergy | ED | ED | 8.1 | 10.2 | 2.1 | 182.3 | 184.4 | 2.1 |
| orange | appendicitis | ED | US_FIRST | 8.5 | 10.4 | 1.9 | 279.5 | 293.4 | 13.9 |
| orange | asthma | ED | ED | 8.2 | 10.1 | 1.9 | 286.1 | 289.7 | 3.6 |
| orange | mi | ED | ED | 7.8 | 9.5 | 1.7 | 282.3 | 287.4 | 5.1 |
| orange | overdose | ED | ED | 8.0 | 10.2 | 2.2 | 284.6 | 288.5 | 4.0 |
| orange | stroke | CT_FIRST | CT_FIRST | 8.2 | 9.8 | 1.6 | 294.1 | 297.3 | 3.3 |
| orange | tbi | ED | CT_FIRST | 7.4 | 10.4 | 3.1 | 277.5 | 292.6 | 15.2 |
| red | cardiac_arrest | ED | ED | 5.0 | 6.2 | 1.3 | 264.6 | 266.0 | 1.4 |
| red | gunshot | ED | CT_FIRST | 5.1 | 6.5 | 1.4 | 269.2 | 280.3 | 11.1 |
| yellow | fracture_ankle | XRAY_FIRST | XRAY_FIRST | 516.8 | 582.6 | 65.8 | 642.5 | 708.3 | 65.8 |
| yellow | fracture_upper_limb | XRAY_FIRST | XRAY_FIRST | 507.7 | 572.8 | 65.1 | 712.1 | 786.0 | 73.9 |
| yellow | head_injury_loc | ED | CT_FIRST | 474.0 | 536.1 | 62.1 | 1007.4 | 739.4 | -268.1 |
| yellow | heart_failure | ED | XRAY_FIRST | 473.3 | 540.8 | 67.5 | 1277.0 | 1068.4 | -208.6 |
| yellow | hip_fracture | XRAY_FIRST | XRAY_FIRST | 499.2 | 565.9 | 66.7 | 927.3 | 1028.0 | 100.6 |
| yellow | knee_injury | ED | XRAY_FIRST | 478.8 | 568.3 | 89.5 | 1007.7 | 738.8 | -268.9 |
| yellow | lung_mass | ED | XRAY_FIRST | 485.0 | 587.7 | 102.7 | 1028.2 | 712.0 | -316.2 |
| yellow | seizure | ED | ED | 477.4 | 510.0 | 32.6 | 592.8 | 625.3 | 32.6 |

