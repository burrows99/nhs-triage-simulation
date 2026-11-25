"""EXPLORATORY (not pre-registered, written after seeing the development-seed fairness gaps).

Writes results_v2/<seeds>/exploratory.md: standardised group gaps and per-presentation outcomes.

Do the sex x ethnicity gaps reflect the router treating groups differently, or the groups'
different case mix? Directly standardise each group's mean doctor wait to the overall presentation
mix: group g's standardised wait = sum over presentations p of w_p * mean wait(g, p), where w_p is the
overall share of p; presentations a group never has are skipped and the weights renormalised.

  python -m v2.explore heldout
"""

import sys

import pandas as pd

from .run import OUT

ARMS = ["rule_mts", "load_aware", "moa_load", "moa_static"]


def standardised(d, metric):
    w = d.presentation.value_counts(normalize=True)
    out = {}
    for g, x in d.groupby(["sex", "ethnicity"]):
        m = x.groupby("presentation")[metric].mean()
        ww = w.reindex(m.index)
        out[f"{g[0]}_{g[1]}"] = float((m * ww).sum() / ww.sum())
    return pd.Series(out)


def main(seeds="heldout"):
    lines = [
        "# Exploratory: case-mix-standardised group outcomes (not pre-registered)\n"
    ]
    for sc in ("base", "stress"):
        rows = {}
        for arm in ARMS:
            f = OUT / seeds / sc / f"patients_{arm}.csv.gz"
            if not f.exists():
                continue
            d = pd.read_csv(
                f,
                usecols=[
                    "seed",
                    "presentation",
                    "sex",
                    "ethnicity",
                    "doctor_wait",
                    "los",
                ],
            )
            raw = d.groupby(["sex", "ethnicity"]).doctor_wait.mean()
            raw.index = [f"{a}_{b}" for a, b in raw.index]
            std = standardised(d, "doctor_wait")
            rows[arm] = {
                "raw gap (min)": raw.max() - raw.min(),
                "standardised gap (min)": std.max() - std.min(),
                **{f"std {k}": v for k, v in std.items()},
            }
        t = pd.DataFrame(rows).round(1)
        lines += [
            f"## {sc}: mean doctor wait by sex x ethnicity (all replications pooled)\n",
            "| | " + " | ".join(t.columns) + " |",
            "|---|" + "---|" * len(t.columns),
        ]
        lines += [
            f"| {i} | " + " | ".join(str(v) for v in r) + " |" for i, r in t.iterrows()
        ]
        lines.append("")
    for sc in ("base", "stress"):
        t = by_presentation(seeds, sc)
        lines += [f"## {sc}: per presentation, all replications pooled (min)\n",
                  "| MTS | presentation | " + " | ".join(t.columns) + " |", "|---|---|" + "---|" * len(t.columns)]
        lines += [f"| {i[0]} | {i[1]} | " + " | ".join(str(v) for v in r) + " |" for i, r in t.iterrows()]
        lines.append("")
    text = "\n".join(lines)
    (OUT / seeds / "exploratory.md").write_text(text + "\n")
    print(text)


def by_presentation(seeds="heldout", sc="base"):
    """Mean doctor wait and LOS per presentation and arm (pooled), with the MoA's modal route."""
    rows = []
    for arm in ARMS:
        f = OUT / seeds / sc / f"patients_{arm}.csv.gz"
        if f.exists():
            d = pd.read_csv(f, usecols=["presentation", "mts", "route", "doctor_wait", "los"])
            g = d.groupby(["mts", "presentation"]).agg(
                n=("los", "size"), dw=("doctor_wait", "mean"), los=("los", "mean"),
                route=("route", lambda r: r.value_counts().idxmax()))
            rows.append(g.add_prefix(f"{arm}:"))
    t = pd.concat(rows, axis=1)
    t["d_los(moa_load-rule)"] = t["moa_load:los"] - t["rule_mts:los"]
    t["d_dw(moa_load-rule)"] = t["moa_load:dw"] - t["rule_mts:dw"]
    cols = ["rule_mts:route", "moa_load:route", "rule_mts:dw", "moa_load:dw", "d_dw(moa_load-rule)",
            "rule_mts:los", "moa_load:los", "d_los(moa_load-rule)"]
    return t[cols].round(1)


if __name__ == "__main__":
    main(*(sys.argv[1:] or ["heldout"]))
