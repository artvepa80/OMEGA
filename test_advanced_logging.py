#!/usr/bin/env python3
"""
🧪 Test Advanced Logging & Metrics System
========================================

Comprehensive test suite for validating the advanced logging and metrics
tracking system implementation in OMEGA PRO AI v10.1.

This script tests:
- Metrics collector initialization
- Rare number detection logging
- Exploration decision logging  
- Statistical analysis logging
- Performance tracking
- Integration with existing modules
- Fallback mechanisms
"""

import sys
import os
import time
import random
import logging
from pathlib import Path

# Add OMEGA modules to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure basic logging for test output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [TEST] %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S"
)
test_logger = logging.getLogger("AdvancedLoggingTest")


def test_metrics_collector_initialization():
    """Test metrics collector initialization"""
    test_logger.info("🚀 Testing metrics collector initialization...")
    
    try:
        from modules.advanced_logging_metrics import (
            get_metrics_collector, 
            initialize_metrics_collector
        )
        
        # Initialize with test settings
        collector = initialize_metrics_collector(
            retention_hours=1,  # Short retention for testing
            enable_dashboard_export=False  # Disable for testing
        )
        
        assert collector is not None, "Metrics collector should not be None"
        test_logger.info("✅ Metrics collector initialized successfully")
        
        # Test global getter
        collector2 = get_metrics_collector()
        assert collector2 is not None, "Global collector should be available"
        test_logger.info("✅ Global metrics collector accessible")
        
        return True
        
    except Exception as e:
        test_logger.error(f"❌ Metrics collector initialization failed: {e}")
        return False


def test_rare_number_detection_logging():
    """Test rare number detection event logging"""
    test_logger.info("🔥 Testing rare number detection logging...")
    
    try:
        from modules.advanced_logging_metrics import get_metrics_collector
        
        collector = get_metrics_collector()
        if collector is None:
            test_logger.warning("⚠️ Collector not available, skipping rare number test")
            return False
        
        # Test rare number detection event
        collector.log_rare_number_detection(
            numbers=[1, 3, 38, 40],
            frequency_scores={1: 0.015, 3: 0.018, 38: 0.012, 40: 0.010},
            boost_applied=0.32,
            combination=[1, 3, 15, 22, 38, 40],
            source_model="test_model",
            detection_method="frequency_analysis_test",
            test_event=True
        )
        
        # Get insights to verify logging
        insights = collector.get_rare_number_insights(lookback_hours=1)
        assert not insights.get('no_data', False), "Should have rare number data"
        assert insights.get('total_detections', 0) > 0, "Should have recorded detections"
        
        test_logger.info("✅ Rare number detection logging successful")
        return True
        
    except Exception as e:
        test_logger.error(f"❌ Rare number detection logging failed: {e}")
        return False


def test_exploration_decision_logging():
    """Test exploration mode decision logging"""
    test_logger.info("🔍 Testing exploration decision logging...")
    
    try:
        from modules.advanced_logging_metrics import get_metrics_collector
        
        collector = get_metrics_collector()
        if collector is None:
            test_logger.warning("⚠️ Collector not available, skipping exploration test")
            return False
        
        # Test exploration decision event
        collector.log_exploration_decision(
            combination=[5, 12, 19, 28, 35, 39],
            exploration_boost=0.15,
            anomaly_score=0.08,
            diversity_bonus=0.12,
            rare_count=2,
            decision_factors={
                "base_score": 0.75,
                "exploration_intensity": 0.4,
                "rare_numbers_available": 12
            },
            final_score=1.10,
            rank_change=5.2,
            test_event=True
        )
        
        # Get insights to verify logging
        insights = collector.get_exploration_insights(lookback_hours=1)
        assert not insights.get('no_data', False), "Should have exploration data"
        assert insights.get('total_exploration_decisions', 0) > 0, "Should have recorded decisions"
        
        test_logger.info("✅ Exploration decision logging successful")
        return True
        
    except Exception as e:
        test_logger.error(f"❌ Exploration decision logging failed: {e}")
        return False


def test_statistical_analysis_logging():
    """Test statistical analysis logging"""
    test_logger.info("📊 Testing statistical analysis logging...")
    
    try:
        from modules.advanced_logging_metrics import get_metrics_collector
        
        collector = get_metrics_collector()
        if collector is None:
            test_logger.warning("⚠️ Collector not available, skipping statistical test")
            return False
        
        # Test statistical analysis event
        collector.log_statistical_analysis(
            analysis_type="entropy_analysis",
            test_name="shannon_entropy_test",
            test_statistic=2.45,
            p_value=0.032,
            significance_level=0.05,
            effect_size=0.68,
            confidence_interval=(2.1, 2.8),
            sample_size=6,
            test_event=True
        )
        
        # Test another type
        collector.log_statistical_analysis(
            analysis_type="distribution_analysis", 
            test_name="chi_square_goodness_of_fit",
            test_statistic=15.23,
            p_value=0.128,
            significance_level=0.05,
            effect_size=0.34,
            confidence_interval=(0.05, 0.25),
            sample_size=100,
            test_event=True
        )
        
        test_logger.info("✅ Statistical analysis logging successful")
        return True
        
    except Exception as e:
        test_logger.error(f"❌ Statistical analysis logging failed: {e}")
        return False


def test_consensus_adjustment_logging():
    """Test consensus engine adjustment logging"""
    test_logger.info("⚖️ Testing consensus adjustment logging...")
    
    try:
        from modules.advanced_logging_metrics import get_metrics_collector
        
        collector = get_metrics_collector()
        if collector is None:
            test_logger.warning("⚠️ Collector not available, skipping consensus test")
            return False
        
        # Test consensus adjustment event
        collector.log_consensus_adjustment(
            model_name="test_lstm_v2",
            old_weight=1.25,
            new_weight=1.45,
            performance_score=0.82,
            adjustment_reason="performance_improvement",
            accuracy_metrics={
                "accuracy": 0.82,
                "precision": 0.78,
                "recall": 0.85,
                "f1_score": 0.81
            },
            test_event=True
        )
        
        test_logger.info("✅ Consensus adjustment logging successful")
        return True
        
    except Exception as e:
        test_logger.error(f"❌ Consensus adjustment logging failed: {e}")
        return False


def test_performance_tracking():
    """Test performance tracking context manager"""
    test_logger.info("⚡ Testing performance tracking...")
    
    try:
        from modules.advanced_logging_metrics import get_metrics_collector
        
        collector = get_metrics_collector()
        if collector is None:
            test_logger.warning("⚠️ Collector not available, skipping performance test")
            return False
        
        # Test performance tracking
        with collector.track_performance(
            operation="test_model_execution",
            model_name="test_model",
            combination_count=50,
            test_event=True
        ):
            # Simulate some work
            time.sleep(0.1)
            # Simulate processing combinations
            for _ in range(50):
                _ = [random.randint(1, 40) for _ in range(6)]
        
        test_logger.info("✅ Performance tracking successful")
        return True
        
    except Exception as e:
        test_logger.error(f"❌ Performance tracking failed: {e}")
        return False


def test_integration_helper():
    """Test the metrics integration helper"""
    test_logger.info("🔗 Testing metrics integration helper...")
    
    try:
        from modules.metrics_integration import (
            initialize_metrics_integration,
            log_rare_number_event,
            log_exploration_event,
            log_statistical_event,
            log_consensus_event,
            get_metrics_summary
        )
        
        # Initialize integration
        success = initialize_metrics_integration(enable_metrics=True)
        assert success, "Integration should initialize successfully"
        
        # Test integrated logging functions
        log_rare_number_event(
            numbers=[2, 13, 37],
            boost_applied=0.24,
            combination=[2, 13, 18, 25, 32, 37],
            source_model="integration_test",
            test_event=True
        )
        
        log_exploration_event(
            combination=[4, 11, 19, 26, 33, 40],
            exploration_boost=0.12,
            anomaly_score=0.06,
            diversity_bonus=0.09,
            rare_count=1,
            test_event=True
        )
        
        log_statistical_event(
            analysis_type="integration_test",
            test_name="test_statistic",
            test_statistic=3.14,
            p_value=0.025,
            test_event=True
        )
        
        log_consensus_event(
            model_name="integration_test_model",
            old_weight=1.0,
            new_weight=1.2,
            performance_score=0.75,
            adjustment_reason="integration_test",
            test_event=True
        )
        
        # Test summary retrieval
        summary = get_metrics_summary(lookback_hours=1)
        assert isinstance(summary, dict), "Summary should be a dictionary"
        
        test_logger.info("✅ Metrics integration helper successful")
        return True
        
    except Exception as e:
        test_logger.error(f"❌ Metrics integration helper failed: {e}")
        return False


def test_statistical_functions():
    """Test enhanced statistical functions with logging"""
    test_logger.info("🧮 Testing enhanced statistical functions...")
    
    try:
        from modules.score_dynamics import (
            calculate_shannon_entropy,
            calculate_z_scores,
            chi_square_goodness_of_fit
        )
        
        # Test data
        test_sequence = [1, 5, 12, 18, 25, 32, 38]
        
        # Test Shannon entropy with logging
        entropy = calculate_shannon_entropy(test_sequence)
        assert entropy > 0, "Entropy should be positive"
        test_logger.info(f"Shannon entropy: {entropy:.4f}")
        
        # Test Z-scores with logging
        z_scores = calculate_z_scores(test_sequence)
        assert len(z_scores) == len(test_sequence), "Z-scores length should match input"
        test_logger.info(f"Z-scores calculated: {len(z_scores)} values")
        
        # Test chi-square test with logging
        p_value = chi_square_goodness_of_fit(test_sequence * 10)  # Repeat for sufficient sample
        assert 0 <= p_value <= 1, "P-value should be between 0 and 1"
        test_logger.info(f"Chi-square p-value: {p_value:.6f}")
        
        test_logger.info("✅ Enhanced statistical functions successful")
        return True
        
    except Exception as e:
        test_logger.error(f"❌ Enhanced statistical functions failed: {e}")
        return False


def test_comprehensive_report():
    """Test comprehensive metrics report generation"""
    test_logger.info("📋 Testing comprehensive report generation...")
    
    try:
        from modules.advanced_logging_metrics import get_metrics_collector
        
        collector = get_metrics_collector()
        if collector is None:
            test_logger.warning("⚠️ Collector not available, skipping report test")
            return False
        
        # Generate comprehensive report
        report = collector.get_comprehensive_report(lookback_hours=1)
        
        # Validate report structure
        assert isinstance(report, dict), "Report should be a dictionary"
        assert 'report_timestamp' in report, "Report should have timestamp"
        assert 'session_info' in report, "Report should have session info"
        assert 'system_stats' in report, "Report should have system stats"
        
        test_logger.info(f"Report generated with {len(report)} sections")
        
        # Test report export
        test_report_path = "test_metrics_report.json"
        collector.export_report_to_file(test_report_path, lookback_hours=1)
        
        # Verify file was created
        if Path(test_report_path).exists():
            test_logger.info("✅ Report export successful")
            # Cleanup test file
            Path(test_report_path).unlink()
        
        test_logger.info("✅ Comprehensive report generation successful")
        return True
        
    except Exception as e:
        test_logger.error(f"❌ Comprehensive report generation failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results"""
    test_logger.info("🧪 Starting Advanced Logging & Metrics System Test Suite")
    test_logger.info("=" * 60)
    
    tests = [
        ("Metrics Collector Initialization", test_metrics_collector_initialization),
        ("Rare Number Detection Logging", test_rare_number_detection_logging),
        ("Exploration Decision Logging", test_exploration_decision_logging),
        ("Statistical Analysis Logging", test_statistical_analysis_logging),
        ("Consensus Adjustment Logging", test_consensus_adjustment_logging),
        ("Performance Tracking", test_performance_tracking),
        ("Integration Helper", test_integration_helper),
        ("Enhanced Statistical Functions", test_statistical_functions),
        ("Comprehensive Report", test_comprehensive_report),
    ]
    
    results = []
    for test_name, test_func in tests:
        test_logger.info(f"\n🔍 Running: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                test_logger.info(f"✅ {test_name}: PASSED")
            else:
                test_logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            test_logger.error(f"💥 {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    test_logger.info("\n" + "=" * 60)
    test_logger.info("📊 TEST RESULTS SUMMARY")
    test_logger.info("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        test_logger.info(f"{status:10} | {test_name}")
    
    test_logger.info("-" * 60)
    test_logger.info(f"TOTAL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        test_logger.info("🎉 ALL TESTS PASSED! Advanced logging system is ready.")
    else:
        test_logger.warning(f"⚠️  {total-passed} tests failed. Review implementation.")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        test_logger.info("\n🛑 Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        test_logger.error(f"💥 Test suite crashed: {e}")
        sys.exit(1)