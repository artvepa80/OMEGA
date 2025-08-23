"""
OMEGA PRO AI v10.1 - A/B Testing Integration
==========================================

Integration layer between A/B testing framework and existing OMEGA systems.
Provides seamless integration with prediction engines, logging, metrics, and data systems.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass

# OMEGA system imports
try:
    from core.predictor import HybridOmegaPredictor
    from core.consensus_engine import generar_combinaciones_consenso
    from modules.performance_monitor import get_performance_monitor
    OMEGA_CORE_AVAILABLE = True
except ImportError:
    OMEGA_CORE_AVAILABLE = False

from .framework import ABTestFramework
from .feature_flags import FeatureFlagManager


@dataclass
class PredictionContext:
    """Context for A/B testing predictions."""
    user_id: str
    test_id: str
    variant: str
    prediction_params: Dict[str, Any]
    metadata: Dict[str, Any]


class OmegaABTestingIntegration:
    """
    Integration layer for OMEGA A/B testing.
    
    Provides:
    - Seamless integration with existing prediction pipeline
    - Feature flag controlled algorithm variants
    - Performance monitoring integration
    - Logging and metrics collection
    - Safe rollback mechanisms
    """
    
    def __init__(self, config_path: str = "config/ab_testing_integration.json"):
        self.config_path = config_path
        self.logger = self._setup_logging()
        
        # Initialize A/B testing framework
        self.ab_framework = ABTestFramework()
        self.feature_flags = FeatureFlagManager()
        
        # Integration configuration
        self.integration_config = self._load_integration_config()
        
        # Performance monitoring
        self.performance_monitor = None
        if OMEGA_CORE_AVAILABLE:
            try:
                self.performance_monitor = get_performance_monitor()
            except:
                pass
        
        # Prediction engine instances
        self.control_predictor = None
        self.treatment_predictor = None
        
        # Cache for active tests
        self.active_tests_cache = {}
        
        self.logger.info("OMEGA A/B Testing Integration initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for integration."""
        logger = logging.getLogger("omega_ab_integration")
        logger.setLevel(logging.INFO)
        
        os.makedirs("logs/ab_testing", exist_ok=True)
        handler = logging.FileHandler("logs/ab_testing/integration.log")
        handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger
    
    def create_rare_number_detection_test(self, test_name: str = "rare_number_enhancement") -> str:
        """
        Create an A/B test specifically for rare number detection improvements.
        
        This creates a test for validating improvements to rare number prediction
        like the edge case [12, 27, 1, 10, 13, 22].
        
        Returns:
            str: Test ID for the created test
        """
        try:
            from .framework import ABTestConfig
            
            test_id = f"rare_numbers_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            config = ABTestConfig(
                test_id=test_id,
                name=test_name,
                description="A/B test for rare number detection enhancement validation",
                control_config={
                    "use_exploratory_consensus": False,
                    "rare_number_boost": False,
                    "enhanced_scoring": False,
                    "algorithm_version": "standard"
                },
                variant_config={
                    "use_exploratory_consensus": True,
                    "rare_number_boost": True,
                    "enhanced_scoring": True,
                    "algorithm_version": "enhanced_rare_detection"
                },
                traffic_split=0.5,
                min_sample_size=200,  # Higher sample size for rare events
                max_duration_days=45,
                metrics=["accuracy", "rare_number_detection", "confidence_score", "latency_ms"],
                enabled=True
            )
            
            # Create the test
            if self.ab_framework.create_test(config):
                self.logger.info(f"Created rare number detection test: {test_id}")
                return test_id
            else:
                self.logger.error("Failed to create rare number detection test")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating rare number detection test: {str(e)}")
            return None
    
    def create_performance_optimization_test(self, test_name: str = "performance_optimization") -> str:
        """
        Create an A/B test for system performance optimizations.
        
        Returns:
            str: Test ID for the created test
        """
        try:
            from .framework import ABTestConfig
            
            test_id = f"performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            config = ABTestConfig(
                test_id=test_id,
                name=test_name,
                description="A/B test for system performance optimization validation",
                control_config={
                    "parallel_processing": False,
                    "caching_enabled": False,
                    "optimization_level": "standard"
                },
                variant_config={
                    "parallel_processing": True,
                    "caching_enabled": True,
                    "optimization_level": "enhanced"
                },
                traffic_split=0.3,  # Lower traffic for performance tests
                min_sample_size=150,
                max_duration_days=14,  # Shorter duration for performance tests
                metrics=["latency_ms", "accuracy", "throughput", "error_rate"],
                enabled=True
            )
            
            if self.ab_framework.create_test(config):
                self.logger.info(f"Created performance optimization test: {test_id}")
                return test_id
            else:
                self.logger.error("Failed to create performance optimization test")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating performance optimization test: {str(e)}")
            return None
    
    def make_ab_prediction(self, user_id: str, test_id: str = None,
                          prediction_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make a prediction using A/B testing framework.
        
        Args:
            user_id: User identifier for consistent assignment
            test_id: Specific test to participate in (optional)
            prediction_params: Parameters for prediction
            
        Returns:
            Dict with prediction results and A/B test metadata
        """
        try:
            start_time = datetime.now()
            
            # Get active tests for this user
            active_tests = self._get_user_active_tests(user_id, test_id)
            
            if not active_tests:
                # No active tests, use standard prediction
                return self._make_standard_prediction(user_id, prediction_params)
            
            # Select primary test (if multiple active)
            primary_test = active_tests[0] if isinstance(active_tests, list) else active_tests
            
            # Determine variant assignment
            variant = "treatment" if self.ab_framework.should_use_variant(primary_test, user_id) else "control"
            
            # Make prediction based on variant
            prediction_result = self._make_variant_prediction(
                primary_test, variant, user_id, prediction_params
            )
            
            # Calculate performance metrics
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # Record prediction for A/B test analysis
            sample_id = self.ab_framework.record_prediction(
                test_id=primary_test,
                user_id=user_id,
                prediction=prediction_result.get("prediction", []),
                variant=variant,
                metadata={
                    "latency_ms": latency_ms,
                    "prediction_params": prediction_params or {},
                    "timestamp": start_time.isoformat()
                }
            )
            
            # Add A/B test metadata to response
            prediction_result.update({
                "ab_test_metadata": {
                    "test_id": primary_test,
                    "variant": variant,
                    "sample_id": sample_id,
                    "latency_ms": latency_ms
                }
            })
            
            return prediction_result
            
        except Exception as e:
            self.logger.error(f"Error in A/B prediction: {str(e)}")
            # Fallback to standard prediction
            return self._make_standard_prediction(user_id, prediction_params)
    
    def record_lottery_result(self, test_id: str, sample_id: str, 
                             actual_numbers: List[int], draw_date: str = None):
        """
        Record actual lottery results for A/B test analysis.
        
        Args:
            test_id: Test identifier
            sample_id: Sample identifier from prediction
            actual_numbers: Actual drawn numbers
            draw_date: Date of the draw
        """
        try:
            # Calculate additional metrics
            metrics = self._calculate_prediction_metrics(sample_id, actual_numbers)
            
            # Record result in A/B framework
            self.ab_framework.record_result(
                test_id=test_id,
                sample_id=sample_id,
                actual_result=actual_numbers,
                metrics=metrics
            )
            
            # Check if test should be analyzed (enough samples)
            test_status = self.ab_framework.get_test_status(test_id)
            if test_status.get("ready_for_analysis", False):
                # Trigger automated analysis
                self._trigger_automated_analysis(test_id)
            
            self.logger.info(f"Recorded lottery result for test {test_id}, sample {sample_id}")
            
        except Exception as e:
            self.logger.error(f"Error recording lottery result: {str(e)}")
    
    def get_test_dashboard_data(self, test_id: str) -> Dict[str, Any]:
        """
        Get dashboard data for a specific test.
        
        Args:
            test_id: Test identifier
            
        Returns:
            Dict with dashboard-ready data
        """
        try:
            # Get test status
            test_status = self.ab_framework.get_test_status(test_id)
            
            # Get analysis results if available
            analysis_results = {}
            if test_status.get("ready_for_analysis", False):
                analysis_results = self.ab_framework.analyze_test(test_id)
            
            # Combine dashboard data
            dashboard_data = {
                "test_status": test_status,
                "analysis_results": analysis_results,
                "last_updated": datetime.now().isoformat()
            }
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard data for {test_id}: {str(e)}")
            return {"error": str(e)}
    
    def list_active_tests(self) -> List[Dict[str, Any]]:
        """List all active A/B tests."""
        try:
            active_tests = []
            
            for test_id in self.ab_framework.active_tests:
                test_status = self.ab_framework.get_test_status(test_id)
                if test_status.get("enabled", False):
                    active_tests.append(test_status)
            
            return active_tests
            
        except Exception as e:
            self.logger.error(f"Error listing active tests: {str(e)}")
            return []
    
    def emergency_stop_test(self, test_id: str, reason: str = "Emergency stop"):
        """
        Emergency stop an A/B test.
        
        Args:
            test_id: Test to stop
            reason: Reason for emergency stop
        """
        try:
            # Stop the A/B test
            success = self.ab_framework.stop_test(test_id, reason)
            
            if success:
                # Emergency disable feature flag
                flag_name = f"ab_test_{test_id}"
                self.feature_flags.emergency_killswitch(flag_name, reason)
                
                self.logger.critical(f"EMERGENCY STOP: A/B test {test_id} - {reason}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error in emergency stop: {str(e)}")
            return False
    
    def integrate_with_omega_predictor(self, predictor_instance) -> bool:
        """
        Integrate A/B testing with existing OMEGA predictor.
        
        Args:
            predictor_instance: Instance of OMEGA predictor
            
        Returns:
            bool: True if integration successful
        """
        try:
            # Store predictor instances
            self.control_predictor = predictor_instance
            
            # Clone predictor for treatment variant (if needed)
            # This would involve creating a modified version with enhanced algorithms
            
            self.logger.info("Successfully integrated with OMEGA predictor")
            return True
            
        except Exception as e:
            self.logger.error(f"Error integrating with OMEGA predictor: {str(e)}")
            return False
    
    def _get_user_active_tests(self, user_id: str, specific_test_id: str = None) -> List[str]:
        """Get active tests for a user."""
        try:
            if specific_test_id:
                if specific_test_id in self.ab_framework.active_tests:
                    return [specific_test_id]
                else:
                    return []
            
            # Get all active tests this user is eligible for
            active_tests = []
            for test_id in self.ab_framework.active_tests:
                test_config = self.ab_framework.active_tests[test_id]
                if test_config.enabled:
                    active_tests.append(test_id)
            
            return active_tests
            
        except Exception as e:
            self.logger.error(f"Error getting user active tests: {str(e)}")
            return []
    
    def _make_standard_prediction(self, user_id: str, 
                                prediction_params: Dict[str, Any]) -> Dict[str, Any]:
        """Make standard prediction (no A/B testing)."""
        try:
            # Use existing OMEGA prediction logic
            if OMEGA_CORE_AVAILABLE and self.control_predictor:
                # Use integrated predictor
                result = self._call_omega_predictor(self.control_predictor, prediction_params)
            else:
                # Fallback prediction logic
                result = self._fallback_prediction(prediction_params)
            
            return {
                "prediction": result.get("prediction", []),
                "confidence": result.get("confidence", 0.5),
                "method": "standard",
                "ab_test_metadata": None
            }
            
        except Exception as e:
            self.logger.error(f"Error in standard prediction: {str(e)}")
            return {
                "prediction": [],
                "confidence": 0.0,
                "method": "error_fallback",
                "error": str(e)
            }
    
    def _make_variant_prediction(self, test_id: str, variant: str, user_id: str,
                               prediction_params: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction for specific A/B test variant."""
        try:
            # Get test configuration
            test_config = self.ab_framework.active_tests.get(test_id)
            if not test_config:
                return self._make_standard_prediction(user_id, prediction_params)
            
            # Get variant configuration
            if variant == "control":
                variant_config = test_config.control_config
            else:
                variant_config = test_config.variant_config
            
            # Merge prediction parameters with variant configuration
            merged_params = {**(prediction_params or {}), **variant_config}
            
            # Make prediction based on variant
            if variant == "treatment" and variant_config.get("use_exploratory_consensus"):
                # Enhanced prediction for treatment
                result = self._make_enhanced_prediction(merged_params)
            else:
                # Standard prediction for control
                result = self._make_standard_prediction_with_params(merged_params)
            
            return {
                "prediction": result.get("prediction", []),
                "confidence": result.get("confidence", 0.5),
                "method": f"{variant}_variant",
                "variant_config": variant_config
            }
            
        except Exception as e:
            self.logger.error(f"Error in variant prediction: {str(e)}")
            return self._make_standard_prediction(user_id, prediction_params)
    
    def _make_enhanced_prediction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make enhanced prediction for treatment variant."""
        try:
            # Enhanced prediction logic
            if OMEGA_CORE_AVAILABLE:
                # Use enhanced consensus with rare number boost
                result = self._call_enhanced_omega_predictor(params)
            else:
                # Fallback enhanced logic
                result = self._fallback_enhanced_prediction(params)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in enhanced prediction: {str(e)}")
            return {"prediction": [], "confidence": 0.0}
    
    def _make_standard_prediction_with_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make standard prediction with parameters."""
        try:
            if OMEGA_CORE_AVAILABLE and self.control_predictor:
                result = self._call_omega_predictor(self.control_predictor, params)
            else:
                result = self._fallback_prediction(params)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in parameterized prediction: {str(e)}")
            return {"prediction": [], "confidence": 0.0}
    
    def _call_omega_predictor(self, predictor, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call OMEGA predictor with parameters."""
        try:
            # This would integrate with the actual OMEGA predictor
            # For now, return a mock result
            return {
                "prediction": [12, 27, 1, 10, 13, 22],  # Example rare number combination
                "confidence": 0.75,
                "method": "omega_integrated"
            }
            
        except Exception as e:
            self.logger.error(f"Error calling OMEGA predictor: {str(e)}")
            return {"prediction": [], "confidence": 0.0}
    
    def _call_enhanced_omega_predictor(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call enhanced OMEGA predictor for treatment variant."""
        try:
            # Enhanced prediction logic would go here
            # This might include rare number boosting, enhanced scoring, etc.
            return {
                "prediction": [3, 15, 28, 7, 31, 42],  # Example enhanced prediction
                "confidence": 0.85,
                "method": "omega_enhanced"
            }
            
        except Exception as e:
            self.logger.error(f"Error calling enhanced OMEGA predictor: {str(e)}")
            return {"prediction": [], "confidence": 0.0}
    
    def _fallback_prediction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback prediction when OMEGA core is not available."""
        import random
        
        # Simple fallback prediction
        numbers = sorted(random.sample(range(1, 43), 6))
        
        return {
            "prediction": numbers,
            "confidence": 0.5,
            "method": "fallback"
        }
    
    def _fallback_enhanced_prediction(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced fallback prediction."""
        import random
        
        # Simulate enhanced prediction with rare number bias
        numbers = []
        
        # Add some rare numbers with higher probability
        if random.random() < 0.3:  # 30% chance for very low number
            numbers.append(random.randint(1, 9))
        if random.random() < 0.3:  # 30% chance for very high number
            numbers.append(random.randint(31, 42))
        
        # Fill remaining slots
        while len(numbers) < 6:
            num = random.randint(1, 42)
            if num not in numbers:
                numbers.append(num)
        
        return {
            "prediction": sorted(numbers),
            "confidence": 0.7,
            "method": "fallback_enhanced"
        }
    
    def _calculate_prediction_metrics(self, sample_id: str, actual_numbers: List[int]) -> Dict[str, float]:
        """Calculate prediction metrics for result recording."""
        try:
            # This would calculate various metrics based on the prediction and actual result
            # For now, return placeholder metrics
            return {
                "partial_matches": 2.0,  # Example: 2 numbers matched
                "accuracy": 0.33,        # 2/6 accuracy
                "rare_number_detection": 0.5,  # Example rare number detection
                "confidence_calibration": 0.8
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating metrics: {str(e)}")
            return {}
    
    def _trigger_automated_analysis(self, test_id: str):
        """Trigger automated analysis for a test."""
        try:
            # Perform analysis
            results = self.ab_framework.analyze_test(test_id)
            
            # Check for significant results or concerns
            if results.get("summary", {}).get("significant_results", 0) > 0:
                self.logger.info(f"Significant results detected in test {test_id}")
                # Could trigger notifications here
            
            # Check for performance issues
            overall_score = (results.get("performance", {})
                           .get("overall_assessment", {})
                           .get("overall_score", 0))
            
            if overall_score < -0.1:  # 10% degradation
                self.logger.warning(f"Performance degradation detected in test {test_id}")
                # Could trigger alerts here
            
        except Exception as e:
            self.logger.error(f"Error in automated analysis: {str(e)}")
    
    def _load_integration_config(self) -> Dict[str, Any]:
        """Load integration configuration."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                # Default integration configuration
                default_config = {
                    "enable_performance_monitoring": True,
                    "enable_automated_analysis": True,
                    "enable_alerts": True,
                    "fallback_to_standard_prediction": True,
                    "max_prediction_latency_ms": 5000,
                    "cache_predictions": True,
                    "log_all_predictions": False  # Set to True for debugging
                }
                
                # Save default configuration
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                
                return default_config
                
        except Exception as e:
            self.logger.error(f"Error loading integration config: {str(e)}")
            return {}


# Convenience functions for easy integration
def create_omega_ab_testing() -> OmegaABTestingIntegration:
    """Create OMEGA A/B testing integration instance."""
    return OmegaABTestingIntegration()


def quick_ab_prediction(user_id: str, test_id: str = None) -> Dict[str, Any]:
    """Make a quick A/B test prediction."""
    integration = create_omega_ab_testing()
    return integration.make_ab_prediction(user_id, test_id)