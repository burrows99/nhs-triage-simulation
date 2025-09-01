"""Metrics-related Enumerations for Manchester Triage System

This module defines enums used throughout the metrics and analysis system
to ensure type safety and consistent categorization.
"""

from enum import Enum, auto
from typing import List


class TriageCategory(Enum):
    """Triage categories as defined by Manchester Triage System"""
    RED = "RED"          # Immediate (0 minutes)
    ORANGE = "ORANGE"    # Very urgent (10 minutes)
    YELLOW = "YELLOW"    # Urgent (60 minutes)
    GREEN = "GREEN"      # Standard (120 minutes)
    BLUE = "BLUE"        # Non-urgent (240 minutes)
    UNKNOWN = "UNKNOWN"  # Unclassified
    
    @classmethod
    def get_wait_time(cls, category: 'TriageCategory') -> int:
        """Get standard wait time in minutes for a triage category
        
        Args:
            category: Triage category
            
        Returns:
            Wait time in minutes
        """
        wait_times = {
            cls.RED: 0,
            cls.ORANGE: 10,
            cls.YELLOW: 60,
            cls.GREEN: 120,
            cls.BLUE: 240,
            cls.UNKNOWN: 0
        }
        return wait_times.get(category, 0)
    
    @classmethod
    def get_priority_order(cls) -> List['TriageCategory']:
        """Get triage categories in priority order (highest to lowest)
        
        Returns:
            List of categories in priority order
        """
        return [cls.RED, cls.ORANGE, cls.YELLOW, cls.GREEN, cls.BLUE, cls.UNKNOWN]


class MetricType(Enum):
    """Types of metrics that can be calculated"""
    WAIT_TIME = "wait_time"
    PROCESSING_TIME = "processing_time"
    RESOURCE_UTILIZATION = "resource_utilization"
    THROUGHPUT = "throughput"
    ARRIVAL_RATE = "arrival_rate"
    QUEUE_LENGTH = "queue_length"
    SERVICE_TIME = "service_time"
    RESPONSE_TIME = "response_time"


class StatisticType(Enum):
    """Types of statistical measures"""
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"
    MIN = "min"
    MAX = "max"
    STD = "std"
    VARIANCE = "variance"
    PERCENTILE_25 = "p25"
    PERCENTILE_75 = "p75"
    PERCENTILE_90 = "p90"
    PERCENTILE_95 = "p95"
    PERCENTILE_99 = "p99"
    COUNT = "count"
    SUM = "sum"


class TimeInterval(Enum):
    """Time intervals for aggregating metrics"""
    MINUTE = (1, "minute")
    FIVE_MINUTES = (5, "5_minutes")
    FIFTEEN_MINUTES = (15, "15_minutes")
    THIRTY_MINUTES = (30, "30_minutes")
    HOUR = (60, "hour")
    TWO_HOURS = (120, "2_hours")
    FOUR_HOURS = (240, "4_hours")
    SIX_HOURS = (360, "6_hours")
    TWELVE_HOURS = (720, "12_hours")
    DAY = (1440, "day")
    WEEK = (10080, "week")
    
    def __init__(self, minutes: int, label: str):
        self.minutes = minutes
        self.label = label
    
    @classmethod
    def get_default_intervals(cls) -> List['TimeInterval']:
        """Get commonly used time intervals
        
        Returns:
            List of default time intervals
        """
        return [cls.FIFTEEN_MINUTES, cls.HOUR, cls.FOUR_HOURS, cls.DAY]


class ResourceType(Enum):
    """Types of resources in the triage system"""
    TRIAGE_NURSE = "triage_nurse"
    PHYSICIAN = "physician"
    SPECIALIST = "specialist"
    BED = "bed"
    EQUIPMENT = "equipment"
    ROOM = "room"
    SYSTEM = "system"
    OVERALL = "overall"


class PerformanceIndicator(Enum):
    """Key performance indicators for the triage system"""
    AVERAGE_WAIT_TIME = "avg_wait_time"
    MEDIAN_WAIT_TIME = "median_wait_time"
    MAX_WAIT_TIME = "max_wait_time"
    PATIENT_THROUGHPUT = "patient_throughput"
    RESOURCE_UTILIZATION = "resource_utilization"
    QUEUE_LENGTH = "queue_length"
    SERVICE_LEVEL = "service_level"
    ABANDONMENT_RATE = "abandonment_rate"
    PATIENT_SATISFACTION = "patient_satisfaction"
    SYSTEM_EFFICIENCY = "system_efficiency"
    PEAK_HOUR_PERFORMANCE = "peak_hour_performance"
    CATEGORY_DISTRIBUTION = "category_distribution"


class FlowchartReason(Enum):
    """Common flowchart reasons in Manchester Triage System"""
    CHEST_PAIN = "chest_pain"
    SHORTNESS_OF_BREATH = "shortness_of_breath"
    ABDOMINAL_PAIN = "abdominal_pain"
    HEADACHE = "headache"
    LIMB_INJURIES = "limb_injuries"
    BACK_PAIN = "back_pain"
    MENTAL_HEALTH = "mental_health"
    CARDIAC_ARREST = "cardiac_arrest"
    TRAUMA = "trauma"
    PEDIATRIC = "pediatric"
    OBSTETRIC = "obstetric"
    NEUROLOGICAL = "neurological"
    RESPIRATORY = "respiratory"
    GASTROINTESTINAL = "gastrointestinal"
    GENITOURINARY = "genitourinary"
    DERMATOLOGICAL = "dermatological"
    OPHTHALMOLOGICAL = "ophthalmological"
    ENT = "ent"
    GENERAL = "general"
    OTHER = "other"
    
    @classmethod
    def get_high_priority_reasons(cls) -> List['FlowchartReason']:
        """Get flowchart reasons typically associated with high priority
        
        Returns:
            List of high-priority flowchart reasons
        """
        return [
            cls.CHEST_PAIN,
            cls.SHORTNESS_OF_BREATH,
            cls.CARDIAC_ARREST,
            cls.TRAUMA,
            cls.NEUROLOGICAL
        ]


class ReportType(Enum):
    """Types of metrics reports that can be generated"""
    SUMMARY = "summary"
    DETAILED = "detailed"
    STATISTICAL = "statistical"
    PERFORMANCE = "performance"
    UTILIZATION = "utilization"
    ARRIVAL_ANALYSIS = "arrival_analysis"
    WAIT_TIME_ANALYSIS = "wait_time_analysis"
    CATEGORY_ANALYSIS = "category_analysis"
    FLOWCHART_ANALYSIS = "flowchart_analysis"
    TREND_ANALYSIS = "trend_analysis"
    COMPARATIVE = "comparative"
    REAL_TIME = "real_time"
    HISTORICAL = "historical"


class VisualizationType(Enum):
    """Types of visualizations for metrics data"""
    HISTOGRAM = "histogram"
    LINE_CHART = "line_chart"
    BAR_CHART = "bar_chart"
    PIE_CHART = "pie_chart"
    SCATTER_PLOT = "scatter_plot"
    BOX_PLOT = "box_plot"
    HEATMAP = "heatmap"
    TIME_SERIES = "time_series"
    DISTRIBUTION = "distribution"
    CORRELATION_MATRIX = "correlation_matrix"
    DASHBOARD = "dashboard"
    GAUGE = "gauge"
    TREEMAP = "treemap"
    SANKEY = "sankey"


class AlertLevel(Enum):
    """Alert levels for performance monitoring"""
    NORMAL = ("normal", 0)
    WARNING = ("warning", 1)
    CRITICAL = ("critical", 2)
    EMERGENCY = ("emergency", 3)
    
    def __init__(self, label: str, priority: int):
        self.label = label
        self.priority = priority
    
    @classmethod
    def get_by_priority(cls, priority: int) -> 'AlertLevel':
        """Get alert level by priority number
        
        Args:
            priority: Priority level (0-3)
            
        Returns:
            Corresponding alert level
        """
        for level in cls:
            if level.priority == priority:
                return level
        return cls.NORMAL


class DataQuality(Enum):
    """Data quality indicators for metrics"""
    EXCELLENT = ("excellent", 95)
    GOOD = ("good", 85)
    FAIR = ("fair", 70)
    POOR = ("poor", 50)
    INSUFFICIENT = ("insufficient", 0)
    
    def __init__(self, label: str, threshold: int):
        self.label = label
        self.threshold = threshold
    
    @classmethod
    def assess_quality(cls, completeness_percentage: float) -> 'DataQuality':
        """Assess data quality based on completeness percentage
        
        Args:
            completeness_percentage: Percentage of complete data
            
        Returns:
            Data quality level
        """
        if completeness_percentage >= 95:
            return cls.EXCELLENT
        elif completeness_percentage >= 85:
            return cls.GOOD
        elif completeness_percentage >= 70:
            return cls.FAIR
        elif completeness_percentage >= 50:
            return cls.POOR
        else:
            return cls.INSUFFICIENT


class AggregationMethod(Enum):
    """Methods for aggregating metrics data"""
    SUM = "sum"
    AVERAGE = "average"
    WEIGHTED_AVERAGE = "weighted_average"
    MEDIAN = "median"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    DISTINCT_COUNT = "distinct_count"
    FIRST = "first"
    LAST = "last"
    PERCENTILE = "percentile"
    STANDARD_DEVIATION = "std"
    VARIANCE = "variance"


class ComparisonOperator(Enum):
    """Operators for comparing metrics values"""
    EQUAL = "=="
    NOT_EQUAL = "!="
    GREATER_THAN = ">"
    GREATER_EQUAL = ">="
    LESS_THAN = "<"
    LESS_EQUAL = "<="
    BETWEEN = "between"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"