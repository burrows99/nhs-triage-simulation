class p:
    """Simulation parameters for the NHS Triage System"""
    # Patient arrival parameters
    inter = 0.1              # Mean time between patient arrivals (minutes) - 10 patients per minute
                             # For Poisson process, this is 1/λ where λ is the arrival rate
                             # Expected number of arrivals per hour = 60/inter = 600 patients/hour
                             # In queuing theory notation, this is the μ parameter for
                             # the exponential distribution of inter-arrival times
    
    # Service time parameters
    mean_consultation = 0.3  # Mean doctor consultation time (minutes) - 18 seconds
    stdev_consultation = 0.1 # Standard deviation of doctor consultation time
    mean_triage = 0.1        # Mean nurse triage time (minutes) - 6 seconds
    stdev_triage = 0.05      # Standard deviation of nurse triage time
    mean_inpatient_wait = 0.5 # Mean inpatient wait time (minutes) - 30 seconds
    
    # Resource parameters
    num_doctors = 5          # Number of doctors available (increased for faster processing)
    num_nurses = 5           # Number of nurses available (increased for faster processing)
    num_cubicles = 10        # Number of A&E cubicles (increased for faster processing)
    
    # Simulation control parameters
    warm_up = 0              # Warm-up period (minutes) - disabled for testing
    sim_duration = 1.0       # Simulation duration (1 minute)
    cycle_patient_data = True # Cycle through patient CSV data repeatedly
    time_based_simulation = True # Control simulation by time only, not patient count