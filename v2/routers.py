"""Non-LLM routers. Both see exactly what the LLM router sees: the triage record (MTS category,
discriminator, complaint, age, sex) and, for the load-aware ones, the same expected-wait bands.

RuleMTS    the static protocol: red/orange/yellow to the ED, green/blue to the UTC; imaging before
           the doctor only for two standard nurse-initiated pathways (suspected stroke -> CT,
           suspected fracture with deformity or inability to weight-bear -> X-ray, yellow+ only).
LoadAware  RuleMTS plus queue-aware streaming: a green/blue patient goes to whichever doctor pool
           (UTC or ED) shows the shorter expected-wait band (ties -> UTC, the protocol default).
"""

import re

STROKE = re.compile(
    r"\bFAST positive\b|facial droop|slurred speech|sudden .*weakness", re.I
)
FRACTURE = re.compile(
    r"deformity|unable to weight-bear|unable to stand|shortened", re.I
)
BAND_RANK = {"short": 0, "moderate": 1, "long": 2}


class RuleMTS:
    name = "rule_mts"

    def route(self, case, state, allowed):
        text, mts = case["complaint"], case["mts"]
        if mts in ("red", "orange") and STROKE.search(text):
            r = "CT_FIRST"
        elif mts in ("red", "orange", "yellow") and FRACTURE.search(text):
            r = "XRAY_FIRST"
        else:
            r = "UTC" if mts in ("green", "blue") else "ED"
        return (r if r in allowed else "ED"), {"source": "rule"}


class LoadAware(RuleMTS):
    name = "load_aware"

    def route(self, case, state, allowed):
        r, meta = super().route(case, state, allowed)
        if r == "UTC" and BAND_RANK[state["UTC"]] > BAND_RANK[state["ED"]]:
            r = "ED"
        return r, meta
