"""Build the v2 case pool from the Synthea encounters committed at 37d31df (output/csv/*.csv).

Every emergency encounter is mapped to a *presentation* using only its own coded data (encounter
description, reason, the conditions and procedures recorded in that encounter). Each presentation
carries what a triage nurse would know (a symptom-level complaint and the MTS category with its
discriminator) and, separately, the ground truth the simulator needs (which imaging, specialist
review and admission the patient actually requires). The router never sees the ground truth.

Ground-truth sources, in order:
  1. the encounter's own records: an X-ray study/procedure -> needs X-ray; an echocardiogram ->
     needs ultrasound; 'Admission to orthopedic department' -> specialist + bed; an encounter whose
     type is a hospital admission or that is followed by an inpatient encounter within 24 h -> bed;
  2. a published guideline where Synthea does not model the test (cited in GUIDELINE below).

v1's data/clean.py derived its labels from a column that held severity names, so every row got
route 'doctor' and no imaging; this module replaces it.

  python -m v2.cases            # writes v2/data/cases.csv
"""

import io
import subprocess
from pathlib import Path

import pandas as pd

SRC_COMMIT = "37d31df"
OUT = Path(__file__).parent / "data" / "cases.csv"

# Guideline-derived needs (Synthea does not simulate CT, ultrasound or specialty referral in ED).
GUIDELINE = {
    "ct_stroke": "NICE NG128: brain imaging immediately for suspected acute stroke",
    "ct_head": "NICE NG232: CT head for head injury with loss of consciousness / reduced GCS",
    "ct_trauma": "NICE NG39: CT for penetrating / major trauma",
    "us_appendix": "ultrasound as first-line imaging for suspected appendicitis (UK practice)",
    "admit": "admission pathway for the condition (stroke unit, PCI, surgery, hip fracture, trauma)",
    "psych": "NICE CG16 / NG225: psychosocial assessment after self-poisoning",
}

# presentation -> (MTS category, MTS discriminator, complaint, ct, us, specialist, admit, guideline note)
# xray / echo / orthopaedic admission come from the encounter's own records, not from this table.
PRESENTATIONS = {
    "cardiac_arrest": (
        "red",
        "airway/breathing compromise (post-arrest)",
        "Collapsed at home; out-of-hospital cardiac arrest, return of spontaneous circulation after paramedic CPR; intubated.",
        False,
        False,
        "cardiology/ICU",
        True,
        "admit",
    ),
    "gunshot": (
        "red",
        "major haemorrhage risk / penetrating trauma",
        "Gunshot wound to the torso, actively bleeding, tachycardic.",
        True,
        False,
        "trauma surgery",
        True,
        "ct_trauma; admit",
    ),
    "stroke": (
        "orange",
        "new neurological deficit < 24 h",
        "Sudden facial droop, right arm weakness and slurred speech, onset 90 minutes ago (FAST positive).",
        True,
        False,
        "stroke team",
        True,
        "ct_stroke; admit",
    ),
    "mi": (
        "orange",
        "cardiac pain",
        "Central crushing chest pain radiating to the left arm for 40 minutes, sweaty and nauseated.",
        False,
        False,
        "cardiology",
        True,
        "admit",
    ),
    "tbi": (
        "orange",
        "altered conscious level after head injury",
        "Head injury after a fall from height, confused, GCS 13, vomited twice.",
        True,
        False,
        "neurosurgery",
        True,
        "ct_head; admit",
    ),
    "appendicitis": (
        "orange",
        "severe pain",
        "Right lower quadrant abdominal pain for 18 hours, fever, vomiting, pain on walking.",
        False,
        True,
        "general surgery",
        True,
        "us_appendix; admit",
    ),
    "overdose": (
        "orange",
        "high lethality / altered conscious level",
        "Took an unknown quantity of tablets 2 hours ago, drowsy but rousable.",
        False,
        False,
        "psychiatric liaison",
        True,
        "psych",
    ),
    "asthma": (
        "orange",
        "unable to speak in full sentences / low SpO2",
        "Wheeze and breathlessness, known asthmatic, not responding to own inhaler, speaking in short phrases.",
        False,
        False,
        "respiratory medicine",
        True,
        "",
    ),
    "allergy": (
        "orange",
        "facial/tongue oedema",
        "Lip and facial swelling with hives after eating, no stridor.",
        False,
        False,
        None,
        False,
        "",
    ),
    "heart_failure": (
        "yellow",
        "moderate shortness of breath",
        "Increasing breathlessness over 4 days, ankle swelling, sleeps on 3 pillows; known heart failure.",
        False,
        False,
        "acute medicine",
        True,
        "",
    ),
    "seizure": (
        "yellow",
        "history of fit, now alert",
        "Witnessed generalised seizure lasting 2 minutes, known epilepsy, now alert and orientated.",
        False,
        False,
        None,
        False,
        "",
    ),
    "head_injury_loc": (
        "yellow",
        "history of unconsciousness",
        "Head injury with brief loss of consciousness, now GCS 15, headache.",
        True,
        False,
        None,
        False,
        "ct_head",
    ),
    "lung_mass": (
        "yellow",
        "haemoptysis / persistent symptoms",
        "Cough for 6 weeks with weight loss and some blood-streaked sputum.",
        False,
        False,
        None,
        False,
        "",
    ),
    "hip_fracture": (
        "yellow",
        "moderate pain, unable to weight-bear",
        "Fall at home, unable to stand, left leg shortened and externally rotated.",
        False,
        False,
        "orthopaedics",
        True,
        "admit",
    ),
    "fracture_upper_limb": (
        "yellow",
        "deformity / moderate pain",
        "Fall onto outstretched arm or shoulder, deformity and bony pain.",
        False,
        False,
        None,
        False,
        "",
    ),
    "fracture_ankle": (
        "yellow",
        "moderate pain, unable to weight-bear",
        "Inversion injury, unable to weight-bear, tender over the lateral malleolus.",
        False,
        False,
        None,
        False,
        "",
    ),
    "knee_injury": (
        "yellow",
        "moderate pain",
        "Twisting knee injury playing sport, swollen knee, painful to weight-bear.",
        False,
        False,
        None,
        False,
        "",
    ),
    "head_injury_minor": (
        "green",
        "minor head injury, no red flags",
        "Bumped head, no loss of consciousness, GCS 15, no vomiting.",
        False,
        False,
        None,
        False,
        "",
    ),
    "sprain": (
        "green",
        "recent mild pain",
        "Twisted joint, mild pain and swelling, able to weight-bear / full movement.",
        False,
        False,
        None,
        False,
        "",
    ),
    "whiplash": (
        "green",
        "recent mild pain",
        "Low-speed rear-end car collision, neck stiffness, walking, no limb symptoms.",
        False,
        False,
        None,
        False,
        "",
    ),
    "laceration": (
        "green",
        "wound, bleeding controlled",
        "Laceration needing closure, bleeding controlled with pressure.",
        False,
        False,
        None,
        False,
        "",
    ),
    "burn": (
        "green",
        "small superficial burn",
        "Small superficial burn from a kettle, intact skin, mild pain.",
        False,
        False,
        None,
        False,
        "",
    ),
    "chronic_pain": (
        "green",
        "recent mild pain, chronic condition",
        "Flare of known fibromyalgia, widespread aches, no new features.",
        False,
        False,
        None,
        False,
        "",
    ),
}


def presentation(desc, reason, conds):
    """Map one encounter's own coded data to a presentation, or None (excluded)."""
    t = " ".join([desc, reason, conds]).lower()
    rules = [
        ("cardiac arrest", "cardiac_arrest"),
        ("bullet wound", "gunshot"),
        ("stroke", "stroke"),
        ("myocardial infarction", "mi"),
        ("brain damage", "tbi"),
        ("appendic", "appendicitis"),
        ("overdose", "overdose"),
        ("asthma", "asthma"),
        ("allergic", "allergy"),
        ("heart failure", "heart_failure"),
        ("seizure", "seizure"),
        ("concussion with loss", "head_injury_loc"),
        ("concussion with no loss", "head_injury_minor"),
        ("lung cancer", "lung_mass"),
        ("fracture of hip", "hip_fracture"),
        ("fracture of ankle", "fracture_ankle"),
        ("fracture", "fracture_upper_limb"),
        ("meniscus", "knee_injury"),
        ("cruciate", "knee_injury"),
        ("patellar", "knee_injury"),
        ("sprain", "sprain"),
        ("whiplash", "whiplash"),
        ("laceration", "laceration"),
        ("burn", "burn"),
        ("fibromyalgia", "chronic_pain"),
    ]
    for needle, key in rules:
        if needle in t:
            return key
    return None  # no coded problem, or obstetric (labour goes to maternity, not the ED)


def git_csv(name):
    root = Path(__file__).resolve().parent.parent
    raw = subprocess.run(
        ["git", "show", f"{SRC_COMMIT}:output/csv/{name}.csv"],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout
    return pd.read_csv(io.BytesIO(raw))


def build():
    enc, pat = git_csv("encounters"), git_csv("patients")
    cond, proc, img = (
        git_csv("conditions"),
        git_csv("procedures"),
        git_csv("imaging_studies"),
    )
    enc["START"] = pd.to_datetime(enc.START)
    ed = enc[enc.ENCOUNTERCLASS == "emergency"].copy()
    inpatient = enc[enc.ENCOUNTERCLASS == "inpatient"]
    by_enc = lambda df: df.groupby("ENCOUNTER").DESCRIPTION.apply(
        lambda s: "; ".join(sorted(set(s)))
    )
    ed["conds"] = ed.Id.map(by_enc(cond)).fillna("")
    ed["procs"] = ed.Id.map(by_enc(proc)).fillna("")
    ed["imaging"] = ed.Id.map(
        img.groupby("ENCOUNTER").MODALITY_DESCRIPTION.apply(
            lambda s: "; ".join(sorted(set(s)))
        )
    ).fillna("")
    ed = ed.merge(
        pat[["Id", "BIRTHDATE", "GENDER", "RACE"]],
        left_on="PATIENT",
        right_on="Id",
        suffixes=("", "_p"),
    )
    rows, excluded = [], {}
    for r in ed.itertuples():
        key = presentation(
            r.DESCRIPTION,
            str(r.REASONDESCRIPTION if pd.notna(r.REASONDESCRIPTION) else ""),
            r.conds,
        )
        if key is None:
            why = (
                "obstetric (maternity pathway)"
                if "obstetric" in r.DESCRIPTION.lower()
                else "no coded presenting problem"
            )
            excluded[why] = excluded.get(why, 0) + 1
            continue
        cat, disc, complaint, ct, us, spec, admit, src = PRESENTATIONS[key]
        procs = r.procs.lower()
        xray = "x-ray" in procs or "radiograph" in r.imaging.lower()
        echo = "echocardiography" in procs
        ortho = "admission to orthopedic" in procs
        admitted_next = (
            (inpatient.PATIENT == r.PATIENT)
            & (inpatient.START >= r.START)
            & (inpatient.START <= r.START + pd.Timedelta(hours=24))
        ).any()
        hosp_adm = "hospital admission" in r.DESCRIPTION.lower()
        age = int(
            (r.START.tz_localize(None) - pd.to_datetime(r.BIRTHDATE)).days // 365.25
        )
        if (
            not 0 <= age <= 100
        ):  # Synthea snapshot artefact: encounter before birth / age > 100
            why = "implausible age (<0 or >100)"
            excluded[why] = excluded.get(why, 0) + 1
            continue
        rows.append(
            dict(
                case_id=r.Id[:8],
                presentation=key,
                mts=cat,
                discriminator=disc,
                complaint=complaint,
                age=age,
                sex=r.GENDER,
                ethnicity=r.RACE,
                needs_xray=bool(xray),
                needs_ct=bool(ct),
                needs_us=bool(us or echo),
                specialist=spec or ("orthopaedics" if ortho else ""),
                needs_bed=bool(admit or ortho or admitted_next or hosp_adm),
                label_source="; ".join(
                    filter(
                        None,
                        [
                            "xray:encounter" if xray else "",
                            "echo:encounter" if echo else "",
                            "ortho-admission:encounter" if ortho else "",
                            "inpatient<24h:encounter" if admitted_next else "",
                            "hospital-admission:encounter" if hosp_adm else "",
                            src,
                        ],
                    )
                ),
                synthea_codes=" | ".join(
                    filter(None, [r.DESCRIPTION, r.conds, r.procs])
                )[:300],
            )
        )
    df = pd.DataFrame(rows).sort_values(["mts", "presentation", "case_id"])
    df["needs_specialist"] = df.specialist != ""
    return df, excluded


def main():
    df, excluded = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"{len(df)} cases written to {OUT}; excluded: {excluded}")
    print(df.mts.value_counts().to_dict())
    print(
        df[["needs_xray", "needs_ct", "needs_us", "needs_specialist", "needs_bed"]]
        .mean()
        .round(3)
        .to_dict()
    )
    print(df.groupby(["sex", "ethnicity"]).size().to_dict())


if __name__ == "__main__":
    main()
