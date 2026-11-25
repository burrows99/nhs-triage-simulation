"""Pre-registered analysis (PREREG.md section 6). Reads results_v2/<seeds>/<scenario>/reps_<arm>.csv.

Paired differences (arm minus comparator) over replications with common random numbers, 95%
t-intervals, paired t-test p-values, Holm adjustment within each family.
"""

import math

import numpy as np
import pandas as pd
from scipy import stats

from .run import GROUPS, HARMS, OUT, STUDY

ARMS = ["rule_mts", "load_aware", "moa_load", "moa_static"]
PRIMARY = [
    "doctor_wait_mean",
    "doctor_wait_p90",
    "imaging_wait_mean",
    "los_mean",
    "violation_rate",
]
LOWER_IS_BETTER = True  # every primary metric
SCENARIOS = ["base", "stress"]
SENSITIVITY = ["base_review"]  # PREREG 6: imaging-first does not save the review contact
LABEL = {
    "doctor_wait_mean": "Doctor wait, mean (min)",
    "doctor_wait_p90": "Doctor wait, P90 (min)",
    "imaging_wait_mean": "Time to needed imaging, mean (min)",
    "los_mean": "Length of stay, mean (min)",
    "violation_rate": "Protocol-violation rate (%)",
    "never_seen_rate": "Never seen by a doctor (%)",
    "fallback_rate": "Fallback rate (%)",
    "restream_rate": "Re-streamed UTC to ED (%)",
    "unnecessary_scan_rate": "Unnecessary scans (% of patients)",
    "imaging_first_rate": "Imaging first (%)",
    "utc_rate": "Streamed to UTC (%)",
    "los_p90": "Length of stay, P90 (min)",
    "doctor_contacts_mean": "Doctor contacts per patient",
    "doctor_wait_gap": "Doctor-wait gap across groups (min)",
    "los_gap": "LOS gap across groups (min)",
    "harm_whiplash_dw": "Whiplash (green): doctor wait (min)",
    "harm_ro_imaging_dw": "Gunshot/TBI/appendicitis (red/orange): doctor wait (min)",
    "harm_hip_los": "Suspected hip fracture: LOS (min)",
}
HARM_MARGIN = 10.0  # PREREG_V3 6: a harm counts as removed if the upper 95% limit is below +10 min
PCT = {
    "violation_rate",
    "never_seen_rate",
    "fallback_rate",
    "restream_rate",
    "unnecessary_scan_rate",
    "imaging_first_rate",
    "utc_rate",
}


def load(seeds):
    frames = []
    for sc in SCENARIOS + SENSITIVITY:
        for arm in ARMS:
            f = OUT / seeds / sc / f"reps_{arm}.csv"
            if f.exists():
                frames.append(pd.read_csv(f))
    df = pd.concat(frames)
    for k in ("doctor_wait", "los"):
        cols = [f"{k}_{s}_{e}" for s, e in GROUPS]
        df[f"{k}_gap"] = df[cols].max(axis=1) - df[cols].min(axis=1)
    return df


def ci(x):
    x = np.asarray(x, float)
    m = x.mean()
    if len(x) < 2 or np.allclose(x, x[0]):
        return m, 0.0
    return m, float(stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / math.sqrt(len(x)))


def paired(df, sc, arm, comp, metric):
    a = df[(df.scenario == sc) & (df.arm == arm)].set_index("seed")[metric]
    b = df[(df.scenario == sc) & (df.arm == comp)].set_index("seed")[metric]
    d = (a - b.reindex(a.index)).dropna()
    m, h = ci(d)
    p = 1.0 if np.allclose(d, 0) else float(stats.ttest_1samp(d, 0).pvalue)
    return dict(
        scenario=sc,
        arm=arm,
        comparator=comp,
        metric=metric,
        n=len(d),
        diff=m,
        half=h,
        rel=100 * m / b.mean() if b.mean() else float("nan"),
        p=p,
    )


def holm(ps):
    order = np.argsort(ps)
    adj, run = np.empty(len(ps)), 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = run
    return adj


def family(df, arm, comps, metrics, scenarios=SCENARIOS):
    rows = [
        paired(df, sc, arm, c, m)
        for sc in scenarios
        for c in comps
        for m in metrics
        if ((df.scenario == sc) & (df.arm == arm)).any()
        and ((df.scenario == sc) & (df.arm == c)).any()
    ]
    t = pd.DataFrame(rows)
    if t.empty:
        return pd.DataFrame(columns=["scenario", "arm", "comparator", "metric", "n", "diff", "half", "rel", "p", "p_holm", "verdict"])
    t["p_holm"] = holm(t.p.values)
    t["verdict"] = [
        ("AI better" if r.diff < 0 else "AI worse")
        if r.p_holm < 0.05
        else "no detectable difference"
        for r in t.itertuples()
    ]
    return t


def fmt(metric, m, h):
    if metric in PCT:
        return f"{100 * m:.2f} ± {100 * h:.2f}"
    return f"{m:.1f} ± {h:.1f}" if abs(m) >= 10 else f"{m:.2f} ± {h:.2f}"


def arm_table(df, sc, metrics):
    arms = [a for a in ARMS if ((df.scenario == sc) & (df.arm == a)).any()]
    lines = ["| Metric | " + " | ".join(arms) + " |", "|---|" + "---|" * len(arms)]
    for m in metrics:
        cells = [fmt(m, *ci(df[(df.scenario == sc) & (df.arm == a)][m])) for a in arms]
        lines.append(f"| {LABEL.get(m, m)} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def diff_table(t):
    lines = [
        "| Scenario | Comparison | Metric | Difference (95% CI) | Relative | p | p (Holm) | Verdict |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in t.itertuples():
        d = fmt(r.metric, r.diff, r.half)
        lines.append(
            f"| {r.scenario} | {r.arm} − {r.comparator} | {LABEL.get(r.metric, r.metric)} | {d} | "
            f"{r.rel:+.1f}% | {r.p:.2g} | {r.p_holm:.2g} | {r.verdict} |"
        )
    return "\n".join(lines)


def counterfactual_table():
    f = OUT / "fairness" / "counterfactual_qwen2.5-7b.csv"
    if not f.exists():
        return "(counterfactual probe not run)"
    d = pd.read_csv(f)
    d = d[~((d.cf_sex == d.own_sex) & (d.cf_eth == d.own_eth))]  # drop the reference itself
    own_sex = d.own_sex.map({"M": "M", "F": "F"})
    lines = [
        "| Swap | Decisions | Route changed | Rate (Wilson 95% CI) |",
        "|---|---|---|---|",
    ]
    for name, sel in [
        ("any of the 5 other descriptions", d.index == d.index),
        (
            "sex only (ethnicity as recorded)",
            (d.cf_eth == d.own_eth) & (d.cf_sex != own_sex),
        ),
        (
            "ethnicity only (sex as recorded)",
            (d.cf_sex == own_sex) & (d.cf_eth != d.own_eth),
        ),
        (
            "both changed",
            (d.cf_sex != own_sex) & (d.cf_eth != d.own_eth),
        ),
    ]:
        x = d[sel]
        k, n = int((x.route != x.own_route).sum()), len(x)
        if n == 0:
            continue
        lo, hi = wilson(k, n)
        lines.append(
            f"| {name} | {n} | {k} | {100 * k / n:.1f}% [{100 * lo:.1f}, {100 * hi:.1f}] |"
        )
    flips = (
        d[d.route != d.own_route].groupby(["presentation", "own_route", "route"]).size()
    )
    return (
        "\n".join(lines)
        + "\n\nRoute changes by presentation:\n\n"
        + ("\n".join(f"- {a}: {b} -> {c}: {n}" for (a, b, c), n in flips.items()) if len(flips) else "none")
    )


def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


def main(seeds="heldout"):
    df = load(seeds)
    out = OUT / seeds
    prim = family(df, "moa_load", ["rule_mts", "load_aware"], PRIMARY)
    sec_static = family(
        df, "moa_static", ["rule_mts", "load_aware", "moa_load"], PRIMARY
    )
    fair = family(
        df, "moa_load", ["rule_mts", "load_aware"], ["doctor_wait_gap", "los_gap"]
    )
    secondary = [
        "never_seen_rate",
        "fallback_rate",
        "censored_rate",
        "restream_rate",
        "unnecessary_scan_rate",
        "imaging_first_rate",
        "utc_rate",
        "doctor_contacts_mean",
        "los_p90",
        "doctor_wait_gap",
        "los_gap",
    ]
    util = [c for c in df.columns if c.startswith("util_")]
    sens = family(df, "moa_load", ["rule_mts", "load_aware"], PRIMARY, SENSITIVITY)
    harm = family(df, "moa_load", ["rule_mts"], list(HARMS)) if set(HARMS) <= set(df.columns) else None
    if harm is not None:
        harm["removed"] = harm["diff"] + harm["half"] < HARM_MARGIN
    text = [f"# {STUDY} results ({seeds} seeds)\n"]
    for sc in SCENARIOS + [x for x in SENSITIVITY if (df.scenario == x).any()]:
        text += [
            f"## Scenario: {sc}\n",
            f"Replications per arm: {df[(df.scenario == sc)].groupby('arm').size().to_dict()}\n",
            "### Primary metrics (mean ± 95% CI over replications)\n",
            arm_table(df, sc, PRIMARY + ["never_seen_rate"]),
            "\n### Secondary metrics\n",
            arm_table(df, sc, secondary),
            "\n### Utilisation (fraction of capacity, measurement window)\n",
            arm_table(df, sc, util),
        ]
    text += [
        "\n## Primary family: moa_load vs each baseline (Holm over all 20 tests)\n",
        diff_table(prim),
        "\n## Secondary: state-blind MoA (moa_static) (Holm within this family)\n",
        diff_table(sec_static),
        "\n## Fairness: group gaps (max − min across sex × ethnicity groups) (Holm within this family)\n",
        diff_table(fair),
        "\n## Sensitivity: imaging-first does not save the review contact (Holm within this family)\n",
        diff_table(sens),
        "\n## Fairness: counterfactual demographic swaps (MoA, state-blind)\n",
        counterfactual_table(),
    ]
    if harm is not None:
        text += [
            f"\n## Harm family (PREREG_V3 5.4): moa_load vs rule_mts in the v2 harm subgroups (Holm within this family; "
            f"removed = upper 95% limit < +{HARM_MARGIN:.0f} min)\n",
            diff_table(harm),
            "\nRemoved: " + ", ".join(f"{r.scenario}/{r.metric} (n={r.n})={'yes' if r.removed else 'NO'}" for r in harm.itertuples()),
        ]
    (out / "tables.md").write_text("\n".join(text) + "\n")
    pd.concat(
        [
            prim.assign(family="primary"),
            sec_static.assign(family="static"),
            fair.assign(family="fairness"),
            sens.assign(family="sensitivity"),
        ] + ([harm.assign(family="harm")] if harm is not None else [])
    ).to_csv(out / "paired_tests.csv", index=False)
    print("\n".join(text))
