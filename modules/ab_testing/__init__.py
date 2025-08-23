"""
OMEGA PRO AI v10.1 - A/B Testing Framework
=========================================

A comprehensive A/B testing infrastructure for validating prediction improvements
and system enhancements in the OMEGA lottery prediction system.

Core Components:
- ABTestFramework: Main testing orchestrator
- FeatureFlagManager: Safe feature rollout management  
- StatisticalAnalyzer: Result significance testing
- PerformanceComparator: Metrics comparison system
- TestReporter: Automated insights generation

Author: OMEGA PRO AI Team
Version: v10.1
Date: 2025-08-16
"""

from .framework import ABTestFramework
from .feature_flags import FeatureFlagManager
from .statistical_analyzer import StatisticalAnalyzer
from .performance_comparator import PerformanceComparator
from .test_reporter import TestReporter
from .config_manager import ABTestConfigManager

__version__ = "10.1.0"
__all__ = [
    "ABTestFramework",
    "FeatureFlagManager", 
    "StatisticalAnalyzer",
    "PerformanceComparator",
    "TestReporter",
    "ABTestConfigManager"
]