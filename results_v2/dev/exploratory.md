# Exploratory: case-mix-standardised group outcomes (not pre-registered)

## base: mean doctor wait by sex x ethnicity (all replications pooled)

| | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| raw gap (min) | 31.1 | 32.7 | 65.6 | 66.5 |
| standardised gap (min) | 19.4 | 18.4 | 73.2 | 79.7 |
| std F_asian | 77.9 | 75.2 | 46.1 | 44.0 |
| std F_black | 83.0 | 83.0 | 119.2 | 121.2 |
| std F_white | 87.4 | 84.9 | 83.4 | 81.8 |
| std M_asian | 88.2 | 83.8 | 62.8 | 53.4 |
| std M_black | 94.9 | 93.2 | 46.1 | 41.4 |
| std M_white | 97.3 | 93.6 | 97.9 | 96.7 |

## stress: mean doctor wait by sex x ethnicity (all replications pooled)

| | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| raw gap (min) | 83.0 | 80.8 | 162.0 | 163.8 |
| standardised gap (min) | 48.2 | 44.8 | 192.1 | 201.3 |
| std F_asian | 175.2 | 173.9 | 108.1 | 102.0 |
| std F_black | 191.6 | 189.8 | 300.2 | 303.3 |
| std F_white | 196.7 | 194.0 | 206.7 | 198.2 |
| std M_asian | 198.6 | 200.8 | 139.5 | 128.5 |
| std M_black | 223.3 | 218.7 | 124.4 | 109.9 |
| std M_white | 215.5 | 212.3 | 235.9 | 231.8 |

## base: per presentation, all replications pooled (min)

| MTS | presentation | rule_mts:route | moa_load:route | rule_mts:dw | moa_load:dw | d_dw(moa_load-rule) | rule_mts:los | moa_load:los | d_los(moa_load-rule) |
|---|---|---|---|---|---|---|---|---|---|
| green | burn | UTC | UTC | 101.0 | 33.8 | -67.2 | 120.5 | 53.5 | -67.1 |
| green | chronic_pain | UTC | UTC | 98.0 | 34.0 | -64.0 | 672.4 | 643.1 | -29.3 |
| green | head_injury_minor | UTC | UTC | 99.5 | 32.0 | -67.5 | 119.4 | 52.0 | -67.4 |
| green | laceration | UTC | UTC | 98.4 | 41.1 | -57.3 | 118.3 | 62.3 | -56.0 |
| green | sprain | UTC | UTC | 98.7 | 48.4 | -50.2 | 118.7 | 71.6 | -47.2 |
| green | whiplash | UTC | ED | 97.0 | 366.8 | 269.8 | 117.1 | 405.6 | 288.5 |
| orange | allergy | ED | ED | 6.1 | 6.4 | 0.3 | 182.5 | 182.8 | 0.3 |
| orange | appendicitis | ED | US_FIRST | 6.0 | 37.1 | 31.1 | 245.0 | 277.4 | 32.4 |
| orange | asthma | ED | ED | 6.0 | 6.7 | 0.7 | 241.5 | 244.3 | 2.8 |
| orange | mi | ED | ED | 6.1 | 5.8 | -0.3 | 236.0 | 236.9 | 0.9 |
| orange | overdose | ED | ED | 6.0 | 6.3 | 0.3 | 243.4 | 245.1 | 1.7 |
| orange | stroke | CT_FIRST | CT_FIRST | 32.3 | 33.2 | 0.9 | 269.6 | 272.9 | 3.4 |
| orange | tbi | ED | CT_FIRST | 6.0 | 32.7 | 26.8 | 238.3 | 267.1 | 28.8 |
| red | cardiac_arrest | ED | ED | 3.8 | 4.5 | 0.7 | 252.5 | 254.2 | 1.7 |
| red | gunshot | ED | CT_FIRST | 4.0 | 29.8 | 25.8 | 255.3 | 281.6 | 26.4 |
| yellow | fracture_ankle | XRAY_FIRST | XRAY_FIRST | 149.1 | 114.1 | -35.1 | 266.7 | 234.3 | -32.3 |
| yellow | fracture_upper_limb | XRAY_FIRST | XRAY_FIRST | 140.0 | 108.1 | -31.9 | 294.4 | 271.0 | -23.4 |
| yellow | head_injury_loc | ED | CT_FIRST | 111.7 | 96.2 | -15.5 | 300.8 | 222.9 | -77.8 |
| yellow | heart_failure | ED | XRAY_FIRST | 111.5 | 91.2 | -20.3 | 422.6 | 374.1 | -48.5 |
| yellow | hip_fracture | XRAY_FIRST | CT_FIRST | 142.8 | 106.7 | -36.0 | 384.4 | 439.7 | 55.2 |
| yellow | knee_injury | ED | XRAY_FIRST | 107.7 | 103.0 | -4.8 | 294.0 | 223.2 | -70.8 |
| yellow | lung_mass | ED | XRAY_FIRST | 111.8 | 109.6 | -2.2 | 300.2 | 225.6 | -74.6 |
| yellow | seizure | ED | ED | 111.4 | 75.1 | -36.4 | 226.7 | 190.4 | -36.4 |

## stress: per presentation, all replications pooled (min)

| MTS | presentation | rule_mts:route | moa_load:route | rule_mts:dw | moa_load:dw | d_dw(moa_load-rule) | rule_mts:los | moa_load:los | d_los(moa_load-rule) |
|---|---|---|---|---|---|---|---|---|---|
| green | burn | UTC | UTC | 205.1 | 87.5 | -117.6 | 224.9 | 107.4 | -117.5 |
| green | chronic_pain | UTC | UTC | 212.9 | 93.4 | -119.5 | 5491.0 | 5144.0 | -347.0 |
| green | head_injury_minor | UTC | UTC | 215.7 | 91.4 | -124.3 | 235.8 | 111.5 | -124.3 |
| green | laceration | UTC | UTC | 214.0 | 98.4 | -115.6 | 234.0 | 118.9 | -115.1 |
| green | sprain | UTC | UTC | 212.2 | 102.6 | -109.6 | 232.3 | 123.6 | -108.7 |
| green | whiplash | UTC | ED | 210.2 | 1011.2 | 801.0 | 230.0 | 1052.8 | 822.8 |
| orange | allergy | ED | ED | 8.6 | 8.1 | -0.5 | 183.1 | 182.6 | -0.5 |
| orange | appendicitis | ED | US_FIRST | 7.6 | 39.3 | 31.7 | 304.7 | 343.7 | 39.0 |
| orange | asthma | ED | ED | 7.7 | 7.8 | 0.1 | 297.8 | 303.1 | 5.3 |
| orange | mi | ED | ED | 7.3 | 8.0 | 0.7 | 300.7 | 305.9 | 5.2 |
| orange | overdose | ED | ED | 8.0 | 7.7 | -0.2 | 305.8 | 310.7 | 5.0 |
| orange | stroke | CT_FIRST | CT_FIRST | 34.2 | 35.8 | 1.6 | 332.6 | 336.9 | 4.3 |
| orange | tbi | ED | CT_FIRST | 8.0 | 33.9 | 25.9 | 305.3 | 339.8 | 34.4 |
| red | cardiac_arrest | ED | ED | 4.8 | 5.2 | 0.4 | 266.9 | 268.9 | 2.1 |
| red | gunshot | ED | CT_FIRST | 4.4 | 30.9 | 26.6 | 271.3 | 299.2 | 27.9 |
| yellow | fracture_ankle | XRAY_FIRST | XRAY_FIRST | 310.3 | 242.9 | -67.4 | 423.9 | 370.9 | -52.9 |
| yellow | fracture_upper_limb | XRAY_FIRST | XRAY_FIRST | 321.1 | 255.4 | -65.7 | 601.6 | 570.0 | -31.6 |
| yellow | head_injury_loc | ED | CT_FIRST | 274.6 | 211.8 | -62.8 | 599.1 | 365.9 | -233.1 |
| yellow | heart_failure | ED | XRAY_FIRST | 273.9 | 212.1 | -61.8 | 1113.6 | 997.2 | -116.4 |
| yellow | hip_fracture | XRAY_FIRST | CT_FIRST | 322.5 | 238.3 | -84.2 | 909.3 | 1032.1 | 122.9 |
| yellow | knee_injury | ED | XRAY_FIRST | 276.9 | 241.0 | -35.9 | 608.6 | 382.3 | -226.3 |
| yellow | lung_mass | ED | XRAY_FIRST | 279.2 | 259.9 | -19.3 | 607.3 | 376.4 | -230.9 |
| yellow | seizure | ED | ED | 272.8 | 187.5 | -85.3 | 387.6 | 302.3 | -85.3 |

