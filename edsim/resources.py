import simpy
from dataclasses import dataclass

@dataclass
class PriorityResource:
    """
    Wrapper for SimPy's PriorityResource to manage resource allocation with triage-based priorities.
    - env: SimPy environment
    - name: Resource name (for identification)
    - capacity: Number of parallel instances (e.g., number of doctors)
    Uses SimPy's built-in priority queuing: higher priority (lower number) patients are served first; within priority, FIFO.
    Queue length tracked via resource.count (total waiting patients, regardless of priority level).
    """
    env: simpy.Environment
    name: str
    capacity: int

    def __post_init__(self):
        # Initialize SimPy PriorityResource
        self.resource = simpy.PriorityResource(self.env, capacity=self.capacity)