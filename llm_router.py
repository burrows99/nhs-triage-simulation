"""Real LLM routers (single agent and mixture-of-agents) via a local Ollama server.

The dissertation-era code has no LLM in the simulation: its single_llm / multi_llm arms are coin
flips (edsim/agents.py) and ai/mixture_of_agents.py was an empty file. This module implements the
two routers from the prompts printed in the dissertation's appendix, so the arms can be run with
real models. Every call is logged; an unparseable answer is recorded as 'invalid' and counted,
never silently replaced by a rule.

  llm-table : route every input the simulator can produce (12 clinical combinations x 6
              gender/ethnicity groups) -> a decision table the `sim` command can replay.
  llm-cases : route the 237 cases in data/nhs_ecds_aligned_routing_dataset.csv and score them
              against that file's ground_truth_route column.
"""

import csv
import json
import os
import random
import time
import urllib.request
from pathlib import Path

OLLAMA = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
ROUTES = ("doctor", "mri", "ultrasound")
OUT = Path("results/llm")

ANSWER = (
    'Answer ONLY with JSON: {"route": "doctor" | "mri" | "ultrasound", "confidence": <integer 1-10>, '
    '"justification": "<one sentence>"}. "doctor" = physician consultation first (standard pathway); '
    '"mri" = direct to MRI, bypassing the physician; "ultrasound" = direct to ultrasound, bypassing the physician.'
)

# Appendix A.3 of the dissertation, condensed to the decision protocol.
SINGLE = """You are an Emergency Department Routing Specialist with 15 years of clinical experience in NHS emergency medicine. Your role is to determine the optimal patient pathway through the emergency department based on triage classification, clinical presentation, and resource availability.
Decision Protocol:
1. For Red-level patients with clear neurological indicators requiring MRI (e.g., sudden onset neurological deficit, suspected stroke), route directly to MRI when clinical evidence is unequivocal
2. For Red or Orange-level patients with abdominal symptoms requiring ultrasound (e.g., acute abdominal pain with specific findings), route directly to ultrasound
3. All other cases should follow the standard physician-first pathway
4. Never bypass physician consultation when clinical evidence is ambiguous or when contraindications exist
Prioritize patient safety above all else. When in doubt, default to physician consultation."""

SPECIALIST = """You are a specialized Emergency Department Clinical Specialist with deep expertise in {domain}. Your role is to provide domain-specific routing recommendations based on your area of expertise.
Remember: Your primary responsibility is patient safety. Never compromise clinical safety for efficiency gains. When clinical evidence is ambiguous, default to physician consultation."""

NEURO = """You are a Neurological Emergency Specialist with expertise in stroke assessment, neurological deficits, and MRI indications. Your primary responsibility is to identify cases where direct MRI access is clinically appropriate.
Key Indicators for Direct MRI Routing: sudden onset neurological deficit (face/arm/leg weakness, speech disturbance); NIH Stroke Scale score >= 4; time since symptom onset < 4.5 hours for potential thrombolysis; specific neurological findings requiring urgent imaging.
Decision Criteria: 1. Route directly to MRI if clear neurological indicators meet established criteria. 2. Do not route directly to MRI if contraindications exist. 3. Flag cases requiring urgent neurology consultation but not immediate MRI.
Prioritize identifying time-sensitive neurological conditions while avoiding inappropriate MRI referrals that would create bottlenecks."""

AGGREGATOR = """You are the Routing Aggregator with responsibility for synthesizing recommendations from multiple clinical specialists into a final routing decision. You have access to all specialist recommendations and must critically evaluate them to determine the optimal patient pathway.
Synthesis Protocol: 1. Evaluate the clinical validity of each specialist's recommendation. 2. Identify areas of agreement and disagreement. 3. Assess confidence levels and justification quality. 4. Consider potential biases in recommendations. 5. Apply safety thresholds: never accept recommendations with confidence <7/10 for direct specialty access.
Decision Principles: 1. Clinical safety is the absolute priority. 2. For Red-level patients with unequivocal clinical evidence, bypass physician consultation. 3. When specialists disagree, prioritize the most conservative (safest) recommendation."""

SPECIALISTS = {
    "neurological": NEURO,
    # The cardiac and abdominal prompts are not printed in the dissertation; the appendix's general
    # specialist template is used with the domain named in section 3.3.3.
    "cardiac": SPECIALIST.format(
        domain="cardiac emergencies such as chest pain, suspected arrhythmia and acute coronary syndromes"
    ),
    "abdominal": SPECIALIST.format(
        domain="abdominal emergencies, particularly those requiring ultrasound or surgical evaluation"
    ),
}


def chat(model, system, user):
    body = json.dumps(
        {
            "model": model,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0, "seed": 0, "num_predict": 200},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
    ).encode()
    req = urllib.request.Request(
        f"{OLLAMA}/api/chat", body, {"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.loads(r.read())["message"]["content"]


def parse(text):
    try:
        d = json.loads(text)
        route = str(d.get("route", "")).strip().lower()
        return (
            (route if route in ROUTES else "invalid"),
            d.get("confidence"),
            str(d.get("justification", ""))[:300],
        )
    except (ValueError, AttributeError):
        return "invalid", None, text[:300]


def single(model, vignette):
    return parse(chat(model, SINGLE, f"{vignette}\n\n{ANSWER}"))


def moa(model, vignette):
    specs = {
        name: parse(chat(model, prompt, f"{vignette}\n\n{ANSWER}"))
        for name, prompt in SPECIALISTS.items()
    }
    lines = "\n".join(
        f"- {n} specialist: route={r}, confidence={c}, justification={j}"
        for n, (r, c, j) in specs.items()
    )
    route, conf, why = parse(
        chat(
            model,
            AGGREGATOR,
            f"{vignette}\n\nSpecialist Recommendations:\n{lines}\n\n{ANSWER}",
        )
    )
    return route, conf, why, {n: v[0] for n, v in specs.items()}


def vignette(triage, complaint, findings, demographics):
    return (
        f"Current Patient Information:\n- Triage Level: {triage.upper()}\n- Chief Complaint: {complaint}\n"
        f"- Relevant Clinical Findings: {findings}\n- Demographics: {demographics}"
    )


def run(model, items, path):
    """items: [(key, vignette)]. Appends to a JSONL file and skips keys already done (resumable)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    done = {json.loads(l)["key"] for l in path.open()} if path.exists() else set()
    with path.open("a") as f:
        for key, v in items:
            if key in done:
                continue
            t0 = time.time()
            r1 = single(model, v)
            t1 = time.time()
            r2 = moa(model, v)
            t2 = time.time()
            rec = {
                "key": key,
                "model": model,
                "single": r1[0],
                "single_conf": r1[1],
                "single_why": r1[2],
                "moa": r2[0],
                "moa_conf": r2[1],
                "moa_why": r2[2],
                "moa_specialists": r2[3],
                "sec_single": round(t1 - t0, 2),
                "sec_moa": round(t2 - t1, 2),
            }
            f.write(json.dumps(rec) + "\n")
            f.flush()
            print(
                key,
                rec["single"],
                rec["moa"],
                rec["moa_specialists"],
                f"{t2 - t0:.1f}s",
                flush=True,
            )
    return [json.loads(l) for l in path.open()]


def slug(model):
    return model.replace(":", "-").replace("/", "_")


def cmd_table(a):
    from reproduce import GROUPS, case_key

    items = []
    for triage in ("red", "orange", "yellow", "green", "blue"):
        for needs_mri in (
            (False, True) if triage == "red" else (False,)
        ):  # edsim: only red patients can need MRI
            for needs_us in (False, True):
                for g in GROUPS:
                    findings = (
                        f"MRI indicated at triage: {'yes' if needs_mri else 'no'}; "
                        f"ultrasound indicated at triage: {'yes' if needs_us else 'no'}; no other findings recorded"
                    )
                    items.append(
                        (
                            case_key(triage, needs_mri, needs_us, g),
                            vignette(
                                triage, "not recorded", findings, f"{g[0]}, {g[1]}"
                            ),
                        )
                    )
    recs = run(a.model, items, OUT / f"table_{slug(a.model)}.jsonl")
    table = {
        "model": a.model,
        "tables": {
            "single": {r["key"]: r["single"] for r in recs},
            "moa": {r["key"]: r["moa"] for r in recs},
        },
    }
    # 'invalid' cannot be replayed; it is counted in the JSONL and replayed as the physician-first pathway
    for t in table["tables"].values():
        for k, v in t.items():
            t[k] = "doctor" if v == "invalid" else v
    (OUT / f"table_{slug(a.model)}.json").write_text(json.dumps(table, indent=1))
    print(f"wrote {OUT}/table_{slug(a.model)}.json")


def wilson(k, n, z=1.96):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / (1 + z * z / n)
    return c - h, c + h


def cmd_cases(a):
    rows = list(csv.DictReader(open("data/nhs_ecds_aligned_routing_dataset.csv")))
    if a.per_group:  # stratified random subsample (fixed seed) when full runs are too slow
        rng, picked = random.Random(0), []
        for g in sorted({(r["gender"], r["ethnicity_code"]) for r in rows}):
            sel = [r for r in rows if (r["gender"], r["ethnicity_code"]) == g]
            picked += rng.sample(sel, min(a.per_group, len(sel)))
        rows = picked
    eth = {"white": "White", "black": "Black", "asian": "Asian"}
    items = []
    for r in rows:
        flags = r["condition_keywords"].strip(", ") or "none"
        findings = (
            f"condition-severity flags from history: {flags}; chronic conditions: {r['chronic_count']}; "
            f"Clinical Frailty Scale {r['cfs_score']} ({r['frailty_category']})"
        )
        demo = f"{r['age_years']}-year-old {'male' if r['gender'] == 'M' else 'female'}, {eth[r['ethnicity_code']]}"
        items.append(
            (
                r["encounter_id"],
                vignette(r["triage_level"], "not recorded in dataset", findings, demo),
            )
        )
    recs = {
        x["key"]: x for x in run(a.model, items, OUT / f"cases_{slug(a.model)}.jsonl")
    }
    lines = [
        f"## Repo-case evaluation ({len(rows)} of 237 cases), {a.model}",
        "",
        "Ground truth = the ground_truth_route column of data/nhs_ecds_aligned_routing_dataset.csv "
        "(script-derived, not expert-reviewed). Accuracy with Wilson 95% CI. rule_based = always physician-first.",
        "",
        "| group | n | rule_based | single | moa |",
        "|---|---|---|---|---|",
    ]
    groups = sorted({(r["gender"], r["ethnicity_code"]) for r in rows})
    acc = {arm: {} for arm in ("rule_based", "single", "moa")}
    for g in [None] + groups:
        sel = [r for r in rows if g is None or (r["gender"], r["ethnicity_code"]) == g]
        cells = []
        for arm in acc:
            k = sum(
                (
                    r["ground_truth_route"] == "doctor"
                    if arm == "rule_based"
                    else recs[r["encounter_id"]][arm] == r["ground_truth_route"]
                )
                for r in sel
            )
            lo, hi = wilson(k, len(sel))
            acc[arm][g] = k / len(sel)
            cells.append(f"{100 * k / len(sel):.1f}% [{100 * lo:.1f}, {100 * hi:.1f}]")
        lines.append(
            f"| {'all' if g is None else ' '.join(g)} | {len(sel)} | "
            + " | ".join(cells)
            + " |"
        )
    lines += [
        "",
        "| arm | parity gap (max - min group accuracy) | max delta_g = max abs(acc_g - mean acc_g) | invalid outputs | routes |",
        "|---|---|---|---|---|",
    ]
    for arm in acc:
        v = [acc[arm][g] for g in groups]
        routes = (
            {}
            if arm == "rule_based"
            else {
                x: sum(recs[r["encounter_id"]][arm] == x for r in rows)
                for x in ROUTES + ("invalid",)
            }
        )
        lines.append(
            f"| {arm} | {100 * (max(v) - min(v)):.1f} pp | {100 * max(abs(x - sum(v) / len(v)) for x in v):.1f} pp | "
            f"{routes.get('invalid', 0)} | {routes} |"
        )
    text = "\n".join(lines) + "\n"
    (OUT / f"cases_{slug(a.model)}.md").write_text(text)
    print(text)


def add_commands(sub):
    t = sub.add_parser(
        "llm-table", help="LLM decision table for every simulator input (needs Ollama)"
    )
    t.add_argument("--model", required=True)
    t.set_defaults(fn=cmd_table)
    c = sub.add_parser(
        "llm-cases", help="route the 237 repo cases and score them (needs Ollama)"
    )
    c.add_argument("--model", required=True)
    c.add_argument("--per-group", type=int, help="score a fixed-seed sample of at most N cases per gender x ethnicity group")
    c.set_defaults(fn=cmd_cases)
