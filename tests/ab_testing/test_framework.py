"""
Test suite for A/B testing framework core functionality.
"""

import unittest
import tempfile
import shutil
import os
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from modules.ab_testing.framework import ABTestFramework, ABTestConfig, TestSample
from modules.ab_testing.feature_flags import FeatureFlagManager
from modules.ab_testing.statistical_analyzer import StatisticalAnalyzer
from modules.ab_testing.performance_comparator import PerformanceComparator


class TestABTestFramework(unittest.TestCase):
    """Test cases for ABTestFramework."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "ab_testing.json")
        self.results_path = os.path.join(self.temp_dir, "results")
        
        # Create framework instance
        self.framework = ABTestFramework(
            config_path=self.config_path,
            results_path=self.results_path
        )
        
        # Test configuration
        self.test_config = ABTestConfig(
            test_id="test_rare_numbers_001",
            name="Rare Number Detection Test",
            description="Test for rare number prediction improvements",
            control_config={"algorithm": "standard"},
            variant_config={"algorithm": "enhanced", "rare_boost": True},
            traffic_split=0.5,
            min_sample_size=50,
            metrics=["accuracy", "rare_number_detection"]
        )
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_test(self):
        """Test creating a new A/B test."""
        result = self.framework.create_test(self.test_config)
        self.assertTrue(result)
        self.assertIn(self.test_config.test_id, self.framework.active_tests)
    
    def test_create_duplicate_test(self):
        """Test creating a duplicate test should fail."""
        self.framework.create_test(self.test_config)
        result = self.framework.create_test(self.test_config)
        self.assertFalse(result)
    
    def test_should_use_variant(self):
        """Test variant assignment consistency."""
        self.framework.create_test(self.test_config)
        
        # Same user should get consistent assignment
        user_id = "user_123"
        assignment1 = self.framework.should_use_variant(self.test_config.test_id, user_id)
        assignment2 = self.framework.should_use_variant(self.test_config.test_id, user_id)
        self.assertEqual(assignment1, assignment2)
    
    def test_record_prediction(self):
        """Test recording a prediction."""
        self.framework.create_test(self.test_config)
        
        sample_id = self.framework.record_prediction(
            test_id=self.test_config.test_id,
            user_id="user_123",
            prediction=[12, 27, 1, 10, 13, 22],
            metadata={"timestamp": datetime.now().isoformat()}
        )
        
        self.assertIsNotNone(sample_id)
        self.assertTrue(len(self.framework.test_samples[self.test_config.test_id]) > 0)
    
    def test_record_result(self):
        """Test recording lottery results."""
        self.framework.create_test(self.test_config)
        
        sample_id = self.framework.record_prediction(
            test_id=self.test_config.test_id,
            user_id="user_123",
            prediction=[12, 27, 1, 10, 13, 22]
        )
        
        # Record result
        self.framework.record_result(
            test_id=self.test_config.test_id,
            sample_id=sample_id,
            actual_result=[15, 22, 30, 35, 40, 42],
            metrics={"accuracy": 0.17}  # 1/6 match
        )
        
        # Check that sample was updated
        samples = self.framework.test_samples[self.test_config.test_id]
        self.assertIsNotNone(samples[0].actual_result)
        self.assertIn("accuracy", samples[0].metrics)
    
    def test_get_test_status(self):
        """Test getting test status."""
        self.framework.create_test(self.test_config)
        
        status = self.framework.get_test_status(self.test_config.test_id)
        
        self.assertEqual(status["test_id"], self.test_config.test_id)
        self.assertEqual(status["total_samples"], 0)
        self.assertFalse(status["ready_for_analysis"])
    
    def test_stop_test(self):
        """Test stopping a test."""
        self.framework.create_test(self.test_config)
        
        result = self.framework.stop_test(self.test_config.test_id, "Test completed")
        
        self.assertTrue(result)
        self.assertFalse(self.framework.active_tests[self.test_config.test_id].enabled)
    
    def test_invalid_test_config(self):
        """Test creating test with invalid configuration."""
        invalid_config = ABTestConfig(
            test_id="",  # Invalid empty ID
            name="Test",
            description="Test",
            control_config={},
            variant_config={},
            traffic_split=1.5  # Invalid traffic split
        )
        
        result = self.framework.create_test(invalid_config)
        self.assertFalse(result)


class TestFeatureFlagManager(unittest.TestCase):
    """Test cases for FeatureFlagManager."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "feature_flags.json")
        
        self.flag_manager = FeatureFlagManager(config_path=self.config_path)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_flag(self):
        """Test creating a feature flag."""
        result = self.flag_manager.create_flag(
            name="test_flag",
            description="Test flag",
            enabled=True,
            rollout_percentage=50
        )
        
        self.assertTrue(result)
        self.assertIn("test_flag", self.flag_manager.flags)
    
    def test_flag_consistent_assignment(self):
        """Test that flag assignment is consistent for same user."""
        self.flag_manager.create_flag("test_flag", enabled=True, rollout_percentage=50)
        
        user_id = "user_123"
        assignment1 = self.flag_manager.is_enabled("test_flag", user_id)
        assignment2 = self.flag_manager.is_enabled("test_flag", user_id)
        
        self.assertEqual(assignment1, assignment2)
    
    def test_rollout_percentage_0(self):
        """Test 0% rollout shows flag to no users."""
        self.flag_manager.create_flag("test_flag", enabled=True, rollout_percentage=0)
        
        # Test multiple users
        for i in range(10):
            self.assertFalse(self.flag_manager.is_enabled("test_flag", f"user_{i}"))
    
    def test_rollout_percentage_100(self):
        """Test 100% rollout shows flag to all users."""
        self.flag_manager.create_flag("test_flag", enabled=True, rollout_percentage=100)
        
        # Test multiple users
        for i in range(10):
            self.assertTrue(self.flag_manager.is_enabled("test_flag", f"user_{i}"))
    
    def test_whitelist_override(self):
        """Test whitelist overrides rollout percentage."""
        self.flag_manager.create_flag(
            "test_flag", 
            enabled=True, 
            rollout_percentage=0,
            user_whitelist={"user_special"}
        )
        
        # Whitelisted user should see flag despite 0% rollout
        self.assertTrue(self.flag_manager.is_enabled("test_flag", "user_special"))
        self.assertFalse(self.flag_manager.is_enabled("test_flag", "user_normal"))
    
    def test_blacklist_override(self):
        """Test blacklist overrides rollout percentage."""
        self.flag_manager.create_flag(
            "test_flag",
            enabled=True,
            rollout_percentage=100,
            user_blacklist={"user_blocked"}
        )
        
        # Blacklisted user should not see flag despite 100% rollout
        self.assertFalse(self.flag_manager.is_enabled("test_flag", "user_blocked"))
        self.assertTrue(self.flag_manager.is_enabled("test_flag", "user_normal"))
    
    def test_emergency_killswitch(self):
        """Test emergency killswitch functionality."""
        self.flag_manager.create_flag("test_flag", enabled=True, rollout_percentage=100)
        
        # Verify flag is enabled
        self.assertTrue(self.flag_manager.is_enabled("test_flag", "user_123"))
        
        # Emergency stop
        result = self.flag_manager.emergency_killswitch("test_flag", "Emergency test")
        
        self.assertTrue(result)
        self.assertFalse(self.flag_manager.is_enabled("test_flag", "user_123"))


class TestStatisticalAnalyzer(unittest.TestCase):
    """Test cases for StatisticalAnalyzer."""
    
    def setUp(self):
        """Set up test environment."""
        self.analyzer = StatisticalAnalyzer()
    
    def create_mock_samples(self, control_metrics: dict, treatment_metrics: dict, 
                          n_control: int = 50, n_treatment: int = 50):
        """Create mock samples for testing."""
        control_samples = []
        treatment_samples = []
        
        # Create control samples
        for i in range(n_control):
            sample = MagicMock()
            sample.metrics = {}
            for metric, base_value in control_metrics.items():
                # Add some noise
                import random
                noise = random.uniform(-0.1, 0.1)
                sample.metrics[metric] = max(0, base_value + noise)
            control_samples.append(sample)
        
        # Create treatment samples
        for i in range(n_treatment):
            sample = MagicMock()
            sample.metrics = {}
            for metric, base_value in treatment_metrics.items():
                # Add some noise
                import random
                noise = random.uniform(-0.1, 0.1)
                sample.metrics[metric] = max(0, base_value + noise)
            treatment_samples.append(sample)
        
        return control_samples, treatment_samples
    
    def test_analyze_significant_improvement(self):
        """Test analysis with significant improvement."""
        # Create samples with clear improvement
        control_samples, treatment_samples = self.create_mock_samples(
            control_metrics={"accuracy": 0.15, "rare_number_detection": 0.08},
            treatment_metrics={"accuracy": 0.25, "rare_number_detection": 0.18}
        )
        
        results = self.analyzer.analyze_test_results(control_samples, treatment_samples)
        
        self.assertNotIn("error", results)
        self.assertIn("metric_results", results)
        self.assertIn("summary", results)
    
    def test_analyze_no_difference(self):
        """Test analysis with no significant difference."""
        # Create samples with no real difference
        control_samples, treatment_samples = self.create_mock_samples(
            control_metrics={"accuracy": 0.15, "rare_number_detection": 0.08},
            treatment_metrics={"accuracy": 0.15, "rare_number_detection": 0.08}
        )
        
        results = self.analyzer.analyze_test_results(control_samples, treatment_samples)
        
        self.assertNotIn("error", results)
        significant_count = results.get("summary", {}).get("significant_results", 0)
        self.assertEqual(significant_count, 0)
    
    def test_power_analysis(self):
        """Test power analysis calculation."""
        # Test with medium effect size
        required_n = self.analyzer.power_analysis(effect_size=0.5, power=0.8)
        
        self.assertIsInstance(required_n, int)
        self.assertGreater(required_n, 0)
        self.assertLess(required_n, 1000)  # Should be reasonable
    
    def test_insufficient_samples(self):
        """Test behavior with insufficient samples."""
        # Create very small samples
        control_samples, treatment_samples = self.create_mock_samples(
            control_metrics={"accuracy": 0.15},
            treatment_metrics={"accuracy": 0.25},
            n_control=5, n_treatment=5
        )
        
        results = self.analyzer.analyze_test_results(control_samples, treatment_samples)
        
        # Should handle gracefully
        self.assertIn("error", results)


class TestPerformanceComparator(unittest.TestCase):
    """Test cases for PerformanceComparator."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.comparator = PerformanceComparator()
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_mock_samples_with_results(self, control_predictions: list, treatment_predictions: list,
                                       actual_results: list):
        """Create mock samples with predictions and actual results."""
        control_samples = []
        treatment_samples = []
        
        for i, (pred, actual) in enumerate(zip(control_predictions, actual_results)):
            sample = MagicMock()
            sample.prediction = pred
            sample.actual_result = actual
            sample.metrics = self._calculate_sample_metrics(pred, actual)
            control_samples.append(sample)
        
        for i, (pred, actual) in enumerate(zip(treatment_predictions, actual_results)):
            sample = MagicMock()
            sample.prediction = pred
            sample.actual_result = actual
            sample.metrics = self._calculate_sample_metrics(pred, actual)
            treatment_samples.append(sample)
        
        return control_samples, treatment_samples
    
    def _calculate_sample_metrics(self, prediction: list, actual: list) -> dict:
        """Calculate metrics for a sample."""
        if not prediction or not actual:
            return {}
        
        matches = len(set(prediction).intersection(set(actual)))
        accuracy = matches / len(actual)
        
        # Check for rare numbers
        rare_numbers = [n for n in actual if n < 10 or n > 30]
        rare_predicted = [n for n in prediction if n < 10 or n > 30]
        rare_detection = len(set(rare_numbers).intersection(set(rare_predicted))) / max(len(rare_numbers), 1)
        
        return {
            "accuracy": accuracy,
            "partial_matches": matches,
            "rare_number_detection": rare_detection,
            "latency_ms": 150 + (accuracy * 50)  # Simulate latency correlation
        }
    
    def test_compare_variants_improvement(self):
        """Test comparison showing improvement."""
        # Create samples where treatment performs better
        control_predictions = [[15, 20, 25, 30, 35, 40]] * 10
        treatment_predictions = [[12, 27, 1, 10, 13, 22]] * 10  # Rare number focus
        actual_results = [[12, 22, 30, 35, 40, 42]] * 10  # Some matches with rare numbers
        
        control_samples, treatment_samples = self.create_mock_samples_with_results(
            control_predictions, treatment_predictions, actual_results
        )
        
        results = self.comparator.compare_variants(control_samples, treatment_samples)
        
        self.assertNotIn("error", results)
        self.assertIn("metric_comparisons", results)
        self.assertIn("overall_assessment", results)
    
    def test_rare_number_analysis(self):
        """Test specific rare number analysis."""
        # Create samples with rare numbers
        predictions_with_rare = [[1, 5, 12, 31, 38, 42]] * 5  # Includes rare numbers
        predictions_standard = [[15, 20, 25, 30, 35, 40]] * 5  # No rare numbers
        actual_with_rare = [[2, 8, 15, 32, 35, 41]] * 5  # Some rare numbers
        
        control_samples, treatment_samples = self.create_mock_samples_with_results(
            predictions_standard, predictions_with_rare, actual_with_rare
        )
        
        results = self.comparator.compare_variants(control_samples, treatment_samples)
        
        self.assertIn("rare_number_analysis", results)
        rare_analysis = results["rare_number_analysis"]
        
        if "error" not in rare_analysis:
            self.assertIn("overall_rare_accuracy", rare_analysis)
    
    def test_edge_case_analysis(self):
        """Test edge case analysis."""
        # Create challenging edge case combinations
        control_predictions = [[15, 20, 25, 30, 35, 40]] * 3
        treatment_predictions = [[12, 27, 1, 10, 13, 22]] * 3  # Edge case pattern
        actual_edge_cases = [
            [12, 27, 1, 10, 13, 22],  # Exact rare number match
            [2, 8, 35, 37, 40, 42],   # Mixed rare/normal
            [1, 3, 5, 7, 9, 11]       # All low numbers
        ]
        
        control_samples, treatment_samples = self.create_mock_samples_with_results(
            control_predictions, treatment_predictions, actual_edge_cases
        )
        
        results = self.comparator.compare_edge_cases(control_samples, treatment_samples)
        
        self.assertIn("sample_counts", results)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete A/B testing framework."""
    
    def setUp(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create framework with temporary directory
        self.framework = ABTestFramework(
            config_path=os.path.join(self.temp_dir, "config.json"),
            results_path=os.path.join(self.temp_dir, "results")
        )
    
    def tearDown(self):
        """Clean up integration test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_complete_ab_test_workflow(self):
        """Test complete A/B test workflow from creation to analysis."""
        # 1. Create test
        test_config = ABTestConfig(
            test_id="integration_test_001",
            name="Integration Test",
            description="Complete workflow test",
            control_config={"algorithm": "standard"},
            variant_config={"algorithm": "enhanced"},
            traffic_split=0.5,
            min_sample_size=20,
            metrics=["accuracy", "rare_number_detection"]
        )
        
        result = self.framework.create_test(test_config)
        self.assertTrue(result)
        
        # 2. Record predictions and results
        sample_ids = []
        for i in range(25):  # Exceed min sample size
            user_id = f"user_{i}"
            prediction = [10 + i, 15 + i, 20 + i, 25 + i, 30 + i, 35]
            
            sample_id = self.framework.record_prediction(
                test_id=test_config.test_id,
                user_id=user_id,
                prediction=prediction
            )
            sample_ids.append(sample_id)
            
            # Record result
            actual_result = [12 + i, 18 + i, 22 + i, 28 + i, 32 + i, 38]
            self.framework.record_result(
                test_id=test_config.test_id,
                sample_id=sample_id,
                actual_result=actual_result,
                metrics={"accuracy": 0.2}  # Mock accuracy
            )
        
        # 3. Check test status
        status = self.framework.get_test_status(test_config.test_id)
        self.assertTrue(status["ready_for_analysis"])
        self.assertEqual(status["completed_samples"], 25)
        
        # 4. Analyze test
        analysis = self.framework.analyze_test(test_config.test_id)
        self.assertNotIn("error", analysis)
        self.assertIn("statistics", analysis)
        self.assertIn("performance", analysis)
        
        # 5. Stop test
        stop_result = self.framework.stop_test(test_config.test_id, "Test completed")
        self.assertTrue(stop_result)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)