import pandas as pd
import glob
import os
import json
from typing import Dict, Any, List, Optional

# Import centralized logger
from src.logger import logger


class DataService:
    """Generic data service for loading and processing Synthea CSV files.
    
    This service dynamically loads all CSV files from a specified folder,
    normalizes FHIR references, and produces patient-centric records.
    """
    
    def __init__(self, csv_folder: str = "./output"):
        """Initialize the data service.
        
        Args:
            csv_folder: Path to folder containing Synthea CSV files
        """
        self.csv_folder = csv_folder
        self.dataframes: Dict[str, pd.DataFrame] = {}
        self.patient_data: Dict[str, Dict[str, Any]] = {}
    
    def load_csvs(self) -> Dict[str, pd.DataFrame]:
        """Load all CSV files from the specified folder into DataFrames.
        
        Returns:
            Dictionary mapping CSV filename (without extension) to DataFrame
        """
        self.dataframes = {}
        
        if not os.path.exists(self.csv_folder):
            raise FileNotFoundError(f"CSV folder not found: {self.csv_folder}")
        
        csv_files = glob.glob(os.path.join(self.csv_folder, "*.csv"))
        
        if not csv_files:
            raise ValueError(f"No CSV files found in {self.csv_folder}")
        
        for csv_file in csv_files:
            name = os.path.basename(csv_file).replace(".csv", "")
            try:
                self.dataframes[name] = pd.read_csv(csv_file)
                logger.info(f"Loaded {name}: {len(self.dataframes[name])} rows")
            except Exception as e:
                logger.error(f"Error loading {csv_file}: {e}")
        
        return self.dataframes
    
    def clean_references(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize FHIR references by extracting IDs from reference strings.
        
        Args:
            df: DataFrame to process
            
        Returns:
            DataFrame with additional *_id columns for FHIR references
        """
        df_copy = df.copy()
        
        for col in df_copy.columns:
            if df_copy[col].dtype == object:
                # Check if column contains FHIR references
                if df_copy[col].astype(str).str.contains("Patient/", na=False).any():
                    df_copy[col + "_id"] = df_copy[col].astype(str).str.replace("Patient/", "", regex=False)
                elif df_copy[col].astype(str).str.contains("Encounter/", na=False).any():
                    df_copy[col + "_id"] = df_copy[col].astype(str).str.replace("Encounter/", "", regex=False)
                elif df_copy[col].astype(str).str.contains("Practitioner/", na=False).any():
                    df_copy[col + "_id"] = df_copy[col].astype(str).str.replace("Practitioner/", "", regex=False)
                elif df_copy[col].astype(str).str.contains("Organization/", na=False).any():
                    df_copy[col + "_id"] = df_copy[col].astype(str).str.replace("Organization/", "", regex=False)
        
        return df_copy
    
    def normalize_all_references(self) -> None:
        """Apply reference normalization to all loaded DataFrames."""
        for name, df in self.dataframes.items():
            self.dataframes[name] = self.clean_references(df)
            logger.info(f"Normalized references for {name}")
    
    def build_patient_records(self) -> Dict[str, Dict[str, Any]]:
        """Build patient-centric records by merging all related data.
        
        Returns:
            Dictionary mapping patient_id to complete patient record
        """
        # Find patient table (case-insensitive)
        patient_table_name = None
        for table_name in self.dataframes.keys():
            if table_name.lower() == 'patients' or table_name.lower() == 'patient':
                patient_table_name = table_name
                break
        
        if patient_table_name is None:
            raise ValueError(f"Patient table not found in loaded data. Available tables: {list(self.dataframes.keys())}")
        
        patients = self.dataframes[patient_table_name]
        related_tables = {k: v for k, v in self.dataframes.items() if k != patient_table_name}
        
        self.patient_data = {}
        
        logger.info(f"Building records for {len(patients)} patients...")
        
        # Find the correct ID column name (case-insensitive)
        id_column = None
        for col in patients.columns:
            if col.lower() in ['id', 'patient_id']:
                id_column = col
                break
        
        if id_column is None:
            raise ValueError(f"No ID column found in patients table. Available columns: {list(patients.columns)}")
        
        for _, patient_row in patients.iterrows():
            patient_id = str(patient_row[id_column])
            
            # Start with base patient data
            patient_record = patient_row.to_dict()
            
            # Attach related data from all other tables
            for table_name, df in related_tables.items():
                # Find columns that might reference this patient
                # First look for columns ending with _id (from FHIR reference normalization)
                patient_ref_cols = [c for c in df.columns if c.endswith("_id") and "patient" in c.lower()]
                
                # Also look for direct patient reference columns (common in Synthea)
                direct_patient_cols = [c for c in df.columns if c.lower() == 'patient']
                
                # Combine both types of reference columns
                all_ref_cols = patient_ref_cols + direct_patient_cols
                
                if not all_ref_cols:
                    # Fallback: look for any column ending with _id or containing 'patient'
                    all_ref_cols = [c for c in df.columns if c.endswith("_id") or 'patient' in c.lower()]
                
                related_records = []
                for ref_col in all_ref_cols:
                    matching_rows = df[df[ref_col].astype(str) == patient_id]
                    if not matching_rows.empty:
                        related_records.extend(matching_rows.to_dict(orient='records'))
                
                if related_records:
                    patient_record[table_name] = related_records
                else:
                    patient_record[table_name] = []
            
            self.patient_data[patient_id] = patient_record
        
        logger.info(f"Built {len(self.patient_data)} patient records")
        return self.patient_data
    
    def get_patient_record(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific patient's complete record.
        
        Args:
            patient_id: ID of the patient
            
        Returns:
            Complete patient record or None if not found
        """
        return self.patient_data.get(str(patient_id))
    
    def get_all_patient_ids(self) -> List[str]:
        """Get list of all patient IDs.
        
        Returns:
            List of patient IDs
        """
        return list(self.patient_data.keys())
    
    def export_patient_record(self, patient_id: str, output_file: str) -> None:
        """Export a patient record to JSON file.
        
        Args:
            patient_id: ID of the patient
            output_file: Path to output JSON file
        """
        record = self.get_patient_record(patient_id)
        if record is None:
            raise ValueError(f"Patient {patient_id} not found")
        
        with open(output_file, 'w') as f:
            json.dump(record, f, indent=2, default=str)
        
        logger.info(f"Exported patient {patient_id} to {output_file}")
    
    def export_all_patients(self, output_file: str) -> None:
        """Export all patient records to JSON file.
        
        Args:
            output_file: Path to output JSON file
        """
        with open(output_file, 'w') as f:
            json.dump(self.patient_data, f, indent=2, default=str)
        
        logger.info(f"Exported {len(self.patient_data)} patients to {output_file}")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics about the loaded data.
        
        Returns:
            Dictionary with summary statistics
        """
        stats = {
            'total_patients': len(self.patient_data),
            'tables_loaded': list(self.dataframes.keys()),
            'table_row_counts': {name: len(df) for name, df in self.dataframes.items()}
        }
        
        if self.patient_data:
            # Sample patient to show available data types
            sample_patient = next(iter(self.patient_data.values()))
            stats['available_data_types'] = [k for k in sample_patient.keys() if isinstance(sample_patient[k], list) and sample_patient[k]]
        
        return stats
    
    def process_all(self) -> Dict[str, Dict[str, Any]]:
        """Complete processing pipeline: load, normalize, and build patient records.
        
        Returns:
            Dictionary of patient records
        """
        logger.info("Starting data processing pipeline...")
        
        # Step 1: Load all CSVs
        self.load_csvs()
        
        # Step 2: Normalize FHIR references
        self.normalize_all_references()
        
        # Step 3: Build patient-centric records
        self.build_patient_records()
        
        logger.info("Data processing complete!")
        return self.patient_data