import numpy as np
import pandas as pd
import os
import json
import logging

logger = logging.getLogger(__name__)

class EDMetrics:
    """Class to track and analyze metrics for the Emergency Department"""
    
    def __init__(self):
        self.patients_data = []
        self.total_patients = 0
        self.admitted_patients = 0
        self.discharged_patients = 0
        logger.info("EDMetrics initialized - ready to track patient data")
        
    def add_patient_data(self, patient):
        """Add a patient's data to the metrics tracking"""
        self.total_patients += 1
        
        logger.info(f"Recording metrics for Patient {patient.id} | "
                    f"Priority: {patient.priority} | "
                    f"Total ED Time: {getattr(patient, 'total_time', 0):.1f} min")
        
        if patient.admitted:
            self.admitted_patients += 1
        else:
            self.discharged_patients += 1
            
        # Store patient data for analysis
        patient_data = {
            'id': patient.id,
            'priority': patient.priority,
            'arrival_time': patient.arrival_time,
            'triage_time': patient.triage_time,
            'wait_for_triage': patient.wait_for_triage,
            'consult_time': patient.consult_time,
            'wait_for_consult': patient.wait_for_consult,
            'discharge_time': patient.discharge_time,
            'total_time': patient.total_time,
            'admitted': patient.admitted
        }
        
        self.patients_data.append(patient_data)
    
    def get_summary_stats(self):
        """Generate summary statistics for the ED"""
        if not self.patients_data:
            logger.info("No patient data available for summary statistics")
            return {
                'total_patients': 0,
                'admitted_rate': 0,
                'avg_wait_for_triage': 0,
                'avg_wait_for_consult': 0,
                'avg_total_time': 0,
                'avg_wait_by_priority': {}
            }
        
        df = pd.DataFrame(self.patients_data)
        
        # Safe division for admission rate
        admission_rate = self.admitted_patients / self.total_patients if self.total_patients > 0 else 0
        avg_consult_wait = df['wait_for_consult'].mean() if len(df) > 0 else 0
        
        logger.info(f"Calculating summary metrics:\n"
                    f"Total Patients: {self.total_patients}\n"
                    f"Admission Rate: {admission_rate:.1%}\n"
                    f"Avg Consultation Wait: {avg_consult_wait:.1f} min")
        
        summary = {
            'total_patients': self.total_patients,
            'admitted_rate': admission_rate,
            'avg_wait_for_triage': df['wait_for_triage'].mean(),
            'avg_wait_for_consult': df['wait_for_consult'].mean(),
            'avg_total_time': df['total_time'].mean(),
            'median_total_time': df['total_time'].median(),
            'avg_wait_by_priority': df.groupby('priority')['wait_for_consult'].mean().to_dict(),
            'avg_total_time_by_priority': df.groupby('priority')['total_time'].mean().to_dict()
        }
        
        return summary
    
    def get_dataframe(self):
        """Return a pandas DataFrame of all patient data"""
        df = pd.DataFrame(self.patients_data)
        logger.debug(f"Generated DataFrame with {len(df)} patient records")
        return df

    def save_patient_data(self, data, triage_type='single'):
        base_dir = f'output/manchester_triage/{triage_type}/json'
        logger.info(f"Saving patient data to {base_dir}/patient_data.json")
        logger.debug(f"Data contains {len(data)} patient records")
        
        try:
            os.makedirs(base_dir, exist_ok=True)
            with open(f'{base_dir}/patient_data.json', 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Successfully saved patient data to {base_dir}/patient_data.json")
        except Exception as e:
            logger.error(f"Failed to save patient data: {e}")
