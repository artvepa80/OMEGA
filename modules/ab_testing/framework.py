"""
OMEGA PRO AI v10.1 - A/B Testing Framework Core
==============================================

Main orchestrator for A/B testing of prediction improvements and system enhancements.
Provides safe, statistically sound testing of new features against baseline performance.
"""

import os
import json
import time
import logging
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

import numpy as np
import pandas as pd

from .feature_flags import FeatureFlagManager
from .statistical_analyzer import StatisticalAnalyzer
from .performance_comparator import PerformanceComparator
from .test_reporter import TestReporter


@dataclass
class ABTestConfig:
    """Configuration for an A/B test."""
    test_id: str
    name: str
    description: str
    control_config: Dict[str, Any]
    variant_config: Dict[str, Any]
    traffic_split: float = 0.5  # Percentage for variant (0.0-1.0)
    min_sample_size: int = 100
    max_duration_days: int = 30
    significance_level: float = 0.05
    power: float = 0.8
    metrics: List[str] = None
    enabled: bool = True
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = ["accuracy", "rare_number_detection", "latency", "confidence_score"]


@dataclass
class TestSample:
    """Individual test sample with prediction and outcome."""
    test_id: str
    variant: str  # "control" or "treatment"
    timestamp: datetime
    user_id: str
    prediction: List[int]
    actual_result: Optional[List[int]]
    metrics: Dict[str, float]
    metadata: Dict[str, Any]


class ABTestFramework:
    """
    Main A/B testing framework for OMEGA PRO AI.
    
    Manages multiple concurrent tests, handles traffic splitting,
    collects metrics, and provides statistical analysis.
    """
    
    def __init__(self, config_path: str = "config/ab_testing.json", 
                 results_path: str = "results/ab_testing"):
        self.config_path = config_path
        self.results_path = results_path
        self.logger = self._setup_logging()
        
        # Initialize components
        self.feature_flags = FeatureFlagManager()
        self.stats_analyzer = StatisticalAnalyzer()
        self.performance_comparator = PerformanceComparator()
        self.reporter = TestReporter()
        
        # Test management
        self.active_tests: Dict[str, ABTestConfig] = {}
        self.test_samples: Dict[str, List[TestSample]] = defaultdict(list)
        self.test_results: Dict[str, Dict] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize storage directories
        os.makedirs(self.results_path, exist_ok=True)
        os.makedirs("logs/ab_testing", exist_ok=True)
        
        # Load existing tests
        self._load_active_tests()
        
        self.logger.info("A/B Testing Framework initialized successfully")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup dedicated logging for A/B testing."""
        logger = logging.getLogger("omega_ab_testing")
        logger.setLevel(logging.INFO)
        
        # Create file handler
        handler = logging.FileHandler("logs/ab_testing/framework.log")
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger
    
    def create_test(self, config: ABTestConfig) -> bool:
        """
        Create and activate a new A/B test.
        
        Args:
            config: Test configuration
            
        Returns:
            bool: True if test created successfully
        """
        with self._lock:
            try:
                # Validate configuration
                if not self._validate_test_config(config):
                    return False
                
                # Check for conflicts with existing tests
                if self._has_test_conflicts(config):
                    self.logger.warning(f"Test {config.test_id} conflicts with existing tests")
                    return False
                
                # Store test configuration
                self.active_tests[config.test_id] = config
                self.test_samples[config.test_id] = []
                
                # Save to disk
                self._save_test_config(config)
                
                # Initialize feature flags
                self.feature_flags.create_flag(
                    f"ab_test_{config.test_id}",
                    enabled=config.enabled,
                    rollout_percentage=int(config.traffic_split * 100)
                )
                
                self.logger.info(f"Created A/B test: {config.test_id} - {config.name}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error creating test {config.test_id}: {str(e)}")
                return False
    
    def should_use_variant(self, test_id: str, user_id: str) -> bool:
        """
        Determine if a user should see the variant version.
        
        Args:
            test_id: Test identifier
            user_id: User identifier for consistent assignment
            
        Returns:
            bool: True if user should see variant
        """
        if test_id not in self.active_tests:
            return False
        
        test_config = self.active_tests[test_id]
        if not test_config.enabled:
            return False
        
        # Use feature flags for consistent assignment
        flag_name = f"ab_test_{test_id}"
        return self.feature_flags.is_enabled(flag_name, user_id)
    
    def record_prediction(self, test_id: str, user_id: str, 
                         prediction: List[int], variant: str = None,
                         metadata: Dict[str, Any] = None) -> str:
        """
        Record a prediction for A/B testing.
        
        Args:
            test_id: Test identifier
            user_id: User identifier
            prediction: Predicted numbers
            variant: Override variant assignment
            metadata: Additional data to store
            
        Returns:
            str: Sample ID for later result recording
        """
        if test_id not in self.active_tests:
            return None
        
        with self._lock:
            # Determine variant
            if variant is None:
                variant = "treatment" if self.should_use_variant(test_id, user_id) else "control"
            
            # Create sample
            sample = TestSample(
                test_id=test_id,
                variant=variant,
                timestamp=datetime.now(),
                user_id=user_id,
                prediction=prediction,
                actual_result=None,
                metrics={},
                metadata=metadata or {}
            )
            
            # Store sample
            self.test_samples[test_id].append(sample)
            sample_id = f"{test_id}_{len(self.test_samples[test_id]) - 1}"
            
            # Save to disk periodically
            if len(self.test_samples[test_id]) % 10 == 0:
                self._save_test_samples(test_id)
            
            return sample_id
    
    def record_result(self, test_id: str, sample_id: str, 
                     actual_result: List[int], metrics: Dict[str, float] = None):
        """
        Record actual lottery result for comparison.
        
        Args:
            test_id: Test identifier  
            sample_id: Sample identifier from record_prediction
            actual_result: Actual drawn numbers
            metrics: Additional computed metrics
        """
        if test_id not in self.test_samples:
            return
        
        try:
            # Extract sample index from ID
            sample_idx = int(sample_id.split('_')[-1])
            
            with self._lock:
                if sample_idx < len(self.test_samples[test_id]):
                    sample = self.test_samples[test_id][sample_idx]
                    sample.actual_result = actual_result
                    sample.metrics.update(metrics or {})
                    
                    # Compute standard metrics
                    sample.metrics.update(
                        self._compute_prediction_metrics(
                            sample.prediction, actual_result
                        )
                    )
                    
                    # Save updated sample
                    self._save_test_samples(test_id)
                    
        except (ValueError, IndexError) as e:
            self.logger.error(f"Error recording result for {sample_id}: {str(e)}")
    
    def get_test_status(self, test_id: str) -> Dict[str, Any]:
        """
        Get current status and preliminary results for a test.
        
        Args:
            test_id: Test identifier
            
        Returns:
            Dict with test status information
        """
        if test_id not in self.active_tests:
            return {"error": "Test not found"}
        
        test_config = self.active_tests[test_id]
        samples = self.test_samples[test_id]
        
        # Filter samples with results
        completed_samples = [s for s in samples if s.actual_result is not None]
        
        control_samples = [s for s in completed_samples if s.variant == "control"]
        treatment_samples = [s for s in completed_samples if s.variant == "treatment"]
        
        status = {
            "test_id": test_id,
            "name": test_config.name,
            "enabled": test_config.enabled,
            "total_samples": len(samples),
            "completed_samples": len(completed_samples),
            "control_samples": len(control_samples),
            "treatment_samples": len(treatment_samples),
            "min_sample_size": test_config.min_sample_size,
            "ready_for_analysis": len(completed_samples) >= test_config.min_sample_size
        }
        
        # Add preliminary results if enough samples
        if status["ready_for_analysis"]:
            try:
                analysis = self.stats_analyzer.analyze_test_results(
                    control_samples, treatment_samples, test_config.significance_level
                )
                status["preliminary_results"] = analysis
            except Exception as e:
                status["analysis_error"] = str(e)
        
        return status
    
    def analyze_test(self, test_id: str) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of A/B test results.
        
        Args:
            test_id: Test identifier
            
        Returns:
            Dict with detailed analysis results
        """
        if test_id not in self.active_tests:
            return {"error": "Test not found"}
        
        test_config = self.active_tests[test_id]
        samples = self.test_samples[test_id]
        
        # Filter completed samples
        completed_samples = [s for s in samples if s.actual_result is not None]
        control_samples = [s for s in completed_samples if s.variant == "control"]
        treatment_samples = [s for s in completed_samples if s.variant == "treatment"]
        
        if len(completed_samples) < test_config.min_sample_size:
            return {
                "error": "Insufficient sample size",
                "required": test_config.min_sample_size,
                "current": len(completed_samples)
            }
        
        try:
            # Statistical analysis
            stats_results = self.stats_analyzer.analyze_test_results(
                control_samples, treatment_samples, test_config.significance_level
            )
            
            # Performance comparison
            perf_results = self.performance_comparator.compare_variants(
                control_samples, treatment_samples, test_config.metrics
            )
            
            # Generate comprehensive report
            report = self.reporter.generate_test_report(
                test_config, stats_results, perf_results, completed_samples
            )
            
            # Store results
            self.test_results[test_id] = {
                "timestamp": datetime.now().isoformat(),
                "statistics": stats_results,
                "performance": perf_results,
                "report": report,
                "sample_count": len(completed_samples)
            }
            
            # Save results
            self._save_test_results(test_id)
            
            return self.test_results[test_id]
            
        except Exception as e:
            self.logger.error(f"Error analyzing test {test_id}: {str(e)}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    def stop_test(self, test_id: str, reason: str = "Manual stop") -> bool:
        """
        Stop an active A/B test.
        
        Args:
            test_id: Test identifier
            reason: Reason for stopping
            
        Returns:
            bool: True if stopped successfully
        """
        with self._lock:
            if test_id not in self.active_tests:
                return False
            
            try:
                # Disable test
                self.active_tests[test_id].enabled = False
                
                # Disable feature flag
                flag_name = f"ab_test_{test_id}"
                self.feature_flags.disable_flag(flag_name)
                
                # Perform final analysis
                final_results = self.analyze_test(test_id)
                
                # Log stop event
                self.logger.info(f"Stopped A/B test {test_id}: {reason}")
                
                # Save updated config
                self._save_test_config(self.active_tests[test_id])
                
                return True
                
            except Exception as e:
                self.logger.error(f"Error stopping test {test_id}: {str(e)}")
                return False
    
    def cleanup_old_tests(self, days_old: int = 90):
        """Remove old test data to save storage."""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        with self._lock:
            tests_to_remove = []
            for test_id, samples in self.test_samples.items():
                if not samples:
                    continue
                    
                # Check if all samples are old
                latest_sample = max(samples, key=lambda s: s.timestamp)
                if latest_sample.timestamp < cutoff_date:
                    tests_to_remove.append(test_id)
            
            for test_id in tests_to_remove:
                self.logger.info(f"Cleaning up old test data: {test_id}")
                del self.test_samples[test_id]
                if test_id in self.active_tests:
                    del self.active_tests[test_id]
                if test_id in self.test_results:
                    del self.test_results[test_id]
    
    def _validate_test_config(self, config: ABTestConfig) -> bool:
        """Validate test configuration."""
        if not config.test_id or not config.name:
            self.logger.error("Test ID and name are required")
            return False
        
        if not (0 < config.traffic_split < 1):
            self.logger.error("Traffic split must be between 0 and 1")
            return False
        
        if config.min_sample_size < 10:
            self.logger.error("Minimum sample size must be at least 10")
            return False
        
        return True
    
    def _has_test_conflicts(self, config: ABTestConfig) -> bool:
        """Check if test conflicts with existing active tests."""
        # For now, just check ID collision
        return config.test_id in self.active_tests
    
    def _compute_prediction_metrics(self, prediction: List[int], 
                                  actual: List[int]) -> Dict[str, float]:
        """Compute standard prediction metrics."""
        if not prediction or not actual:
            return {}
        
        # Convert to sets for easier comparison
        pred_set = set(prediction)
        actual_set = set(actual)
        
        # Exact match
        exact_match = 1.0 if pred_set == actual_set else 0.0
        
        # Partial matches (numbers in common)
        intersection = pred_set.intersection(actual_set)
        partial_matches = len(intersection)
        
        # Accuracy as percentage of correct predictions
        accuracy = partial_matches / max(len(actual_set), 1)
        
        # Rare number detection (numbers > 30 or < 10)
        rare_numbers_actual = [n for n in actual if n < 10 or n > 30]
        rare_numbers_predicted = [n for n in prediction if n < 10 or n > 30]
        
        rare_number_accuracy = 0.0
        if rare_numbers_actual:
            rare_correct = len(set(rare_numbers_actual).intersection(set(rare_numbers_predicted)))
            rare_number_accuracy = rare_correct / len(rare_numbers_actual)
        
        return {
            "exact_match": exact_match,
            "partial_matches": partial_matches,
            "accuracy": accuracy,
            "rare_number_detection": rare_number_accuracy,
            "confidence_score": 1.0 - abs(len(prediction) - len(actual)) / max(len(actual), 1)
        }
    
    def _load_active_tests(self):
        """Load active tests from disk."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    for test_data in data.get('active_tests', []):
                        config = ABTestConfig(**test_data)
                        self.active_tests[config.test_id] = config
                        
                        # Load samples if they exist
                        samples_file = f"{self.results_path}/{config.test_id}_samples.json"
                        if os.path.exists(samples_file):
                            self._load_test_samples(config.test_id)
                            
        except Exception as e:
            self.logger.error(f"Error loading active tests: {str(e)}")
    
    def _save_test_config(self, config: ABTestConfig):
        """Save test configuration to disk."""
        try:
            # Load existing data
            data = {"active_tests": []}
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
            
            # Update or add test config
            test_data = asdict(config)
            existing_tests = [t for t in data['active_tests'] if t['test_id'] != config.test_id]
            existing_tests.append(test_data)
            data['active_tests'] = existing_tests
            
            # Save back to disk
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
        except Exception as e:
            self.logger.error(f"Error saving test config: {str(e)}")
    
    def _save_test_samples(self, test_id: str):
        """Save test samples to disk."""
        try:
            samples = self.test_samples[test_id]
            samples_data = []
            
            for sample in samples:
                sample_dict = asdict(sample)
                sample_dict['timestamp'] = sample.timestamp.isoformat()
                samples_data.append(sample_dict)
            
            samples_file = f"{self.results_path}/{test_id}_samples.json"
            with open(samples_file, 'w') as f:
                json.dump(samples_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving samples for {test_id}: {str(e)}")
    
    def _load_test_samples(self, test_id: str):
        """Load test samples from disk."""
        try:
            samples_file = f"{self.results_path}/{test_id}_samples.json"
            if os.path.exists(samples_file):
                with open(samples_file, 'r') as f:
                    samples_data = json.load(f)
                
                samples = []
                for sample_dict in samples_data:
                    sample_dict['timestamp'] = datetime.fromisoformat(sample_dict['timestamp'])
                    samples.append(TestSample(**sample_dict))
                
                self.test_samples[test_id] = samples
                
        except Exception as e:
            self.logger.error(f"Error loading samples for {test_id}: {str(e)}")
    
    def _save_test_results(self, test_id: str):
        """Save test results to disk."""
        try:
            if test_id in self.test_results:
                results_file = f"{self.results_path}/{test_id}_results.json"
                with open(results_file, 'w') as f:
                    json.dump(self.test_results[test_id], f, indent=2, default=str)
                    
        except Exception as e:
            self.logger.error(f"Error saving results for {test_id}: {str(e)}")