class PriorityLabels:
    IMMEDIATE = 'Immediate (Red)'
    VERY_URGENT = 'Very Urgent (Orange)'
    URGENT = 'Urgent (Yellow)'
    STANDARD = 'Standard (Green)'
    NON_URGENT = 'Non-Urgent (Blue)'

class SymptomSeverity:
    LEVELS = {
        'life_threatening': 0.9,
        'potentially_life_threatening': 0.7,
        'serious': 0.5,
        'standard': 0.3,
        'minor': 0.1
    }

class LogMessages:
    PATIENT_ARRIVAL = 'Patient {} arrived at ED | Time: {:.1f} minutes'
    TRIAGE_COMPLETE = 'Triage completed for Patient {} | Priority: {} | Duration: {:.1f} min'
    TRIAGE_DECISION = 'Triage Decision | Patient {} | RR: {} | O2: {}% | Priority: {}'
    DISCHARGE = 'Patient {} discharged | Consult wait: {:.1f} min | Admitted: {}'
    TRIAGE_ERROR = 'Triage error for Patient {} | {}'

class PlotTitles:
    WAIT_TIMES = 'Wait Times by Priority'
    ED_DISTRIBUTION = 'Distribution of Total Time in ED'
    POISSON_VERIFICATION = 'Distribution of Arrivals per Time Interval'
    INTERARRIVAL = 'Distribution of Inter-arrival Times'