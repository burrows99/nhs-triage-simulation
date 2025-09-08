# Emergency Department (ED) Simulation

This Python script uses SimPy for discrete-event simulation to model patient flow in an ED, comparing rule-based routing against two LLM-based routing scenarios (single LLM and multi-LLM mixture). The simulation tracks wait times, queue lengths, resource utilization, specific case handling (e.g., urgent MRI bypasses), and mock LLM evaluation for routing accuracy.

## Overview
- **Purpose**: Simulate ED operations with priority queuing based on triage levels. Patients arrive, are triaged, routed to tasks (resources), and processed sequentially. Different routing agents simulate deterministic vs. probabilistic (AI-like) decision-making.
- **Key Components**:
  - Patient generation via Poisson arrivals.
  - Routing to resources (doctor, MRI, ultrasound, bed) with triage-based priorities.
  - Custom priority resources using SimPy's `PriorityResource`.
  - Analysis of waits, queues, utilization, urgent case tracking, and mock LLM evaluation.
  - Plots and inferences for per-scenario and comparisons.
- **Scenarios**:
  - `rule_based`: Deterministic routing (always doctor first, then imaging if needed, then bed). No bypass for urgent MRI (set factor: 0.0).
  - `single_llm`: Probabilistic routing with 80% accuracy for critical cases (red triage needing MRI routed to MRI; otherwise doctor).
  - `multi_llm`: Similar but with 70% routing factor (simulates ensemble variability, potentially lower reliability).
- **Specific Case Tracking**: Monitors "urgent MRI cases" (red triage patients needing MRI and bed). Tracks total such cases and how many bypassed doctor (direct to MRI). Rule-based: 0 bypasses. LLM scenarios: probabilistic bypass.
- **Mock LLM Evaluation**: Simulates evaluation of routing accuracy using simulation patients as proxy for Synthea synthetic data. For urgent cases, computes simulated accuracy (fraction correctly bypassed) and compares to set factor. Mocks real process of querying LLM responses per patient with synthetic timestamps.
- **Output**:
  - Per-scenario: `output/{scenario}/` with wait.png, queue.png, util.png, inferences.txt (includes urgent case notes and mock eval accuracy).
  - Comparisons: `output/comparison/` with wait_comparison.png, util_comparison.png, queue_comparison.png, inferences.txt (includes cross-scenario urgent case and accuracy comparisons).

## Assumptions
- **Patient Arrival**: Poisson process with configurable rate (default 6 per hour). Interarrival times ~ Exponential(mean = 60 / rate minutes).
- **Triage Distribution**: Weighted random choice: red (10%, highest priority), orange (15%), yellow (25%), green (25%), blue (25%, lowest priority).
- **Resource Needs**:
  - MRI: Only red patients, with 50% probability (defines "urgent MRI case").
  - Ultrasound: All patients, with 20% probability.
  - All patients require bed. Doctor required unless bypassed in LLM scenarios for urgent MRI.
- **Service Times**: Exponential distribution with means (minutes): doctor=15, MRI=30, ultrasound=20, bed=60.
- **Priorities**: Mapped to integers 0 (red, highest) to 4 (blue, lowest) for SimPy `PriorityResource`. Higher priority patients served first; FIFO within priority.
- **Patient Flow**: Sequential task processing (e.g., doctor -> MRI -> bed). No parallel tasks.
- **Routing**:
  - Rule-based: Perfect, no errors, no bypass.
  - LLM-based: Introduces misrouting probability to simulate AI inaccuracies (e.g., critical patient sent to doctor instead of MRI). Bypass only for urgent MRI cases.
- **Capacities**: Configurable (defaults: 3 doctors, 1 MRI, 1 ultrasound, 5 beds).
- **Simulation Duration**: Default 480 minutes (~8 hours).
- **Queue Tracking**: Total queue length per resource (all priorities summed) recorded at patient arrival times (discrete points, not continuous).
- **Edge Cases**: If no patients use a resource, wait stats default to 0. Empty queues/plots handled gracefully. If no urgent cases, bypass rate/simulated accuracy = 0%.

## Calculations
- **Wait Time (per resource)**: Time from resource request to service start (queue wait only, excludes service time). Collected for all patients using the resource; stats are average/median.
- **Queue Length**: Total number of patients waiting (SimPy `resource.count`). Timeline plotted over simulation time at arrival events.
- **Utilization (%)**: (Total accumulated service time across all instances) / (simulation duration × capacity) × 100. Measures percentage of time resources are busy.
- **Urgent MRI Tracking**:
  - Total: Count of patients with triage=='red' and needs_mri=True.
  - Bypassed: Subset where tasks[0]=='mri' (skipped doctor).
  - Bypass Rate: (bypassed / total) × 100% if total > 0, else 0%.
- **Mock LLM Evaluation**:
  - Filters urgent patients from simulation data (proxy for Synthea patients).
  - Simulated Accuracy: (number correctly bypassed / total urgent) as fraction.
  - Set Factor: Scenario-specific expected accuracy (0.0 for rule_based, 0.8 for single_llm, 0.7 for multi_llm).
  - Difference: |simulated - set_factor|.
  - Reproduces real eval by using simulation outcomes to mimic LLM response accuracy for each patient.
- **Statistics**:
  - Average/Median Wait: `np.mean`/`np.median` of wait times list per resource.
  - Max Queue: `np.max` of queue timeline column per resource.
- **Inferences** (Heuristic, per scenario):
  - Wait: "High" if avg > 1.5 × mean service time; "low" if < 0.8 × mean service time.
  - Utilization: "Heavily utilized" if >90%; "underutilized" if <50%.
  - Queue: "High max queue" if >5 (arbitrary threshold indicating potential bottleneck).
  - Urgent MRI: Reports total cases, number bypassed, and bypass rate.
  - Model Accuracy: Simulated accuracy, set factor, difference, and eval details/note.
- **Comparison Inferences** (across scenarios):
  - For each resource: Scenario with lowest average wait time.
  - For each resource: Scenario with highest utilization.
  - Urgent MRI: Scenario with highest bypass rate; scenario with most total urgent cases handled.
  - Model Accuracy: Scenario with highest simulated accuracy; scenario with smallest difference to set factor.

## How to Run
1. Install dependencies: `pip install simpy numpy matplotlib`.
2. Run: `python script.py` (uses defaults) or e.g., `python script.py --arrival_rate 8 --num_doctors 4`.
3. Outputs saved to `output/` directory.
4. View plots and read `inferences.txt` files for insights, including urgent case notes and mock model accuracy for all scenarios.

## Known Limitations & Fixes Applied
- **Queue Timelines Always 0**: Fixed by using SimPy `PriorityResource` properly (no premature popping). Now tracks actual waiting patients via `resource.count`.
- **No Comparison Inferences**: Added `generate_comparison_inferences` and output to `output/comparison/inferences.txt`.
- **No Tracking of Specific Cases**: Added `urgent_mri_total` and `urgent_mri_bypassed` counters. Inferences now include notes on urgent MRI bypasses for each scenario and comparisons (e.g., highest bypass rate).
- **No Model Accuracy in Inferences**: Added mock evaluation function (`mock_llm_evaluation`) that computes simulated accuracy based on simulation results, compared to set factors. Integrated into per-scenario and comparison inferences.
- **Other Errors**:
  - Slicing bugs in plots: Updated to single-column per resource (no summing needed).
  - Misused wait_times: Now correctly computes and appends actual queue wait times.
  - Max queue in inferences: Now per-resource specific.
  - Busy tracking: Accumulates service times correctly for multi-instance resources.
- **Constants**: All constants (e.g., triage weights, probabilities, thresholds, scenario factors) now grouped at the top.
- **Improvements**: Added extensive comments; switched to proper SimPy priority queuing for accuracy and efficiency. Inferences cover urgent case and model accuracy for all scenarios. Mock eval reproduces evaluation logic accurately to simulation and set factors.

## Potential Extensions
- Continuous queue monitoring (e.g., via timer process every minute).
- Parallel task processing (e.g., imaging while waiting for bed).
- More realistic routing (e.g., LLM prompts simulated via external calls).
- Additional case tracking (e.g., ultrasound needs, full patient throughput times).
- Integrate actual Synthea data loading for real eval (beyond mock).
- Cost metrics or patient outcomes.
- Sensitivity analysis on parameters.

For questions, refer to code comments or contact the maintainer.