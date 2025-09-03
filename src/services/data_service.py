"""Enhanced Data Service for Synthea Models

Loads CSV files and constructs Synthea models with populated relationship fields.
"""

import pandas as pd
import glob
import os
from typing import Dict, List, Optional, Any

from src.logger import logger
from src.models.synthea_models import (
    Allergy, CarePlan, Condition, Encounter, ImagingStudy,
    Immunization, Medication, Observation, Organization,
    Patient, PayerTransition, Payer, Procedure, Provider
)


class DataService:
    """Enhanced service for loading Synthea CSV files and constructing models with relationships."""
    
    def __init__(self, csv_folder: str = "./output/csv"):
        """Initialize the data service.
        
        Args:
            csv_folder: Path to folder containing Synthea CSV files
        """
        self.csv_folder = csv_folder
        self.patients: List[Patient] = []
        self.encounters: List[Encounter] = []
        self.organizations: List[Organization] = []
        self.providers: List[Provider] = []
        self.payers: List[Payer] = []
        
    def load_and_construct_data(self) -> None:
        """Load all CSV files and construct models with relationships."""
        logger.info("🔄 DATA_TRANSFER_START: DataService.load_and_construct_data() initiated")
        logger.info(f"📊 TRANSFER_SOURCE: CSV files from {self.csv_folder}")
        logger.info(f"📍 TRANSFER_DESTINATION: DataService memory objects")
        
        # Step 1: Load all raw data
        logger.info("🔄 DATA_TRANSFER: Loading CSV files...")
        raw_data = self._load_all_csvs()
        logger.info(f"📊 TRANSFER_PAYLOAD: CSV data loaded - {dict((k, len(v) if isinstance(v, list) else str(type(v))) for k, v in raw_data.items())}")
        
        # Step 2: Create base models
        logger.info("🔄 DATA_TRANSFER: Creating patient models...")
        patients = self._create_patients(raw_data.get('patients', []))
        logger.info(f"📊 TRANSFER_RESULT: Patients created - count: {len(patients)}, sample: {str(patients[0].__dict__ if patients else 'None')}")
        
        logger.info("🔄 DATA_TRANSFER: Creating encounter models...")
        encounters = self._create_encounters(raw_data.get('encounters', []))
        logger.info(f"📊 TRANSFER_RESULT: Encounters created - count: {len(encounters)}, sample: {str(encounters[0].__dict__ if encounters else 'None')}")
        
        logger.info("🔄 DATA_TRANSFER: Creating organization models...")
        organizations = self._create_organizations(raw_data.get('organizations', []))
        logger.info(f"📊 TRANSFER_RESULT: Organizations created - count: {len(organizations)}, sample: {str(organizations[0].__dict__ if organizations else 'None')}")
        
        logger.info("🔄 DATA_TRANSFER: Creating provider models...")
        providers = self._create_providers(raw_data.get('providers', []))
        logger.info(f"📊 TRANSFER_RESULT: Providers created - count: {len(providers)}, sample: {str(providers[0].__dict__ if providers else 'None')}")
        
        logger.info("🔄 DATA_TRANSFER: Creating payer models...")
        payers = self._create_payers(raw_data.get('payers', []))
        logger.info(f"📊 TRANSFER_RESULT: Payers created - count: {len(payers)}, sample: {str(payers[0].__dict__ if payers else 'None')}")
        
        # Step 3: Create related data models
        logger.info("🔄 DATA_TRANSFER: Creating allergy models...")
        allergies = self._create_allergies(raw_data.get('allergies', []))
        logger.info(f"📊 TRANSFER_RESULT: Allergies created - count: {len(allergies)}, sample: {str(allergies[0].__dict__ if allergies else 'None')}")
        
        logger.info("🔄 DATA_TRANSFER: Creating careplan models...")
        careplans = self._create_careplans(raw_data.get('careplans', []))
        logger.info(f"📊 TRANSFER_RESULT: Careplans created - count: {len(careplans)}, sample: {str(careplans[0].__dict__ if careplans else 'None')}")
        
        logger.info("🔄 DATA_TRANSFER: Creating condition models...")
        conditions = self._create_conditions(raw_data.get('conditions', []))
        logger.info(f"📊 TRANSFER_RESULT: Conditions created - count: {len(conditions)}, sample: {str(conditions[0].__dict__ if conditions else 'None')}")
        
        logger.info("🔄 DATA_TRANSFER: Creating imaging study models...")
        imaging_studies = self._create_imaging_studies(raw_data.get('imaging_studies', []))
        logger.info(f"📊 TRANSFER_RESULT: Imaging studies created - count: {len(imaging_studies)}, sample: {str(imaging_studies[0].__dict__ if imaging_studies else 'None')}")
        
        logger.info("🔄 DATA_TRANSFER: Creating immunization models...")
        immunizations = self._create_immunizations(raw_data.get('immunizations', []))
        logger.info(f"📊 TRANSFER_RESULT: Immunizations created - count: {len(immunizations)}, sample: {str(immunizations[0].__dict__ if immunizations else 'None')}")
        
        logger.info("🔄 DATA_TRANSFER: Creating medication models...")
        medications = self._create_medications(raw_data.get('medications', []))
        logger.info(f"📊 TRANSFER_RESULT: Medications created - count: {len(medications)}, sample: {str(medications[0].__dict__ if medications else 'None')}")
        
        logger.info("🔄 DATA_TRANSFER: Creating observation models...")
        observations = self._create_observations(raw_data.get('observations', []))
        logger.info(f"📊 TRANSFER_RESULT: Observations created - count: {len(observations)}, sample: {str(observations[0].__dict__ if observations else 'None')}")
        
        logger.info("🔄 DATA_TRANSFER: Creating procedure models...")
        procedures = self._create_procedures(raw_data.get('procedures', []))
        logger.info(f"📊 TRANSFER_RESULT: Procedures created - count: {len(procedures)}, sample: {str(procedures[0].__dict__ if procedures else 'None')}")
        
        logger.info("🔄 DATA_TRANSFER: Creating payer transition models...")
        payer_transitions = self._create_payer_transitions(raw_data.get('payer_transitions', []))
        logger.info(f"📊 TRANSFER_RESULT: Payer transitions created - count: {len(payer_transitions)}, sample: {str(payer_transitions[0].__dict__ if payer_transitions else 'None')}")
        
        # Step 4: Populate relationships
        logger.info("🔄 DATA_TRANSFER: Populating encounter relationships...")
        self._populate_encounter_relationships(encounters, allergies, careplans, conditions, 
                                             imaging_studies, immunizations, medications, 
                                             observations, procedures)
        logger.info(f"📊 TRANSFER_RESULT: Encounter relationships populated - encounters with relationships: {sum(1 for e in encounters if e.allergies)}")
        
        logger.info("🔄 DATA_TRANSFER: Populating patient relationships...")
        self._populate_patient_relationships(patients, payer_transitions)
        logger.info(f"📊 TRANSFER_RESULT: Patient relationships populated - patients with payer transitions: {sum(1 for p in patients if p.payer_transitions)}")
        
        # Store constructed data
        logger.info("🔄 DATA_TRANSFER: Storing constructed data in DataService instance...")
        self.patients = patients
        self.encounters = encounters
        self.organizations = organizations
        self.providers = providers
        self.payers = payers
        
        logger.info(f"✅ DATA_TRANSFER_SUCCESS: DataService.load_and_construct_data() completed - Final counts: patients={len(patients)}, encounters={len(encounters)}, organizations={len(organizations)}, providers={len(providers)}, payers={len(payers)}")
        logger.info(f"📊 FINAL_PAYLOAD_SUMMARY: {{'patients': {len(patients)}, 'encounters': {len(encounters)}, 'organizations': {len(organizations)}, 'providers': {len(providers)}, 'payers': {len(payers)}}}")
    
    def get_all_patients(self, deep: bool = False) -> List[Patient]:
        """Get all patients with optional deep relationships.
        
        Args:
            deep: If True, includes all related data (encounters, conditions, etc.)
                 If False, returns patients with basic relationships only
                 
        Returns:
            List of Patient instances with populated relationships
        """
        logger.info(f"🔄 DATA_TRANSFER_START: DataService.get_all_patients(deep={deep}) initiated")
        
        if not self.patients:
            logger.info("📊 TRANSFER_CONDITION: No patients loaded, triggering data load...")
            self.load_and_construct_data()
            
        if deep:
            logger.info("🔄 DATA_TRANSFER: Populating deep patient relationships...")
            # Add encounters to each patient with all their related medical data
            for patient in self.patients:
                patient_encounters = [enc for enc in self.encounters if enc.PATIENT == patient.Id]
                patient.encounters = patient_encounters
                logger.info(f"📊 TRANSFER_RESULT: Patient {patient.Id} populated with {len(patient_encounters)} encounters")
                # Note: encounters already have their related data populated
                # This creates the full deep relationship structure
                
        logger.info(f"✅ DATA_TRANSFER_SUCCESS: Returning {len(self.patients)} patients (deep={deep})")
        logger.info(f"📊 FINAL_PAYLOAD: {{'patient_count': {len(self.patients)}, 'deep_mode': {deep}, 'sample_patient': {str(self.patients[0].__dict__ if self.patients else 'None')}}}")
        return self.patients
    
    def _load_all_csvs(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load all CSV files into raw data dictionaries."""
        logger.info(f"🔄 DATA_TRANSFER: _load_all_csvs() scanning {self.csv_folder}")
        raw_data = {}
        csv_files = glob.glob(os.path.join(self.csv_folder, "*.csv"))
        logger.info(f"📊 TRANSFER_SOURCE: Found {len(csv_files)} CSV files: {[os.path.basename(f) for f in csv_files]}")
        
        for csv_file in csv_files:
            filename = os.path.basename(csv_file).replace(".csv", "")
            try:
                logger.info(f"🔄 DATA_TRANSFER: Loading {csv_file}...")
                df = pd.read_csv(csv_file)
                logger.info(f"📊 TRANSFER_PAYLOAD: DataFrame loaded - shape: {df.shape}, columns: {list(df.columns)}")
                
                # Convert to list of dictionaries with NaN handling
                records = []
                for _, row in df.iterrows():
                    row_dict = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
                    records.append(row_dict)
                raw_data[filename] = records
                logger.info(f"📊 TRANSFER_RESULT: {filename} converted - {len(records)} records, sample: {str(records[0] if records else 'None')}")
            except Exception as e:
                logger.error(f"❌ DATA_TRANSFER_ERROR: Error loading {csv_file}: {e}")
                
        logger.info(f"✅ DATA_TRANSFER_SUCCESS: _load_all_csvs() completed - {len(raw_data)} datasets loaded")
        return raw_data
    
    def _create_patients(self, records: List[Dict[str, Any]]) -> List[Patient]:
        """Create Patient instances from raw data."""
        patients = []
        for record in records:
            try:
                patient = Patient(**record)
                patients.append(patient)
            except Exception as e:
                logger.error(f"Error creating Patient: {e}")
        return patients
    
    def _create_encounters(self, records: List[Dict[str, Any]]) -> List[Encounter]:
        """Create Encounter instances from raw data."""
        encounters = []
        for record in records:
            try:
                encounter = Encounter(**record)
                encounters.append(encounter)
            except Exception as e:
                logger.error(f"Error creating Encounter: {e}")
        return encounters
    
    def _create_organizations(self, records: List[Dict[str, Any]]) -> List[Organization]:
        """Create Organization instances from raw data."""
        organizations = []
        for record in records:
            try:
                org = Organization(**record)
                organizations.append(org)
            except Exception as e:
                logger.error(f"Error creating Organization: {e}")
        return organizations
    
    def _create_providers(self, records: List[Dict[str, Any]]) -> List[Provider]:
        """Create Provider instances from raw data."""
        providers = []
        for record in records:
            try:
                provider = Provider(**record)
                providers.append(provider)
            except Exception as e:
                logger.error(f"Error creating Provider: {e}")
        return providers
    
    def _create_payers(self, records: List[Dict[str, Any]]) -> List[Payer]:
        """Create Payer instances from raw data."""
        payers = []
        for record in records:
            try:
                payer = Payer(**record)
                payers.append(payer)
            except Exception as e:
                logger.error(f"Error creating Payer: {e}")
        return payers
    
    def _create_allergies(self, records: List[Dict[str, Any]]) -> List[Allergy]:
        """Create Allergy instances from raw data."""
        allergies = []
        for record in records:
            try:
                allergy = Allergy(**record)
                allergies.append(allergy)
            except Exception as e:
                logger.error(f"Error creating Allergy: {e}")
        return allergies
    
    def _create_careplans(self, records: List[Dict[str, Any]]) -> List[CarePlan]:
        """Create CarePlan instances from raw data."""
        careplans = []
        for record in records:
            try:
                careplan = CarePlan(**record)
                careplans.append(careplan)
            except Exception as e:
                logger.error(f"Error creating CarePlan: {e}")
        return careplans
    
    def _create_conditions(self, records: List[Dict[str, Any]]) -> List[Condition]:
        """Create Condition instances from raw data."""
        conditions = []
        for record in records:
            try:
                condition = Condition(**record)
                conditions.append(condition)
            except Exception as e:
                logger.error(f"Error creating Condition: {e}")
        return conditions
    
    def _create_imaging_studies(self, records: List[Dict[str, Any]]) -> List[ImagingStudy]:
        """Create ImagingStudy instances from raw data."""
        studies = []
        for record in records:
            try:
                study = ImagingStudy(**record)
                studies.append(study)
            except Exception as e:
                logger.error(f"Error creating ImagingStudy: {e}")
        return studies
    
    def _create_immunizations(self, records: List[Dict[str, Any]]) -> List[Immunization]:
        """Create Immunization instances from raw data."""
        immunizations = []
        for record in records:
            try:
                immunization = Immunization(**record)
                immunizations.append(immunization)
            except Exception as e:
                logger.error(f"Error creating Immunization: {e}")
        return immunizations
    
    def _create_medications(self, records: List[Dict[str, Any]]) -> List[Medication]:
        """Create Medication instances from raw data."""
        medications = []
        for record in records:
            try:
                medication = Medication(**record)
                medications.append(medication)
            except Exception as e:
                logger.error(f"Error creating Medication: {e}")
        return medications
    
    def _create_observations(self, records: List[Dict[str, Any]]) -> List[Observation]:
        """Create Observation instances from raw data."""
        observations = []
        for record in records:
            try:
                observation = Observation(**record)
                observations.append(observation)
            except Exception as e:
                logger.error(f"Error creating Observation: {e}")
        return observations
    
    def _create_procedures(self, records: List[Dict[str, Any]]) -> List[Procedure]:
        """Create Procedure instances from raw data."""
        procedures = []
        for record in records:
            try:
                procedure = Procedure(**record)
                procedures.append(procedure)
            except Exception as e:
                logger.error(f"Error creating Procedure: {e}")
        return procedures
    
    def _create_payer_transitions(self, records: List[Dict[str, Any]]) -> List[PayerTransition]:
        """Create PayerTransition instances from raw data."""
        transitions = []
        for record in records:
            try:
                transition = PayerTransition(**record)
                transitions.append(transition)
            except Exception as e:
                logger.error(f"Error creating PayerTransition: {e}")
        return transitions
    
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