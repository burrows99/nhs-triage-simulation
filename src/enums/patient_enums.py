from enum import Enum


class PresentingComplaint(Enum):
    """Common presenting complaints in emergency departments."""
    CHEST_PAIN = "Chest Pain"
    SHORTNESS_OF_BREATH = "Shortness of Breath"
    ABDOMINAL_PAIN = "Abdominal Pain"
    HEADACHE = "Headache"
    TRAUMA = "Trauma"
    FEVER = "Fever"
    NAUSEA_VOMITING = "Nausea/Vomiting"
    DIZZINESS = "Dizziness"
    BACK_PAIN = "Back Pain"
    ALLERGIC_REACTION = "Allergic Reaction"
    MENTAL_HEALTH = "Mental Health Crisis"
    OVERDOSE = "Overdose"
    CARDIAC_ARREST = "Cardiac Arrest"
    STROKE_SYMPTOMS = "Stroke Symptoms"
    SEIZURE = "Seizure"


class ArrivalMode(Enum):
    """Methods of arrival to the emergency department."""
    WALK_IN = "Walk-in"
    AMBULANCE = "Ambulance"
    POLICE = "Police"
    HELICOPTER = "Helicopter"
    PRIVATE_VEHICLE = "Private Vehicle"
    WHEELCHAIR = "Wheelchair"
    STRETCHER = "Stretcher"


class AgeGroup(Enum):
    """Age groups for patient categorization."""
    INFANT = (0, 2)
    TODDLER = (3, 5)
    CHILD = (6, 12)
    ADOLESCENT = (13, 17)
    YOUNG_ADULT = (18, 35)
    MIDDLE_AGED = (36, 55)
    SENIOR = (56, 75)
    ELDERLY = (76, 100)

    def __init__(self, min_age: int, max_age: int):
        self.min_age = min_age
        self.max_age = max_age