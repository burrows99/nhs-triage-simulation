# Constants used across the ED simulation
# Triage levels from highest priority (red) to lowest (blue)
TRIAGE_LEVELS = ['red', 'orange', 'yellow', 'green', 'blue']
# Resources available in the Emergency Department (ED)
RESOURCES = ['doctor', 'mri', 'ultrasound', 'bed']
# Mean service times in minutes for each resource; service times follow an exponential distribution
SERVICE_TIMES = {'doctor': 15, 'mri': 30, 'ultrasound': 20, 'bed': 60}
# Priority mapping for SimPy PriorityResource: lower number = higher priority
PRIORITY = {'red': 0, 'orange': 1, 'yellow': 2, 'green': 3, 'blue': 4}
# Triage weights for random choice: [red, orange, yellow, green, blue]
TRIAGE_WEIGHTS = [0.1, 0.15, 0.25, 0.25, 0.25]
# Probability a red patient needs MRI (urgent case)
MRI_NEED_PROB = 0.5
# Probability any patient needs ultrasound
ULTRASOUND_NEED_PROB = 0.2
# Inference thresholds
WAIT_HIGH_FACTOR = 1.5
WAIT_LOW_FACTOR = 0.8
UTIL_HIGH_THRESHOLD = 90
UTIL_LOW_THRESHOLD = 50
MAX_QUEUE_THRESHOLD = 5
# Scenario-specific factors for mock evaluation (bypass accuracy for urgent MRI)
SCENARIO_FACTOR = {'rule_based': 0.0, 'single_llm': 0.8, 'multi_llm': 0.7}