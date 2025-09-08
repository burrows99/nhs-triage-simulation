#!/usr/bin/env python3
import simpy
import numpy as np
import random
from dataclasses import dataclass, field
from typing import List, Dict
from pathlib import Path
import matplotlib.pyplot as plt
import argparse

# --------------------------
# CONSTANTS
# --------------------------
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

# --------------------------
# PATIENT
# --------------------------
@dataclass
class Patient:
    """
    Represents a patient in the ED simulation.
    - pid: Unique patient ID
    - triage: Triage level (string)
    - needs_mri: Boolean indicating if MRI is needed (assumed only for red triage with 50% probability)
    - needs_ultrasound: Boolean indicating if ultrasound is needed (20% probability for all)
    - tasks: List of resources/tasks the patient needs, determined by routing agent
    - wait_times: Per-task wait times (from request to start of service); not used in global stats but available for per-patient analysis
    - start_times: Per-task start times
    - end_times: Per-task end times
    """
    pid: int
    triage: str
    needs_mri: bool = False
    needs_ultrasound: bool = False
    tasks: List[str] = field(default_factory=list)
    wait_times: Dict[str, float] = field(default_factory=dict)
    start_times: Dict[str, float] = field(default_factory=dict)
    end_times: Dict[str, float] = field(default_factory=dict)

# --------------------------
# ROUTING AGENT
# --------------------------
@dataclass
class RoutingAgent:
    """
    Agent responsible for routing patients to their initial and subsequent tasks/resources.
    - routing_factor: Probability (0-1) for multi_llm scenario to correctly route red patients needing MRI directly to MRI
    - accuracy: Probability (0-1) for single_llm scenario to correctly route red patients needing MRI directly to MRI
    Assumptions:
    - All patients always see a doctor unless specifically routed to MRI first (for critical cases).
    - Ultrasound is added if needed, after initial routing.
    - All patients end with bed assignment.
    - Rule-based is deterministic; LLM-based introduces probabilistic misrouting to simulate AI errors.
    """
    routing_factor: float = 0.7
    accuracy: float = 0.8

    def route(self, patient: Patient, scenario: str) -> List[str]:
        tasks = []
        if scenario == 'rule_based':
            # Deterministic rule-based routing: doctor first, then imaging if needed, then bed
            tasks.append('doctor')
            if patient.needs_mri:
                tasks.append('mri')
            if patient.needs_ultrasound:
                tasks.append('ultrasound')
            tasks.append('bed')
        elif scenario == 'single_llm':
            # Single LLM routing: probabilistic accuracy for critical (red + MRI) cases; may misroute to doctor instead of MRI
            if patient.triage == 'red' and patient.needs_mri and random.random() < self.accuracy:
                tasks.append('mri')
            else:
                tasks.append('doctor')
            if patient.needs_ultrasound:
                tasks.append('ultrasound')
            tasks.append('bed')
        elif scenario == 'multi_llm':
            # Multi-LLM (mixture-of-agents) routing: uses routing_factor (potentially lower than accuracy to simulate ensemble variability)
            if patient.triage == 'red' and patient.needs_mri and random.random() < self.routing_factor:
                tasks.append('mri')
            else:
                tasks.append('doctor')
            if patient.needs_ultrasound:
                tasks.append('ultrasound')
            tasks.append('bed')
        return tasks

# --------------------------
# PRIORITY RESOURCE
# --------------------------
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

# --------------------------
# ED SIMULATION
# --------------------------
@dataclass
class EDSimulation:
    """
    Main ED simulation class using SimPy for discrete-event simulation.
    Parameters:
    - duration: Simulation duration in minutes (default 480, ~8 hours)
    - arrival_rate: Patient arrival rate per hour (default 6); interarrival times ~ Exponential(60/arrival_rate)
    - num_doctors, num_mri, num_ultrasound, num_beds: Resource capacities (defaults: 3,1,1,5)
    - scenario: Routing scenario ('rule_based', 'single_llm', 'multi_llm')
    - routing_factor: For multi_llm (default 0.7)
    - llm_accuracy: For single_llm (default 0.8)
    Tracks:
    - patients: List of all patients
    - resources: Dict of PriorityResource instances
    - agent: Routing agent
    - wait_times: Dict of lists; per-resource average wait times (request to start)
    - queue_lengths: List of [time, queue_doctor, queue_mri, queue_us, queue_bed] at arrival events (approximate timeline)
    - resource_busy_time: Total service time per resource (for utilization calc)
    - patient_id: Counter for patient IDs
    - urgent_mri_total: Number of patients who are red triage and need MRI (urgent cases)
    - urgent_mri_bypassed: Number of urgent MRI patients who bypassed doctor (routed directly to MRI)
    Assumptions:
    - Patients process tasks sequentially (e.g., doctor -> MRI -> bed)
    - Wait time per resource: Time from request to grant (queue wait time)
    - Utilization: (sum of all service times) / (duration * capacity) * 100%
    - Queue lengths recorded at patient arrival times (Poisson points); not continuous but sufficient for trends
    - No parallel task processing; patient flows linearly through tasks
    - Exponential service times with given means
    - Triage distribution: weights [0.1 red, 0.15 orange, 0.25 yellow, 0.25 green, 0.25 blue]
    - Needs: MRI only for red (50% prob), Ultrasound for all (20% prob)
    """
    duration: int = 480
    arrival_rate: float = 6
    num_doctors: int = 3
    num_mri: int = 1
    num_ultrasound: int = 1
    num_beds: int = 5
    scenario: str = 'rule_based'
    routing_factor: float = 0.7
    llm_accuracy: float = 0.8

    env: simpy.Environment = field(default_factory=simpy.Environment, init=False)
    patients: List[Patient] = field(default_factory=list)
    resources: Dict[str, PriorityResource] = field(init=False)
    agent: RoutingAgent = field(init=False)
    wait_times: Dict[str, List[float]] = field(default_factory=lambda: {r: [] for r in RESOURCES})
    queue_lengths: List[List] = field(default_factory=list)
    resource_busy_time: Dict[str, float] = field(default_factory=lambda: {r: 0.0 for r in RESOURCES})
    patient_id: int = 0
    urgent_mri_total: int = 0
    urgent_mri_bypassed: int = 0

    def __post_init__(self):
        # Initialize resources with SimPy PriorityResource
        self.resources = {
            'doctor': PriorityResource(self.env, 'doctor', self.num_doctors),
            'mri': PriorityResource(self.env, 'mri', self.num_mri),
            'ultrasound': PriorityResource(self.env, 'ultrasound', self.num_ultrasound),
            'bed': PriorityResource(self.env, 'bed', self.num_beds)
        }
        # Initialize routing agent with scenario-specific factors (defaults apply)
        self.agent = RoutingAgent(self.routing_factor, self.llm_accuracy)

    def mock_llm_evaluation(self):
        """
        Mock evaluation function to reproduce LLM routing accuracy assessment.
        Simulates evaluation on synthetic patient data (using simulation patients as proxy for Synthea-like data with synthetic timestamps).
        For each urgent patient (red triage needing MRI), checks if routing was correct (bypassed doctor, i.e., tasks[0] == 'mri').
        Computes simulated accuracy as (correct routings / total urgent cases).
        Compares to the scenario's set factor (expected accuracy).
        Assumes ground truth for urgent cases is to bypass doctor and go directly to MRI.
        For rule_based, set factor is 0.0 (no bypass expected).
        This mocks real evaluation where LLM responses are queried for each patient based on timestamps/needs.
        Returns dict with simulated_accuracy, set_factor, difference, and note.
        """
        urgent_patients = [p for p in self.patients if p.triage == 'red' and p.needs_mri]
        total_urgent = len(urgent_patients)
        correct_bypasses = sum(1 for p in urgent_patients if p.tasks and p.tasks[0] == 'mri')
        simulated_accuracy = correct_bypasses / total_urgent if total_urgent > 0 else 0.0
        set_factor = SCENARIO_FACTOR[self.scenario]
        difference = abs(simulated_accuracy - set_factor)
        note = "Mock evaluation: Assessed routing accuracy for urgent MRI cases using simulation outcomes as proxy for Synthea synthetic data and LLM responses. Ground truth: bypass doctor for urgent cases."
        return {
            'simulated_accuracy': simulated_accuracy,
            'set_factor': set_factor,
            'difference': difference,
            'total_urgent': total_urgent,
            'correct_bypasses': correct_bypasses,
            'note': note
        }

    def patient_generator(self):
        # Generate patients via Poisson process until duration exceeded
        while self.env.now < self.duration:
            # Assign triage level with given weights
            triage = random.choices(TRIAGE_LEVELS, weights=TRIAGE_WEIGHTS)[0]
            # Determine needs based on assumptions
            p = Patient(
                pid=self.patient_id,
                triage=triage,
                needs_mri=(triage == 'red' and random.random() < MRI_NEED_PROB),
                needs_ultrasound=(random.random() < ULTRASOUND_NEED_PROB)
            )
            self.patient_id += 1
            # Track urgent MRI cases
            if p.triage == 'red' and p.needs_mri:
                self.urgent_mri_total += 1
            # Route to tasks using agent
            p.tasks = self.agent.route(p, self.scenario)
            # Track bypasses for urgent cases
            if p.triage == 'red' and p.needs_mri and p.tasks and p.tasks[0] == 'mri':
                self.urgent_mri_bypassed += 1
            self.patients.append(p)
            # Start patient processing process
            self.env.process(self.process_patient(p))
            # Advance time to next arrival (exponential interarrival)
            yield self.env.timeout(np.random.exponential(60 / self.arrival_rate))
            # Record queue lengths at arrival times (total waiting per resource via SimPy count)
            self.queue_lengths.append([self.env.now] + [self.resources[r].resource.count for r in RESOURCES])

    def process_patient(self, patient: Patient):
        # Process each task sequentially for the patient
        for task in patient.tasks:
            res = self.resources[task]
            # Record request time
            request_time = self.env.now
            # Request resource with priority based on triage (yields until granted)
            with res.resource.request(priority=PRIORITY[patient.triage]) as req:
                yield req
                # Service starts now
                start_time = self.env.now
                # Compute wait time for this resource
                wait_time = start_time - request_time
                # Record global wait time for stats
                self.wait_times[task].append(wait_time)
                # Sample service time (exponential)
                service_time = np.random.exponential(SERVICE_TIMES[task])
                # Accumulate busy time for utilization
                self.resource_busy_time[task] += service_time
                # Perform service
                yield self.env.timeout(service_time)
                # Service ends (release automatic via 'with')

    def run(self):
        # Run the simulation: start patient generator and advance to duration
        self.env.process(self.patient_generator())
        self.env.run(until=self.duration)

    # --------------------------
    # ANALYSIS
    # --------------------------
    def analyze(self):
        # Compute wait time statistics per resource (avg and median; 0 if no usage)
        stats = {
            r: {
                'avg': np.mean(self.wait_times[r]) if self.wait_times[r] else 0.0,
                'median': np.median(self.wait_times[r]) if self.wait_times[r] else 0.0
            }
            for r in RESOURCES
        }
        # Queue timeline array: rows = [time, q_doctor, q_mri, q_us, q_bed]
        queue_arr = np.array(self.queue_lengths)
        # Resource capacities for utilization calc
        num_map = {
            'doctor': self.num_doctors,
            'mri': self.num_mri,
            'ultrasound': self.num_ultrasound,
            'bed': self.num_beds
        }
        # Utilization: percentage busy time = (total service time) / (duration * capacity) * 100
        utilization = {r: self.resource_busy_time[r] / (self.duration * num_map[r]) * 100 for r in RESOURCES}
        # Urgent MRI tracking
        urgent_stats = {
            'total': self.urgent_mri_total,
            'bypassed': self.urgent_mri_bypassed,
            'bypass_rate': (self.urgent_mri_bypassed / self.urgent_mri_total * 100) if self.urgent_mri_total > 0 else 0.0
        }
        # Mock LLM evaluation
        mock_eval = self.mock_llm_evaluation()
        return stats, queue_arr, utilization, urgent_stats, mock_eval

# --------------------------
# PLOTTING HELPERS
# --------------------------
def plot_generic_bar(data: Dict[str, float], filepath: str, title: str, ylabel: str):
    # Bar plot for generic data (e.g., waits or util per resource)
    plt.figure(figsize=(8, 5))
    plt.bar(list(data.keys()), list(data.values()), color='skyblue')
    plt.ylabel(ylabel)
    plt.title(title)
    plt.savefig(filepath)
    plt.close()

def plot_queue_timeline(queue_arr: np.ndarray, filepath: str, title: str):
    # Line plot of total queue lengths over time per resource
    # queue_arr shape: (n_times, 1 + len(RESOURCES))
    plt.figure(figsize=(10, 5))
    for r_idx, r in enumerate(RESOURCES):
        # Extract timeline for this resource (column r_idx + 1)
        timeline = queue_arr[:, r_idx + 1]
        plt.plot(queue_arr[:, 0], timeline, label=r)
    plt.xlabel('Time (minutes)')
    plt.ylabel('Total Queue Length')
    plt.title(title)
    plt.legend()
    plt.savefig(filepath)
    plt.close()

def plot_comparison_bar(results: Dict[str, Dict[str, float]], filepath: str, title: str, ylabel: str):
    # Grouped bar plot comparing metrics across scenarios and resources
    plt.figure(figsize=(10, 6))
    bar_width = 0.25
    x = np.arange(len(RESOURCES))
    for i, sc in enumerate(results.keys()):
        vals = [results[sc][r] for r in RESOURCES]
        plt.bar(x + i * bar_width, vals, width=bar_width, label=sc)
    plt.xticks(x + bar_width, RESOURCES)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.savefig(filepath)
    plt.close()

# --------------------------
# DYNAMIC INFERENCE
# --------------------------
def generate_inferences(stats: Dict[str, Dict[str, float]], queue_arr: np.ndarray, util: Dict[str, float], urgent_stats: Dict[str, float], mock_eval: Dict):
    """
    Generate simple heuristic inferences based on thresholds.
    - Wait: Compare avg wait to 1.5x mean service time (high if longer, low if shorter)
    - Utilization: High if >90%, low if <50%
    - Queue: High if max queue length >5 (arbitrary threshold for 'high')
    - Urgent MRI: Notes on total cases and bypass rate for the scenario
    - Model Accuracy: From mock evaluation, including simulated accuracy, set factor, and difference
    Returns list of inference strings.
    """
    inf = []
    for r_idx, r in enumerate(RESOURCES):
        avg = stats[r]['avg']
        median = stats[r]['median']
        service_mean = SERVICE_TIMES[r]
        if avg > service_mean * WAIT_HIGH_FACTOR:
            inf.append(f"{r} avg wait {avg:.1f} min is high (threshold: {service_mean * WAIT_HIGH_FACTOR:.1f} min)")
        elif avg < service_mean * WAIT_LOW_FACTOR:
            inf.append(f"{r} avg wait {avg:.1f} min is low (threshold: {service_mean * WAIT_LOW_FACTOR:.1f} min)")
        # Max queue for this resource
        max_queue = np.max(queue_arr[:, r_idx + 1]) if queue_arr.shape[0] > 0 else 0
        if max_queue > MAX_QUEUE_THRESHOLD:
            inf.append(f"{r} experienced high max queue of {max_queue}")
        if util[r] > UTIL_HIGH_THRESHOLD:
            inf.append(f"{r} heavily utilized at {util[r]:.1f}%")
        elif util[r] < UTIL_LOW_THRESHOLD:
            inf.append(f"{r} underutilized at {util[r]:.1f}%")
    # Urgent MRI notes
    total = urgent_stats['total']
    bypassed = urgent_stats['bypassed']
    rate = urgent_stats['bypass_rate']
    inf.append(f"Urgent MRI cases: {total} total patients needed urgent MRI and bed")
    inf.append(f"Out of {total}, {bypassed} bypassed doctor and went directly to MRI ({rate:.1f}% bypass rate)")
    # Model accuracy from mock evaluation
    sim_acc = mock_eval['simulated_accuracy']
    set_factor = mock_eval['set_factor']
    diff = mock_eval['difference']
    total_urgent = mock_eval['total_urgent']
    correct = mock_eval['correct_bypasses']
    inf.append(f"Model accuracy (mock eval): Simulated {sim_acc:.1%} (set factor: {set_factor:.1%}), difference: {diff:.3f}")
    inf.append(f"Mock eval details: {total_urgent} urgent cases evaluated, {correct} correctly bypassed doctor")
    inf.append(mock_eval['note'])
    return inf


def generate_comparison_inferences(results_wait: Dict[str, Dict[str, float]], results_util: Dict[str, Dict[str, float]], results_urgent: Dict[str, Dict[str, float]], results_mock: Dict[str, Dict]):
    """
    Generate inferences comparing scenarios.
    - For each resource: Scenario with lowest avg wait time
    - For each resource: Scenario with highest utilization
    - Urgent MRI: Scenario with highest bypass rate for urgent cases
    - Model Accuracy: Scenario with highest simulated accuracy from mock eval; smallest difference to set factor
    Returns list of comparison strings.
    """
    scenarios = list(results_wait.keys())
    comp_inf = []
    for r in RESOURCES:
        avg_waits = [results_wait[sc][r] for sc in scenarios]
        min_wait = min(avg_waits)
        best_sc_wait = scenarios[avg_waits.index(min_wait)]
        comp_inf.append(f"{r}: lowest avg wait {min_wait:.1f} min in {best_sc_wait}")
        utils = [results_util[sc][r] for sc in scenarios]
        max_util = max(utils)
        best_sc_util = scenarios[utils.index(max_util)]
        comp_inf.append(f"{r}: highest utilization {max_util:.1f}% in {best_sc_util}")
    # Urgent MRI comparison
    bypass_rates = [results_urgent[sc]['bypass_rate'] for sc in scenarios]
    max_rate = max(bypass_rates)
    best_sc_bypass = scenarios[bypass_rates.index(max_rate)]
    comp_inf.append(f"Urgent MRI bypass: highest rate {max_rate:.1f}% in {best_sc_bypass}")
    totals = [results_urgent[sc]['total'] for sc in scenarios]
    max_total_sc = scenarios[totals.index(max(totals))]
    comp_inf.append(f"Most urgent MRI cases handled: {max(totals)} in {max_total_sc}")
    # Model accuracy comparison from mock eval
    sim_accs = [results_mock[sc]['simulated_accuracy'] for sc in scenarios]
    max_sim_acc = max(sim_accs)
    best_sc_sim = scenarios[sim_accs.index(max_sim_acc)]
    comp_inf.append(f"Model accuracy: highest simulated accuracy {max_sim_acc:.1%} in {best_sc_sim}")
    diffs = [results_mock[sc]['difference'] for sc in scenarios]
    min_diff = min(diffs)
    best_sc_diff = scenarios[diffs.index(min_diff)]
    comp_inf.append(f"Model accuracy: closest to set factor (diff {min_diff:.3f}) in {best_sc_diff}")
    return comp_inf

# --------------------------
# MAIN
# --------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ED simulation with different routing scenarios.")
    parser.add_argument("--duration", type=int, default=480, help="Simulation duration in minutes")
    parser.add_argument("--arrival_rate", type=float, default=6, help="Patient arrival rate per hour")
    parser.add_argument("--num_doctors", type=int, default=3, help="Number of doctors")
    parser.add_argument("--num_mri", type=int, default=1, help="Number of MRI machines")
    parser.add_argument("--num_ultrasound", type=int, default=1, help="Number of ultrasound machines")
    parser.add_argument("--num_beds", type=int, default=5, help="Number of beds")
    args = parser.parse_args()

    scenarios = ['rule_based', 'single_llm', 'multi_llm']
    results_wait = {}
    results_util = {}
    results_queue = {}
    results_urgent = {}
    results_mock = {}

    # Create output directories
    Path("output").mkdir(exist_ok=True)
    Path("output/comparison").mkdir(exist_ok=True)

    for sc in scenarios:
        print(f"\nRunning scenario: {sc}")
        sim = EDSimulation(
            duration=args.duration,
            arrival_rate=args.arrival_rate,
            num_doctors=args.num_doctors,
            num_mri=args.num_mri,
            num_ultrasound=args.num_ultrasound,
            num_beds=args.num_beds,
            scenario=sc
        )
        sim.run()
        stats, queue_arr, util, urgent_stats, mock_eval = sim.analyze()
        results_wait[sc] = {r: stats[r]['avg'] for r in RESOURCES}
        results_util[sc] = util
        results_queue[sc] = queue_arr
        results_urgent[sc] = urgent_stats
        results_mock[sc] = mock_eval

        # Create per-scenario output directory
        Path(f"output/{sc}").mkdir(exist_ok=True)
        # Per-scenario plots
        plot_generic_bar(results_wait[sc], f"output/{sc}/wait.png", f"{sc} Average Wait Times", "Minutes")
        plot_queue_timeline(queue_arr, f"output/{sc}/queue.png", f"{sc} Queue Timeline")
        plot_generic_bar(util, f"output/{sc}/util.png", f"{sc} Resource Utilization", "%")

        # Per-scenario inferences
        inf = generate_inferences(stats, queue_arr, util, urgent_stats, mock_eval)
        with open(f"output/{sc}/inferences.txt", "w") as f:
            f.write("\n".join(inf))
        print(f"Inferences for {sc}:")
        for i in inf:
            print("-", i)

    # Comparison plots
    plot_comparison_bar(results_wait, "output/comparison/wait_comparison.png", "Wait Time Comparison Across Scenarios", "Minutes")
    plot_comparison_bar(results_util, "output/comparison/util_comparison.png", "Utilization Comparison Across Scenarios", "%")
    # Queue timeline comparison (one line per resource-scenario)
    plt.figure(figsize=(10, 6))
    for r_idx, r in enumerate(RESOURCES):
        for sc in scenarios:
            q_arr = results_queue[sc]
            # Extract timeline for this resource (single column now)
            timeline = q_arr[:, r_idx + 1]
            plt.plot(q_arr[:, 0], timeline, label=f"{r}-{sc}")
    plt.xlabel('Time (minutes)')
    plt.ylabel('Total Queue Length')
    plt.title('Queue Timeline Comparison Across Scenarios')
    plt.legend(fontsize=8)
    plt.savefig("output/comparison/queue_comparison.png")
    plt.close()

    # Comparison inferences
    comp_inf = generate_comparison_inferences(results_wait, results_util, results_urgent, results_mock)
    with open("output/comparison/inferences.txt", "w") as f:
        f.write("\n".join(comp_inf))
    print("\nComparison inferences:")
    for i in comp_inf:
        print("-", i)