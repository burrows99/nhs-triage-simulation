"""v2 experiment CLI.

python -m v2.run cases                                  # rebuild v2/data/cases.csv from Synthea
python -m v2.run welch --scenario base                  # warm-up check (development seeds)
python -m v2.run specialists --model qwen2.5:7b         # pre-fill the specialist cache (optional)
python -m v2.run sim --scenario base --seeds dev --arms rule_mts,load_aware,moa_load,moa_static
python -m v2.run sim --scenario base --seeds heldout ... # the pre-registered evaluation (run once)
python -m v2.run fairness --model qwen2.5:7b            # counterfactual demographic swaps
python -m v2.run analyze --seeds heldout                # tables -> results_v2/heldout/*.md
"""

import argparse
import json
import time
from pathlib import Path

import pandas as pd

from .routers import LoadAware, RuleMTS
from .scenarios import scenario
from .sim import CASES, EDSim, allowed_routes

SEEDS = {"dev": list(range(100, 120)), "heldout": list(range(1000, 1030))}
OUT = Path(__file__).resolve().parent.parent / "results_v2"
MODEL = "qwen2.5:7b"
GROUPS = [(s, e) for s in ("F", "M") for e in ("asian", "black", "white")]


def make_router(arm, model=MODEL):
    if arm == "rule_mts":
        return RuleMTS()
    if arm == "load_aware":
        return LoadAware()
    from .moa import MoARouter

    return MoARouter(model, queue_aware=(arm == "moa_load"))


def rep_metrics(sim):
    df = sim.patient_frame()
    m = {
        "patients": len(df),
        "doctor_wait_mean": df.doctor_wait.mean(),
        "doctor_wait_p90": df.doctor_wait.quantile(0.9),
        "imaging_wait_mean": df.imaging_wait.mean(),
        "los_mean": df.los.mean(),
        "los_p90": df.los.quantile(0.9),
        "violation_rate": df.violation.mean(),
        "fallback_rate": df.fallback.mean(),
        "never_seen_rate": 1 - df.seen_by_doctor.mean(),
        "censored_rate": df.censored.mean(),
        "restream_rate": df.restreamed.mean(),
        "unnecessary_scan_rate": df.unnecessary_scan.mean(),
        "imaging_first_rate": df.route.isin(
            ["CT_FIRST", "US_FIRST", "XRAY_FIRST"]
        ).mean(),
        "utc_rate": (df.route == "UTC").mean(),
        "doctor_contacts_mean": df.doctor_contacts.mean(),
    }
    for k, v in sim.utilisation().items():
        m[f"util_{k}"] = v
    for s, e in GROUPS:
        g = df[(df.sex == s) & (df.ethnicity == e)]
        m[f"doctor_wait_{s}_{e}"] = g.doctor_wait.mean()
        m[f"los_{s}_{e}"] = g.los.mean()
    return m, df


def cmd_sim(a):
    out = OUT / a.seeds / a.scenario
    out.mkdir(parents=True, exist_ok=True)
    seeds = SEEDS[a.seeds][: a.reps] if a.reps else SEEDS[a.seeds]
    for arm in a.arms.split(","):
        router = make_router(arm, a.model)
        rows, frames, t0 = [], [], time.time()
        for seed in seeds:
            sim = EDSim(scenario(a.scenario), router, seed).run()
            m, df = rep_metrics(sim)
            rows.append(dict(arm=arm, scenario=a.scenario, seed=seed, **m))
            frames.append(df.assign(arm=arm, seed=seed))
            llm = getattr(getattr(router, "llm", None), "stats", {})
            print(
                f"{a.scenario} {arm} seed={seed} dw={m['doctor_wait_mean']:.1f} los={m['los_mean']:.1f} "
                f"viol={m['violation_rate']:.4f} fb={m['fallback_rate']:.4f} llm={llm} {time.time() - t0:.0f}s",
                flush=True,
            )
        pd.DataFrame(rows).to_csv(out / f"reps_{arm}.csv", index=False)
        pd.concat(frames).to_csv(out / f"patients_{arm}.csv.gz", index=False)
        if hasattr(router, "llm"):
            (out / f"llm_stats_{arm}.json").write_text(
                json.dumps(router.llm.stats, indent=1)
            )


def cmd_specialists(a):
    from .moa import MoARouter

    r = MoARouter(a.model)
    cases = pd.read_csv(CASES).to_dict("records")
    for i, c in enumerate(cases):
        r.specialists(c)
        print(i, c["case_id"], r.llm.stats, flush=True)


def cmd_welch(a):
    """Hourly mean doctor wait and LOS by arrival hour since t=0, averaged over development seeds,
    with a 0 h warm-up and a 10-day horizon: the curve should be flat after the warm-up."""
    rows = []
    for seed in SEEDS["dev"]:
        cfg = scenario(a.scenario)
        cfg.warmup_h, cfg.horizon_h = 0.0, 10 * 24.0
        df = EDSim(cfg, RuleMTS(), seed).run().patient_frame()
        df["day"] = (df.arrival // 1440).astype(int)
        rows.append(df.groupby("day")[["doctor_wait", "los"]].mean().assign(seed=seed))
    t = (
        pd.concat(rows)
        .reset_index()
        .groupby("day")[["doctor_wait", "los"]]
        .agg(["mean", "std"])
    )
    out = OUT / "dev"
    out.mkdir(parents=True, exist_ok=True)
    t.to_csv(out / f"welch_{a.scenario}.csv")
    print(t.round(1))


def cmd_fairness(a):
    """Counterfactual swaps (PREREG 5.3): one case per presentation (the first by case_id), routed by
    the state-blind MoA under each of the 6 sex x ethnicity descriptions, with ethnicity STATED in
    the vignette (the deployed router never receives ethnicity, so this probes the model itself).
    The reference is the description matching the case's own recorded sex and ethnicity."""
    from .moa import MoARouter

    cases = pd.read_csv(CASES).sort_values("case_id").groupby("presentation").head(1).to_dict("records")
    rows = []
    for c in cases:
        res = {}
        for s, e in GROUPS:
            demo = f"{c['age']}-year-old {'man' if s == 'M' else 'woman'}, ethnicity {e}"
            r = MoARouter(a.model, queue_aware=False, demographics=demo)
            res[(s, e)] = r.route(c, None, allowed_routes(c["mts"]))[0]
        own = res[(c["sex"], c["ethnicity"])]
        for (s, e), route in res.items():
            rows.append(dict(case_id=c["case_id"], presentation=c["presentation"], mts=c["mts"], own_sex=c["sex"],
                             own_eth=c["ethnicity"], cf_sex=s, cf_eth=e, route=route, own_route=own))
        print(c["case_id"], c["presentation"], res, flush=True)
    out = OUT / "fairness"
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / f"counterfactual_{a.model.replace(':', '-')}.csv", index=False)


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sim")
    s.add_argument("--scenario", choices=["base", "stress", "base_review"], required=True)
    s.add_argument("--seeds", choices=list(SEEDS), required=True)
    s.add_argument("--arms", default="rule_mts,load_aware,moa_load,moa_static")
    s.add_argument("--model", default=MODEL)
    s.add_argument("--reps", type=int)
    s.set_defaults(fn=cmd_sim)
    w = sub.add_parser("welch")
    w.add_argument("--scenario", default="base")
    w.set_defaults(fn=cmd_welch)
    sp = sub.add_parser("specialists")
    sp.add_argument("--model", default=MODEL)
    sp.set_defaults(fn=cmd_specialists)
    f = sub.add_parser("fairness")
    f.add_argument("--model", default=MODEL)
    f.set_defaults(fn=cmd_fairness)
    c = sub.add_parser("cases")
    c.set_defaults(fn=lambda a: __import__("v2.cases", fromlist=["main"]).main())
    an = sub.add_parser("analyze")
    an.add_argument("--seeds", choices=list(SEEDS), default="heldout")
    an.set_defaults(
        fn=lambda a: __import__("v2.analyze", fromlist=["main"]).main(a.seeds)
    )
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
