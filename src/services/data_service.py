"""Enhanced Data Service for Synthea Models

Loads CSV files and constructs Synthea models with populated relationship fields.
"""

import pandas as pd
import glob
import os
from typing import Dict, List, Optional, Any, Type
from functools import partial

from src.models.synthea_models import (
    Allergy, CarePlan, Condition, Encounter, ImagingStudy,
    Immunization, Medication, Observation, Organization,
    Patient, PayerTransition, Payer, Procedure, Provider
)


import attr

@attr.s(auto_attribs=True)
class DataService:
    """Enhanced service for loading Synthea CSV files and constructing models with relationships."""
    
    csv_folder: str = "./output/csv"
    
    # Initialize empty collections using attr.Factory
    patients: List[Patient] = attr.Factory(list)
    encounters: List[Encounter] = attr.Factory(list)
    organizations: List[Organization] = attr.Factory(list)
    providers: List[Provider] = attr.Factory(list)
    payers: List[Payer] = attr.Factory(list)
    
    def load_and_construct_data(self) -> None:
        """Load all CSV files and construct models with relationships."""
        # Step 1: Load all raw data
        raw_data = self._load_all_csvs()
        
        # Step 2: Create models using pandas and generic factory - eliminate custom wrappers
        model_mapping = {
            'patients': Patient,
            'encounters': Encounter, 
            'organizations': Organization,
            'providers': Provider,
            'payers': Payer,
            'allergies': Allergy,
            'careplans': CarePlan,
            'conditions': Condition,
            'imaging_studies': ImagingStudy,
            'immunizations': Immunization,
            'medications': Medication,
            'observations': Observation,
            'procedures': Procedure,
            'payer_transitions': PayerTransition
        }
        
        # Required keys validation
        required_keys = ['patients', 'encounters', 'organizations', 'providers', 'payers']
        missing_keys = [key for key in required_keys if key not in raw_data]
        if missing_keys:
            raise KeyError(f"Required data keys missing: {missing_keys}. Available: {list(raw_data.keys())}")
        
        # Create all models using generic factory
        created_models = {}
        for key, model_class in model_mapping.items():
            if key in raw_data:
                created_models[key] = self._create_models_generic(raw_data[key], model_class)
            else:
                created_models[key] = []
        
        # Unpack created models
        patients = created_models['patients']
        encounters = created_models['encounters']
        organizations = created_models['organizations']
        providers = created_models['providers']
        payers = created_models['payers']
        allergies = created_models['allergies']
        careplans = created_models['careplans']
        conditions = created_models['conditions']
        imaging_studies = created_models['imaging_studies']
        immunizations = created_models['immunizations']
        medications = created_models['medications']
        observations = created_models['observations']
        procedures = created_models['procedures']
        payer_transitions = created_models['payer_transitions']
        
        # Step 4: Populate relationships
        self._populate_encounter_relationships(encounters, allergies, careplans, conditions, 
                                             imaging_studies, immunizations, medications, 
                                             observations, procedures)
        self._populate_patient_relationships(patients, payer_transitions)
        
        # Store constructed data
        self.patients = patients
        self.encounters = encounters
        self.organizations = organizations
        self.providers = providers
        self.payers = payers
    
    def get_all_patients(self, deep: bool = False) -> List[Patient]:
        """Get all patients with optional deep relationships.
        
        Args:
            deep: If True, includes all related data (encounters, conditions, etc.)
                 If False, returns patients with basic relationships only
                 
        Returns:
            List of Patient instances with populated relationships
        """
        if not self.patients:
            self.load_and_construct_data()
            
        if deep:
            # Add encounters to each patient with all their related medical data
            for patient in self.patients:
                patient.encounters = [enc for enc in self.encounters if enc.PATIENT == patient.Id]
                
        return self.patients
    
    def _load_all_csvs(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load all CSV files into raw data dictionaries."""
        raw_data = {}
        csv_files = glob.glob(os.path.join(self.csv_folder, "*.csv"))
        
        for csv_file in csv_files:
            filename = os.path.basename(csv_file).replace(".csv", "")
            try:
                df = pd.read_csv(csv_file)
                
                # Convert to list of dictionaries with NaN handling
                records = []
                for _, row in df.iterrows():
                    row_dict = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
                    records.append(row_dict)
                raw_data[filename] = records
            except Exception as e:
                print(f"Error loading {csv_file}: {e}")
                
        return raw_data
    
    def _create_models_generic(self, records: List[Dict[str, Any]], model_class: Type) -> List:
        """Generic model factory using pandas for efficient processing.
        
        Args:
            records: List of dictionaries containing model data
            model_class: The model class to instantiate
            
        Returns:
            List of successfully created model instances
        """
        if not records:
            return []
        
        # Use pandas for efficient data processing
        df = pd.DataFrame(records)
        successful_models = []
        
        for _, row in df.iterrows():
            try:
                model_instance = model_class(**row.to_dict())
                successful_models.append(model_instance)
            except Exception as e:
                print(f"Error creating {model_class.__name__}: {e}")
                continue
        
        return successful_models
    
    def _populate_encounter_relationships(self, encounters: List[Encounter], 
                                        allergies: List[Allergy], careplans: List[CarePlan],
                                        conditions: List[Condition], imaging_studies: List[ImagingStudy],
                                        immunizations: List[Immunization], medications: List[Medication],
                                        observations: List[Observation], procedures: List[Procedure]) -> None:
        """Populate encounter relationship fields with related data."""
        for encounter in encounters:
            encounter_id = encounter.Id
            
            # Populate all relationship lists
            encounter.allergies = [a for a in allergies if a.ENCOUNTER == encounter_id]
            encounter.careplans = [c for c in careplans if c.ENCOUNTER == encounter_id]
            encounter.conditions = [c for c in conditions if c.ENCOUNTER == encounter_id]
            encounter.imaging_studies = [i for i in imaging_studies if i.ENCOUNTER == encounter_id]
            encounter.immunizations = [i for i in immunizations if i.ENCOUNTER == encounter_id]
            encounter.medications = [m for m in medications if m.ENCOUNTER == encounter_id]
            encounter.observations = [o for o in observations if o.ENCOUNTER == encounter_id]
            encounter.procedures = [p for p in procedures if p.ENCOUNTER == encounter_id]
    
    def _populate_patient_relationships(self, patients: List[Patient], 
                                      payer_transitions: List[PayerTransition]) -> None:
        """Populate patient relationship fields with related data."""
        for patient in patients:
            patient_id = patient.Id
            
            # Populate payer transitions
            patient.payer_transitions = [pt for pt in payer_transitions if pt.PATIENT == patient_id]

# DataService().load_and_construct_data()  # Removed: This was causing double data loading