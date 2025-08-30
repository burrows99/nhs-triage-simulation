import random
import numpy as np
from src.config.parameters import p

def estimate_triage_time():
    """Estimate time for nurse triage based on parameters"""
    return random.lognormvariate(np.log(p.mean_nurse_triage), p.stdev_nurse_triage / p.mean_nurse_triage)

def estimate_consult_time(priority):
    """Estimate doctor consultation time based on patient priority"""
    consult_mean = p.mean_doc_consult * (priority / 3)  # Adjust time based on priority
    return random.lognormvariate(np.log(consult_mean), p.stdev_doc_consult / consult_mean)

def estimate_admission_wait_time():
    """Estimate wait time for admission to hospital"""
    return random.expovariate(1.0 / p.mean_ip_wait)

def generate_patient_priority():
    """Generate patient priority based on NHS Manchester Triage System"""
    return random.choices([1,2,3,4,5], weights=[0.05, 0.15, 0.3, 0.3, 0.2])[0]

def generate_interarrival_time():
    """Generate patient inter-arrival times following a Poisson process
    
    In queuing theory, a Poisson arrival process has exponentially distributed
    inter-arrival times. This function generates these times based on the
    mean arrival rate parameter (p.inter).
    
    Returns:
        float: Time until next patient arrival in minutes
    """
    # For a Poisson process, inter-arrival times follow an exponential distribution
    # with parameter lambda = 1/mean_interarrival_time
    return random.expovariate(1.0 / p.inter)