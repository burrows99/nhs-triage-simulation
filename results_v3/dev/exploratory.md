# Exploratory: case-mix-standardised group outcomes (not pre-registered)

## base: mean doctor wait by sex x ethnicity (all replications pooled)

| | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| raw gap (min) | 40.0 | 42.8 | 55.4 | 59.8 |
| standardised gap (min) | 18.4 | 19.2 | 25.6 | 27.8 |
| std F_asian | 93.0 | 91.1 | 97.2 | 96.2 |
| std F_black | 100.2 | 102.0 | 105.7 | 116.7 |
| std F_white | 99.7 | 100.0 | 107.4 | 105.6 |
| std M_asian | 103.9 | 104.1 | 113.8 | 109.7 |
| std M_black | 108.7 | 109.6 | 109.5 | 100.1 |
| std M_white | 111.4 | 110.2 | 122.7 | 124.0 |

## stress: mean doctor wait by sex x ethnicity (all replications pooled)

| | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| raw gap (min) | 145.1 | 148.1 | 184.5 | 187.9 |
| standardised gap (min) | 47.6 | 52.3 | 69.9 | 65.6 |
| std F_asian | 274.2 | 280.0 | 292.3 | 293.0 |
| std F_black | 313.3 | 312.7 | 349.5 | 335.8 |
| std F_white | 282.9 | 294.3 | 316.7 | 306.0 |
| std M_asian | 304.2 | 302.4 | 357.9 | 338.6 |
| std M_black | 321.8 | 332.3 | 346.4 | 326.7 |
| std M_white | 316.1 | 327.6 | 362.2 | 358.5 |

## base: per presentation, all replications pooled (min)

| MTS | presentation | rule_mts:route | moa_load:route | rule_mts:dw | moa_load:dw | d_dw(moa_load-rule) | rule_mts:los | moa_load:los | d_los(moa_load-rule) |
|---|---|---|---|---|---|---|---|---|---|
| green | burn | UTC | UTC | 101.0 | 91.7 | -9.3 | 120.5 | 111.8 | -8.7 |
| green | chronic_pain | UTC | UTC | 98.0 | 101.3 | 3.3 | 766.6 | 807.2 | 40.7 |
| green | head_injury_minor | UTC | UTC | 99.5 | 86.8 | -12.7 | 119.4 | 107.3 | -12.2 |
| green | laceration | UTC | UTC | 98.4 | 98.1 | -0.3 | 118.3 | 119.0 | 0.7 |
| green | sprain | UTC | UTC | 98.7 | 93.9 | -4.8 | 118.7 | 114.8 | -3.9 |
| green | whiplash | UTC | UTC | 97.0 | 100.3 | 3.3 | 117.1 | 121.6 | 4.4 |
| orange | allergy | ED | ED | 6.9 | 8.4 | 1.5 | 183.3 | 184.7 | 1.5 |
| orange | appendicitis | ED | US_FIRST | 7.4 | 8.6 | 1.3 | 244.7 | 256.8 | 12.1 |
| orange | asthma | ED | ED | 6.8 | 8.4 | 1.6 | 241.8 | 243.4 | 1.7 |
| orange | mi | ED | ED | 6.8 | 8.8 | 1.9 | 234.0 | 237.3 | 3.3 |
| orange | overdose | ED | ED | 6.8 | 8.4 | 1.6 | 243.3 | 245.4 | 2.1 |
| orange | stroke | CT_FIRST | CT_FIRST | 6.8 | 9.1 | 2.2 | 246.2 | 249.6 | 3.4 |
| orange | tbi | ED | CT_FIRST | 6.3 | 7.5 | 1.2 | 240.1 | 249.5 | 9.4 |
| red | cardiac_arrest | ED | ED | 4.6 | 5.5 | 0.9 | 252.5 | 253.6 | 1.1 |
| red | gunshot | ED | CT_FIRST | 4.3 | 5.6 | 1.3 | 254.7 | 266.3 | 11.6 |
| yellow | fracture_ankle | XRAY_FIRST | XRAY_FIRST | 190.5 | 214.1 | 23.6 | 318.0 | 341.6 | 23.6 |
| yellow | fracture_upper_limb | XRAY_FIRST | XRAY_FIRST | 179.7 | 201.2 | 21.4 | 337.8 | 359.6 | 21.7 |
| yellow | head_injury_loc | ED | CT_FIRST | 152.3 | 189.0 | 36.7 | 374.0 | 332.5 | -41.5 |
| yellow | heart_failure | ED | XRAY_FIRST | 151.0 | 187.0 | 36.0 | 473.1 | 449.9 | -23.1 |
| yellow | hip_fracture | XRAY_FIRST | XRAY_FIRST | 183.5 | 206.0 | 22.4 | 420.9 | 443.2 | 22.3 |
| yellow | knee_injury | ED | XRAY_FIRST | 148.5 | 194.5 | 46.0 | 365.7 | 328.5 | -37.1 |
| yellow | lung_mass | ED | XRAY_FIRST | 153.0 | 204.9 | 51.9 | 373.6 | 331.3 | -42.4 |
| yellow | seizure | ED | ED | 151.1 | 160.8 | 9.7 | 266.4 | 276.1 | 9.7 |

## stress: per presentation, all replications pooled (min)

| MTS | presentation | rule_mts:route | moa_load:route | rule_mts:dw | moa_load:dw | d_dw(moa_load-rule) | rule_mts:los | moa_load:los | d_los(moa_load-rule) |
|---|---|---|---|---|---|---|---|---|---|
| green | burn | UTC | UTC | 205.1 | 202.6 | -2.5 | 224.9 | 222.5 | -2.5 |
| green | chronic_pain | UTC | UTC | 212.9 | 256.6 | 43.7 | 19104.9 | 20039.1 | 934.2 |
| green | head_injury_minor | UTC | UTC | 215.7 | 214.0 | -1.7 | 235.8 | 234.1 | -1.7 |
| green | laceration | UTC | UTC | 214.0 | 249.6 | 35.6 | 234.0 | 269.7 | 35.7 |
| green | sprain | UTC | UTC | 212.2 | 247.9 | 35.7 | 232.3 | 268.1 | 35.8 |
| green | whiplash | UTC | UTC | 210.2 | 249.1 | 38.9 | 230.0 | 269.0 | 39.0 |
| orange | allergy | ED | ED | 8.6 | 11.4 | 2.8 | 183.1 | 185.8 | 2.8 |
| orange | appendicitis | ED | US_FIRST | 8.4 | 10.0 | 1.6 | 294.4 | 305.0 | 10.6 |
| orange | asthma | ED | ED | 8.4 | 10.4 | 2.0 | 286.4 | 287.8 | 1.4 |
| orange | mi | ED | ED | 7.7 | 10.0 | 2.3 | 285.8 | 291.0 | 5.2 |
| orange | overdose | ED | ED | 8.4 | 10.4 | 2.0 | 293.8 | 295.5 | 1.7 |
| orange | stroke | CT_FIRST | CT_FIRST | 8.0 | 9.6 | 1.6 | 294.7 | 297.0 | 2.3 |
| orange | tbi | ED | CT_FIRST | 8.5 | 10.3 | 1.8 | 292.1 | 300.4 | 8.3 |
| red | cardiac_arrest | ED | ED | 4.7 | 6.0 | 1.3 | 265.2 | 266.7 | 1.5 |
| red | gunshot | ED | CT_FIRST | 4.6 | 5.8 | 1.2 | 267.7 | 279.4 | 11.7 |
| yellow | fracture_ankle | XRAY_FIRST | XRAY_FIRST | 576.7 | 645.2 | 68.5 | 700.3 | 768.8 | 68.5 |
| yellow | fracture_upper_limb | XRAY_FIRST | XRAY_FIRST | 592.9 | 666.9 | 74.0 | 823.2 | 904.8 | 81.6 |
| yellow | head_injury_loc | ED | CT_FIRST | 546.7 | 608.8 | 62.1 | 1172.7 | 831.8 | -340.9 |
| yellow | heart_failure | ED | XRAY_FIRST | 549.8 | 606.4 | 56.6 | 1540.8 | 1269.7 | -271.1 |
| yellow | hip_fracture | XRAY_FIRST | XRAY_FIRST | 568.1 | 642.6 | 74.4 | 1003.0 | 1119.5 | 116.5 |
| yellow | knee_injury | ED | XRAY_FIRST | 554.7 | 648.5 | 93.9 | 1189.7 | 852.9 | -336.8 |
| yellow | lung_mass | ED | XRAY_FIRST | 557.7 | 670.7 | 113.0 | 1186.3 | 795.6 | -390.7 |
| yellow | seizure | ED | ED | 548.3 | 579.6 | 31.3 | 663.1 | 694.4 | 31.3 |

