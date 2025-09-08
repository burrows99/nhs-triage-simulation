# clean_data.py
# Clean Synthea CSV output for NHS Emergency Department Bias-Aware Patient Routing Research
# Implements ECDS-aligned data processing with MTS triage assignment

import pandas as pd  # type: ignore
import numpy as np  # type: ignore
import os
import warnings
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from edsim.mts import assign_mts_triage
warnings.filterwarnings('ignore')

# --------------------------
# CONFIGURATION
# --------------------------
INPUT_DIR = './output/csv'
OUTPUT_DIR = './data/cleaned'
os.makedirs(OUTPUT_DIR, exist_ok=True)

required_files = ['patients.csv', 'encounters.csv', 'conditions.csv', 'observations.csv']
for f in required_files:
    if not os.path.exists(os.path.join(INPUT_DIR, f)):
        raise FileNotFoundError(f"Missing required file: {f}")

# --------------------------
# LOAD DATA
# --------------------------
print("Loading Synthea data...")

patients = pd.read_csv(os.path.join(INPUT_DIR, 'patients.csv'))  # type: ignore
encounters = pd.read_csv(os.path.join(INPUT_DIR, 'encounters.csv'))  # type: ignore
conditions = pd.read_csv(os.path.join(INPUT_DIR, 'conditions.csv'))  # type: ignore
observations = pd.read_csv(os.path.join(INPUT_DIR, 'observations.csv'))  # type: ignore

# Filter for emergency (Type 1) A&E encounters
ed_encounters = encounters[encounters['ENCOUNTERCLASS'] == 'emergency'].copy()  # type: ignore

# Merge with patient demographics
df = ed_encounters.merge(  # type: ignore
    patients[['Id', 'GENDER', 'RACE', 'ETHNICITY', 'BIRTHDATE']],
    left_on='PATIENT', right_on='Id', suffixes=('', '_patient')
).drop('Id_patient', axis=1)

# Calculate age from birthdate
df['age_years'] = pd.to_datetime('today').year - pd.to_datetime(df['BIRTHDATE']).dt.year  # type: ignore

# --------------------------
# NHS ECDS-ALIGNED CHIEF COMPLAINTS AND MTS TRIAGE MAPPING
# --------------------------
# Based on NHS Emergency Care Data Set (ECDS) chief complaint categories
# and Manchester Triage System clinical discriminators

# Add condition flags using centralized MTS logic
from edsim.mts import MTSTriageSystem

df['condition_keywords'] = ''

for severity, terms in MTSTriageSystem.ACUTE_KEYWORDS.items():
    mask = conditions['DESCRIPTION'].str.contains('|'.join(terms), case=False, na=False)  # type: ignore
    cond_patients = conditions[mask]['PATIENT'].unique()  # type: ignore
    df[f'has_{severity}_condition'] = df['PATIENT'].isin(cond_patients)  # type: ignore
    # Add to keyword list
    if df[f'has_{severity}_condition'].any():  # type: ignore
        df.loc[df[f'has_{severity}_condition'], 'condition_keywords'] += f"{severity}, "  # type: ignore

# --------------------------
# VITAL SIGNS (from observations)
# --------------------------
# Filter observations for vital signs during ED encounter
vitals = observations[
    observations['DESCRIPTION'].isin([
        'Systolic blood pressure', 'Diastolic blood pressure',
        'Heart rate', 'Respiratory rate', 'Oxygen saturation', 'Body temperature'
    ])
]

# Pivot to get vitals per patient
vitals_pivot = vitals.pivot_table(  # type: ignore
    index='PATIENT',
    columns='DESCRIPTION',
    values='VALUE',
    aggfunc='first'  # take first reading
)

# Convert to numeric
vitals_pivot = vitals_pivot.apply(pd.to_numeric, errors='coerce')  # type: ignore

# Merge with df
df = df.merge(vitals_pivot, left_on='PATIENT', right_on='PATIENT', how='left')  # type: ignore

# --------------------------
# MTS TRIAGE ASSIGNMENT USING CENTRALIZED LOGIC
# --------------------------
# Use centralized Manchester Triage System (MTS) logic

df['triage_level'] = df.apply(assign_mts_triage, axis=1)  # type: ignore

# --------------------------
# NHS PATHWAY-BASED RESOURCE REQUIREMENTS
# --------------------------
# Determine resource needs based on clinical pathways and NICE guidelines

# MRI Requirements - Based on NICE guidelines for stroke, head injury, and spinal conditions
df['needs_mri'] = (  # type: ignore
    df['condition_keywords'].str.contains(
        'stroke|cerebrovascular|intracranial hemorrhage|subarachnoid|head injury|spinal injury|trauma', 
        case=False, na=False
    ) |
    (df['triage_level'] == 'red') & df['condition_keywords'].str.contains(
        'neurological|seizure|altered consciousness', case=False, na=False
    )
)

# Ultrasound Requirements - Abdominal presentations and cardiac assessments
df['needs_ultrasound'] = (  # type: ignore
    df['condition_keywords'].str.contains(
        'abdominal pain|appendicitis|gallbladder|renal colic|ectopic pregnancy|aortic aneurysm', 
        case=False, na=False
    ) |
    (df['triage_level'].isin(['red', 'orange'])) & df['condition_keywords'].str.contains(
        'chest pain|dyspnea|cardiac', case=False, na=False
    )
)

# CT Scan Requirements (for future expansion)
df['needs_ct'] = (  # type: ignore
    df['condition_keywords'].str.contains(
        'pulmonary embolism|aortic dissection|major trauma|severe abdominal pain', 
        case=False, na=False
    )
)

# Doctor Assessment - All patients require clinical assessment unless direct pathway indicated
df['needs_doctor'] = True  # Default - can be bypassed by intelligent routing

# Bed Requirements - Based on triage level and expected length of stay
df['needs_bed'] = (  # type: ignore
    (df['triage_level'].isin(['red', 'orange'])) |  # High acuity always needs bed
    (df['triage_level'] == 'yellow') & df['condition_keywords'].str.contains(
        'fracture|pneumonia|dehydration|infection', case=False, na=False
    )  # Yellow with conditions requiring observation
)

# Specialist Referral Requirements
df['needs_specialist'] = (  # type: ignore
    (df['triage_level'] == 'red') |
    df['condition_keywords'].str.contains(
        'cardiac|stroke|trauma|psychiatric|overdose', case=False, na=False
    )
)

# Ground Truth for Routing Evaluation
# Optimal pathway: Red + MRI should bypass doctor and go direct to MRI
df['optimal_direct_mri'] = (  # type: ignore
    (df['triage_level'] == 'red') & 
    df['needs_mri'] & 
    df['condition_keywords'].str.contains('stroke|head injury|intracranial', case=False, na=False)
)

# Ground truth routing decision for evaluation
df['ground_truth_route'] = df.apply(  # type: ignore
    lambda x: 'mri' if x['optimal_direct_mri'] else 'doctor', axis=1
)

# --------------------------
# NHS CLINICAL FRAILTY SCALE (CFS) SIMULATION
# --------------------------
# Based on NHS England frailty identification requirements (Dec 2024)
# Simulates CFS scores 1-9 based on age, chronic conditions, and functional status

# Identify chronic conditions associated with frailty
frailty_conditions = conditions[conditions['DESCRIPTION'].str.contains(  # type: ignore
    'diabetes|chronic kidney disease|heart failure|dementia|COPD|stroke|arthritis|osteoporosis|depression', 
    case=False, na=False
)]
chronic_patients = frailty_conditions['PATIENT'].unique()  # type: ignore

# Age-based frailty risk stratification
df['age_65_plus'] = df['age_years'] >= 65
df['age_75_plus'] = df['age_years'] >= 75
df['age_85_plus'] = df['age_years'] >= 85
df['has_chronic'] = df['PATIENT'].isin(chronic_patients)

# Count chronic conditions per patient
chronic_counts = frailty_conditions.groupby('PATIENT').size().reset_index(name='chronic_count')  # type: ignore
df = df.merge(chronic_counts, left_on='PATIENT', right_on='PATIENT', how='left')  # type: ignore
df['chronic_count'] = df['chronic_count'].fillna(0)  # type: ignore

# Simulate Clinical Frailty Scale (1-9)
def assign_cfs_score(row):
    """Assign Clinical Frailty Scale score based on age and comorbidities"""
    age = row['age_years']
    chronic_count = row['chronic_count']
    
    if age < 65:
        return np.random.choice([1, 2, 3], p=[0.7, 0.2, 0.1])  # Mostly fit
    elif age < 75:
        if chronic_count == 0:
            return np.random.choice([2, 3, 4], p=[0.5, 0.3, 0.2])
        elif chronic_count <= 2:
            return np.random.choice([3, 4, 5], p=[0.3, 0.4, 0.3])
        else:
            return np.random.choice([4, 5, 6], p=[0.2, 0.4, 0.4])
    elif age < 85:
        if chronic_count == 0:
            return np.random.choice([3, 4, 5], p=[0.3, 0.4, 0.3])
        elif chronic_count <= 2:
            return np.random.choice([4, 5, 6], p=[0.2, 0.4, 0.4])
        else:
            return np.random.choice([5, 6, 7], p=[0.2, 0.4, 0.4])
    else:  # 85+
        if chronic_count <= 1:
            return np.random.choice([4, 5, 6], p=[0.2, 0.3, 0.5])
        elif chronic_count <= 3:
            return np.random.choice([5, 6, 7], p=[0.2, 0.4, 0.4])
        else:
            return np.random.choice([6, 7, 8], p=[0.2, 0.4, 0.4])

np.random.seed(42)  # For reproducibility
df['cfs_score'] = df.apply(assign_cfs_score, axis=1)  # type: ignore

# Define frailty categories based on CFS
df['frailty_category'] = df['cfs_score'].map({  # type: ignore
    1: 'Very Fit', 2: 'Well', 3: 'Managing Well', 4: 'Vulnerable',
    5: 'Mildly Frail', 6: 'Moderately Frail', 7: 'Severely Frail',
    8: 'Very Severely Frail', 9: 'Terminally Ill'
})

# Binary frailty indicator (CFS >= 5 indicates frailty)
df['simulated_frailty'] = df['cfs_score'] >= 5

# Additional demographic factors for bias analysis
df['vulnerable_population'] = (  # type: ignore
    df['simulated_frailty'] | 
    (df['age_years'] >= 75) | 
    df['condition_keywords'].str.contains('dementia|psychiatric', case=False, na=False)
)

# --------------------------
# SELECT FINAL COLUMNS FOR NHS ECDS-ALIGNED DATASET
# --------------------------
columns = [
    # Core identifiers and timestamps
    'Id', 'START', 'END', 'PATIENT', 'ORGANIZATION',
    
    # Demographics (ECDS required fields)
    'GENDER', 'RACE', 'ETHNICITY', 'age_years',
    
    # Clinical assessment
    'triage_level', 'condition_keywords',
    
    # Resource requirements (for routing evaluation)
    'needs_mri', 'needs_ultrasound', 'needs_ct', 'needs_doctor', 'needs_bed', 'needs_specialist',
    
    # Routing ground truth
    'optimal_direct_mri', 'ground_truth_route',
    
    # Frailty and vulnerability (NHS CFS requirements)
    'cfs_score', 'frailty_category', 'simulated_frailty', 'vulnerable_population',
    'age_65_plus', 'age_75_plus', 'age_85_plus', 'chronic_count',
    
    # Vital signs (clinical discriminators)
    'Systolic blood pressure', 'Diastolic blood pressure', 'Heart rate', 
    'Respiratory rate', 'Oxygen saturation', 'Body temperature'
]

# Filter to available columns
available_columns = [col for col in columns if col in df.columns]
df_final = df[available_columns].copy()

# Rename columns to match ECDS standards
df_final.rename(columns={  # type: ignore
    'Id': 'encounter_id',
    'START': 'arrival_time',
    'END': 'departure_time',
    'PATIENT': 'patient_id',
    'ORGANIZATION': 'provider_org',
    'GENDER': 'gender',
    'RACE': 'ethnicity_code',
    'ETHNICITY': 'ethnicity_detail'
}, inplace=True)

# Add derived fields for analysis
df_final['dataset_version'] = '1.0'
df_final['processing_date'] = pd.Timestamp.now().strftime('%Y-%m-%d')
df_final['source'] = 'synthea_massachusetts'

# --------------------------
# SAVE CLEANED DATASET
# --------------------------
# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

output_path = os.path.join(OUTPUT_DIR, 'nhs_ecds_aligned_routing_dataset.csv')
df_final.to_csv(output_path, index=False)  # type: ignore

# Save summary statistics
summary_stats = {
    'total_encounters': len(df_final),
    'unique_patients': df_final['patient_id'].nunique() if 'patient_id' in df_final.columns else 'N/A',
    'triage_distribution': df_final['triage_level'].value_counts().to_dict(),
    'age_distribution': {
        'mean_age': df_final['age_years'].mean(),  # type: ignore
        'age_65_plus': (df_final['age_years'] >= 65).sum(),  # type: ignore
        'age_75_plus': (df_final['age_years'] >= 75).sum()  # type: ignore
    },
    'frailty_distribution': df_final['frailty_category'].value_counts().to_dict() if 'frailty_category' in df_final.columns else {},
    'resource_requirements': {
        'needs_mri': df_final['needs_mri'].sum() if 'needs_mri' in df_final.columns else 0,
        'needs_ultrasound': df_final['needs_ultrasound'].sum() if 'needs_ultrasound' in df_final.columns else 0,
        'optimal_direct_mri': df_final['optimal_direct_mri'].sum() if 'optimal_direct_mri' in df_final.columns else 0
    },
    'bias_analysis_ready': {
        'gender_categories': df_final['gender'].nunique() if 'gender' in df_final.columns else 0,
        'ethnicity_categories': df_final['ethnicity_code'].nunique() if 'ethnicity_code' in df_final.columns else 0,
        'vulnerable_population': df_final['vulnerable_population'].sum() if 'vulnerable_population' in df_final.columns else 0
    }
}

# Save summary
import json
summary_path = os.path.join(OUTPUT_DIR, 'dataset_summary.json')
with open(summary_path, 'w') as f:
    json.dump(summary_stats, f, indent=2, default=str)

# --------------------------
# DISPLAY RESULTS
# --------------------------
print("\n" + "="*80)
print("🏥 NHS EMERGENCY DEPARTMENT BIAS-AWARE ROUTING DATASET")
print("="*80)
print(f"✅ Cleaned dataset saved to: {output_path}")
print(f"📊 Dataset shape: {df_final.shape}")
print(f"🔢 Unique encounters: {summary_stats['total_encounters']}")
print(f"👥 Unique patients: {summary_stats['unique_patients']}")

print(f"\n🚨 TRIAGE DISTRIBUTION (MTS-aligned):")
for level, count in summary_stats['triage_distribution'].items():
    percentage = (count / summary_stats['total_encounters']) * 100
    print(f"   {level.upper()}: {count:,} ({percentage:.1f}%)")

print(f"\n🧓 AGE & FRAILTY ANALYSIS:")
print(f"   Mean age: {summary_stats['age_distribution']['mean_age']:.1f} years")
print(f"   Age 65+: {summary_stats['age_distribution']['age_65_plus']:,} patients")
print(f"   Age 75+: {summary_stats['age_distribution']['age_75_plus']:,} patients")

if summary_stats['frailty_distribution']:
    print(f"\n🦽 CLINICAL FRAILTY SCALE DISTRIBUTION:")
    for category, count in summary_stats['frailty_distribution'].items():
        percentage = (count / summary_stats['total_encounters']) * 100
        print(f"   {category}: {count:,} ({percentage:.1f}%)")

print(f"\n🔬 RESOURCE REQUIREMENTS:")
print(f"   MRI needed: {summary_stats['resource_requirements']['needs_mri']:,} patients")
print(f"   Ultrasound needed: {summary_stats['resource_requirements']['needs_ultrasound']:,} patients")
print(f"   Optimal direct MRI: {summary_stats['resource_requirements']['optimal_direct_mri']:,} patients")

print(f"\n⚖️  BIAS ANALYSIS READINESS:")
print(f"   Gender categories: {summary_stats['bias_analysis_ready']['gender_categories']}")
print(f"   Ethnicity categories: {summary_stats['bias_analysis_ready']['ethnicity_categories']}")
print(f"   Vulnerable population: {summary_stats['bias_analysis_ready']['vulnerable_population']:,} patients")

print(f"\n📋 Summary statistics saved to: {summary_path}")
print("\n🎯 Dataset ready for Mixture-of-Agents routing evaluation and bias analysis!")
print("="*80)