"""Report Generation Utilities

Utility class for generating comparison reports between triage systems.
Follows single responsibility principle with focused methods.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import Counter

from src.logger import logger
from src.triage.triage_constants import TriageCategories


class ReportUtils:
    """Utility class for generating triage system comparison reports."""
    
    @staticmethod
    def should_generate_report(results_summary: Dict[str, Any], quiet: bool = False) -> bool:
        """Check if comparison report should be generated.
        
        Args:
            results_summary: Dictionary of simulation results by system name
            quiet: Whether to suppress logging
            
        Returns:
            True if report should be generated, False otherwise
        """
        if len(results_summary) <= 1:
            if not quiet:
                logger.info("⏭️  Skipping comparison report - only one system result available")
            return False
        return True
    
    @staticmethod
    def load_detailed_metrics(simulations: List[Dict], results_summary: Dict[str, Any]) -> Dict[str, Dict]:
        """Load detailed NHS metrics for each simulation system.
        
        Args:
            simulations: List of simulation configurations
            results_summary: Dictionary of simulation results by system name
            
        Returns:
            Dictionary mapping system names to their detailed metrics
        """
        detailed_metrics = {}
        
        for sim_config in simulations:
            system_name = sim_config['name']
            if system_name in results_summary:
                metrics_file = os.path.join(sim_config['output_dir'], 'metrics', 'nhs_metrics.json')
                
                if os.path.exists(metrics_file):
                    try:
                        with open(metrics_file, 'r') as f:
                            detailed_metrics[system_name] = json.load(f)
                    except Exception as e:
                        logger.warning(f"⚠️  Could not load detailed metrics for {system_name}: {e}")
                        detailed_metrics[system_name] = {'error': f'Could not load metrics: {e}'}
                else:
                    detailed_metrics[system_name] = {'error': 'Metrics file not found'}
        
        return detailed_metrics
    
    @staticmethod
    def log_performance_comparison(results_summary: Dict[str, Any], detailed_metrics: Dict[str, Dict]):
        """Log performance comparison to console.
        
        Args:
            results_summary: Dictionary of simulation results by system name
            detailed_metrics: Dictionary of detailed NHS metrics by system name
        """
        logger.info("🏥 PERFORMANCE COMPARISON:")
        
        for system_name, results in results_summary.items():
            metrics = detailed_metrics.get(system_name, {})
            
            if 'error' not in metrics:
                compliance = metrics.get('4hour_standard_compliance_pct', 'N/A')
                median_time = metrics.get('median_total_time_minutes', 'N/A')
                admission_rate = metrics.get('admission_rate_pct', 'N/A')
                
                logger.info(f"   {system_name}:")
                logger.info(f"     • Patients: {results['total_patients']}")
                logger.info(f"     • Avg Time: {results['avg_time']:.1f} min")
                logger.info(f"     • Median Time: {median_time if median_time == 'N/A' else f'{median_time:.1f} min'}")
                logger.info(f"     • 4-Hour Compliance: {compliance if compliance == 'N/A' else f'{compliance:.1f}%'}")
                logger.info(f"     • Admission Rate: {admission_rate if admission_rate == 'N/A' else f'{admission_rate:.1f}%'}")
            else:
                logger.info(f"   {system_name}: {metrics['error']}")
    
    @staticmethod
    def log_triage_distribution(results_summary: Dict[str, Any]):
        """Log triage category distribution comparison to console.
        
        Args:
            results_summary: Dictionary of simulation results by system name
        """
        logger.info("\n🏷️  TRIAGE DISTRIBUTION COMPARISON:")
        
        for system_name, results in results_summary.items():
            if results['total_patients'] > 0:
                category_counts = Counter(results['categories'])
                logger.info(f"   {system_name}:")
                
                for category in [TriageCategories.RED, TriageCategories.ORANGE, 
                               TriageCategories.YELLOW, TriageCategories.GREEN, TriageCategories.BLUE]:
                    count = category_counts.get(category, 0)
                    percentage = (count / results['total_patients'] * 100)
                    logger.info(f"     • {category}: {count} ({percentage:.1f}%)")
    
    @staticmethod
    def generate_systematic_logging(results_summary: Dict[str, Any], detailed_metrics: Dict[str, Dict]):
        """Generate systematic comparison analysis logging.
        
        Args:
            results_summary: Dictionary of simulation results by system name
            detailed_metrics: Dictionary of detailed NHS metrics by system name
        """
        logger.info("📊 SYSTEMATIC COMPARISON ANALYSIS")
        logger.info("=" * 80)
        
        ReportUtils.log_performance_comparison(results_summary, detailed_metrics)
        ReportUtils.log_triage_distribution(results_summary)
    
    @staticmethod
    def save_markdown_report(content: str, output_path: str) -> str:
        """Save markdown report content to file.
        
        Args:
            content: Markdown content to save
            output_path: Path where to save the report
            
        Returns:
            Path where report was saved
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(content)
        
        return output_path
    
    @staticmethod
    def generate_report_header(args) -> str:
        """Generate markdown report header section.
        
        Args:
            args: Command line arguments
            
        Returns:
            Markdown header content
        """
        return f"""# Hospital Triage Systems Comparison Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Simulation Duration:** {args.duration} minutes ({args.duration/60:.1f} hours)
**Arrival Rate:** {args.arrival_rate} patients/hour
**Resources:** {args.nurses} nurses, {args.doctors} doctors, {args.beds} beds
"""
    
    @staticmethod
    def generate_executive_summary(results_summary: Dict[str, Any]) -> str:
        """Generate executive summary section.
        
        Args:
            results_summary: Dictionary of simulation results by system name
            
        Returns:
            Markdown executive summary content
        """
        summary = f"\n## Executive Summary\n\nThis report compares the performance of {len(results_summary)} triage systems:\n"
        
        for system_name in results_summary.keys():
            summary += f"- **{system_name}**\n"
        
        return summary
    
    @staticmethod
    def generate_performance_table(results_summary: Dict[str, Any], detailed_metrics: Dict[str, Dict]) -> str:
        """Generate performance overview table.
        
        Args:
            results_summary: Dictionary of simulation results by system name
            detailed_metrics: Dictionary of detailed NHS metrics by system name
            
        Returns:
            Markdown table content
        """
        table = "\n## Performance Overview\n\n"
        table += "| System | Patients | Avg Time (min) | Median Time (min) | 4-Hour Compliance (%) | Admission Rate (%) |\n"
        table += "|--------|----------|----------------|-------------------|----------------------|-------------------|\n"
        
        for system_name, results in results_summary.items():
            metrics = detailed_metrics.get(system_name, {})
            
            if 'error' not in metrics:
                compliance = metrics.get('4hour_standard_compliance_pct', 'N/A')
                median_time = metrics.get('median_total_time_minutes', 'N/A')
                admission_rate = metrics.get('admission_rate_pct', 'N/A')
                
                table += f"| {system_name} | {results['total_patients']} | {results['avg_time']:.1f} | "
                table += f"{median_time if median_time == 'N/A' else f'{median_time:.1f}'} | "
                table += f"{compliance if compliance == 'N/A' else f'{compliance:.1f}'} | "
                table += f"{admission_rate if admission_rate == 'N/A' else f'{admission_rate:.1f}'} |\n"
            else:
                table += f"| {system_name} | Error | Error | Error | Error | Error |\n"
        
        return table
    
    @staticmethod
    def generate_system_analysis(system_name: str, results: Dict[str, Any], metrics: Dict[str, Any]) -> str:
        """Generate detailed analysis for a single system.
        
        Args:
            system_name: Name of the triage system
            results: Simulation results for the system
            metrics: Detailed metrics for the system
            
        Returns:
            Markdown content for system analysis
        """
        analysis = f"### {system_name}\n\n"
        
        if 'error' not in metrics:
            analysis += ReportUtils._generate_performance_metrics(results, metrics)
            analysis += ReportUtils._generate_triage_distribution(results)
            analysis += ReportUtils._generate_nhs_indicators(metrics)
        else:
            analysis += f"**Error:** {metrics['error']}\n\n"
        
        return analysis
    
    @staticmethod
    def _generate_performance_metrics(results: Dict[str, Any], metrics: Dict[str, Any]) -> str:
        """Generate performance metrics section for a system."""
        section = "**Performance Metrics:**\n"
        section += f"- Total Attendances: {results['total_patients']}\n"
        section += f"- Average Journey Time: {results['avg_time']:.1f} minutes\n"
        section += f"- Median Journey Time: {metrics.get('median_total_time_minutes', 'N/A')} minutes\n"
        section += f"- 95th Percentile Time: {metrics.get('95th_percentile_time_minutes', 'N/A')} minutes\n"
        section += f"- 4-Hour Standard Compliance: {metrics.get('4hour_standard_compliance_pct', 'N/A')}%\n"
        section += f"- Admission Rate: {metrics.get('admission_rate_pct', 'N/A')}%\n\n"
        return section
    
    @staticmethod
    def _generate_triage_distribution(results: Dict[str, Any]) -> str:
        """Generate triage distribution section for a system."""
        if results['total_patients'] <= 0:
            return ""
        
        section = "**Triage Category Distribution:**\n"
        category_counts = Counter(results['categories'])
        
        for category in [TriageCategories.RED, TriageCategories.ORANGE, 
                        TriageCategories.YELLOW, TriageCategories.GREEN, TriageCategories.BLUE]:
            count = category_counts.get(category, 0)
            percentage = (count / results['total_patients'] * 100)
            section += f"- {category}: {count} patients ({percentage:.1f}%)\n"
        
        section += "\n"
        return section
    
    @staticmethod
    def _generate_nhs_indicators(metrics: Dict[str, Any]) -> str:
        """Generate NHS quality indicators section for a system."""
        if '3_time_to_initial_assessment_avg_minutes' not in metrics:
            return ""
        
        section = "**NHS Quality Indicators:**\n"
        section += f"- Time to Initial Assessment: {metrics.get('3_time_to_initial_assessment_avg_minutes', 'N/A')} minutes\n"
        section += f"- Time to Treatment: {metrics.get('4_time_to_treatment_avg_minutes', 'N/A')} minutes\n"
        section += f"- Left Before Being Seen Rate: {metrics.get('1_left_before_being_seen_rate_pct', 'N/A')}%\n"
        section += f"- Re-attendance Rate: {metrics.get('2_reattendance_rate_pct', 'N/A')}%\n\n"
        return section
    
    @staticmethod
    def generate_comparative_analysis(results_summary: Dict[str, Any], detailed_metrics: Dict[str, Dict]) -> str:
        """Generate comparative analysis section.
        
        Args:
            results_summary: Dictionary of simulation results by system name
            detailed_metrics: Dictionary of detailed NHS metrics by system name
            
        Returns:
            Markdown comparative analysis content
        """
        valid_systems = {name: metrics for name, metrics in detailed_metrics.items() if 'error' not in metrics}
        
        if len(valid_systems) <= 1:
            return ""
        
        analysis = "## Comparative Analysis\n\n"
        
        # Best compliance
        best_compliance = max(valid_systems.items(), key=lambda x: x[1].get('4hour_standard_compliance_pct', 0))
        analysis += f"**Best 4-Hour Compliance:** {best_compliance[0]} ({best_compliance[1].get('4hour_standard_compliance_pct', 0):.1f}%)\n\n"
        
        # Fastest average time
        fastest_system = min(results_summary.items(), key=lambda x: x[1]['avg_time'])
        analysis += f"**Fastest Average Time:** {fastest_system[0]} ({fastest_system[1]['avg_time']:.1f} minutes)\n\n"
        
        # Most patients processed
        most_patients = max(results_summary.items(), key=lambda x: x[1]['total_patients'])
        analysis += f"**Most Patients Processed:** {most_patients[0]} ({most_patients[1]['total_patients']} patients)\n\n"
        
        return analysis
    
    @staticmethod
    def generate_methodology_section(args) -> str:
        """Generate methodology section.
        
        Args:
            args: Command line arguments
            
        Returns:
            Markdown methodology content
        """
        methodology = "## Methodology\n\n"
        methodology += "- **Simulation Engine:** Discrete Event Simulation using SimPy\n"
        methodology += "- **Patient Data:** Synthea synthetic healthcare data\n"
        methodology += "- **Metrics:** NHS England A&E Quality Indicators\n"
        methodology += f"- **Duration:** {args.duration} minutes simulation time\n"
        methodology += f"- **Resources:** {args.nurses} nurses, {args.doctors} doctors, {args.beds} beds\n\n"
        methodology += "---\n*Report generated by Hospital Simulation Comparison System*\n"
        return methodology
    
    @staticmethod
    def generate_complete_markdown_report(results_summary: Dict[str, Any], detailed_metrics: Dict[str, Dict], args) -> str:
        """Generate complete markdown report content.
        
        Args:
            results_summary: Dictionary of simulation results by system name
            detailed_metrics: Dictionary of detailed NHS metrics by system name
            args: Command line arguments
            
        Returns:
            Complete markdown report content
        """
        report = ReportUtils.generate_report_header(args)
        report += ReportUtils.generate_executive_summary(results_summary)
        report += ReportUtils.generate_performance_table(results_summary, detailed_metrics)
        
        # Detailed analysis for each system
        report += "\n## Detailed System Analysis\n\n"
        for system_name, results in results_summary.items():
            metrics = detailed_metrics.get(system_name, {})
            report += ReportUtils.generate_system_analysis(system_name, results, metrics)
        
        report += ReportUtils.generate_comparative_analysis(results_summary, detailed_metrics)
        report += ReportUtils.generate_methodology_section(args)
        
        return report