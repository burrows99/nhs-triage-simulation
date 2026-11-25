# Exploratory: case-mix-standardised group outcomes (not pre-registered)

## base: mean doctor wait by sex x ethnicity (all replications pooled)

| | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| raw gap (min) | 31.3 | 33.7 | 64.9 | 63.8 |
| standardised gap (min) | 23.0 | 23.1 | 72.6 | 76.9 |
| std F_asian | 73.9 | 71.4 | 44.3 | 43.7 |
| std F_black | 87.9 | 85.8 | 116.9 | 120.6 |
| std F_white | 86.2 | 83.4 | 80.3 | 79.2 |
| std M_asian | 88.6 | 83.8 | 67.5 | 56.1 |
| std M_black | 96.9 | 94.5 | 48.1 | 44.9 |
| std M_white | 96.2 | 93.7 | 97.8 | 95.4 |

## stress: mean doctor wait by sex x ethnicity (all replications pooled)

| | rule_mts | load_aware | moa_load | moa_static |
|---|---|---|---|---|
| raw gap (min) | 65.4 | 66.4 | 149.6 | 152.7 |
| standardised gap (min) | 42.9 | 41.6 | 203.4 | 201.7 |
| std F_asian | 171.5 | 166.6 | 102.4 | 97.7 |
| std F_black | 187.8 | 183.4 | 305.8 | 299.4 |
| std F_white | 191.3 | 185.7 | 191.8 | 189.6 |
| std M_asian | 187.4 | 180.6 | 126.8 | 118.7 |
| std M_black | 214.5 | 208.2 | 114.1 | 103.7 |
| std M_white | 211.8 | 205.3 | 225.4 | 223.5 |

## base: per presentation, all replications pooled (min)

| MTS | presentation | rule_mts:route | moa_load:route | rule_mts:dw | moa_load:dw | d_dw(moa_load-rule) | rule_mts:los | moa_load:los | d_los(moa_load-rule) |
|---|---|---|---|---|---|---|---|---|---|
| green | burn | UTC | UTC | 98.5 | 35.2 | -63.3 | 118.6 | 55.5 | -63.1 |
| green | chronic_pain | UTC | UTC | 102.1 | 39.3 | -62.8 | 676.3 | 655.1 | -21.2 |
| green | head_injury_minor | UTC | UTC | 98.2 | 37.3 | -60.8 | 118.0 | 57.5 | -60.6 |
| green | laceration | UTC | UTC | 99.4 | 42.3 | -57.1 | 119.3 | 63.7 | -55.6 |
| green | sprain | UTC | UTC | 99.9 | 52.0 | -48.0 | 119.9 | 75.0 | -44.9 |
| green | whiplash | UTC | ED | 98.7 | 360.8 | 262.0 | 118.8 | 401.2 | 282.4 |
| orange | allergy | ED | ED | 5.9 | 6.7 | 0.8 | 179.7 | 180.5 | 0.8 |
| orange | appendicitis | ED | US_FIRST | 5.9 | 35.2 | 29.3 | 242.8 | 273.4 | 30.6 |
| orange | asthma | ED | ED | 5.6 | 6.1 | 0.4 | 247.0 | 248.3 | 1.3 |
| orange | mi | ED | ED | 5.6 | 6.2 | 0.5 | 251.0 | 251.1 | 0.1 |
| orange | overdose | ED | ED | 6.0 | 6.5 | 0.5 | 244.8 | 246.7 | 1.9 |
| orange | stroke | CT_FIRST | CT_FIRST | 32.0 | 33.8 | 1.8 | 270.8 | 272.8 | 2.0 |
| orange | tbi | ED | CT_FIRST | 5.6 | 32.1 | 26.5 | 236.2 | 264.6 | 28.4 |
| red | cardiac_arrest | ED | ED | 4.0 | 4.4 | 0.4 | 254.9 | 256.2 | 1.3 |
| red | gunshot | ED | CT_FIRST | 4.0 | 29.5 | 25.5 | 261.8 | 287.8 | 26.0 |
| yellow | fracture_ankle | XRAY_FIRST | XRAY_FIRST | 139.2 | 107.6 | -31.6 | 253.8 | 224.2 | -29.6 |
| yellow | fracture_upper_limb | XRAY_FIRST | XRAY_FIRST | 139.5 | 108.3 | -31.1 | 293.3 | 269.5 | -23.8 |
| yellow | head_injury_loc | ED | CT_FIRST | 105.4 | 92.4 | -13.1 | 288.3 | 216.4 | -71.9 |
| yellow | heart_failure | ED | XRAY_FIRST | 109.6 | 91.4 | -18.2 | 424.3 | 377.2 | -47.1 |
| yellow | hip_fracture | XRAY_FIRST | CT_FIRST | 137.4 | 104.8 | -32.7 | 386.9 | 421.2 | 34.3 |
| yellow | knee_injury | ED | XRAY_FIRST | 107.1 | 105.1 | -2.0 | 293.0 | 225.8 | -67.1 |
| yellow | lung_mass | ED | XRAY_FIRST | 105.8 | 107.6 | 1.7 | 289.1 | 222.2 | -66.8 |
| yellow | seizure | ED | ED | 108.0 | 73.5 | -34.5 | 223.0 | 188.5 | -34.5 |

## stress: per presentation, all replications pooled (min)

| MTS | presentation | rule_mts:route | moa_load:route | rule_mts:dw | moa_load:dw | d_dw(moa_load-rule) | rule_mts:los | moa_load:los | d_los(moa_load-rule) |
|---|---|---|---|---|---|---|---|---|---|
| green | burn | UTC | UTC | 209.6 | 84.6 | -125.0 | 229.7 | 104.8 | -124.9 |
| green | chronic_pain | UTC | UTC | 218.9 | 89.2 | -129.7 | 5094.8 | 4613.3 | -481.4 |
| green | head_injury_minor | UTC | UTC | 214.1 | 83.7 | -130.5 | 234.2 | 103.8 | -130.4 |
| green | laceration | UTC | UTC | 214.5 | 96.4 | -118.1 | 234.6 | 117.1 | -117.5 |
| green | sprain | UTC | UTC | 218.2 | 103.4 | -114.7 | 238.0 | 124.5 | -113.5 |
| green | whiplash | UTC | ED | 213.7 | 982.1 | 768.4 | 233.7 | 1023.5 | 789.8 |
| orange | allergy | ED | ED | 7.4 | 7.6 | 0.2 | 181.1 | 181.3 | 0.2 |
| orange | appendicitis | ED | US_FIRST | 7.2 | 38.1 | 30.9 | 300.7 | 336.7 | 36.0 |
| orange | asthma | ED | ED | 6.9 | 7.0 | 0.1 | 292.8 | 296.8 | 4.0 |
| orange | mi | ED | ED | 6.6 | 7.1 | 0.5 | 304.2 | 308.1 | 3.9 |
| orange | overdose | ED | ED | 7.3 | 7.6 | 0.3 | 301.4 | 304.5 | 3.1 |
| orange | stroke | CT_FIRST | CT_FIRST | 33.5 | 35.1 | 1.6 | 324.8 | 329.6 | 4.9 |
| orange | tbi | ED | CT_FIRST | 6.7 | 34.9 | 28.1 | 293.3 | 329.8 | 36.4 |
| red | cardiac_arrest | ED | ED | 4.4 | 5.0 | 0.6 | 268.9 | 270.0 | 1.1 |
| red | gunshot | ED | CT_FIRST | 4.7 | 31.2 | 26.5 | 269.2 | 296.5 | 27.3 |
| yellow | fracture_ankle | XRAY_FIRST | XRAY_FIRST | 297.4 | 227.9 | -69.4 | 412.7 | 352.6 | -60.0 |
| yellow | fracture_upper_limb | XRAY_FIRST | XRAY_FIRST | 296.6 | 230.4 | -66.1 | 547.5 | 513.1 | -34.4 |
| yellow | head_injury_loc | ED | CT_FIRST | 257.2 | 196.7 | -60.5 | 565.6 | 343.7 | -221.9 |
| yellow | heart_failure | ED | XRAY_FIRST | 255.4 | 194.0 | -61.4 | 992.3 | 894.4 | -97.9 |
| yellow | hip_fracture | XRAY_FIRST | CT_FIRST | 296.7 | 210.9 | -85.8 | 892.4 | 1020.8 | 128.3 |
| yellow | knee_injury | ED | XRAY_FIRST | 254.8 | 219.1 | -35.8 | 564.1 | 357.4 | -206.7 |
| yellow | lung_mass | ED | XRAY_FIRST | 253.7 | 226.0 | -27.6 | 561.2 | 344.9 | -216.2 |
| yellow | seizure | ED | ED | 261.2 | 174.9 | -86.3 | 376.7 | 290.4 | -86.3 |

