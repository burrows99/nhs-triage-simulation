#!/usr/bin/env python3
"""Reproducibility harness for the dissertation simulator.

`edsim/` and `run_simulation.py` are restored verbatim from commit 37d31df (2025-09-08, the
last commit before the dissertation PDF was produced on 2025-09-09). This script does not change
the model; it only (a) seeds it, (b) runs every arm N times with the same seeds, (c) recomputes
the metrics with a warm-up cut, clipping to the horizon and a count of patients still waiting,
and (d) reports 95% t-intervals and paired differences. See AUDIT.md / RESULTS.md.

  python reproduce.py sim --config dissertation --reps 30
  python reproduce.py sim --config code --reps 30
  python reproduce.py llm-table --model qwen2.5:7b          # needs a local Ollama
  python reproduce.py sim --config dissertation --reps 30 --llm-table results/llm/table_qwen2.5-7b.json
  python reproduce.py llm-cases --model qwen2.5:7b
"""

import argparse
import csv
import json
import math
import random
from pathlib import Path

import numpy as np
from scipy import stats

from edsim.constants import PRIORITY, RESOURCES, SERVICE_TIMES
from edsim.services import EDSimulation

CONFIGS = {
    # run_simulation.py defaults at 37d31df: what produced the committed output/comparison/inferences.txt
    "code": dict(duration=5000, arrival_rate=25),
    # dissertation 3.1 / Appendix A-1: lambda = 12/h, 30 days. Capacities are not stated in the
    # dissertation, so the code defaults (3 doctors, 1 MRI, 1 ultrasound, 5 beds) are kept.
    "dissertation": dict(duration=30 * 1440, arrival_rate=12),
}
CAPACITY = dict(num_doctors=3, num_mri=1, num_ultrasound=1, num_beds=5)
CODE_ARMS = [
    "rule_based",
    "single_llm",
    "multi_llm",
]  # single/multi_llm = coin flips (p=0.8 / 0.7), no LLM
GROUPS = [(g, e) for g in ("male", "female") for e in ("White", "Black", "Asian")]
RESULTS = Path("results")


class TracedSim(EDSimulation):
    """The original EDSimulation plus a per-task trace. Same random draws, in the same order."""

    def __post_init__(self):
        super().__post_init__()
        self.trace = []  # [patient_arrival, task, request_time, start_time | None, service_time | None]

    def process_patient(self, patient):
        arrival = self.env.now
        for task in patient.tasks:
            res = self.resources[task]
            rec = [arrival, task, self.env.now, None, None]
            self.trace.append(rec)
            with res.resource.request(priority=PRIORITY[patient.triage]) as req:
                yield req
                rec[3] = self.env.now
                self.wait_times[task].append(float(rec[3] - rec[2]))
                service_time = float(np.random.exponential(SERVICE_TIMES[task]))
                rec[4] = service_time
                self.resource_busy_time[task] += service_time
                yield self.env.timeout(service_time)


def needed(p):
    """Every service the patient needs, physician first (the rule_based pathway)."""
    return ["doctor"] + (["mri"] if p.needs_mri else []) + (["ultrasound"] if p.needs_ultrasound else []) + ["bed"]


def table_router(table, seed):
    """Route from an LLM decision table keyed by the only facts a simulated patient has."""
    demo = random.Random(seed)  # own stream: does not disturb the simulator's random / np.random draws

    def route(p, _scenario):
        p.group = demo.choice(GROUPS)
        first = table[case_key(p.triage, p.needs_mri, p.needs_ultrasound, p.group)]
        if first == "doctor":
            return needed(p)
        # same semantics as the original bypass arms: the imaging task replaces the doctor visit
        return [first] + [t for t in needed(p) if t not in (first, "doctor")]

    return route


def fixed(route):
    """--fix-routing: nobody loses a service they need; a bypass only moves the imaging first.

    The original arms (edsim/agents.py) drop the doctor visit of every bypassed patient AND drop the
    MRI of every red+MRI patient who is not bypassed."""
    def wrapped(p, sc):
        first = route(p, sc)[0]  # still consumes the original arm's random draw
        rest = needed(p)
        return rest if first == "doctor" else [first] + [t for t in rest if t != first]

    return wrapped


def case_key(triage, needs_mri, needs_us, group):
    return f"{triage}|mri={int(needs_mri)}|us={int(needs_us)}|{group[0]}|{group[1]}"


def run_one(arm, seed, cfg, warmup, table=None, fix_routing=False):
    random.seed(seed)
    np.random.seed(seed)
    sim = TracedSim(
        scenario=arm if arm in CODE_ARMS else "rule_based",
        single_llm_accuracy=0.8,
        multi_llm_accuracy=0.7,
        **cfg,
    )
    if table is not None:
        sim.agent.route = table_router(table, seed)
    if fix_routing:
        sim.agent.route = fixed(sim.agent.route)
    sim.run()
    return summarize(sim, warmup)


def summarize(sim, warmup):
    T = sim.duration
    cap = {
        "doctor": sim.num_doctors,
        "mri": sim.num_mri,
        "ultrasound": sim.num_ultrasound,
        "bed": sim.num_beds,
    }
    wait_stats, _, util_as_coded, urgent, _ = sim.analyze()  # the original metric code
    row = {}
    for r in RESOURCES:
        recs = [x for x in sim.trace if x[1] == r and x[0] >= warmup]
        served = [x[3] - x[2] for x in recs if x[3] is not None]
        busy = sum(
            max(0.0, min(x[3] + x[4], T) - max(x[3], warmup))
            for x in sim.trace
            if x[1] == r and x[3] is not None
        )
        row[f"{r}_wait_ascoded"] = wait_stats[r]["avg"]
        row[f"{r}_util_ascoded"] = util_as_coded[r]
        row[f"{r}_wait"] = float(np.mean(served)) if served else math.nan
        row[f"{r}_still_waiting"] = (
            sum(x[3] is None for x in recs) / len(recs) if recs else 0.0
        )
        row[f"{r}_util"] = 100.0 * busy / (cap[r] * (T - warmup))
    row["mean_util_ascoded"] = float(
        np.mean([row[f"{r}_util_ascoded"] for r in RESOURCES])
    )
    row["mean_util"] = float(np.mean([row[f"{r}_util"] for r in RESOURCES]))
    row["patients"] = len(sim.patients)
    row["never_see_doctor"] = float(
        np.mean(["doctor" not in p.tasks for p in sim.patients])
    )
    row["urgent_mri_bypass_rate"] = urgent["bypass_rate"]
    return row


def mean_ci(x):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    if len(x) < 2:
        return (float(x.mean()) if len(x) else math.nan), math.nan
    return float(x.mean()), float(
        stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / math.sqrt(len(x))
    )


def holm(pvals):
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    adj, running = [0.0] * len(pvals), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(pvals) - rank) * pvals[i]))
        adj[i] = running
    return adj


METRICS = ["doctor_wait", "mri_wait", "ultrasound_wait", "bed_wait", "mean_util"]


def report(rows, arms, title):
    by = {a: [r for r in rows if r["arm"] == a] for a in arms}
    out = [
        f"## {title}",
        "",
        f"N = {len(by[arms[0]])} replications per arm, same seeds across arms; "
        "mean +/- 95% t half-width across replications.",
        "",
    ]
    cols = (
        ["patients", "never_see_doctor", "urgent_mri_bypass_rate"]
        + [f"{r}_wait_ascoded" for r in RESOURCES]
        + [f"{r}_wait" for r in RESOURCES]
        + [f"{r}_still_waiting" for r in RESOURCES]
        + [f"{r}_util_ascoded" for r in RESOURCES]
        + [f"{r}_util" for r in RESOURCES]
        + ["mean_util_ascoded", "mean_util"]
    )
    out.append("| metric | " + " | ".join(arms) + " |")
    out.append("|---|" + "---|" * len(arms))
    for c in cols:
        out.append(
            f"| {c} | "
            + " | ".join("%.3g +/- %.2g" % mean_ci([r[c] for r in by[a]]) for a in arms)
            + " |"
        )
    base = by[arms[0]]
    tests = []
    for a in arms[1:]:
        for m in METRICS:
            pairs = [
                (x[m], y[m])
                for x, y in zip(base, by[a])
                if not (math.isnan(x[m]) or math.isnan(y[m]))
            ]
            d = [y - x for x, y in pairs]
            md, h = mean_ci(d)
            p = (
                float(
                    stats.ttest_rel([y for _, y in pairs], [x for x, _ in pairs]).pvalue
                )
                if len(pairs) > 1
                else math.nan
            )
            rel = 100.0 * md / np.mean([x for x, _ in pairs])
            tests.append([a, m, md, h, rel, p])
    for t, padj in zip(tests, holm([t[5] for t in tests])):
        t.append(padj)
    out += [
        "",
        f"Paired differences vs {arms[0]} (arm minus baseline; Holm-adjusted over the {len(tests)} tests):",
        "",
        "| arm | metric | diff +/- 95% CI | relative | p | p (Holm) |",
        "|---|---|---|---|---|---|",
    ]
    out += [
        "| %s | %s | %.3g +/- %.2g | %+.1f%% | %.2g | %.2g |" % tuple(t) for t in tests
    ]
    return "\n".join(out) + "\n"


def cmd_sim(a):
    cfg = dict(CONFIGS[a.config], **CAPACITY)
    if a.doctors:
        cfg["num_doctors"] = a.doctors
    if a.beds:
        cfg["num_beds"] = a.beds
    arms = list(CODE_ARMS)
    tables = {}
    if a.llm_table:
        t = json.loads(Path(a.llm_table).read_text())
        tables = {f"llm_{k}": v for k, v in t["tables"].items()}
        arms = ["rule_based"] + list(tables)
    tag = a.tag or f"sim_{a.config}" + (
        f"_{Path(a.llm_table).stem}" if a.llm_table else ""
    )
    out_dir = RESULTS / tag
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for arm in arms:
        for rep in range(a.reps):
            seed = a.seed0 + rep
            row = run_one(
                arm, seed, cfg, a.warmup, tables.get(arm), a.fix_routing
            )
            rows.append(dict(arm=arm, rep=rep, seed=seed, **row))
            print(
                f"{arm} rep={rep} doctor_wait(as coded)={row['doctor_wait_ascoded']:.1f}",
                flush=True,
            )
    with open(out_dir / "reps.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    title = f"{tag}: {cfg}, warm-up {a.warmup} min" + (
        ", --fix-routing" if a.fix_routing else ""
    )
    text = report(rows, arms, title)
    (out_dir / "summary.md").write_text(text)
    print(text)


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sim", help="run every arm N times with fixed seeds")
    s.add_argument("--config", choices=CONFIGS, default="dissertation")
    s.add_argument("--reps", type=int, default=30)
    s.add_argument("--seed0", type=int, default=1000)
    s.add_argument(
        "--warmup",
        type=float,
        default=1440,
        help="minutes excluded from the corrected metrics",
    )
    s.add_argument("--doctors", type=int)
    s.add_argument("--beds", type=int)
    s.add_argument(
        "--llm-table",
        help="decision table from `llm-table`; replaces the coin-flip arms",
    )
    s.add_argument("--fix-routing", action="store_true", help="keep every needed service; a bypass only reorders")
    s.add_argument("--tag")
    s.set_defaults(fn=cmd_sim)
    import llm_router

    llm_router.add_commands(sub)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
