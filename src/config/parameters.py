class p:
    """Simulation parameters for the NHS Triage System"""
    # Patient arrival parameters
    inter = 5                # Mean time between patient arrivals (minutes)
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
    warm_up = 120            # Warm-up period (minutes)
    sim_duration = 1440      # Simulation duration (24 hours in minutes)