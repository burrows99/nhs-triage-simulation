class p:
    """Simulation parameters for the NHS Triage System"""
    # Patient arrival parameters
    inter = 2                # Mean time between patient arrivals (minutes) - faster for testing
                             # For Poisson process, this is 1/λ where λ is the arrival rate
                             # Expected number of arrivals per hour = 60/inter
                             # In queuing theory notation, this is the μ parameter for
                             # the exponential distribution of inter-arrival times
    
    # Service time parameters
    mean_doc_consult = 30    # Mean doctor consultation time (minutes)
    stdev_doc_consult = 10   # Standard deviation of doctor consultation time
    mean_nurse_triage = 10   # Mean nurse triage time (minutes)
    stdev_nurse_triage = 5   # Standard deviation of nurse triage time
    mean_ip_wait = 90        # Mean inpatient wait time (minutes)
    
    # Resource parameters
    number_docs = 3          # Number of doctors available
    number_nurses = 2        # Number of nurses available
    ae_cubicles = 7          # Number of A&E cubicles
    
    # Simulation control parameters
    warm_up = 0              # Warm-up period (minutes) - disabled for testing
    sim_duration = 10        # Simulation duration (10 minutes for faster testing)
    cycle_patient_data = True # Cycle through patient CSV data repeatedly
    time_based_simulation = True # Control simulation by time only, not patient count