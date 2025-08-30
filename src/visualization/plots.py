import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats
import os
import numpy as np
import logging
from src.config.config_manager import get_visualization_config, get_output_paths, create_output_directories

logger = logging.getLogger(__name__)

class EDVisualizer:
    def __init__(self, metrics, triage_type):
        self.metrics = metrics
        self.triage_type = triage_type
        
        # Get configuration and setup paths
        self.viz_config = get_visualization_config()
        triage_system_name = self.triage_type.get_triage_system_name()
        self.paths = get_output_paths(triage_system_name)
        
        # Create output directories
        create_output_directories(triage_system_name)
        self.base_dir = self.paths['plots']
        
        self.df = self.metrics.get_dataframe()
        logger.info(f"EDVisualizer initialized for {triage_system_name}")
        logger.info(f"Plot output directory: {self.base_dir}")
        logger.debug(f"DataFrame contains {len(self.df)} patient records for visualization")

    def create_wait_time_plots(self):
        if self.df.empty:
            logger.warning("No data available for wait time plots")
            return None
        
        logger.info("Creating wait time plots by priority")
        plt.figure(figsize=(10, 6))
        wait_times = self.df.groupby('priority')['wait_for_consult'].mean()
        logger.debug(f"Average wait times by priority: {wait_times.to_dict()}")
        
        wait_times.plot(kind='bar')
        plt.title('Average Wait for Consultation by Priority')
        plt.xlabel('Priority')
        plt.ylabel('Wait Time (minutes)')
        plt.tight_layout()
        return self._save_figure('wait_for_consult.png')

    def create_priority_distribution_plot(self):
        if self.df.empty:
            logger.warning("No data available for priority distribution plot")
            return None
        
        logger.info("Creating priority distribution plot")
        plt.figure(figsize=(10, 6))
        priority_counts = self.df['priority'].value_counts().sort_index()
        logger.debug(f"Priority distribution: {priority_counts.to_dict()}")
        
        priority_counts.plot(kind='bar')
        plt.title('Priority Distribution')
        plt.xlabel('Priority')
        plt.ylabel('Patient Count')
        plt.tight_layout()
        return self._save_figure('priority_distribution.png')

    def verify_poisson_arrivals(self):
        if self.df.empty:
            logger.warning("No data available for Poisson arrival verification")
            return None
        
        logger.info("Creating Poisson arrival verification plot")
        plt.figure(figsize=(10, 6))
        interarrival_times = self.df['arrival_time'].diff().dropna()
        logger.debug(f"Mean interarrival time: {interarrival_times.mean():.2f} minutes")
        logger.debug(f"Std interarrival time: {interarrival_times.std():.2f} minutes")
        
        interarrival_times.hist(bins=20)
        plt.title('Interarrival Times (Poisson Check)')
        plt.xlabel('Minutes Between Arrivals')
        plt.ylabel('Frequency')
        plt.tight_layout()
        return self._save_figure('poisson_arrivals.png')

    def _save_figure(self, filename):
        full_path = os.path.join(self.base_dir, filename)
        try:
            plt.savefig(full_path, bbox_inches='tight')
            plt.close()
            logger.info(f"Successfully saved plot: {full_path}")
            return full_path
        except Exception as e:
            logger.error(f"Failed to save plot {filename}: {e}")
            plt.close()
            return None