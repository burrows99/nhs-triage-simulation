from typing import List
import itertools

# Global constants
TRIAGE_PRIORITIES: List[str] = ["Red", "Orange", "Yellow", "Green", "Blue"]
STEP_COUNTER = itertools.count(1)
SNAPSHOT_COUNTER = itertools.count(1)

def priority_rank(priority: str) -> int:
    """Return the rank of a triage priority (lower number = higher priority)."""
    return TRIAGE_PRIORITIES.index(priority)