#!/usr/bin/env python3
import argparse
from pathlib import Path
from typing import Dict, Union, List

import numpy as np
from numpy.typing import NDArray

from edsim.services import EDSimulation
from edsim.constants import RESOURCES
from edsim.utils import (
    plot_generic_bar,
    plot_queue_timeline,
    plot_comparison_bar,
    plot_queue_comparison,
    generate_inferences,
    generate_comparison_inferences,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ED simulation with different routing scenarios.")
    parser.add_argument("--duration", type=int, default=5000, help="Simulation duration in minutes")
    parser.add_argument("--arrival_rate", type=float, default=25, help="Patient arrival rate per hour")
    parser.add_argument("--num_doctors", type=int, default=3, help="Number of doctors")
    parser.add_argument("--num_mri", type=int, default=1, help="Number of MRI machines")
    parser.add_argument("--num_ultrasound", type=int, default=1, help="Number of ultrasound machines")
    parser.add_argument("--num_beds", type=int, default=5, help="Number of beds")
    parser.add_argument("--single_llm_accuracy", type=float, default=0.8, 
                        help="Accuracy for single_llm scenario (0.0-1.0). Probability of correct routing decisions for urgent cases.")
    parser.add_argument("--multi_llm_accuracy", type=float, default=0.7, 
                        help="Accuracy for multi_llm scenario (0.0-1.0). Probability of correct routing decisions for urgent cases.")
    parser.add_argument("--scenarios", nargs="*", default=['rule_based', 'single_llm', 'multi_llm'], help="Scenarios to run")
    args = parser.parse_args()

    scenarios: List[str] = list(args.scenarios)
    results_wait: Dict[str, Dict[str, float]] = {}
    results_util: Dict[str, Dict[str, float]] = {}
    results_queue: Dict[str, NDArray[np.float64]] = {}
    results_urgent: Dict[str, Dict[str, float]] = {}
    results_mock: Dict[str, Dict[str, Union[float, int, str]]] = {}

    Path("output").mkdir(exist_ok=True)
    Path("output/comparison").mkdir(exist_ok=True)

    for sc in scenarios:
        print(f"\nRunning scenario: {sc}")
        sim = EDSimulation(
            scenario=sc,
            duration=args.duration,
            arrival_rate=args.arrival_rate,
            num_doctors=args.num_doctors,
            num_mri=args.num_mri,
            num_ultrasound=args.num_ultrasound,
            num_beds=args.num_beds,
            single_llm_accuracy=args.single_llm_accuracy,
            multi_llm_accuracy=args.multi_llm_accuracy
        )
        sim.run()
        stats, queue_arr, util, urgent_stats, mock_eval = sim.analyze()
        results_wait[sc] = {r: stats[r]['avg'] for r in RESOURCES}
        results_util[sc] = util
        results_queue[sc] = queue_arr
        results_urgent[sc] = urgent_stats
        results_mock[sc] = mock_eval

        Path(f"output/{sc}").mkdir(exist_ok=True)
        plot_generic_bar(results_wait[sc], f"output/{sc}/wait.png", f"{sc} Average Wait Times", "Minutes")
        plot_queue_timeline(queue_arr, f"output/{sc}/queue.png", f"{sc} Queue Timeline")
        plot_generic_bar(util, f"output/{sc}/util.png", f"{sc} Resource Utilization", "%")

        inf = generate_inferences(stats, queue_arr, util, urgent_stats, mock_eval)
        with open(f"output/{sc}/inferences.txt", "w") as f:
            f.write("\n".join(inf))
        print(f"Inferences for {sc}:")
        for i in inf:
            print("-", i)

    plot_comparison_bar(results_wait, "output/comparison/wait_comparison.png", "Wait Time Comparison Across Scenarios", "Minutes")
    plot_comparison_bar(results_util, "output/comparison/util_comparison.png", "Utilization Comparison Across Scenarios", "%")
    plot_queue_comparison(results_queue, scenarios, "output/comparison/queue_comparison.png")

    comp_inf = generate_comparison_inferences(results_wait, results_util, results_urgent, results_mock)
    with open("output/comparison/inferences.txt", "w") as f:
        f.write("\n".join(comp_inf))
    print("\nComparison inferences:")
    for i in comp_inf:
        print("-", i)


if __name__ == "__main__":
    main()