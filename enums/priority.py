from __future__ import annotations
from enum import IntEnum

class Priority(IntEnum):
    IMMEDIATE = 1  # Red – see immediately per MTS five-tier system <mcreference link="https://pmc.ncbi.nlm.nih.gov/articles/PMC5289484/" index="1">1</mcreference>
    VERY_URGENT = 2  # Orange – within ~10 minutes <mcreference link="https://codimg.com/healthcare/blog/en/manchester-triage-system" index="5">5</mcreference>
    URGENT = 3  # Yellow – within ~60 minutes <mcreference link="https://codimg.com/healthcare/blog/en/manchester-triage-system" index="5">5</mcreference>
    STANDARD = 4  # Green – within ~2 hours <mcreference link="https://codimg.com/healthcare/blog/en/manchester-triage-system" index="5">5</mcreference>
    NON_URGENT = 5  # Blue – up to ~4 hours <mcreference link="https://codimg.com/healthcare/blog/en/manchester-triage-system" index="5">5</mcreference>