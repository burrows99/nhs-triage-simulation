"""python test_reproduce.py -- the traced simulator must reproduce the original byte-for-byte."""

import random

import numpy as np

from edsim.services import EDSimulation
from reproduce import CAPACITY, TracedSim, holm


def test_traced_sim_matches_original():
    cfg = dict(
        duration=3000,
        arrival_rate=12,
        single_llm_accuracy=0.8,
        multi_llm_accuracy=0.7,
        **CAPACITY,
    )
    for arm in ("rule_based", "multi_llm"):
        out = []
        for cls in (EDSimulation, TracedSim):
            random.seed(7)
            np.random.seed(7)
            sim = cls(scenario=arm, **cfg)
            sim.run()
            out.append(
                (
                    sim.wait_times,
                    sim.resource_busy_time,
                    [p.tasks for p in sim.patients],
                )
            )
        assert out[0] == out[1], arm


def test_holm():
    assert holm([0.01, 0.04, 0.03]) == [0.03, 0.06, 0.06]


if __name__ == "__main__":
    test_traced_sim_matches_original()
    test_holm()
    print("ok")
