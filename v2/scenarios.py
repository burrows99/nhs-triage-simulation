"""Scenario inputs. Published figures are marked [P] with their source; assumptions are [A].

[P] Type 1 attendances in England 2024-25: 17,351,235 (NHS England Digital, Hospital A&E Activity
    2024-25, MSitAE Table 2, https://files.digital.nhs.uk/3A/55A989/AE2425_ECDS_MSitAE_Tables.xlsx).
[P] Type 1 EDs in England: 178 (RCEM, England's Emergency Medicine Workforce Census 2024,
    https://rcem.ac.uk/wp-content/uploads/2025/10/England-Workforce-Census.pdf).
    -> 17,351,235 / 178 / 365 = 267 arrivals per department per day = 11.1 per hour (our arithmetic).
[P] Arrivals by hour of day, weekday mean, 2024-25, all department types (ECDS National Data
    Tables, sheet "Time of day distribution",
    https://files.digital.nhs.uk/C4/82ACBB/AE2425_ECDS_National_Data_Tables.xlsx).
[P] 27.9% of Type 1 attendances admitted (NHS England Statistical Commentary, March 2025,
    https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2025/04/Statistical-commentary-March-2025-Ob6L82f.pdf).
[P] Validation targets (all types, Oct 2025, NHS England Digital Provisional A&E Quality
    Indicators): median time to treatment 63 min; median total time in A&E 166 min.
[A] Service times (lognormal mean, sd in minutes) and capacities below are assumptions; capacities
    were chosen on development seeds so that the base scenario is stable over the day and its
    median time to first doctor and median length of stay are near the validation targets.
"""

from .sim import Config

HOURLY_SHARE = (
    2.23,
    1.43,
    1.08,
    0.99,
    0.97,
    1.04,
    1.01,
    1.81,
    4.92,
    6.62,
    7.22,
    7.45,
    7.14,
    6.73,
    6.47,
    6.32,
    6.40,
    6.22,
    5.76,
    5.00,
    4.35,
    3.59,
    2.91,
    2.33,
)
PROFILE = tuple(24 * s / sum(HOURLY_SHARE) for s in HOURLY_SHARE)  # multipliers, mean 1

LAMBDA_BASE = 17_351_235 / 178 / 365 / 24  # 11.1 per hour
STRESS_FACTOR = 1.2  # [A] +20% arrivals with the same staff

SERVICE = {  # [A]
    "assess": (25, 12),  # ED doctor initial assessment
    "review": (10, 5),  # ED/UTC doctor review of imaging results
    "utc": (20, 10),  # UTC doctor consultation
    "xray": (12, 5),
    "ct": (20, 8),
    "us": (25, 10),
    "specialist": (40, 20),  # specialty team review before admission
    "bed": (720, 480),  # assessment-unit bed held for the first 12 h of the admission
    "treat": {  # treatment / observation / results, parallel to imaging, not a modelled resource
        "red": (180, 90),
        "orange": (150, 75),
        "yellow": (90, 45),
        "green": (20, 15),
        "blue": (15, 10),
    },
}

CAPACITY = {  # [A] chosen on development seeds (development seeds; warm-up check: `python -m v2.run welch`)
    "ed_doctor": 4,
    "utc_doctor": 2,
    "xray": 1,
    "ct": 1,
    "us": 1,
    "specialist": 3,
    "bed": 45,
}


def scenario(name):
    lam = LAMBDA_BASE * (STRESS_FACTOR if name == "stress" else 1.0)
    return Config(
        arrivals_per_hour=lam,
        hourly_profile=PROFILE,
        admit_share=0.279,
        capacity=dict(CAPACITY),
        service=SERVICE,
    )
