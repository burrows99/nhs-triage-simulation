import attr

@attr.s(auto_attribs=True)
class VitalSigns:
    """Patient vital signs data"""
    bp_systolic: float
    bp_diastolic: float
    heart_rate: float
    temperature: float
    oxygen_saturation: float