"""LLM mixture-of-agents (MoA) router, run on a local Ollama model.

Layer 1, four specialist agents (neurology, cardio-respiratory, abdominal/surgical, trauma and
musculoskeletal). Each reads only the triage record (MTS category and discriminator, complaint,
age, sex; never ethnicity, never queue state) and returns structured JSON: is the case in its
scope, which scan (if any) should precede the doctor, its confidence, and whether the patient
needs ED-level care (so must not be streamed to the UTC). Their answers depend only on the case,
so each specialist is called once per case.

Layer 2, an aggregator. It reads the triage record, the specialists' JSON, the protocol's hard
rules, the routes the protocol allows for this patient, and (queue-aware variant) the
expected-wait band of each candidate route. It returns {"route", "rationale"}.

Safety: the JSON schema lets the aggregator name ANY route, so a protocol breach is possible and is
measured: the simulator's guard (sim.allowed_routes) blocks it, executes the static protocol route
instead, and counts both the violation and the fallback. A transport error or unparseable answer
also falls back to the static protocol route and is counted. Nothing is silently replaced.

Every call is cached in SQLite by sha256(model, options, schema, system, user): with temperature 0
the cache is an exact replay, not an approximation.
"""

import hashlib
import json
import os
import sqlite3
import subprocess
import time
import urllib.request
from pathlib import Path

from .routers import RuleMTS
from .sim import IMAGING_OF

HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11435")
NUM_CTX = int(
    os.environ.get("OLLAMA_NUM_CTX", "12288")
)  # the shared server keeps 12288 loaded
OPTIONS = {"temperature": 0, "seed": 0, "num_predict": 220, "num_ctx": NUM_CTX}
CACHE = Path(__file__).parent / "cache" / "llm_cache.sqlite"
PROMPT_VERSION = (
    "v2.2"  # bump on any prompt change; part of every cache key via the prompt text
    # v2.0 -> v2.1 (development seeds only): the v2.0 aggregator sent most green patients to the ED
    # instead of the UTC and passed protocol-blocked imaging proposals through; v2.1 states the
    # protocol defaults, offers only protocol-allowed candidates, and narrows the trauma scope.
    # v2.1 -> v2.2: spells out what the UTC can do (v2.1 still sent wounds and low-risk neck
    # injuries to the ED as "ED care").
)

MODALITY = {"ct": "CT_FIRST", "ultrasound": "US_FIRST", "xray": "XRAY_FIRST"}
ROUTE_TEXT = {
    "ED": "ED doctor first (standard pathway; any imaging is ordered by the doctor and reviewed afterwards)",
    "UTC": "Urgent Treatment Centre doctor (minor illness/injury; can X-ray; cannot do CT, ultrasound, specialist referral or admission, such patients are sent back to the ED and assessed twice)",
    "CT_FIRST": "CT scan before the ED doctor (the doctor then sees the patient with the result)",
    "US_FIRST": "ultrasound before the ED doctor",
    "XRAY_FIRST": "X-ray before the ED doctor",
}
BAND_TEXT = {"short": "under 30 min", "moderate": "30-90 min", "long": "over 90 min"}

COMMON = """You work in an NHS Type 1 emergency department with a co-located Urgent Treatment Centre (UTC). Patients have already been triaged with the Manchester Triage System (MTS): red = immediate, orange = very urgent, yellow = urgent, green = standard, blue = non-urgent. You advise on the post-triage pathway only. Patient safety comes first. Answer only with the requested JSON."""

SPECIALISTS = {
    "neurology": """You are the neurology and head-injury specialist. In scope: suspected stroke/TIA, seizures, head injury, confusion, headache.
Imaging-before-doctor guidance: suspected acute stroke (sudden focal deficit, FAST positive) -> CT immediately (NICE NG128 stroke pathway); head injury with loss of consciousness, GCS below 15, repeated vomiting or confusion -> CT head within 1 hour (NICE NG232). A known epileptic who has recovered from a typical seizure, or a minor head injury without these features, needs no imaging first.""",
    "cardiorespiratory": """You are the cardio-respiratory specialist. In scope: chest pain, breathlessness, palpitations, collapse, cardiac arrest, asthma, heart failure, cough/haemoptysis.
Imaging-before-doctor guidance: chest pain and cardiac arrest need the doctor and an ECG first, not a scan first; echocardiography is requested by the doctor. Breathlessness with suspected heart failure, or persistent cough/haemoptysis, commonly gets a chest X-ray requested at triage. Acute asthma needs treatment, not imaging first.""",
    "abdominal": """You are the abdominal and general-surgical specialist. In scope: abdominal pain, vomiting, GI bleeding, urinary and gynaecological problems, overdose/poisoning (as a medical emergency).
Imaging-before-doctor guidance: right iliac fossa pain with fever/vomiting (suspected appendicitis) -> ultrasound is a reasonable first scan; suspected ruptured aneurysm or peritonitis needs the doctor first. Overdose needs the doctor, observations and bloods, not imaging.""",
    "trauma_msk": """You are the trauma and musculoskeletal specialist. In scope: injuries, fractures, sprains, wounds, burns, back and neck pain, penetrating or major trauma.
Imaging-before-doctor guidance: suspected fracture (deformity, unable to weight-bear, bony tenderness, shortened/rotated leg) -> X-ray first (Ottawa-type criteria); penetrating or major trauma -> trauma team and CT; low-risk neck injury after a minor collision (Canadian C-spine rule: walking, simple rear-end collision, no limb symptoms) needs no imaging at all; simple sprains with weight-bearing, wounds and small burns need no imaging first and suit the UTC.
Out of scope: medical collapse or cardiac arrest without injury, stroke, chest pain.""",
}

SPECIALIST_TASK = """Give your specialist view of this patient.
- in_scope: true if the presentation falls in your specialty.
- imaging_first: the ONE scan that should be done before the doctor sees the patient ("ct", "ultrasound", "xray"), or "none".
- confidence: 1-10 for your imaging_first answer.
- ed_care_needed: true if the patient will probably need ED-level care (CT, ultrasound, specialist referral, admission or resuscitation), i.e. must not be streamed to the UTC.
- rationale: one short sentence (at most 20 words)."""

SPECIALIST_SCHEMA = {
    "type": "object",
    "properties": {
        "in_scope": {"type": "boolean"},
        "imaging_first": {
            "type": "string",
            "enum": ["none", "ct", "ultrasound", "xray"],
        },
        "confidence": {"type": "integer", "minimum": 1, "maximum": 10},
        "ed_care_needed": {"type": "boolean"},
        "rationale": {"type": "string"},
    },
    "required": [
        "in_scope",
        "imaging_first",
        "confidence",
        "ed_care_needed",
        "rationale",
    ],
}

AGGREGATOR = """You are the routing aggregator. You combine the specialists' views into ONE route for the patient.
Protocol default (MTS streaming): red, orange and yellow patients see the ED doctor; green and blue patients go to the UTC. Depart from the default only for a clear reason:
 - an imaging-first route, when the specialist whose domain matches the complaint recommends a clearly indicated scan;
 - the ED instead of the UTC for a green or blue patient, when an in-scope specialist says ED-level care is needed{load_exception};
 - the UTC for a yellow patient, only if every in-scope specialist says ED-level care is not needed and the injury or illness is minor.
ED-level care means CT, ultrasound, specialist referral, admission or resuscitation. The UTC treats minor injuries and illnesses: wound closure, burns, sprains, low-risk neck and head injuries, and plain X-rays.
Hard protocol rules (never break them):
 H1. Red and orange patients are never sent to the UTC.
 H2. Green and blue patients never go to imaging before a doctor.
 H3. Every patient sees a doctor (all routes include one).
How to decide:
 - Weigh the in-scope specialists most; an imaging-first route is right only when the scan is clearly indicated, because an unnecessary scan wastes scanner time.
 - Imaging first (when indicated) gets the scan done sooner and saves a second doctor contact.
 - The UTC suits minor illness and injury; sending a patient who needs ED-level care there costs a second assessment in the ED.
{load_rule}"""

LOAD_RULE = " - Expected waits are given for the candidate routes. Among routes that are clinically appropriate, prefer the one with the shorter wait; never trade safety for speed."
STATIC_RULE = " - Choose on clinical grounds."

AGG_SCHEMA = {
    "type": "object",
    "properties": {
        "route": {
            "type": "string",
            "enum": ["ED", "UTC", "CT_FIRST", "US_FIRST", "XRAY_FIRST"],
        },
        "rationale": {"type": "string"},
    },
    "required": ["route", "rationale"],
}


def vignette(case, demographics=None):
    who = (
        demographics
        or f"{case['age']}-year-old {'man' if case['sex'] == 'M' else 'woman'}"
    )
    return (
        f"Triage record:\n- MTS category: {case['mts'].upper()} (discriminator: {case['discriminator']})\n"
        f"- Presenting complaint: {case['complaint']}\n- Patient: {who}"
    )


def free_memory_pct():
    try:
        out = subprocess.run(
            ["memory_pressure"], capture_output=True, text=True, timeout=10
        ).stdout
        return float(out.rsplit(":", 1)[1].strip().rstrip("%"))
    except Exception:
        return 100.0


class LLM:
    def __init__(self, model, cache=CACHE):
        self.model = model
        cache.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(cache, timeout=60)
        self.db.execute("pragma journal_mode=wal")
        self.db.execute(
            "create table if not exists calls (key text primary key, model text, system text, user text, response text, seconds real, created real)"
        )
        self.stats = {"calls": 0, "cache_hits": 0, "errors": 0, "seconds": 0.0}
        self.mem = {}

    def ask(self, system, user, schema):
        body = {
            "model": self.model,
            "stream": False,
            "format": schema,
            "options": OPTIONS,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        key = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
        if key in self.mem:
            self.stats["cache_hits"] += 1
            return self.mem[key]
        row = self.db.execute(
            "select response from calls where key=?", (key,)
        ).fetchone()
        if row:
            self.stats["cache_hits"] += 1
            self.mem[key] = json.loads(row[0])
            return self.mem[key]
        if self.stats["calls"] % 20 == 0:
            while (
                free_memory_pct() < 10
            ):  # memory guard: other agents share this machine
                print("memory guard: free < 10%, pausing 60 s", flush=True)
                time.sleep(60)
        t0 = time.time()
        req = urllib.request.Request(
            f"{HOST}/api/chat",
            json.dumps(body).encode(),
            {"Content-Type": "application/json"},
        )
        for attempt in range(
            5
        ):  # transport retries only (server busy/restarting); never on content
            try:
                with urllib.request.urlopen(req, timeout=600) as r:
                    text = json.loads(r.read())["message"]["content"]
                break
            except Exception as e:  # noqa: BLE001
                if attempt == 4:
                    self.stats["errors"] += 1
                    return {"_error": repr(e)}
                time.sleep(30)
        dt = time.time() - t0
        self.stats["calls"] += 1
        self.stats["seconds"] += dt
        try:
            parsed = json.loads(text)
        except ValueError:
            parsed = {"_unparseable": text[:500]}
        self.db.execute(
            "insert or replace into calls values (?,?,?,?,?,?,?)",
            (key, self.model, system, user, json.dumps(parsed), dt, time.time()),
        )
        self.db.commit()
        self.mem[key] = parsed
        return parsed


def valid_specialist(d):
    return (
        isinstance(d, dict)
        and isinstance(d.get("in_scope"), bool)
        and isinstance(d.get("ed_care_needed"), bool)
        and d.get("imaging_first") in ("none", "ct", "ultrasound", "xray")
        and isinstance(d.get("confidence"), int)
    )


class MoARouter:
    """route(case, state, allowed) -> (route, meta). state=None or queue_aware=False -> state-blind."""

    def __init__(self, model="qwen2.5:7b", queue_aware=True, demographics=None):
        self.llm, self.queue_aware, self.demographics = (
            LLM(model),
            queue_aware,
            demographics,
        )
        self.name = f"moa_{'load' if queue_aware else 'static'}_{model}"
        self.rule = RuleMTS()

    def specialists(self, case):
        v = vignette(case, self.demographics)
        out = {}
        for name, prompt in SPECIALISTS.items():
            d = self.llm.ask(
                f"{COMMON}\n\n{prompt}", f"{v}\n\n{SPECIALIST_TASK}", SPECIALIST_SCHEMA
            )
            out[name] = (
                d if valid_specialist(d) else None
            )  # None = abstained (invalid output), counted
        return out

    def route(self, case, state, allowed):
        specs = self.specialists(case)
        invalid_specs = sum(v is None for v in specs.values())
        proposed = {
            MODALITY[d["imaging_first"]]
            for d in specs.values()
            if d and d["in_scope"] and d["imaging_first"] != "none"
        }
        # candidates shown to the aggregator: the doctor-first routes the protocol allows, plus the
        # imaging-first routes a specialist proposed (even a disallowed one, so a breach can happen)
        # v2.1: only protocol-allowed routes are offered; a blocked proposal is shown as blocked. The
        # schema still accepts all five routes, so a breach remains possible and is measured.
        candidates = [r for r in ("ED", "UTC") if r in allowed] + sorted(proposed & set(allowed))
        blocked = sorted(proposed - set(allowed))
        meta = {
            "source": "moa",
            "invalid_specialists": invalid_specs,
            "candidates": candidates,
            "blocked": blocked,
        }
        if len(candidates) == 1:  # v2: always ["ED"]; v3 (R1): ["UTC"] for green/blue
            return candidates[0], dict(meta, source="moa_single_candidate")
        lines = []
        for name, d in specs.items():
            if d is None:
                lines.append(f"- {name}: no valid answer")
            else:
                lines.append(
                    f"- {name}: in_scope={d['in_scope']}, imaging_first={d['imaging_first']} "
                    f"(confidence {d['confidence']}), ed_care_needed={d['ed_care_needed']}; {d['rationale']}"
                )
        aware = self.queue_aware and state is not None
        opts = []
        for r in candidates:
            wait = f"; expected wait {BAND_TEXT[state[r]]}" if aware else ""
            opts.append(f"- {r}: {ROUTE_TEXT[r]}{wait}")
        system = f"{COMMON}\n\n" + AGGREGATOR.format(
            load_rule=LOAD_RULE if aware else STATIC_RULE,
            load_exception=", or when the UTC's expected wait is longer than the ED's" if aware else "",
        )
        user = (
            f"{vignette(case, self.demographics)}\n\nSpecialist views:\n"
            + "\n".join(lines)
            + "\n\nCandidate routes:\n"
            + "\n".join(opts)
            + ("\n(Proposed but blocked by the protocol: " + ", ".join(blocked) + ")" if blocked else "")
            + f"\n\nRoutes the protocol allows for a {case['mts'].upper()} patient: {', '.join(allowed)}."
            + "\nReturn the route and a rationale of at most 20 words."
        )
        d = self.llm.ask(system, user, AGG_SCHEMA)
        route = d.get("route") if isinstance(d, dict) else None
        if route not in IMAGING_OF and route not in ("ED", "UTC"):
            fb = self.rule.route(case, state, allowed)[0]
            return fb, dict(
                meta, source="fallback_invalid", fallback=True, raw=str(d)[:200]
            )
        return route, dict(meta, rationale=str(d.get("rationale", ""))[:300])
