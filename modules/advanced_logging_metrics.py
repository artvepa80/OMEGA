# OMEGA_PRO_AI_v10.1/modules/advanced_logging_metrics.py
"""
🚀 OMEGA PRO AI Advanced Logging & Metrics System v10.1
=====================================

Comprehensive logging and metrics tracking system for monitoring:
- Rare number prediction performance
- Exploration mode decisions and outcomes  
- Statistical analysis results and significance
- Consensus engine weight adjustments
- Filter pass/fail rates for combination types
- Prediction accuracy tracking over time
- System performance metrics (latency, memory usage)

Features:
- Thread-safe metric collection
- Real-time performance monitoring
- Statistical analysis logging
- Prediction accuracy tracking
- Exploration mode insights
- Rare number detection events
- Dashboard data collection
- Performance profiling
"""

import time
import psutil
import threading
import logging
import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from collections import defaultdict, deque, Counter
from dataclasses import dataclass, asdict, field
from pathlib import Path
import statistics
from contextlib import contextmanager
from functools import wraps

from utils.logging import get_logger


@dataclass
class RareNumberEvent:
    """Event tracking for rare number detection and application"""
    timestamp: float
    numbers: List[int]
    frequency_scores: Dict[int, float]
    boost_applied: float
    combination: List[int]
    source_model: str
    hit_count: int
    total_frequency: float
    detection_method: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExplorationDecision:
    """Event tracking for exploration mode decisions"""
    timestamp: float
    combination: List[int]
    exploration_boost: float
    anomaly_score: float
    diversity_bonus: float
    rare_count: int
    decision_factors: Dict[str, float]
    final_score: float
    rank_change: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StatisticalAnalysis:
    """Statistical analysis results and significance tests"""
    timestamp: float
    analysis_type: str
    test_name: str
    test_statistic: float
    p_value: float
    significance_level: float
    is_significant: bool
    effect_size: float
    confidence_interval: Tuple[float, float]
    sample_size: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsensusAdjustment:
    """Consensus engine weight adjustments and model performance"""
    timestamp: float
    model_name: str
    old_weight: float
    new_weight: float
    performance_score: float
    adjustment_reason: str
    accuracy_metrics: Dict[str, float]
    prediction_quality: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FilterPerformance:
    """Filter pass/fail rates and performance metrics"""
    timestamp: float
    filter_type: str
    combination_type: str
    total_processed: int
    passed: int
    failed: int
    pass_rate: float
    avg_score: float
    execution_time_ms: float
    rejection_reasons: Dict[str, int]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PredictionAccuracy:
    """Prediction accuracy tracking over time"""
    timestamp: float
    session_id: str
    prediction_set: List[List[int]]
    actual_result: List[int]
    hit_counts: Dict[str, int]  # exact, partial_5, partial_4, etc.
    accuracy_score: float
    model_contributions: Dict[str, float]
    rare_number_performance: Dict[str, Any]
    statistical_significance: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetric:
    """System performance metrics"""
    timestamp: float
    operation: str
    duration_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    model_name: Optional[str]
    combination_count: int
    success: bool
    error_details: Optional[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class AdvancedMetricsCollector:
    """
    Advanced metrics collector for OMEGA PRO AI system
    Provides comprehensive tracking of rare number predictions,
    exploration decisions, and system performance.
    """
    
    def __init__(self, retention_hours: int = 72, enable_dashboard_export: bool = True):
        self.retention_hours = retention_hours
        self.enable_dashboard_export = enable_dashboard_export
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Event storage
        self.rare_number_events: deque = deque(maxlen=50000)
        self.exploration_decisions: deque = deque(maxlen=25000)
        self.statistical_analyses: deque = deque(maxlen=10000)
        self.consensus_adjustments: deque = deque(maxlen=5000)
        self.filter_performances: deque = deque(maxlen=15000)
        self.prediction_accuracies: deque = deque(maxlen=5000)
        self.performance_metrics: deque = deque(maxlen=100000)
        
        # Real-time aggregations
        self._rare_number_stats = defaultdict(lambda: {'count': 0, 'total_boost': 0.0, 'avg_boost': 0.0})
        self._model_performance = defaultdict(lambda: {'predictions': 0, 'accuracy_sum': 0.0, 'avg_accuracy': 0.0})
        self._exploration_impact = defaultdict(float)
        self._filter_efficiency = defaultdict(lambda: {'total': 0, 'passed': 0, 'rate': 0.0})
        
        # Session tracking
        self.current_session_id = f"session_{int(time.time())}"
        self.session_start_time = time.time()
        self.session_predictions = 0
        self.session_rare_detections = 0
        
        # Logger
        self.logger = get_logger("AdvancedMetricsCollector")
        
        # Dashboard export path
        self.dashboard_path = Path("dashboard/metrics_data")
        self.dashboard_path.mkdir(parents=True, exist_ok=True)
        
        # Performance monitoring
        self._performance_thread = None
        self._monitoring_active = True
        
        self.logger.info("🚀 Advanced Metrics Collector initialized")
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background monitoring and cleanup tasks"""
        def background_worker():
            while self._monitoring_active:
                try:
                    self._cleanup_old_events()
                    self._update_aggregations()
                    if self.enable_dashboard_export:
                        self._export_dashboard_data()
                    time.sleep(300)  # Every 5 minutes
                except Exception as e:
                    self.logger.error(f"Background task error: {e}")
                    time.sleep(60)
        
        self._performance_thread = threading.Thread(target=background_worker, daemon=True)
        self._performance_thread.start()
    
    # === RARE NUMBER DETECTION LOGGING ===
    
    def log_rare_number_detection(self, numbers: List[int], frequency_scores: Dict[int, float],
                                boost_applied: float, combination: List[int], 
                                source_model: str, detection_method: str = "frequency_analysis",
                                **metadata):
        """Log rare number detection event with comprehensive details"""
        try:
            total_frequency = sum(frequency_scores.values()) / len(frequency_scores) if frequency_scores else 0.0
            hit_count = len([n for n in numbers if n in combination])
            
            event = RareNumberEvent(
                timestamp=time.time(),
                numbers=sorted(numbers),
                frequency_scores=frequency_scores,
                boost_applied=boost_applied,
                combination=sorted(combination),
                source_model=source_model,
                hit_count=hit_count,
                total_frequency=total_frequency,
                detection_method=detection_method,
                metadata=metadata
            )
            
            with self._lock:
                self.rare_number_events.append(event)
                self.session_rare_detections += 1
                
                # Update real-time stats
                for num in numbers:
                    stats = self._rare_number_stats[num]
                    stats['count'] += 1
                    stats['total_boost'] += boost_applied
                    stats['avg_boost'] = stats['total_boost'] / stats['count']
            
            self.logger.info(
                f"🔥 RARE NUMBER DETECTION: Numbers {numbers}, Boost: +{boost_applied:.3f}, "
                f"Model: {source_model}, Method: {detection_method}, Hits: {hit_count}/6"
            )
            
            # Log detailed frequency analysis
            if frequency_scores:
                freq_details = ", ".join([f"{num}: {score:.4f}" for num, score in frequency_scores.items()])
                self.logger.info(f"📊 Frequency Scores: {freq_details}")
            
        except Exception as e:
            self.logger.error(f"Error logging rare number detection: {e}")
    
    def get_rare_number_insights(self, lookback_hours: int = 24) -> Dict[str, Any]:
        """Get insights into rare number detection performance"""
        cutoff_time = time.time() - (lookback_hours * 3600)
        
        with self._lock:
            recent_events = [e for e in self.rare_number_events if e.timestamp >= cutoff_time]
        
        if not recent_events:
            return {"no_data": True}
        
        # Analyze rare number performance
        rare_number_freq = Counter()
        boost_distribution = []
        model_performance = defaultdict(list)
        detection_methods = Counter()
        
        for event in recent_events:
            for num in event.numbers:
                rare_number_freq[num] += 1
            boost_distribution.append(event.boost_applied)
            model_performance[event.source_model].append(event.boost_applied)
            detection_methods[event.detection_method] += 1
        
        insights = {
            "period_hours": lookback_hours,
            "total_detections": len(recent_events),
            "unique_rare_numbers": len(rare_number_freq),
            "most_detected_rare": rare_number_freq.most_common(10),
            "avg_boost": statistics.mean(boost_distribution) if boost_distribution else 0.0,
            "boost_percentiles": {
                "p50": statistics.median(boost_distribution) if boost_distribution else 0.0,
                "p90": np.percentile(boost_distribution, 90) if boost_distribution else 0.0,
                "p95": np.percentile(boost_distribution, 95) if boost_distribution else 0.0
            },
            "model_effectiveness": {
                model: {
                    "detections": len(boosts),
                    "avg_boost": statistics.mean(boosts) if boosts else 0.0,
                    "max_boost": max(boosts) if boosts else 0.0
                }
                for model, boosts in model_performance.items()
            },
            "detection_methods": dict(detection_methods),
            "timestamp": time.time()
        }
        
        return insights
    
    # === EXPLORATION MODE DECISION LOGGING ===
    
    def log_exploration_decision(self, combination: List[int], exploration_boost: float,
                               anomaly_score: float, diversity_bonus: float, rare_count: int,
                               decision_factors: Dict[str, float], final_score: float,
                               rank_change: float = 0.0, **metadata):
        """Log exploration mode decision with detailed reasoning"""
        try:
            decision = ExplorationDecision(
                timestamp=time.time(),
                combination=sorted(combination),
                exploration_boost=exploration_boost,
                anomaly_score=anomaly_score,
                diversity_bonus=diversity_bonus,
                rare_count=rare_count,
                decision_factors=decision_factors.copy(),
                final_score=final_score,
                rank_change=rank_change,
                metadata=metadata
            )
            
            with self._lock:
                self.exploration_decisions.append(decision)
                self._exploration_impact[f"boost_{exploration_boost:.2f}"] += 1
            
            if exploration_boost > 0 or anomaly_score > 0:
                self.logger.info(
                    f"🔍 EXPLORATION DECISION: Combo {combination}, "
                    f"Boost: +{exploration_boost:.3f}, Anomaly: +{anomaly_score:.3f}, "
                    f"Diversity: +{diversity_bonus:.3f}, Rare Count: {rare_count}, "
                    f"Final Score: {final_score:.3f}"
                )
                
                # Log decision factors
                factors_str = ", ".join([f"{k}: {v:.3f}" for k, v in decision_factors.items()])
                self.logger.info(f"📋 Decision Factors: {factors_str}")
                
                if rank_change != 0:
                    self.logger.info(f"📈 Rank Change: {rank_change:+.1f}")
            
        except Exception as e:
            self.logger.error(f"Error logging exploration decision: {e}")
    
    def get_exploration_insights(self, lookback_hours: int = 24) -> Dict[str, Any]:
        """Get insights into exploration mode effectiveness"""
        cutoff_time = time.time() - (lookback_hours * 3600)
        
        with self._lock:
            recent_decisions = [d for d in self.exploration_decisions if d.timestamp >= cutoff_time]
        
        if not recent_decisions:
            return {"no_data": True}
        
        # Analyze exploration effectiveness
        total_boost = sum(d.exploration_boost for d in recent_decisions)
        total_anomaly = sum(d.anomaly_score for d in recent_decisions)
        total_diversity = sum(d.diversity_bonus for d in recent_decisions)
        
        rare_count_dist = Counter(d.rare_count for d in recent_decisions)
        rank_changes = [d.rank_change for d in recent_decisions if d.rank_change != 0]
        
        insights = {
            "period_hours": lookback_hours,
            "total_exploration_decisions": len(recent_decisions),
            "decisions_with_boost": len([d for d in recent_decisions if d.exploration_boost > 0]),
            "total_exploration_boost": total_boost,
            "total_anomaly_score": total_anomaly,
            "total_diversity_bonus": total_diversity,
            "avg_rare_count": statistics.mean([d.rare_count for d in recent_decisions]) if recent_decisions else 0,
            "rare_count_distribution": dict(rare_count_dist),
            "rank_impact": {
                "decisions_with_rank_change": len(rank_changes),
                "avg_rank_change": statistics.mean(rank_changes) if rank_changes else 0.0,
                "max_rank_boost": max(rank_changes) if rank_changes else 0.0
            },
            "timestamp": time.time()
        }
        
        return insights
    
    # === STATISTICAL ANALYSIS LOGGING ===
    
    def log_statistical_analysis(self, analysis_type: str, test_name: str, test_statistic: float,
                                p_value: float, significance_level: float = 0.05,
                                effect_size: float = 0.0, confidence_interval: Tuple[float, float] = (0.0, 0.0),
                                sample_size: int = 0, **metadata):
        """Log statistical analysis results and significance tests"""
        try:
            is_significant = p_value < significance_level
            
            analysis = StatisticalAnalysis(
                timestamp=time.time(),
                analysis_type=analysis_type,
                test_name=test_name,
                test_statistic=test_statistic,
                p_value=p_value,
                significance_level=significance_level,
                is_significant=is_significant,
                effect_size=effect_size,
                confidence_interval=confidence_interval,
                sample_size=sample_size,
                metadata=metadata
            )
            
            with self._lock:
                self.statistical_analyses.append(analysis)
            
            significance_indicator = "✅ SIGNIFICANT" if is_significant else "❌ NOT SIGNIFICANT"
            self.logger.info(
                f"📊 STATISTICAL ANALYSIS: {analysis_type} - {test_name}, "
                f"Test Stat: {test_statistic:.4f}, p-value: {p_value:.6f}, "
                f"{significance_indicator}, Effect Size: {effect_size:.3f}"
            )
            
            if confidence_interval != (0.0, 0.0):
                self.logger.info(f"📈 Confidence Interval: {confidence_interval}")
                
            if sample_size > 0:
                self.logger.info(f"🔢 Sample Size: {sample_size}")
            
        except Exception as e:
            self.logger.error(f"Error logging statistical analysis: {e}")
    
    # === CONSENSUS ENGINE LOGGING ===
    
    def log_consensus_adjustment(self, model_name: str, old_weight: float, new_weight: float,
                               performance_score: float, adjustment_reason: str,
                               accuracy_metrics: Dict[str, float], **metadata):
        """Log consensus engine weight adjustments"""
        try:
            prediction_quality = accuracy_metrics.get('prediction_quality', 0.0)
            
            adjustment = ConsensusAdjustment(
                timestamp=time.time(),
                model_name=model_name,
                old_weight=old_weight,
                new_weight=new_weight,
                performance_score=performance_score,
                adjustment_reason=adjustment_reason,
                accuracy_metrics=accuracy_metrics.copy(),
                prediction_quality=prediction_quality,
                metadata=metadata
            )
            
            with self._lock:
                self.consensus_adjustments.append(adjustment)
            
            weight_change = new_weight - old_weight
            change_indicator = "📈 INCREASED" if weight_change > 0 else "📉 DECREASED" if weight_change < 0 else "➡️ UNCHANGED"
            
            self.logger.info(
                f"⚖️ CONSENSUS ADJUSTMENT: {model_name} weight {old_weight:.3f} → {new_weight:.3f} "
                f"({weight_change:+.3f}), {change_indicator}, Performance: {performance_score:.3f}"
            )
            
            self.logger.info(f"📝 Reason: {adjustment_reason}")
            
            # Log accuracy metrics
            acc_details = ", ".join([f"{k}: {v:.3f}" for k, v in accuracy_metrics.items()])
            self.logger.info(f"📊 Accuracy Metrics: {acc_details}")
            
        except Exception as e:
            self.logger.error(f"Error logging consensus adjustment: {e}")
    
    # === FILTER PERFORMANCE LOGGING ===
    
    def log_filter_performance(self, filter_type: str, combination_type: str, total_processed: int,
                             passed: int, failed: int, avg_score: float, execution_time_ms: float,
                             rejection_reasons: Dict[str, int], **metadata):
        """Log filter pass/fail rates and performance"""
        try:
            pass_rate = passed / total_processed if total_processed > 0 else 0.0
            
            performance = FilterPerformance(
                timestamp=time.time(),
                filter_type=filter_type,
                combination_type=combination_type,
                total_processed=total_processed,
                passed=passed,
                failed=failed,
                pass_rate=pass_rate,
                avg_score=avg_score,
                execution_time_ms=execution_time_ms,
                rejection_reasons=rejection_reasons.copy(),
                metadata=metadata
            )
            
            with self._lock:
                self.filter_performances.append(performance)
                
                # Update filter efficiency stats
                key = f"{filter_type}_{combination_type}"
                stats = self._filter_efficiency[key]
                stats['total'] += total_processed
                stats['passed'] += passed
                stats['rate'] = stats['passed'] / stats['total'] if stats['total'] > 0 else 0.0
            
            self.logger.info(
                f"🔍 FILTER PERFORMANCE: {filter_type} ({combination_type}), "
                f"Processed: {total_processed}, Pass Rate: {pass_rate:.1%}, "
                f"Avg Score: {avg_score:.3f}, Time: {execution_time_ms:.1f}ms"
            )
            
            # Log top rejection reasons
            if rejection_reasons:
                top_reasons = sorted(rejection_reasons.items(), key=lambda x: x[1], reverse=True)[:3]
                reasons_str = ", ".join([f"{reason}: {count}" for reason, count in top_reasons])
                self.logger.info(f"❌ Top Rejection Reasons: {reasons_str}")
            
        except Exception as e:
            self.logger.error(f"Error logging filter performance: {e}")
    
    # === PREDICTION ACCURACY TRACKING ===
    
    def log_prediction_accuracy(self, prediction_set: List[List[int]], actual_result: List[int],
                              model_contributions: Dict[str, float], 
                              rare_number_performance: Dict[str, Any], **metadata):
        """Log prediction accuracy results for continuous monitoring"""
        try:
            # Calculate hit counts
            hit_counts = {}
            for i, prediction in enumerate(prediction_set):
                hits = len(set(prediction) & set(actual_result))
                hit_type = f"prediction_{i}_hits_{hits}"
                hit_counts[hit_type] = hits
            
            # Overall accuracy score
            max_hits = max([len(set(pred) & set(actual_result)) for pred in prediction_set]) if prediction_set else 0
            accuracy_score = max_hits / 6.0 if actual_result else 0.0
            
            # Statistical significance (placeholder for future enhancement)
            statistical_significance = 0.0
            
            accuracy = PredictionAccuracy(
                timestamp=time.time(),
                session_id=self.current_session_id,
                prediction_set=[sorted(p) for p in prediction_set],
                actual_result=sorted(actual_result),
                hit_counts=hit_counts,
                accuracy_score=accuracy_score,
                model_contributions=model_contributions.copy(),
                rare_number_performance=rare_number_performance.copy(),
                statistical_significance=statistical_significance,
                metadata=metadata
            )
            
            with self._lock:
                self.prediction_accuracies.append(accuracy)
                self.session_predictions += 1
                
                # Update model performance stats
                for model, contribution in model_contributions.items():
                    stats = self._model_performance[model]
                    stats['predictions'] += 1
                    stats['accuracy_sum'] += accuracy_score * contribution
                    stats['avg_accuracy'] = stats['accuracy_sum'] / stats['predictions']
            
            self.logger.info(
                f"🎯 PREDICTION ACCURACY: Max Hits: {max_hits}/6 ({accuracy_score:.1%}), "
                f"Predictions: {len(prediction_set)}, Session: {self.current_session_id}"
            )
            
            # Log model contributions
            if model_contributions:
                contrib_details = ", ".join([f"{model}: {contrib:.3f}" for model, contrib in model_contributions.items()])
                self.logger.info(f"🤖 Model Contributions: {contrib_details}")
            
            # Log rare number performance
            if rare_number_performance.get('rare_hits', 0) > 0:
                self.logger.info(
                    f"🔥 Rare Number Performance: {rare_number_performance.get('rare_hits', 0)} hits, "
                    f"Boost Impact: {rare_number_performance.get('boost_impact', 0.0):.3f}"
                )
            
        except Exception as e:
            self.logger.error(f"Error logging prediction accuracy: {e}")
    
    # === PERFORMANCE METRICS ===
    
    @contextmanager
    def track_performance(self, operation: str, model_name: Optional[str] = None, 
                         combination_count: int = 0, **metadata):
        """Context manager for tracking operation performance"""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        start_cpu = psutil.cpu_percent()
        success = True
        error_details = None
        
        try:
            yield
        except Exception as e:
            success = False
            error_details = str(e)
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            end_memory = self._get_memory_usage()
            end_cpu = psutil.cpu_percent()
            
            memory_usage_mb = end_memory - start_memory
            cpu_usage = (start_cpu + end_cpu) / 2
            
            self._log_performance_metric(
                operation, duration_ms, memory_usage_mb, cpu_usage,
                model_name, combination_count, success, error_details, metadata
            )
    
    def _log_performance_metric(self, operation: str, duration_ms: float, memory_usage_mb: float,
                              cpu_usage_percent: float, model_name: Optional[str], 
                              combination_count: int, success: bool, error_details: Optional[str],
                              metadata: Dict[str, Any]):
        """Log performance metric"""
        try:
            metric = PerformanceMetric(
                timestamp=time.time(),
                operation=operation,
                duration_ms=duration_ms,
                memory_usage_mb=memory_usage_mb,
                cpu_usage_percent=cpu_usage_percent,
                model_name=model_name,
                combination_count=combination_count,
                success=success,
                error_details=error_details,
                metadata=metadata
            )
            
            with self._lock:
                self.performance_metrics.append(metric)
            
            status_indicator = "✅ SUCCESS" if success else "❌ FAILED"
            model_info = f", Model: {model_name}" if model_name else ""
            
            self.logger.info(
                f"⚡ PERFORMANCE: {operation} - {duration_ms:.1f}ms, "
                f"Memory: {memory_usage_mb:+.1f}MB, CPU: {cpu_usage_percent:.1f}%{model_info}, "
                f"Combos: {combination_count}, {status_indicator}"
            )
            
            if error_details:
                self.logger.error(f"❌ Error Details: {error_details}")
            
        except Exception as e:
            self.logger.error(f"Error logging performance metric: {e}")
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except:
            return 0.0
    
    # === DATA MANAGEMENT ===
    
    def _cleanup_old_events(self):
        """Clean up old events based on retention policy"""
        cutoff_time = time.time() - (self.retention_hours * 3600)
        
        with self._lock:
            # Clean up each event type
            self.rare_number_events = deque(
                [e for e in self.rare_number_events if e.timestamp >= cutoff_time],
                maxlen=self.rare_number_events.maxlen
            )
            self.exploration_decisions = deque(
                [d for d in self.exploration_decisions if d.timestamp >= cutoff_time],
                maxlen=self.exploration_decisions.maxlen
            )
            self.statistical_analyses = deque(
                [s for s in self.statistical_analyses if s.timestamp >= cutoff_time],
                maxlen=self.statistical_analyses.maxlen
            )
            self.consensus_adjustments = deque(
                [c for c in self.consensus_adjustments if c.timestamp >= cutoff_time],
                maxlen=self.consensus_adjustments.maxlen
            )
            self.filter_performances = deque(
                [f for f in self.filter_performances if f.timestamp >= cutoff_time],
                maxlen=self.filter_performances.maxlen
            )
            self.prediction_accuracies = deque(
                [p for p in self.prediction_accuracies if p.timestamp >= cutoff_time],
                maxlen=self.prediction_accuracies.maxlen
            )
            self.performance_metrics = deque(
                [p for p in self.performance_metrics if p.timestamp >= cutoff_time],
                maxlen=self.performance_metrics.maxlen
            )
    
    def _update_aggregations(self):
        """Update real-time aggregations"""
        with self._lock:
            # Update rare number stats
            for stats in self._rare_number_stats.values():
                if stats['count'] > 0:
                    stats['avg_boost'] = stats['total_boost'] / stats['count']
            
            # Update model performance
            for stats in self._model_performance.values():
                if stats['predictions'] > 0:
                    stats['avg_accuracy'] = stats['accuracy_sum'] / stats['predictions']
    
    def _export_dashboard_data(self):
        """Export metrics data for dashboard consumption"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Export current session summary
            session_summary = {
                "session_id": self.current_session_id,
                "start_time": self.session_start_time,
                "current_time": time.time(),
                "predictions_made": self.session_predictions,
                "rare_detections": self.session_rare_detections,
                "insights": {
                    "rare_numbers": self.get_rare_number_insights(lookback_hours=24),
                    "exploration": self.get_exploration_insights(lookback_hours=24),
                    "model_performance": dict(self._model_performance),
                    "filter_efficiency": dict(self._filter_efficiency)
                }
            }
            
            dashboard_file = self.dashboard_path / f"session_summary_{timestamp}.json"
            with open(dashboard_file, 'w') as f:
                json.dump(session_summary, f, indent=2, default=str)
            
        except Exception as e:
            self.logger.error(f"Error exporting dashboard data: {e}")
    
    def get_comprehensive_report(self, lookback_hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive metrics report"""
        report = {
            "report_timestamp": time.time(),
            "lookback_hours": lookback_hours,
            "session_info": {
                "session_id": self.current_session_id,
                "session_duration_hours": (time.time() - self.session_start_time) / 3600,
                "predictions_made": self.session_predictions,
                "rare_detections": self.session_rare_detections
            },
            "rare_number_insights": self.get_rare_number_insights(lookback_hours),
            "exploration_insights": self.get_exploration_insights(lookback_hours),
            "model_performance": dict(self._model_performance),
            "filter_efficiency": dict(self._filter_efficiency),
            "system_stats": {
                "events_stored": {
                    "rare_number_events": len(self.rare_number_events),
                    "exploration_decisions": len(self.exploration_decisions),
                    "statistical_analyses": len(self.statistical_analyses),
                    "consensus_adjustments": len(self.consensus_adjustments),
                    "filter_performances": len(self.filter_performances),
                    "prediction_accuracies": len(self.prediction_accuracies),
                    "performance_metrics": len(self.performance_metrics)
                }
            }
        }
        
        return report
    
    def export_report_to_file(self, file_path: Optional[str] = None, lookback_hours: int = 24):
        """Export comprehensive report to file"""
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"logs/omega_metrics_report_{timestamp}.json"
        
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            report = self.get_comprehensive_report(lookback_hours)
            
            with open(file_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.info(f"📊 Comprehensive metrics report exported to: {file_path}")
            
        except Exception as e:
            self.logger.error(f"Error exporting report: {e}")
    
    def stop(self):
        """Stop metrics collection and export final report"""
        self._monitoring_active = False
        
        # Export final session report
        self.export_report_to_file(lookback_hours=72)
        
        # Export final dashboard data
        if self.enable_dashboard_export:
            self._export_dashboard_data()
        
        self.logger.info("🛑 Advanced Metrics Collector stopped")


# === DECORATORS FOR AUTOMATIC METRICS COLLECTION ===

def track_rare_number_detection(metrics_collector: AdvancedMetricsCollector, 
                               source_model: str, detection_method: str = "frequency_analysis"):
    """Decorator to automatically track rare number detection events"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Extract rare number information from result
                if isinstance(result, dict) and 'rare_numbers' in result:
                    metrics_collector.log_rare_number_detection(
                        numbers=result.get('rare_numbers', []),
                        frequency_scores=result.get('frequency_scores', {}),
                        boost_applied=result.get('boost_applied', 0.0),
                        combination=result.get('combination', []),
                        source_model=source_model,
                        detection_method=detection_method,
                        function_name=func.__name__
                    )
                
                return result
                
            except Exception as e:
                metrics_collector.logger.error(f"Error in rare number detection tracking: {e}")
                raise
        return wrapper
    return decorator


def track_exploration_decision(metrics_collector: AdvancedMetricsCollector):
    """Decorator to automatically track exploration mode decisions"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Extract exploration information from result
                if isinstance(result, dict) and 'exploration_boost' in result:
                    metrics_collector.log_exploration_decision(
                        combination=result.get('combination', []),
                        exploration_boost=result.get('exploration_boost', 0.0),
                        anomaly_score=result.get('anomaly_score', 0.0),
                        diversity_bonus=result.get('diversity_bonus', 0.0),
                        rare_count=result.get('rare_count', 0),
                        decision_factors=result.get('decision_factors', {}),
                        final_score=result.get('final_score', 0.0),
                        rank_change=result.get('rank_change', 0.0),
                        function_name=func.__name__
                    )
                
                return result
                
            except Exception as e:
                metrics_collector.logger.error(f"Error in exploration decision tracking: {e}")
                raise
        return wrapper
    return decorator


# === GLOBAL METRICS COLLECTOR INSTANCE ===
_global_metrics_collector: Optional[AdvancedMetricsCollector] = None


def get_metrics_collector() -> AdvancedMetricsCollector:
    """Get or create global metrics collector instance"""
    global _global_metrics_collector
    if _global_metrics_collector is None:
        _global_metrics_collector = AdvancedMetricsCollector()
    return _global_metrics_collector


def initialize_metrics_collector(retention_hours: int = 72, enable_dashboard_export: bool = True) -> AdvancedMetricsCollector:
    """Initialize global metrics collector with specific settings"""
    global _global_metrics_collector
    _global_metrics_collector = AdvancedMetricsCollector(retention_hours, enable_dashboard_export)
    return _global_metrics_collector