#!/usr/bin/env python3
"""
NHS Emergency Department Bias Analysis

Analyzes routing decisions and bias across demographic groups in emergency department
patient routing. Evaluates fairness metrics and identifies potential disparities
in care delivery across different patient populations.

Author: Research Team
Date: December 2024
Version: 1.0
"""

import pandas as pd  # type: ignore
import numpy as np  # type: ignore
import os
import json
from typing import Dict, Any

# --------------------------
# CONFIGURATION
# --------------------------
CLEANED_DATA_PATH = './data/cleaned/nhs_ecds_aligned_routing_dataset.csv'
RESULTS_OUTPUT_DIR = './data/analysis'
os.makedirs(RESULTS_OUTPUT_DIR, exist_ok=True)

def load_and_prepare_data() -> pd.DataFrame:
    """
    Load and prepare the cleaned dataset for bias analysis.
    
    Returns:
        pd.DataFrame: Prepared dataset with routing decisions
    """
    if not os.path.exists(CLEANED_DATA_PATH):
        raise FileNotFoundError(f"Cleaned dataset not found at {CLEANED_DATA_PATH}")
    
    print(f"📊 Loading dataset from {CLEANED_DATA_PATH}...")
    df = pd.read_csv(CLEANED_DATA_PATH)  # type: ignore
    
    print(f"✅ Loaded {len(df)} patient encounters")
    print(f"📋 Dataset columns: {list(df.columns)}")
    
    return df

def compute_demographic_statistics(data: pd.DataFrame, group_col: str) -> Dict[str, Any]:
    """
    Compute demographic statistics for a given grouping column.
    
    Args:
        data: DataFrame with patient data
        group_col: Column name to group by (e.g., 'gender', 'ethnicity_code')
    
    Returns:
        Dict containing demographic statistics
    """
    if group_col not in data.columns:
        return {'error': f'Column {group_col} not found in dataset'}
    
    results = []
    groups = data[group_col].dropna().unique()  # type: ignore
    
    for group in groups:
        subgroup = data[data[group_col] == group]  # type: ignore
        
        # Basic demographics
        count = len(subgroup)  # type: ignore
        mean_age = subgroup['age_years'].mean() if 'age_years' in subgroup.columns else None  # type: ignore
        
        # Triage distribution
        triage_dist = subgroup['triage_level'].value_counts().to_dict() if 'triage_level' in subgroup.columns else {}  # type: ignore
        
        # Resource needs
        needs_mri = subgroup['needs_mri'].sum() if 'needs_mri' in subgroup.columns else 0  # type: ignore
        needs_ultrasound = subgroup['needs_ultrasound'].sum() if 'needs_ultrasound' in subgroup.columns else 0  # type: ignore
        
        # Frailty indicators
        vulnerable_pop = subgroup['vulnerable_population'].sum() if 'vulnerable_population' in subgroup.columns else 0  # type: ignore
        
        # Optimal routing
        optimal_direct_mri = subgroup['optimal_direct_mri'].sum() if 'optimal_direct_mri' in subgroup.columns else 0  # type: ignore
        
        results.append({  # type: ignore
            'group': str(group),  # type: ignore
            'count': count,
            'percentage': (count / len(data)) * 100,
            'mean_age': mean_age,
            'triage_distribution': triage_dist,
            'needs_mri': int(needs_mri),  # type: ignore
            'needs_ultrasound': int(needs_ultrasound),  # type: ignore
            'vulnerable_population': int(vulnerable_pop),  # type: ignore
            'optimal_direct_mri': int(optimal_direct_mri),  # type: ignore
            'mri_rate': (int(needs_mri) / count * 100) if count > 0 else 0,  # type: ignore
            'ultrasound_rate': (int(needs_ultrasound) / count * 100) if count > 0 else 0,  # type: ignore
            'vulnerability_rate': (int(vulnerable_pop) / count * 100) if count > 0 else 0  # type: ignore
        })
    
    return {
        'group_column': group_col,
        'total_patients': len(data),
        'groups': results,
        'summary': {
            'num_groups': len(groups),  # type: ignore
            'largest_group': max(results, key=lambda x: x['count'])['group'] if results else None,  # type: ignore
            'smallest_group': min(results, key=lambda x: x['count'])['group'] if results else None  # type: ignore
        }
    }


def analyze_resource_allocation_bias(data: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze potential bias in resource allocation across demographic groups.
    
    Args:
        data: DataFrame with patient data
    
    Returns:
        Dict containing bias analysis results
    """
    analysis_results = {}
    
    # Demographic columns to analyze
    demographic_cols = ['gender', 'ethnicity_code', 'ethnicity_detail']
    
    for col in demographic_cols:
        if col in data.columns:
            print(f"\n🔍 Analyzing bias by {col.upper()}...")
            stats = compute_demographic_statistics(data, col)
            analysis_results[col] = stats
            
            # Print summary
            if 'groups' in stats:
                print(f"   Found {len(stats['groups'])} groups:")
                for group_data in stats['groups']:
                    print(f"   • {group_data['group']}: {group_data['count']} patients ({group_data['percentage']:.1f}%)")
                    print(f"     - MRI rate: {group_data['mri_rate']:.1f}%")
                    print(f"     - Vulnerability rate: {group_data['vulnerability_rate']:.1f}%")
    
    return analysis_results


def analyze_triage_fairness(data: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze fairness in triage assignment across demographic groups.
    
    Args:
        data: DataFrame with patient data
    
    Returns:
        Dict containing triage fairness analysis
    """
    if 'triage_level' not in data.columns:
        return {'error': 'Triage level column not found'}
    
    fairness_results = {}
    
    # Overall triage distribution
    overall_triage = data['triage_level'].value_counts().to_dict()  # type: ignore
    fairness_results['overall_distribution'] = overall_triage
    
    # Analyze by demographic groups
    demographic_cols = ['gender', 'ethnicity_code']
    
    for col in demographic_cols:
        if col in data.columns:
            group_analysis = []
            groups = data[col].dropna().unique()  # type: ignore
            
            for group in groups:
                subgroup = data[data[col] == group]  # type: ignore
                triage_dist = subgroup['triage_level'].value_counts(normalize=True).to_dict()  # type: ignore
                
                # Calculate high-acuity rate (red + orange)
                high_acuity_rate = (
                    triage_dist.get('red', 0) + triage_dist.get('orange', 0)  # type: ignore
                ) * 100
                
                group_analysis.append({  # type: ignore
                    'group': str(group),  # type: ignore
                    'count': len(subgroup),  # type: ignore
                    'triage_distribution': triage_dist,
                    'high_acuity_rate': float(high_acuity_rate)  # type: ignore
                })
            
            fairness_results[col] = group_analysis
    
    return fairness_results

def generate_bias_report(data: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate comprehensive bias analysis report.
    
    Args:
        data: DataFrame with patient data
    
    Returns:
        Dict containing complete bias analysis
    """
    print("\n" + "="*80)
    print("🏥 NHS EMERGENCY DEPARTMENT BIAS ANALYSIS REPORT")
    print("="*80)
    
    report = {
        'dataset_summary': {
            'total_encounters': len(data),
            'unique_patients': data['patient_id'].nunique() if 'patient_id' in data.columns else None,  # type: ignore
            'date_range': {
                'start': data['arrival_time'].min() if 'arrival_time' in data.columns else None,  # type: ignore
                'end': data['arrival_time'].max() if 'arrival_time' in data.columns else None  # type: ignore
            }
        }
    }
    
    print(f"📊 Dataset Overview:")
    print(f"   Total encounters: {report['dataset_summary']['total_encounters']:,}")
    if report['dataset_summary']['unique_patients']:  # type: ignore
        print(f"   Unique patients: {report['dataset_summary']['unique_patients']:,}")
    
    # Demographic analysis
    print(f"\n🧍 Demographic Analysis:")
    demographic_analysis = analyze_resource_allocation_bias(data)
    report['demographic_analysis'] = demographic_analysis
    
    # Triage fairness analysis
    print(f"\n🚨 Triage Fairness Analysis:")
    triage_analysis = analyze_triage_fairness(data)
    report['triage_fairness'] = triage_analysis
    
    # Resource allocation analysis
    print(f"\n🔬 Resource Allocation Analysis:")
    if 'needs_mri' in data.columns and 'needs_ultrasound' in data.columns:
        total_mri = data['needs_mri'].sum()  # type: ignore
        total_ultrasound = data['needs_ultrasound'].sum()  # type: ignore
        total_optimal_mri = data['optimal_direct_mri'].sum() if 'optimal_direct_mri' in data.columns else 0  # type: ignore
        
        print(f"   MRI requirements: {int(total_mri)} patients ({int(total_mri)/len(data)*100:.1f}%)")  # type: ignore
        print(f"   Ultrasound requirements: {int(total_ultrasound)} patients ({int(total_ultrasound)/len(data)*100:.1f}%)")  # type: ignore
        print(f"   Optimal direct MRI cases: {int(total_optimal_mri)} patients ({int(total_optimal_mri)/len(data)*100:.1f}%)")  # type: ignore
        
        report['resource_allocation'] = {
            'mri_total': int(total_mri),  # type: ignore
            'ultrasound_total': int(total_ultrasound),  # type: ignore
            'optimal_direct_mri': int(total_optimal_mri),  # type: ignore
            'mri_rate': float(int(total_mri)/len(data)*100),  # type: ignore
            'ultrasound_rate': float(int(total_ultrasound)/len(data)*100)  # type: ignore
        }
    
    return report

def save_analysis_results(report: Dict[str, Any]) -> None:
    """
    Save analysis results to files.
    
    Args:
        report: Complete bias analysis report
    """
    # Save JSON report
    json_path = os.path.join(RESULTS_OUTPUT_DIR, 'bias_analysis_report.json')
    with open(json_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n💾 Analysis results saved:")
    print(f"   📄 JSON report: {json_path}")
    
    # Save demographic summary CSV
    if 'demographic_analysis' in report:
        for demo_col, demo_data in report['demographic_analysis'].items():
            if 'groups' in demo_data:
                df_demo = pd.DataFrame(demo_data['groups'])  # type: ignore
                csv_path = os.path.join(RESULTS_OUTPUT_DIR, f'demographic_analysis_{demo_col}.csv')
                df_demo.to_csv(csv_path, index=False)  # type: ignore
                print(f"   📊 {demo_col} analysis: {csv_path}")


def main() -> None:
    """
    Main analysis function.
    """
    try:
        # Load data
        data = load_and_prepare_data()
        
        # Generate comprehensive bias report
        report = generate_bias_report(data)
        
        # Save results
        save_analysis_results(report)
        
        print(f"\n✅ Bias analysis completed successfully!")
        print(f"🎯 Key findings:")
        print(f"   • Analyzed {report['dataset_summary']['total_encounters']:,} patient encounters")
        if 'demographic_analysis' in report:
            print(f"   • Examined {len(report['demographic_analysis'])} demographic dimensions")
        if 'resource_allocation' in report:
            print(f"   • MRI utilization rate: {report['resource_allocation']['mri_rate']:.1f}%")
            print(f"   • Ultrasound utilization rate: {report['resource_allocation']['ultrasound_rate']:.1f}%")
        
        print(f"\n📋 Next steps:")
        print(f"   1. Review demographic disparities in resource allocation")
        print(f"   2. Examine triage fairness across patient groups")
        print(f"   3. Identify opportunities for bias mitigation")
        print(f"   4. Implement routing algorithm improvements")
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        raise


if __name__ == '__main__':
    main()