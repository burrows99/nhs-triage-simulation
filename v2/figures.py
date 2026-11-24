"""Figures for RESULTS_V2.md and the paper: python -m v2.figures [heldout|dev]"""

import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from .analyze import LABEL, PRIMARY  # noqa: E402
from .run import OUT  # noqa: E402
from .scenarios import HOURLY_SHARE  # noqa: E402

ARM_LABEL = {
    "rule_mts": "Static MTS protocol",
    "load_aware": "Load-aware heuristic",
    "moa_load": "LLM MoA, queue-aware",
    "moa_static": "LLM MoA, state-blind",
}
COLOR = {
    "rule_mts": "#7f7f7f",
    "load_aware": "#1f77b4",
    "moa_load": "#d62728",
    "moa_static": "#ff7f0e",
}
plt.rcParams.update(
    {"font.size": 8, "axes.spines.top": False, "axes.spines.right": False}
)


def save(fig, out, name):
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(out / f"{name}.{ext}", dpi=200)
    plt.close(fig)


def forest(out, tests):
    t = tests[tests.family == "primary"]
    fig, axes = plt.subplots(1, len(PRIMARY), figsize=(7.2, 2.2))
    for ax, m in zip(axes, PRIMARY):
        sub = t[t.metric == m]
        ys, labels = [], []
        for i, r in enumerate(sub.itertuples()):
            scale = 100 if m == "violation_rate" else 1
            ax.errorbar(
                r.diff * scale,
                i,
                xerr=r.half * scale,
                fmt="o",
                ms=3,
                color="#d62728" if r.p_holm < 0.05 else "#555555",
                capsize=2,
            )
            ys.append(i)
            labels.append(f"{r.scenario}: vs {r.comparator.replace('_', ' ')}")
        ax.axvline(0, color="k", lw=0.6)
        ax.set_yticks(ys)
        ax.set_yticklabels(labels if m == PRIMARY[0] else [])
        ax.set_title(
            LABEL[m].replace(" (min)", "\n(min)").replace(" (%)", "\n(pp)"), fontsize=7
        )
        ax.invert_yaxis()
    fig.suptitle(
        "Queue-aware LLM MoA minus baseline (paired, 95% CI; red = Holm p < 0.05; left of 0 = MoA better)",
        fontsize=7,
    )
    save(fig, out, "fig_primary_forest")


def by_hour(out, seeds):
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.3))
    ax = axes[0]
    ax.bar(range(24), HOURLY_SHARE, color="#bbbbbb")
    ax.set_xlabel("arrival hour")
    ax.set_ylabel("share of arrivals (%)")
    ax.set_title("Arrival profile (ECDS 2024-25)", fontsize=8)
    ax = axes[1]
    for arm in ARM_LABEL:
        f = OUT / seeds / "base" / f"patients_{arm}.csv.gz"
        if not f.exists():
            continue
        d = pd.read_csv(f, usecols=["arrival", "doctor_wait"])
        h = (d.arrival // 60 % 24).astype(int)
        ax.plot(
            d.groupby(h).doctor_wait.mean(),
            label=ARM_LABEL[arm],
            color=COLOR[arm],
            lw=1.2,
        )
    ax.set_xlabel("arrival hour")
    ax.set_ylabel("mean doctor wait (min)")
    ax.set_title("Base scenario", fontsize=8)
    ax.legend(fontsize=6, frameon=False)
    save(fig, out, "fig_hourly")


def routes(out, seeds):
    fig, axes = plt.subplots(1, 4, figsize=(7.2, 2.2), sharey=True)
    order = ["ED", "UTC", "XRAY_FIRST", "CT_FIRST", "US_FIRST"]
    cols = ["#7f7f7f", "#2ca02c", "#1f77b4", "#9467bd", "#8c564b"]
    for ax, arm in zip(axes, ARM_LABEL):
        f = OUT / seeds / "base" / f"patients_{arm}.csv.gz"
        if not f.exists():
            continue
        d = pd.read_csv(f, usecols=["mts", "route"])
        tab = pd.crosstab(d.mts, d.route, normalize="index").reindex(
            ["red", "orange", "yellow", "green"]
        )
        left = np.zeros(len(tab))
        for r, c in zip(order, cols):
            v = tab[r].values if r in tab else np.zeros(len(tab))
            ax.barh(tab.index, v, left=left, color=c, label=r)
            left += v
        ax.set_title(ARM_LABEL[arm], fontsize=7)
        ax.invert_yaxis()
    axes[-1].legend(fontsize=6, frameon=False, bbox_to_anchor=(1, 1), loc="upper left")
    save(fig, out, "fig_routes")


def welch(out):
    fig, ax = plt.subplots(figsize=(3.5, 2.2))
    for sc, c in (("base", "#1f77b4"), ("stress", "#d62728")):
        f = OUT / "dev" / f"welch_{sc}.csv"
        if f.exists():
            t = pd.read_csv(f, header=[0, 1], index_col=0)
            ax.plot(
                t.index,
                t[("doctor_wait", "mean")],
                "o-",
                ms=3,
                color=c,
                label=f"{sc}: doctor wait",
            )
            ax.plot(
                t.index, t[("los", "mean")], "s--", ms=3, color=c, label=f"{sc}: LOS"
            )
    ax.axvspan(-0.5, 1.5, color="#eeeeee")
    ax.set_xlabel("day of arrival (empty start)")
    ax.set_ylabel("mean (min), 20 dev seeds")
    ax.legend(fontsize=6, frameon=False)
    save(fig, out, "fig_warmup")


def main(seeds="heldout"):
    out = OUT / seeds / "figures"
    out.mkdir(parents=True, exist_ok=True)
    tests = pd.read_csv(OUT / seeds / "paired_tests.csv")
    forest(out, tests)
    by_hour(out, seeds)
    routes(out, seeds)
    welch(out)
    print("figures in", out)


if __name__ == "__main__":
    main(*(sys.argv[1:] or ["heldout"]))
