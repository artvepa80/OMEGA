# OMEGA_PRO_AI_v10.1/modules/metrics_integration.py
"""
🔗 OMEGA PRO AI Metrics Integration Helper v10.1
===============================================

Helper module to seamlessly integrate advanced logging and metrics
across all OMEGA modules without breaking existing functionality.

This module provides backwards-compatible wrappers and integration
utilities to enable advanced metrics collection throughout the system.
"""

import logging
import functools
from typing import Dict, Any, List, Optional, Union
from contextlib import contextmanager


# Global metrics collector instance
_metrics_collector = None
_integration_enabled = True
_fallback_logger = None


def initialize_metrics_integration(enable_metrics: bool = True, 
                                 fallback_logger: Optional[logging.Logger] = None) -> bool:
    """
    Initialize metrics integration system
    
    Args:
        enable_metrics: Whether to enable advanced metrics collection
        fallback_logger: Logger to use if metrics collection fails
        
    Returns:
        bool: True if initialization successful
    """
    global _metrics_collector, _integration_enabled, _fallback_logger
    
    _integration_enabled = enable_metrics
    _fallback_logger = fallback_logger or logging.getLogger("MetricsIntegration")
    
    if not enable_metrics:
        _fallback_logger.info("📊 Metrics integration disabled by configuration")
        return True
    
    try:
        from modules.advanced_logging_metrics import get_metrics_collector
        _metrics_collector = get_metrics_collector()
        _fallback_logger.info("🚀 Advanced metrics integration initialized successfully")
        return True
    except ImportError as e:
        _fallback_logger.warning(f"⚠️ Advanced metrics not available: {e}")
        _integration_enabled = False
        return False
    except Exception as e:
        _fallback_logger.error(f"❌ Failed to initialize metrics integration: {e}")
        _integration_enabled = False
        return False


def get_integrated_metrics_collector():
    """Get the integrated metrics collector instance"""
    global _metrics_collector, _integration_enabled
    
    if not _integration_enabled or _metrics_collector is None:
        return None
    
    return _metrics_collector


def log_rare_number_event(numbers: List[int], boost_applied: float, 
                         combination: List[int], source_model: str,
                         **metadata) -> bool:
    """
    Log rare number detection event with fallback handling
    
    Args:
        numbers: Detected rare numbers
        boost_applied: Boost value applied
        combination: Full number combination
        source_model: Model that detected the rare numbers
        **metadata: Additional metadata
        
    Returns:
        bool: True if logged successfully
    """
    collector = get_integrated_metrics_collector()
    
    if collector is None:
        if _fallback_logger:
            _fallback_logger.info(
                f"🔥 RARE NUMBERS (fallback): {numbers} boost: +{boost_applied:.3f} "
                f"model: {source_model} combo: {combination}"
            )
        return False
    
    try:
        frequency_scores = metadata.get('frequency_scores', {})
        detection_method = metadata.get('detection_method', 'frequency_analysis')
        
        collector.log_rare_number_detection(
            numbers=numbers,
            frequency_scores=frequency_scores,
            boost_applied=boost_applied,
            combination=combination,
            source_model=source_model,
            detection_method=detection_method,
            **{k: v for k, v in metadata.items() if k not in ['frequency_scores', 'detection_method']}
        )
        return True
    except Exception as e:
        if _fallback_logger:
            _fallback_logger.warning(f"⚠️ Failed to log rare number event: {e}")
        return False


def log_exploration_event(combination: List[int], exploration_boost: float,
                         anomaly_score: float, diversity_bonus: float,
                         rare_count: int, **metadata) -> bool:
    """
    Log exploration mode decision with fallback handling
    
    Args:
        combination: Number combination
        exploration_boost: Exploration boost applied
        anomaly_score: Anomaly score
        diversity_bonus: Diversity bonus
        rare_count: Count of rare numbers
        **metadata: Additional metadata
        
    Returns:
        bool: True if logged successfully
    """
    collector = get_integrated_metrics_collector()
    
    if collector is None:
        if _fallback_logger:
            _fallback_logger.info(
                f"🔍 EXPLORATION (fallback): {combination} boost: +{exploration_boost:.3f} "
                f"anomaly: +{anomaly_score:.3f} diversity: +{diversity_bonus:.3f} "
                f"rare: {rare_count}"
            )
        return False
    
    try:
        decision_factors = metadata.get('decision_factors', {})
        final_score = metadata.get('final_score', 0.0)
        rank_change = metadata.get('rank_change', 0.0)
        
        collector.log_exploration_decision(
            combination=combination,
            exploration_boost=exploration_boost,
            anomaly_score=anomaly_score,
            diversity_bonus=diversity_bonus,
            rare_count=rare_count,
            decision_factors=decision_factors,
            final_score=final_score,
            rank_change=rank_change,
            **{k: v for k, v in metadata.items() if k not in ['decision_factors', 'final_score', 'rank_change']}
        )
        return True
    except Exception as e:
        if _fallback_logger:
            _fallback_logger.warning(f"⚠️ Failed to log exploration event: {e}")
        return False


def log_statistical_event(analysis_type: str, test_name: str, test_statistic: float,
                         p_value: float, **metadata) -> bool:
    """
    Log statistical analysis with fallback handling
    
    Args:
        analysis_type: Type of analysis performed
        test_name: Name of statistical test
        test_statistic: Test statistic value
        p_value: P-value from test
        **metadata: Additional metadata
        
    Returns:
        bool: True if logged successfully
    """
    collector = get_integrated_metrics_collector()
    
    if collector is None:
        if _fallback_logger:
            significance = "SIGNIFICANT" if p_value < 0.05 else "NOT SIGNIFICANT"
            _fallback_logger.info(
                f"📊 STATISTICS (fallback): {analysis_type} - {test_name} "
                f"stat: {test_statistic:.4f} p: {p_value:.6f} {significance}"
            )
        return False
    
    try:
        significance_level = metadata.get('significance_level', 0.05)
        effect_size = metadata.get('effect_size', 0.0)
        confidence_interval = metadata.get('confidence_interval', (0.0, 0.0))
        sample_size = metadata.get('sample_size', 0)
        
        collector.log_statistical_analysis(
            analysis_type=analysis_type,
            test_name=test_name,
            test_statistic=test_statistic,
            p_value=p_value,
            significance_level=significance_level,
            effect_size=effect_size,
            confidence_interval=confidence_interval,
            sample_size=sample_size,
            **{k: v for k, v in metadata.items() if k not in [
                'significance_level', 'effect_size', 'confidence_interval', 'sample_size'
            ]}
        )
        return True
    except Exception as e:
        if _fallback_logger:
            _fallback_logger.warning(f"⚠️ Failed to log statistical event: {e}")
        return False


def log_consensus_event(model_name: str, old_weight: float, new_weight: float,
                       performance_score: float, adjustment_reason: str,
                       **metadata) -> bool:
    """
    Log consensus adjustment with fallback handling
    
    Args:
        model_name: Name of the model
        old_weight: Previous weight value
        new_weight: New weight value
        performance_score: Performance score
        adjustment_reason: Reason for adjustment
        **metadata: Additional metadata
        
    Returns:
        bool: True if logged successfully
    """
    collector = get_integrated_metrics_collector()
    
    if collector is None:
        if _fallback_logger:
            weight_change = new_weight - old_weight
            _fallback_logger.info(
                f"⚖️ CONSENSUS (fallback): {model_name} {old_weight:.3f} → {new_weight:.3f} "
                f"({weight_change:+.3f}) perf: {performance_score:.3f} reason: {adjustment_reason}"
            )
        return False
    
    try:
        accuracy_metrics = metadata.get('accuracy_metrics', {})
        
        collector.log_consensus_adjustment(
            model_name=model_name,
            old_weight=old_weight,
            new_weight=new_weight,
            performance_score=performance_score,
            adjustment_reason=adjustment_reason,
            accuracy_metrics=accuracy_metrics,
            **{k: v for k, v in metadata.items() if k != 'accuracy_metrics'}
        )
        return True
    except Exception as e:
        if _fallback_logger:
            _fallback_logger.warning(f"⚠️ Failed to log consensus event: {e}")
        return False


@contextmanager
def track_performance_context(operation: str, model_name: Optional[str] = None,
                            combination_count: int = 0, **metadata):
    """
    Context manager for tracking performance with fallback
    
    Args:
        operation: Name of operation being tracked
        model_name: Name of model (optional)
        combination_count: Number of combinations processed
        **metadata: Additional metadata
    """
    collector = get_integrated_metrics_collector()
    
    if collector is None:
        # Simple timing fallback
        import time
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            if _fallback_logger:
                _fallback_logger.info(
                    f"⚡ PERFORMANCE (fallback): {operation} {duration*1000:.1f}ms "
                    f"model: {model_name or 'N/A'} combos: {combination_count}"
                )
    else:
        try:
            with collector.track_performance(operation, model_name, combination_count, **metadata):
                yield
        except Exception as e:
            if _fallback_logger:
                _fallback_logger.warning(f"⚠️ Performance tracking failed: {e}")
            yield


def get_metrics_summary(lookback_hours: int = 24) -> Dict[str, Any]:
    """
    Get metrics summary with fallback
    
    Args:
        lookback_hours: Hours to look back for metrics
        
    Returns:
        dict: Metrics summary or fallback info
    """
    collector = get_integrated_metrics_collector()
    
    if collector is None:
        return {
            "integration_status": "disabled",
            "fallback_mode": True,
            "lookback_hours": lookback_hours,
            "timestamp": "N/A"
        }
    
    try:
        return collector.get_comprehensive_report(lookback_hours)
    except Exception as e:
        if _fallback_logger:
            _fallback_logger.warning(f"⚠️ Failed to get metrics summary: {e}")
        return {
            "integration_status": "error",
            "error": str(e),
            "lookback_hours": lookback_hours
        }


def export_metrics_report(file_path: Optional[str] = None, lookback_hours: int = 24) -> bool:
    """
    Export metrics report with fallback
    
    Args:
        file_path: Path to export file (optional)
        lookback_hours: Hours to look back
        
    Returns:
        bool: True if export successful
    """
    collector = get_integrated_metrics_collector()
    
    if collector is None:
        if _fallback_logger:
            _fallback_logger.info("📊 Metrics export skipped - integration disabled")
        return False
    
    try:
        collector.export_report_to_file(file_path, lookback_hours)
        return True
    except Exception as e:
        if _fallback_logger:
            _fallback_logger.warning(f"⚠️ Failed to export metrics report: {e}")
        return False


# Decorator for automatic rare number detection logging
def auto_log_rare_numbers(source_model: str, detection_method: str = "auto"):
    """Decorator for automatic rare number detection logging"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Try to extract rare number information from result
                if isinstance(result, dict):
                    rare_numbers = result.get('rare_numbers', [])
                    boost_applied = result.get('boost_applied', 0.0)
                    combination = result.get('combination', [])
                    
                    if rare_numbers and boost_applied > 0:
                        log_rare_number_event(
                            numbers=rare_numbers,
                            boost_applied=boost_applied,
                            combination=combination,
                            source_model=source_model,
                            detection_method=detection_method,
                            function_name=func.__name__,
                            auto_detected=True
                        )
                
                return result
            except Exception as e:
                if _fallback_logger:
                    _fallback_logger.warning(f"⚠️ Auto-logging failed for {func.__name__}: {e}")
                return func(*args, **kwargs)  # Return original function result
        return wrapper
    return decorator


# Decorator for automatic exploration decision logging  
def auto_log_exploration(func):
    """Decorator for automatic exploration decision logging"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            
            # Try to extract exploration information from result
            if isinstance(result, dict):
                combination = result.get('combination', [])
                exploration_boost = result.get('exploration_boost', 0.0)
                anomaly_score = result.get('anomaly_score', 0.0)
                diversity_bonus = result.get('diversity_bonus', 0.0)
                rare_count = result.get('rare_count', 0)
                
                if exploration_boost > 0 or anomaly_score > 0:
                    log_exploration_event(
                        combination=combination,
                        exploration_boost=exploration_boost,
                        anomaly_score=anomaly_score,
                        diversity_bonus=diversity_bonus,
                        rare_count=rare_count,
                        function_name=func.__name__,
                        auto_detected=True
                    )
            
            return result
        except Exception as e:
            if _fallback_logger:
                _fallback_logger.warning(f"⚠️ Auto-logging failed for {func.__name__}: {e}")
            return func(*args, **kwargs)  # Return original function result
    return wrapper


# Initialize with default settings on import
initialize_metrics_integration()