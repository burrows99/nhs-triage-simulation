class p:
    """Simulation parameters for the NHS Triage System"""
    # Patient arrival parameters
    inter = 0.0167            # Mean time between patient arrivals (minutes) - 100 patients in 100 seconds
                             # For Poisson process, this is 1/λ where λ is the arrival rate
                             # Expected number of arrivals per hour = 60/inter = 60 patients/hour
                             # In queuing theory notation, this is the μ parameter for
                             # the exponential distribution of inter-arrival times
    
    # Service time parameters
    mean_consultation = 30   # Mean doctor consultation time (minutes)
    stdev_consultation = 10  # Standard deviation of doctor consultation time
    mean_triage = 10         # Mean nurse triage time (minutes)
    stdev_triage = 5         # Standard deviation of nurse triage time
    mean_inpatient_wait = 90 # Mean inpatient wait time (minutes)
    
    # Resource parameters
    num_doctors = 3          # Number of doctors available
    num_nurses = 2           # Number of nurses available
    num_cubicles = 7         # Number of A&E cubicles
    
    # Simulation control parameters
    warm_up = 0              # Warm-up period (minutes) - disabled for testing
    sim_duration = 1.67      # Simulation duration (100 seconds = 1.67 minutes for 100 patients)
    cycle_patient_data = True # Cycle through patient CSV data repeatedly
    time_based_simulation = True # Control simulation by time only, not patient count