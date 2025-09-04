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