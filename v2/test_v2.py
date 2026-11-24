"""Self-checks for the v2 simulator: python -m v2.test_v2"""

from .routers import RuleMTS
from .scenarios import scenario
from .sim import ROUTES, EDSim


class Always:
    """Proposes the same route for everyone (breaches the protocol on purpose)."""

    def __init__(self, r):
        self.r = r

    def route(self, case, state, allowed):
        return self.r, {"source": "test"}


def short():
    cfg = scenario("base")
    cfg.warmup_h, cfg.horizon_h = 12, 48
    return cfg


def main():
    base = EDSim(short(), RuleMTS(), 7).run().patient_frame()
    assert base.seen_by_doctor.all() and not base.censored.any()
    for r in ROUTES:
        df = EDSim(short(), Always(r), 7).run().patient_frame()
        # common random numbers: same patients, same cases, same arrival times in every arm
        assert (df.case_id.values == base.case_id.values).all() and (
            df.arrival.values == base.arrival.values
        ).all()
        # every patient who completed care saw a doctor (an absurd router such as "everyone to
        # ultrasound first" can overload a scanner so that some patients are still queuing at the
        # end of the drain; those are reported as censored, never dropped)
        done = df[~df.censored]
        assert done.seen_by_doctor.all(), f"{r}: a patient left without seeing a doctor"
        # the guard: UTC is never executed for red/orange, imaging-first never for green/blue
        assert not ((df.route == "UTC") & df.mts.isin(["red", "orange"])).any()
        assert not (
            df.route.str.endswith("_FIRST") & df.mts.isin(["green", "blue"])
        ).any()
        breach = (r == "UTC") & df.mts.isin(["red", "orange"]) | r.endswith(
            "_FIRST"
        ) & df.mts.isin(["green", "blue"])
        assert (df.violation == breach).all() and (df.fallback == breach).all()
        # every needed scan is done: time to imaging exists for every patient who needs imaging
        assert done[done.needs_imaging].imaging_wait.notna().all()
    print("v2 self-checks passed")


if __name__ == "__main__":
    main()
