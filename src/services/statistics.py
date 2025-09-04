import random
import math
from ..enums.Triage import Priority

class StatisticsService:
    
    @staticmethod
    def nhs_service_time(priority: Priority) -> float:
        """
        Return patient treatment time (minutes) based on Manchester Triage System (MTS) priority.

        Priority assumptions & sources:
        RED: ~30 min, highest urgency, log-normal distribution
             - Source: NHS Stroke Centres AI Tool, Guardian, 2025
               (https://www.theguardian.com/society/2025/sep/01/stroke-centres-in-england-given-ai-tool-that-will-help-50-of-patients-recover)
        ORANGE: ~20 min, very urgent, log-normal
                - Same source as RED
        YELLOW: ~12 min, urgent, log-normal
                - Same source as RED
        GREEN: ~8 min, standard, log-normal
               - Same source as RED
        BLUE: 5-8 min, non-urgent, uniform
              - Same source as RED

        Distribution rationale:
        - Log-normal is used to model right-skewed healthcare durations (long tail for complex cases)
          Reference: Faddy et al., 2009, PubMed
          (https://pubmed.ncbi.nlm.nih.gov/20667062/)
        """
        
        if priority == Priority.RED:
            mu, sigma = math.log(30), 0.4
            return random.lognormvariate(mu, sigma)
        elif priority == Priority.ORANGE:
            mu, sigma = math.log(20), 0.35
            return random.lognormvariate(mu, sigma)
        elif priority == Priority.YELLOW:
            mu, sigma = math.log(12), 0.3
            return random.lognormvariate(mu, sigma)
        elif priority == Priority.GREEN:
            mu, sigma = math.log(8), 0.2
            return random.lognormvariate(mu, sigma)
        else:  # BLUE
            return random.uniform(5, 8)
    
    # Log-normal parameters per priority (mean service times in minutes)
    PRIORITY_LOGNORMAL_PARAMS = {
        Priority.RED: (math.log(30), 0.4),
        Priority.ORANGE: (math.log(20), 0.35),
        Priority.YELLOW: (math.log(12), 0.3),
        Priority.GREEN: (math.log(8), 0.2),
        Priority.BLUE: (math.log(6), 0.15)  # BLUE usually very low priority
    }
    
    @staticmethod
    def estimated_wait_time(priority: Priority, 
                           Nq_eff: int, 
                           num_doctors: int, 
                           stochastic: bool = False) -> float:
        """
        🔹 Estimate wait time for a patient based on priority and effective queue length.
        
        Args:
            priority: Patient priority (Priority enum)
            Nq_eff: Effective number of patients ahead (higher + same priority)
            num_doctors: Number of available doctors
            stochastic: If True, sample service times for each patient ahead; else use mean
            
        Returns:
            Estimated wait time in minutes
        """
        mu, sigma = StatisticsService.PRIORITY_LOGNORMAL_PARAMS[priority]
        
        if num_doctors <= 0:
            num_doctors = 1  # avoid division by zero
        
        if stochastic:
            total_service = sum([random.lognormvariate(mu, sigma) for _ in range(Nq_eff)])
            return total_service / num_doctors
        else:
            mean_service = math.exp(mu + (sigma**2)/2)
            return (Nq_eff / num_doctors) * mean_service