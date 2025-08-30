class Patient:
    """Patient class for NHS Triage Simulation
    
    Represents a patient in the emergency department with tracking
    of various timestamps and wait times throughout their journey.
    """
    def __init__(self, id, arrival_time=0):
        self.id = id
        self.arrival_time = arrival_time
        self.priority = 0  # 1: immediate, 2: very urgent, 3: urgent, 4: standard, 5: non-urgent
        self.triage_time = 0
        self.wait_for_triage = 0
        self.consult_time = 0
        self.wait_for_consult = 0
        self.discharge_time = 0
        self.admitted = False
        
    def calculate_wait_times(self):
        """Calculate various wait times based on recorded timestamps"""
        if self.triage_time > 0:
            self.wait_for_triage = self.triage_time - self.arrival_time
        if self.consult_time > 0:
            self.wait_for_consult = self.consult_time - self.triage_time
        if self.discharge_time > 0:
            self.total_time = self.discharge_time - self.arrival_time