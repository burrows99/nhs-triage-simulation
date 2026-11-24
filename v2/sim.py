"""v2 emergency-department simulator (SimPy).

One Type 1 ED with a co-located Urgent Treatment Centre (UTC). After triage, a router picks one
route per patient; the simulator then executes the full care pathway, so a route only changes the
ORDER and the PLACE of care, never removes a service the patient needs:

  ED          ED doctor assessment -> needed imaging -> ED doctor review (only if imaging was done
              after the assessment) -> specialist review (if needed) -> bed (if admitted)
  CT_FIRST / US_FIRST / XRAY_FIRST
              that scan first (performed even if it turns out unnecessary), then the ED pathway; the
              assessment already has the result, so no review is needed for that scan
  UTC         UTC doctor consultation; X-ray-only patients get the X-ray and a UTC review; a patient
              who needs CT, ultrasound, a specialist or a bed is re-streamed to the ED pathway

Hard protocol rules (the guard in `allowed_routes`; a router cannot override them):
  H1 red and orange patients are never streamed to the UTC;
  H2 green and blue patients never go to imaging before a doctor;
  H3 every patient sees a doctor (structural: every pathway contains a doctor contact).

Statistics are collected for patients arriving in [warmup, warmup + horizon]; arrivals continue
after the window and the run continues until every window patient has left (no censoring).
Common random numbers: arrivals and case draws come from one stream, and every patient's service
times are pre-drawn at arrival from a patient-specific stream, so two arms with the same seed see
the same patients with the same service-time draws.
"""

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import simpy

ROUTES = ("ED", "UTC", "CT_FIRST", "US_FIRST", "XRAY_FIRST")
IMAGING_OF = {"CT_FIRST": "ct", "US_FIRST": "us", "XRAY_FIRST": "xray"}
PRIORITY = {"red": 0, "orange": 1, "yellow": 2, "green": 3, "blue": 4}
CASES = Path(__file__).parent / "data" / "cases.csv"


def allowed_routes(mts):
    if mts in ("red", "orange"):
        return ("ED", "CT_FIRST", "US_FIRST", "XRAY_FIRST")  # H1
    if mts in ("green", "blue"):
        return ("ED", "UTC")  # H2
    return ROUTES


@dataclass
class Config:
    arrivals_per_hour: float = 12.0
    hourly_profile: tuple = (
        1.0,
    ) * 24  # multipliers, mean 1 (set from published data in scenarios.py)
    admit_share: float | None = (
        None  # target share of admitted patients; None = uniform case draw
    )
    capacity: dict = field(default_factory=dict)
    # lognormal (mean, sd) in minutes
    service: dict = field(default_factory=dict)
    warmup_h: float = 48.0
    horizon_h: float = 7 * 24.0
    max_drain_h: float = 14 * 24.0
    band_edges: tuple = (
        30.0,
        90.0,
    )  # expected-wait bands shown to load-aware routers (minutes)


@dataclass
class Patient:
    pid: int
    arrival: float
    case: dict
    draws: dict
    route: str = ""
    decision: dict = field(default_factory=dict)
    t_doctor: float | None = None  # first doctor contact (ED or UTC)
    t_imaging: float | None = None  # start of first NEEDED scan
    t_depart: float | None = None
    restreamed: bool = False
    unnecessary_scan: bool = False
    doctor_contacts: int = 0


def lognormal(rng, mean, sd, size=None):
    s2 = np.log(1 + (sd / mean) ** 2)
    return rng.lognormal(np.log(mean) - s2 / 2, np.sqrt(s2), size)


class Station:
    """A SimPy priority resource plus the bookkeeping the metrics need."""

    def __init__(self, env, name, capacity, mean_service):
        self.env, self.name, self.capacity, self.mean_service = (
            env,
            name,
            capacity,
            mean_service,
        )
        self.res = simpy.PriorityResource(env, capacity=capacity)
        self.busy = []  # (start, end) of every service

    def expected_wait(self, priority):
        """Rough wait a new patient of this priority would face: work ahead of them / servers."""
        ahead = sum(1 for r in self.res.queue if r.priority <= priority)
        excess = ahead + self.res.count - self.capacity + 1
        return max(0.0, excess) * self.mean_service / self.capacity

    def serve(self, p, minutes):
        with self.res.request(priority=PRIORITY[p.case["mts"]]) as req:
            yield req
            start = self.env.now
            yield self.env.timeout(minutes)
            self.busy.append((start, self.env.now))
            return start

    def utilisation(self, t0, t1):
        busy = sum(max(0.0, min(e, t1) - max(s, t0)) for s, e in self.busy)
        busy += sum(
            max(0.0, t1 - max(r.usage_since, t0))
            for r in self.res.users
            if getattr(r, "usage_since", None) is not None
        )
        return busy / (self.capacity * (t1 - t0))


class EDSim:
    def __init__(
        self, cfg: Config, router, seed: int, cases: pd.DataFrame | None = None
    ):
        self.cfg, self.router, self.seed = cfg, router, seed
        self.cases = (cases if cases is not None else pd.read_csv(CASES)).to_dict(
            "records"
        )
        self.env = simpy.Environment()
        sv = cfg.service
        mean = {
            "ed_doctor": sv["assess"][0],
            "utc_doctor": sv["utc"][0],
            "xray": sv["xray"][0],
            "ct": sv["ct"][0],
            "us": sv["us"][0],
            "specialist": sv["specialist"][0],
            "bed": sv["bed"][0],
        }
        self.st = {k: Station(self.env, k, cfg.capacity[k], mean[k]) for k in mean}
        self.patients = []
        self.W, self.T = cfg.warmup_h * 60, cfg.horizon_h * 60
        self.weights = self._case_weights()

    def _case_weights(self):
        n = len(self.cases)
        if self.cfg.admit_share is None:
            return np.full(n, 1 / n)
        adm = np.array([bool(c["needs_bed"]) for c in self.cases])
        a = self.cfg.admit_share
        return np.where(adm, a / adm.sum(), (1 - a) / (~adm).sum())

    # ---- state shown to load-aware routers -------------------------------------------------
    def band(self, minutes):
        lo, hi = self.cfg.band_edges
        return "short" if minutes < lo else ("moderate" if minutes < hi else "long")

    def state(self, p):
        pr = PRIORITY[p.case["mts"]]
        return {
            "ED": self.band(self.st["ed_doctor"].expected_wait(pr)),
            "UTC": self.band(self.st["utc_doctor"].expected_wait(pr)),
            "CT_FIRST": self.band(self.st["ct"].expected_wait(pr)),
            "US_FIRST": self.band(self.st["us"].expected_wait(pr)),
            "XRAY_FIRST": self.band(self.st["xray"].expected_wait(pr)),
        }

    # ---- processes -------------------------------------------------------------------------
    def arrivals(self):
        rng = np.random.default_rng([self.seed, 0])
        lam_max = self.cfg.arrivals_per_hour * max(self.cfg.hourly_profile) / 60.0
        pid = 0
        while True:  # thinning for the non-homogeneous Poisson process
            yield self.env.timeout(rng.exponential(1 / lam_max))
            hour = int(self.env.now // 60) % 24
            accept = rng.random() < self.cfg.hourly_profile[hour] / max(
                self.cfg.hourly_profile
            )
            idx = rng.choice(len(self.cases), p=self.weights)
            if not accept:
                continue
            prng = np.random.default_rng([self.seed, 1, pid])
            sv = self.cfg.service
            draws = {
                k: float(lognormal(prng, *sv[k]))
                for k in (
                    "assess",
                    "review",
                    "utc",
                    "xray",
                    "ct",
                    "us",
                    "specialist",
                    "bed",
                )
            }
            draws["treat"] = float(
                lognormal(prng, *sv["treat"][self.cases[idx]["mts"]])
            )
            p = Patient(pid, self.env.now, self.cases[idx], draws)
            pid += 1
            self.patients.append(p)
            self.env.process(self.pathway(p))

    def decide(self, p):
        allowed = allowed_routes(p.case["mts"])
        proposed, meta = self.router.route(p.case, self.state(p), allowed)
        meta = dict(meta, proposed=proposed, violation=proposed not in allowed)
        if meta[
            "violation"
        ]:  # guard: the fallback is the static protocol route, and it is counted
            from .routers import RuleMTS

            proposed = RuleMTS().route(p.case, None, allowed)[0]
            meta["fallback"] = True
        return proposed, meta

    def doctor(self, p, station, minutes):
        start = yield from self.st[station].serve(p, minutes)
        p.doctor_contacts += 1
        if p.t_doctor is None:
            p.t_doctor = start

    def scan(self, p, modality):
        start = yield from self.st[modality].serve(p, p.draws[modality])
        if p.case[f"needs_{modality}"] and p.t_imaging is None:
            p.t_imaging = start

    def pathway(self, p):
        p.route, p.decision = self.decide(p)
        c = p.case
        needed = [m for m in ("ct", "us", "xray") if c[f"needs_{m}"]]
        if p.route == "UTC":
            yield from self.doctor(p, "utc_doctor", p.draws["utc"])
            if (
                c["needs_ct"]
                or c["needs_us"]
                or c["needs_specialist"]
                or c["needs_bed"]
            ):
                p.restreamed = (
                    True  # UTC cannot complete the care: back to the ED pathway
                )
            else:
                if needed:
                    for m in needed:
                        yield from self.scan(p, m)
                    yield from self.doctor(p, "utc_doctor", p.draws["review"])
                p.t_depart = self.env.now
                return
        done = []
        if p.route in IMAGING_OF:
            m = IMAGING_OF[p.route]
            yield from self.scan(p, m)
            done.append(m)
            p.unnecessary_scan = m not in needed
        yield from self.doctor(p, "ed_doctor", p.draws["assess"])
        # treatment / observation / blood results run in parallel with any imaging (not a modelled
        # resource); disposition waits for both
        treatment = self.env.timeout(p.draws["treat"])
        rest = [m for m in needed if m not in done]
        for m in rest:
            yield from self.scan(p, m)
        if rest:
            yield from self.doctor(p, "ed_doctor", p.draws["review"])
        yield treatment
        if c["needs_specialist"]:
            yield from self.st["specialist"].serve(p, p.draws["specialist"])
        if c["needs_bed"]:
            # the patient leaves the ED when an assessment-unit bed is free; the bed is then held
            # for the inpatient stay (draws['bed']) in a separate process
            req = self.st["bed"].res.request(priority=PRIORITY[c["mts"]])
            yield req
            p.t_depart = self.env.now
            self.env.process(self._hold_bed(req, p.draws["bed"]))
            return
        p.t_depart = self.env.now

    def _hold_bed(self, req, minutes):
        start = self.env.now
        yield self.env.timeout(minutes)
        self.st["bed"].res.release(req)
        self.st["bed"].busy.append((start, self.env.now))

    # ---- run ------------------------------------------------------------------------------
    def run(self):
        self.env.process(self.arrivals())
        end = self.W + self.T
        self.env.run(until=end)
        window = [p for p in self.patients if self.W <= p.arrival < end]
        limit = end + self.cfg.max_drain_h * 60
        while any(p.t_depart is None for p in window) and self.env.now < limit:
            self.env.run(until=self.env.now + 60)
        self.window = window
        return self

    def patient_frame(self):
        rows, now = [], self.env.now
        for p in self.window:
            c = p.case
            needs_img = c["needs_ct"] or c["needs_us"] or c["needs_xray"]
            rows.append(
                dict(
                    pid=p.pid,
                    case_id=c["case_id"],
                    presentation=c["presentation"],
                    mts=c["mts"],
                    sex=c["sex"],
                    ethnicity=c["ethnicity"],
                    route=p.route,
                    proposed=p.decision.get("proposed"),
                    source=p.decision.get("source"),
                    violation=p.decision.get("violation", False),
                    fallback=p.decision.get("fallback", False),
                    arrival=p.arrival,
                    # censored patients (still in the system when the drain limit is hit) are kept,
                    # with their time so far as a lower bound
                    doctor_wait=(p.t_doctor if p.t_doctor is not None else now) - p.arrival,
                    needs_imaging=needs_img,
                    imaging_wait=((p.t_imaging if p.t_imaging is not None else now) - p.arrival)
                    if needs_img
                    else np.nan,
                    los=(p.t_depart if p.t_depart is not None else now) - p.arrival,
                    censored=p.t_depart is None,
                    seen_by_doctor=p.t_doctor is not None,
                    restreamed=p.restreamed,
                    unnecessary_scan=p.unnecessary_scan,
                    doctor_contacts=p.doctor_contacts,
                )
            )
        return pd.DataFrame(rows)

    def utilisation(self):
        return {k: s.utilisation(self.W, self.W + self.T) for k, s in self.st.items()}
