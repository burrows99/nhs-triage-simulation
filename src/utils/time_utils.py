import random
import numpy as np
from src.config.config_manager import get_service_time_config, get_simulation_config, get_patient_generation_config

def estimate_triage_time():
    """Estimate time for nurse triage based on configuration"""
    service_config = get_service_time_config()
    mean_time = service_config['triage']['mean']
    stdev_time = service_config['triage']['stdev']
    return random.lognormvariate(np.log(mean_time), stdev_time / mean_time)

def estimate_consult_time(priority):
    """Estimate doctor consultation time based on patient priority"""
    service_config = get_service_time_config()
    base_mean = service_config['consultation']['mean']
    stdev = service_config['consultation']['stdev']
    consult_mean = base_mean * (priority / 3)  # Adjust time based on priority
    return random.lognormvariate(np.log(consult_mean), stdev / consult_mean)

def estimate_admission_wait_time():
    """Estimate wait time for admission to hospital"""
    service_config = get_service_time_config()
    mean_wait = service_config['admission_wait']['mean']
    return random.expovariate(1.0 / mean_wait)

def generate_patient_priority():
    """Generate patient priority based on NHS Manchester Triage System"""
    patient_config = get_patient_generation_config()
    weights = patient_config['priority_weights']
    return random.choices([1,2,3,4,5], weights=weights)[0]

def generate_interarrival_time():
    """Generate patient inter-arrival times following a Poisson process
    
    In queuing theory, a Poisson arrival process has exponentially distributed
    inter-arrival times. This function generates these times based on the
    configured arrival rate parameter.
    
    Returns:
        float: Time until next patient arrival in minutes
    """
    # For a Poisson process, inter-arrival times follow an exponential distribution
    # with parameter lambda = 1/mean_interarrival_time
    sim_config = get_simulation_config()
    return random.expovariate(1.0 / sim_config['patient_arrival_rate'])