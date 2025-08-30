import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats
import os
import numpy as np

class EDVisualizer:
    def __init__(self, metrics, triage_type):
        self.metrics = metrics
        self.triage_type = triage_type
        self.base_dir = f'output/{self.triage_type.get_triage_system_name()}/plots'
        os.makedirs(self.base_dir, exist_ok=True)
        self.df = self.metrics.get_dataframe()

    def create_wait_time_plots(self):
        if self.df.empty:
            return None
        plt.figure(figsize=(10, 6))
        self.df.groupby('priority')['wait_for_consult'].mean().plot(kind='bar')
        plt.title('Average Wait for Consultation by Priority')
        plt.xlabel('Priority')
        plt.ylabel('Wait Time (minutes)')
        plt.tight_layout()
        return self._save_figure('wait_for_consult.png')

    def create_priority_distribution_plot(self):
        if self.df.empty:
            return None
        plt.figure(figsize=(10, 6))
        self.df['priority'].value_counts().sort_index().plot(kind='bar')
        plt.title('Priority Distribution')
        plt.xlabel('Priority')
        plt.ylabel('Patient Count')
        plt.tight_layout()
        return self._save_figure('priority_distribution.png')

    def verify_poisson_arrivals(self):
        if self.df.empty:
            return None
        plt.figure(figsize=(10, 6))
        self.df['arrival_time'].diff().dropna().hist(bins=20)
        plt.title('Interarrival Times (Poisson Check)')
        plt.xlabel('Minutes Between Arrivals')
        plt.ylabel('Frequency')
        plt.tight_layout()
        return self._save_figure('poisson_arrivals.png')

    def _save_figure(self, filename):
        full_path = os.path.join(self.base_dir, filename)
        plt.savefig(full_path, bbox_inches='tight')
        plt.close()
        return full_path