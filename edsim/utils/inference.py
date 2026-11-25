from typing import Dict, List, Union
import numpy as np
from numpy.typing import NDArray

from ..constants import (
    RESOURCES,
    SERVICE_TIMES,
    WAIT_HIGH_FACTOR,
    WAIT_LOW_FACTOR,
    UTIL_HIGH_THRESHOLD,
    UTIL_LOW_THRESHOLD,
    MAX_QUEUE_THRESHOLD,
)


def generate_inferences(
    stats: Dict[str, Dict[str, float]],
    queue_arr: NDArray[np.float64],
    util: Dict[str, float],
    urgent_stats: Dict[str, float],
    mock_eval: Dict[str, Union[float, int, str]],
) -> List[str]:
    inf: List[str] = []
    
    # Header with simulation overview
    inf.append("=== DETAILED SIMULATION ANALYSIS ===")
    inf.append("")
    
    # Resource-specific detailed analysis
    inf.append("--- RESOURCE PERFORMANCE ANALYSIS ---")
    for r_idx, r in enumerate(RESOURCES):
        inf.append(f"\n{r.upper()} RESOURCE:")
        
        avg = stats[r]['avg']
        median = stats[r]['median']
        service_mean = SERVICE_TIMES[r]
        
        # Wait time analysis
        inf.append(f"  Wait Times: Average {avg:.2f} min, Median {median:.2f} min (Service time: {service_mean} min)")
        
        wait_ratio = avg / service_mean if service_mean > 0 else 0
        if avg > service_mean * WAIT_HIGH_FACTOR:
            inf.append(f"  ⚠️  HIGH WAIT TIME: {wait_ratio:.2f}x service time (threshold: {WAIT_HIGH_FACTOR}x)")
            inf.append(f"      This indicates potential bottleneck - consider increasing capacity")
        elif avg < service_mean * WAIT_LOW_FACTOR:
            inf.append(f"  ✅ LOW WAIT TIME: {wait_ratio:.2f}x service time (threshold: {WAIT_LOW_FACTOR}x)")
            inf.append(f"      Efficient service delivery with minimal delays")
        else:
            inf.append(f"  📊 MODERATE WAIT TIME: {wait_ratio:.2f}x service time - within acceptable range")
        
        # Queue analysis
        if queue_arr.size > 0:
            queue_data = queue_arr[:, r_idx + 1]
            max_queue = np.max(queue_data)
            avg_queue = np.mean(queue_data)
            queue_std = np.std(queue_data)
            
            inf.append(f"  Queue Statistics: Max {max_queue:.0f}, Average {avg_queue:.2f}, Std Dev {queue_std:.2f}")
            
            if max_queue > MAX_QUEUE_THRESHOLD:
                inf.append(f"  ⚠️  HIGH QUEUE PEAK: {max_queue:.0f} patients (threshold: {MAX_QUEUE_THRESHOLD})")
                inf.append(f"      Queue variability suggests demand spikes - consider load balancing")
            else:
                inf.append(f"  ✅ MANAGEABLE QUEUES: Peak within acceptable limits")
        
        # Utilization analysis
        inf.append(f"  Utilization: {util[r]:.2f}%")
        if util[r] > UTIL_HIGH_THRESHOLD:
            inf.append(f"  ⚠️  HIGH UTILIZATION: Risk of service degradation and longer waits")
            inf.append(f"      Recommendation: Increase capacity or optimize workflow")
        elif util[r] < UTIL_LOW_THRESHOLD:
            inf.append(f"  📉 LOW UTILIZATION: Potential for resource optimization")
            inf.append(f"      Recommendation: Consider capacity reduction or workload redistribution")
        else:
            inf.append(f"  ✅ OPTIMAL UTILIZATION: Good balance between efficiency and service quality")
    
    # Comprehensive routing analysis
    inf.append("\n--- COMPREHENSIVE PATIENT ROUTING ANALYSIS ---")
    
    # Analyze all routing patterns from the patient data
    # Get all patients from the mock_eval data (we need to access the patients list)
    # For now, we'll work with the urgent stats and expand the analysis
    total = int(urgent_stats['total'])
    bypassed = int(urgent_stats['bypassed'])
    rate = float(urgent_stats['bypass_rate'])
    
    inf.append(f"🚨 URGENT MRI CASES ANALYSIS:")
    inf.append(f"  Total Urgent Cases: {total} patients (red triage + MRI needed)")
    inf.append(f"  Direct MRI Routing: {bypassed} patients bypassed doctor ({rate:.1f}% bypass rate)")
    inf.append(f"  Doctor-First Routing: {total - bypassed} patients went to doctor first ({100-rate:.1f}%)")
    
    if rate > 80:
        inf.append(f"  ✅ EXCELLENT URGENT ROUTING: High bypass rate optimizes critical care workflow")
    elif rate > 50:
        inf.append(f"  📊 GOOD URGENT ROUTING: Moderate bypass rate with room for improvement")
    elif rate > 20:
        inf.append(f"  ⚠️  SUBOPTIMAL URGENT ROUTING: Low bypass rate may delay critical care")
    else:
        inf.append(f"  ❌ POOR URGENT ROUTING: Very low bypass rate significantly delays critical care")
    
    # Comprehensive routing pathway analysis using the new data
    total_patients = int(mock_eval.get('total_patients', 0))
    doctor_only = int(mock_eval.get('doctor_only', 0))
    doctor_mri_bed = int(mock_eval.get('doctor_mri_bed', 0))
    doctor_ultrasound_bed = int(mock_eval.get('doctor_ultrasound_bed', 0))
    doctor_both_imaging_bed = int(mock_eval.get('doctor_both_imaging_bed', 0))
    direct_mri = int(mock_eval.get('direct_mri', 0))
    direct_ultrasound = int(mock_eval.get('direct_ultrasound', 0))
    
    inf.append(f"\n📋 COMPREHENSIVE ROUTING PATHWAY ANALYSIS:")
    inf.append(f"  Total Patients Processed: {total_patients}")
    inf.append(f"")
    inf.append(f"  🏥 ROUTING PATHWAYS BREAKDOWN:")
    
    if total_patients > 0:
        inf.append(f"    • Doctor-Only Path: {doctor_only} patients ({doctor_only/total_patients*100:.1f}%)")
        inf.append(f"      └─ No imaging required, direct to bed after doctor consultation")
        
        inf.append(f"    • Doctor → MRI → Bed: {doctor_mri_bed} patients ({doctor_mri_bed/total_patients*100:.1f}%)")
        inf.append(f"      └─ Standard MRI pathway through doctor first")
        
        inf.append(f"    • Doctor → Ultrasound → Bed: {doctor_ultrasound_bed} patients ({doctor_ultrasound_bed/total_patients*100:.1f}%)")
        inf.append(f"      └─ Standard ultrasound pathway through doctor first")
        
        inf.append(f"    • Doctor → Both Imaging → Bed: {doctor_both_imaging_bed} patients ({doctor_both_imaging_bed/total_patients*100:.1f}%)")
        inf.append(f"      └─ Complex cases requiring both MRI and ultrasound")
        
        inf.append(f"    • Direct MRI Access: {direct_mri} patients ({direct_mri/total_patients*100:.1f}%)")
        inf.append(f"      └─ Bypassed doctor consultation for urgent cases")
        
        inf.append(f"    • Direct Ultrasound Access: {direct_ultrasound} patients ({direct_ultrasound/total_patients*100:.1f}%)")
        inf.append(f"      └─ Direct ultrasound routing (if implemented)")
    
    # Triage distribution analysis
    triage_red = int(mock_eval.get('triage_red', 0))
    triage_orange = int(mock_eval.get('triage_orange', 0))
    triage_yellow = int(mock_eval.get('triage_yellow', 0))
    triage_green = int(mock_eval.get('triage_green', 0))
    triage_blue = int(mock_eval.get('triage_blue', 0))
    
    inf.append(f"\n  🚨 TRIAGE DISTRIBUTION:")
    if total_patients > 0:
        inf.append(f"    • Red (Critical): {triage_red} patients ({triage_red/total_patients*100:.1f}%)")
        inf.append(f"    • Orange (Urgent): {triage_orange} patients ({triage_orange/total_patients*100:.1f}%)")
        inf.append(f"    • Yellow (Less Urgent): {triage_yellow} patients ({triage_yellow/total_patients*100:.1f}%)")
        inf.append(f"    • Green (Non-Urgent): {triage_green} patients ({triage_green/total_patients*100:.1f}%)")
        inf.append(f"    • Blue (Lowest Priority): {triage_blue} patients ({triage_blue/total_patients*100:.1f}%)")
    
    # Imaging needs analysis
    mri_needed = int(mock_eval.get('mri_needed', 0))
    ultrasound_needed = int(mock_eval.get('ultrasound_needed', 0))
    both_imaging = int(mock_eval.get('both_imaging', 0))
    no_imaging = int(mock_eval.get('no_imaging', 0))
    
    inf.append(f"\n  🔬 IMAGING REQUIREMENTS:")
    if total_patients > 0:
        inf.append(f"    • MRI Required: {mri_needed} patients ({mri_needed/total_patients*100:.1f}%)")
        inf.append(f"    • Ultrasound Required: {ultrasound_needed} patients ({ultrasound_needed/total_patients*100:.1f}%)")
        inf.append(f"    • Both Imaging Required: {both_imaging} patients ({both_imaging/total_patients*100:.1f}%)")
        inf.append(f"    • No Imaging Required: {no_imaging} patients ({no_imaging/total_patients*100:.1f}%)")
    
    # Routing efficiency analysis
    inf.append(f"\n  📊 ROUTING EFFICIENCY INSIGHTS:")
    if direct_ultrasound > 0:
        inf.append(f"    ✅ Direct ultrasound routing is implemented and utilized")
    else:
        inf.append(f"    📝 Direct ultrasound routing not implemented - all ultrasound via doctor")
    
    if doctor_only > 0:
        inf.append(f"    ✅ Efficient doctor-only pathway for {doctor_only} patients requiring no imaging")
    
    if both_imaging > 0:
        inf.append(f"    🔄 Complex cases: {both_imaging} patients required multiple imaging modalities")
    
    # Recommendations based on pathway analysis
    inf.append(f"\n  💡 PATHWAY OPTIMIZATION RECOMMENDATIONS:")
    if direct_ultrasound == 0 and ultrasound_needed > 0:
        inf.append(f"    • Consider implementing direct ultrasound routing for appropriate cases")
    if direct_mri/total_patients < 0.1 and mri_needed > 0:
        inf.append(f"    • Evaluate opportunities for more direct MRI access beyond urgent cases")
    if doctor_only/total_patients > 0.5:
        inf.append(f"    • High proportion of doctor-only cases - ensure adequate doctor capacity")
    if both_imaging > 0:
        inf.append(f"    • Optimize scheduling for patients requiring multiple imaging studies")
    
    # Model accuracy analysis
    inf.append("\n--- MODEL ACCURACY EVALUATION ---")
    sim_acc = float(mock_eval['simulated_accuracy'])
    set_factor = float(mock_eval['set_factor'])
    diff = float(mock_eval['difference'])
    total_urgent = int(mock_eval['total_urgent'])
    correct = int(mock_eval['correct_bypasses'])
    
    inf.append(f"Routing Accuracy Assessment:")
    inf.append(f"  Simulated Accuracy: {sim_acc:.1%}")
    inf.append(f"  Expected Accuracy: {set_factor:.1%}")
    inf.append(f"  Accuracy Difference: {diff:.3f} ({abs(diff/set_factor*100):.1f}% deviation)" if set_factor > 0 else f"  Accuracy Difference: {diff:.3f}")
    inf.append(f"  Sample Size: {total_urgent} urgent cases evaluated")
    inf.append(f"  Correct Decisions: {correct} out of {total_urgent} cases")
    
    if diff < 0.05:
        inf.append(f"✅ EXCELLENT MODEL PERFORMANCE: Accuracy very close to expected")
    elif diff < 0.15:
        inf.append(f"📊 GOOD MODEL PERFORMANCE: Accuracy reasonably close to expected")
    elif diff < 0.25:
        inf.append(f"⚠️  MODERATE MODEL PERFORMANCE: Some deviation from expected accuracy")
    else:
        inf.append(f"❌ POOR MODEL PERFORMANCE: Significant deviation from expected accuracy")
    
    # Technical note
    note = str(mock_eval['note'])
    inf.append(f"\nTechnical Note: {note}")
    
    return inf


def generate_comparison_inferences(
    results_wait: Dict[str, Dict[str, float]],
    results_util: Dict[str, Dict[str, float]],
    results_urgent: Dict[str, Dict[str, float]],
    results_mock: Dict[str, Dict[str, Union[float, int, str]]],
) -> List[str]:
    scenarios = list(results_wait.keys())
    comp_inf: List[str] = []
    
    comp_inf.append("=== COMPREHENSIVE SCENARIO COMPARISON ===")
    comp_inf.append(f"Comparing {len(scenarios)} scenarios: {', '.join(scenarios)}")
    comp_inf.append("")
    
    # Resource-by-resource detailed comparison
    comp_inf.append("--- RESOURCE PERFORMANCE COMPARISON ---")
    
    # Initialize variables for later use
    wait_data = []
    bypass_data = []
    diff_data = []
    
    for r in RESOURCES:
        comp_inf.append(f"\n{r.upper()} RESOURCE COMPARISON:")
        
        # Wait time comparison
        avg_waits = [results_wait[sc][r] for sc in scenarios]
        wait_data = list(zip(scenarios, avg_waits))
        wait_data.sort(key=lambda x: x[1])  # Sort by wait time
        
        comp_inf.append(f"  Wait Time Ranking (best to worst):")
        for i, (sc, wait) in enumerate(wait_data, 1):
            improvement = ""
            if i == 1:
                improvement = " 🏆 BEST"
            elif i == len(wait_data):
                improvement = " ❌ WORST"
            comp_inf.append(f"    {i}. {sc}: {wait:.2f} min{improvement}")
        
        # Calculate performance differences
        best_wait = wait_data[0][1]
        worst_wait = wait_data[-1][1]
        if best_wait > 0:
            improvement_pct = ((worst_wait - best_wait) / best_wait) * 100
            comp_inf.append(f"  Performance Gap: {improvement_pct:.1f}% difference between best and worst")
        
        # Utilization comparison
        utils = [results_util[sc][r] for sc in scenarios]
        util_data = list(zip(scenarios, utils))
        util_data.sort(key=lambda x: x[1], reverse=True)  # Sort by utilization (high to low)
        
        comp_inf.append(f"  Utilization Ranking (highest to lowest):")
        for i, (sc, util_val) in enumerate(util_data, 1):
            status = ""
            if util_val > UTIL_HIGH_THRESHOLD:
                status = " ⚠️  HIGH"
            elif util_val < UTIL_LOW_THRESHOLD:
                status = " 📉 LOW"
            else:
                status = " ✅ OPTIMAL"
            comp_inf.append(f"    {i}. {sc}: {util_val:.1f}%{status}")
    
    # Urgent care routing comparison
    comp_inf.append("\n--- URGENT CARE ROUTING COMPARISON ---")
    
    bypass_rates = [results_urgent[sc]['bypass_rate'] for sc in scenarios]
    bypass_data = list(zip(scenarios, bypass_rates))
    bypass_data.sort(key=lambda x: x[1], reverse=True)  # Sort by bypass rate (high to low)
    
    comp_inf.append(f"Urgent MRI Bypass Rate Ranking:")
    for i, (sc, rate) in enumerate(bypass_data, 1):
        status = ""
        if rate > 80:
            status = " 🏆 EXCELLENT"
        elif rate > 50:
            status = " ✅ GOOD"
        elif rate > 20:
            status = " ⚠️  SUBOPTIMAL"
        else:
            status = " ❌ POOR"
        comp_inf.append(f"  {i}. {sc}: {rate:.1f}%{status}")
    
    # Total urgent cases comparison
    totals = [results_urgent[sc]['total'] for sc in scenarios]
    total_data = list(zip(scenarios, totals))
    comp_inf.append(f"\nUrgent Cases Volume:")
    for sc, total in total_data:
        comp_inf.append(f"  {sc}: {total} urgent MRI cases")
    
    # Model accuracy detailed comparison
    comp_inf.append("\n--- MODEL ACCURACY COMPARISON ---")
    
    # Simulated accuracy comparison
    sim_accs = [float(results_mock[sc]['simulated_accuracy']) for sc in scenarios]
    acc_data = list(zip(scenarios, sim_accs))
    acc_data.sort(key=lambda x: x[1], reverse=True)
    
    comp_inf.append(f"Simulated Accuracy Ranking:")
    for i, (sc, acc) in enumerate(acc_data, 1):
        comp_inf.append(f"  {i}. {sc}: {acc:.1%}")
    
    # Accuracy difference from expected
    diffs = [float(results_mock[sc]['difference']) for sc in scenarios]
    diff_data = list(zip(scenarios, diffs))
    diff_data.sort(key=lambda x: x[1])  # Sort by difference (low to high)
    
    comp_inf.append(f"\nAccuracy Deviation from Expected (closest to furthest):")
    for i, (sc, diff) in enumerate(diff_data, 1):
        status = ""
        if diff < 0.05:
            status = " 🏆 EXCELLENT"
        elif diff < 0.15:
            status = " ✅ GOOD"
        elif diff < 0.25:
            status = " ⚠️  MODERATE"
        else:
            status = " ❌ POOR"
        comp_inf.append(f"  {i}. {sc}: {diff:.3f} deviation{status}")
    
    # Overall performance summary
    comp_inf.append("\n--- OVERALL PERFORMANCE SUMMARY ---")
    
    # Calculate overall scores for each scenario
    scenario_scores: Dict[str, int] = {}
    for sc in scenarios:
        score = 0
        # Wait time score (lower is better) - use first resource's wait data as representative
        if wait_data:
            try:
                avg_wait_rank = [s for s, _ in wait_data].index(sc) + 1
                score += (len(scenarios) - avg_wait_rank + 1) * 2  # Weight wait times heavily
            except ValueError:
                pass
        
        # Bypass rate score (higher is better)
        if bypass_data:
            try:
                bypass_rank = [s for s, _ in bypass_data].index(sc) + 1
                score += (len(scenarios) - bypass_rank + 1) * 3  # Weight routing accuracy heavily
            except ValueError:
                pass
        
        # Accuracy deviation score (lower difference is better)
        if diff_data:
            try:
                diff_rank = [s for s, _ in diff_data].index(sc) + 1
                score += (len(scenarios) - diff_rank + 1) * 2  # Weight model accuracy
            except ValueError:
                pass
        
        scenario_scores[sc] = score
    
    # Rank scenarios by overall score
    ranked_scenarios = sorted(scenario_scores.items(), key=lambda x: x[1], reverse=True)
    
    comp_inf.append(f"Overall Performance Ranking (weighted by wait times, routing accuracy, and model accuracy):")
    for i, (sc, score) in enumerate(ranked_scenarios, 1):
        medal = ""
        if i == 1:
            medal = " 🥇"
        elif i == 2:
            medal = " 🥈"
        elif i == 3:
            medal = " 🥉"
        comp_inf.append(f"  {i}. {sc}: Score {score}{medal}")
    
    # Recommendations
    comp_inf.append("\n--- RECOMMENDATIONS ---")
    best_scenario = ranked_scenarios[0][0]
    comp_inf.append(f"🎯 RECOMMENDED SCENARIO: {best_scenario}")
    comp_inf.append(f"   Rationale: Best overall balance of wait times, routing accuracy, and model performance")
    
    if len(scenarios) >= 2:
        worst_scenario = ranked_scenarios[-1][0]
        comp_inf.append(f"⚠️  AVOID: {worst_scenario} shows poorest overall performance")
    
    # Specific improvement suggestions
    comp_inf.append(f"\n💡 IMPROVEMENT OPPORTUNITIES:")
    for sc in scenarios:
        issues: List[str] = []
        # Check for high wait times
        high_wait_resources = [r for r in RESOURCES if results_wait[sc][r] > SERVICE_TIMES[r] * WAIT_HIGH_FACTOR]
        if high_wait_resources:
            issues.append(f"reduce wait times for {', '.join(high_wait_resources)}")
        
        # Check for low utilization
        low_util_resources = [r for r in RESOURCES if results_util[sc][r] < UTIL_LOW_THRESHOLD]
        if low_util_resources:
            issues.append(f"optimize utilization of {', '.join(low_util_resources)}")
        
        # Check for poor routing
        if results_urgent[sc]['bypass_rate'] < 50:
            issues.append("improve urgent case routing accuracy")
        
        if issues:
            comp_inf.append(f"  {sc}: {'; '.join(issues)}")
        else:
            comp_inf.append(f"  {sc}: performing well across all metrics")
    
    return comp_inf