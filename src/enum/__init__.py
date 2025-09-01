"""Enum package for Manchester Triage System

This package contains all enumeration definitions used throughout the system.
"""

from .metrics import (
    TriageCategory, MetricType, StatisticType, TimeInterval,
    ResourceType, PerformanceIndicator, FlowchartReason,
    ReportType, VisualizationType, AlertLevel, DataQuality,
    AggregationMethod, ComparisonOperator
)

__all__ = [
    'TriageCategory', 'MetricType', 'StatisticType', 'TimeInterval',
    'ResourceType', 'PerformanceIndicator', 'FlowchartReason',
    'ReportType', 'VisualizationType', 'AlertLevel', 'DataQuality',
    'AggregationMethod', 'ComparisonOperator'
]